import hashlib
import json
import os
import platform
import re
import shutil
import signal
import stat
import subprocess
import sys
import time
import zipfile
import zlib
from datetime import datetime, timezone

READY_LINE = "serverk: bot process starting"

EXIT_FAILURE = 1

EXIT_CONFIG = 78

SYNC_MAX_AGE_SECONDS = 600

DEFAULT_STATE_DIR = "/home/container/.serverk"

DEFAULT_BRANCH = "main"

GIT_ASKPASS = "/serverk/git-askpass"

DETECT_TABLE_PATH = "/serverk/detect.json"

DETECT_TABLE_VERSION = 2

REPO_URL_PATTERN = re.compile(r"^https://[^\s@/]+/\S+$")

REPO_BRANCH_PATTERN = re.compile(r"^(?!HEAD$)(?!.*(?:\.\.|//|/\.|\.lock(?:/|$)|[/.]$))[A-Za-z0-9_][A-Za-z0-9._/-]{0,127}$")

REPO_REF_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")

ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

COMMIT_PATTERN = re.compile(r"[0-9a-f]{40,64}")

ROOT_DIRECTORY_PATTERN = re.compile(r"^(?![./])(?!.*(?:^|/)\.{1,2}(?:/|$))(?!.*//)[A-Za-z0-9._\-/]*[A-Za-z0-9._-]$")

ROOT_DIRECTORY_LENGTH_LIMIT = 255

LAUNCHER_KEYS = (
    "SERVERK_REPO_URL",
    "SERVERK_REPO_REF",
    "SERVERK_REPO_BRANCH",
    "SERVERK_GIT_TOKEN",
    "SERVERK_START_COMMAND",
    "SERVERK_INSTALL_COMMAND",
    "SERVERK_ROOT_DIRECTORY",
    "SERVERK_DEPLOYMENT_ID",
    "SERVERK_SNAPSHOT_ID",
    "SERVERK_STATE_DIR",
    "SERVERK_DETECT_TABLE",
    "SERVERK_LAUNCH_RESUME",
)

RESUME_KEY = "SERVERK_LAUNCH_RESUME"

BUILT_IN_TABLE = {
    "version": DETECT_TABLE_VERSION,
    "procfile": {
        "file": "Procfile",
        "line": r"^(worker|bot)\s*:\s*(.+)$",
        "processes": ["worker", "bot"],
    },
    "serverkJson": {
        "file": "serverk.json",
        "commandLengthLimit": 1024,
        "runtimes": ["node", "python"],
        "platforms": ["discord", "telegram"],
        "frameworks": [
            "discord-js",
            "eris",
            "oceanic-js",
            "grammy",
            "telegraf",
            "node-telegram-bot-api",
            "discord-py",
            "py-cord",
            "nextcord",
            "disnake",
            "hikari",
            "python-telegram-bot",
            "aiogram",
            "pyrogram",
            "telethon",
        ],
        "envLimit": 100,
        "envKey": "^[A-Za-z_][A-Za-z0-9_]*$",
        "envKeyLengthLimit": 64,
        "exampleLengthLimit": 256,
    },
    "python": {
        "startFiles": ["main.py", "bot.py", "app.py", "src/main.py", "src/bot.py"],
        "manifests": [
            {"file": "requirements.txt", "manager": "requirements"},
            {"file": "uv.lock", "manager": "uv"},
            {"file": "poetry.lock", "manager": "poetry"},
            {"file": "pdm.lock", "manager": "pdm"},
            {"file": "Pipfile", "manager": "pipenv"},
            {"file": "pyproject.toml", "manager": "project"},
        ],
        "installCommands": {
            "requirements": ["uv", "pip", "install", "-r", "requirements.txt"],
            "uv": ["uv", "sync", "--locked", "--no-dev"],
            "poetry": ["uv", "pip", "install", "."],
            "pdm": ["uv", "pip", "install", "."],
            "pipenv": ["pipenv", "install"],
            "project": ["uv", "pip", "install", "."],
        },
        "unhonouredManagers": ["poetry", "pdm"],
        "versionFiles": [
            {"file": ".python-version"},
            {"file": "runtime.txt", "prefix": "python-"},
            {"file": "Pipfile", "key": "python_version"},
            {"file": ".tool-versions", "tool": "python"},
        ],
        "defaultVersion": "3.12",
    },
}

TOOL_UV = "uv"

TOOL_PIPENV = "pipenv"

INSTALL_TOOLS = frozenset((TOOL_UV, TOOL_PIPENV))

UV_SYNC = (TOOL_UV, "sync")

PYPROJECT_FILE = "pyproject.toml"

MANIFEST_COMPANIONS = {
    "uv.lock": PYPROJECT_FILE,
    "poetry.lock": PYPROJECT_FILE,
    "pdm.lock": PYPROJECT_FILE,
    "Pipfile": "Pipfile.lock",
}

PACKAGE_MAIN = "__main__.py"

PACKAGE_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

SKIPPED_FOLDERS = frozenset(("node_modules", ".venv", "venv", "__pycache__", ".git", ".serverk", "site-packages"))

NOT_A_BOT_PACKAGE = frozenset(("tests", "test", "docs", "examples", "scripts"))

VERSION_NUMBER = re.compile(r"^v?([0-9]+(?:\.[0-9]+)*)")

PYTHON_VERSION_PARTS = 2

UV_CACHE_DIR = ("cache", "uv")

UV_PYTHON_INSTALL_DIR = ("cache", "python")

PIPENV_CACHE_DIR = ("cache", "pipenv")

NO_MANIFEST_LINE = "no requirements.txt, Pipfile or pyproject.toml, skipping dependencies"

VENV = ".venv"

VENV_PYTHON = ".venv/bin/python"

VENV_CONFIG = "pyvenv.cfg"

VENV_VERSION_KEYS = ("version", "version_info")

DEPLOY_MARKER = "deploy-requested"

LEGACY_REINSTALL_MARKER = "reinstall-requested"

DEPS_STAMP = "deps.json"

SYNC_STAMP = "sync.json"

DEPLOYMENT_STAMP = "deployment.json"

SOURCE_FILES = "source-files.json"

DIGEST_PATTERN = re.compile(r"[0-9a-f]{64}")

HASH_CHUNK_BYTES = 1024 * 1024

SNAPSHOTS_DIR = "snapshots"

HISTORY_DIR = "history"

SNAPSHOT_MAX_BYTES = 64 * 1024 * 1024

SNAPSHOT_EXPANDED_MAX_BYTES = 512 * 1024 * 1024

SNAPSHOT_ENTRY_LIMIT = 20000

HISTORY_KEEP = 10

SNAPSHOT_STALE_SECONDS = 15 * 60

PARTIAL_SUFFIX = ".partial"

STAGE_SYNC = "sync"

STAGE_SNAPSHOT = "snapshot"

STAGE_INSTALL = "install"

STAGE_START = "start"

SOURCE_GIT = "git"

SOURCE_SNAPSHOT = "snapshot"

SOURCE_LOCAL = "local"

OUTCOME_READY = "ready"

OUTCOME_FAILED = "failed"

STATE_ENTRY = ".serverk"

DEPENDENCY_ENTRIES = frozenset((STATE_ENTRY, "node_modules", ".venv", "__pycache__"))

SHELL_OPERATORS = frozenset(";&|()\n")

NO_EXEC_WORDS = frozenset(
    (
        ".",
        ":",
        "!",
        "[[",
        "{",
        "}",
        "alias",
        "bg",
        "break",
        "case",
        "cd",
        "command",
        "continue",
        "do",
        "done",
        "elif",
        "else",
        "esac",
        "eval",
        "exec",
        "exit",
        "export",
        "fg",
        "fi",
        "for",
        "function",
        "getopts",
        "hash",
        "if",
        "jobs",
        "local",
        "read",
        "readonly",
        "return",
        "select",
        "set",
        "shift",
        "source",
        "then",
        "times",
        "trap",
        "type",
        "typeset",
        "ulimit",
        "umask",
        "unalias",
        "unset",
        "until",
        "wait",
        "while",
    )
)

ASSIGNMENT_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")

GIT_HARDENING = (
    "-c",
    "core.hooksPath=/dev/null",
    "-c",
    "core.fsmonitor=false",
    "-c",
    "protocol.allow=never",
    "-c",
    "protocol.https.allow=always",
)

GIT_CONFIG = "[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n\tbare = false\n\tlogallrefupdates = false\n"

GIT_ENVIRONMENT_KEYS = ("PATH", "HOME", "TZ", "LANG", "LC_ALL", "LC_CTYPE")

STATE_TRACKED = "repository tracks .serverk"

JS_WHITESPACE = "\t\n\v\f\r                  　﻿"

JS_SPACE_CHARS = re.escape(JS_WHITESPACE)

JS_SPACE = re.compile(f"[{JS_SPACE_CHARS}]+")

DETAIL_LIMIT = 200

OUT_OF_MEMORY_DETAIL = "out-of-memory"

COMMIT_LENGTH = 12

REDACTED = "***"

HISTORY_IDENTITY = ("-c", "user.name=Serverk", "-c", "user.email=deploy@serverk.gg", "-c", "commit.gpgsign=false")

SYNC_HINT = "تعذّر سحب كود بوتك من الريبو. تأكد من وجود الريبو والفرع، وإذا كان الريبو خاصًا فتأكد أن تطبيق سيرفرك على GitHub لديه صلاحية الوصول إليه."

PINNED_HINT = "الكوميت المطلوب نشره غير موجود في الريبو، وقد يكون حُذف من الفرع. انشر من جديد من آخر كوميت."

TRACKED_STATE_HINT = "يحتوي الريبو على مجلد .serverk، وهذا الاسم محجوز لمنصة سيرفرك. احذف المجلد من الريبو وانشر من جديد."

LINK_HINT = "رابط الريبو أو اسم الفرع غير صحيح. استخدم رابط https كاملًا دون اسم مستخدم أو كلمة مرور، واسم فرع Git صحيحًا."

REQUEST_HINT = "طلب النشر ناقص أو غير صحيح. انشر من جديد من صفحة البوت."

OCCUPIED_HINT = "يحتوي مجلد بوتك على ملفات ليست من ريبو Git، ولذلك تعذّر سحب الريبو فوقها. احذف الملفات من مدير الملفات وانشر من جديد."

SNAPSHOT_MISSING_HINT = "نسخة الكود المطلوب نشرها غير موجودة. ارفعها من جديد ثم انشر."

SNAPSHOT_BROKEN_HINT = "تعذّر فك ضغط ملف الكود المرفوع. تأكد أنه ملف zip سليم وارفعه من جديد."

ROOT_HINT = "مجلد الكود المحدد غير موجود داخل ملفات بوتك. تأكد من اسم المجلد في إعدادات البوت وانشر من جديد."

INSTALL_HINT = "تعذّر تثبيت مكتبات بوتك. راجع السطور السابقة في الكونسول، ثم صحّح requirements.txt وانشر من جديد."

START_HINT = "لم نجد طريقة لتشغيل بوتك. أضف ملف main.py أو bot.py، أو اضبط أمر التشغيل من إعدادات البوت."

MEMORY_HINT = "نفدت الرام أثناء تثبيت مكتبات بوتك، فتوقف التثبيت. ارفع الباقة للحصول على رام أكثر، ثم انشر من جديد."


class LaunchFailure(Exception):
    def __init__(self, stage, arabic, english, detail, code=EXIT_FAILURE):
        super().__init__(english)
        self.stage = stage
        self.arabic = arabic
        self.english = english
        self.detail = detail
        self.code = code


def killed(code):
    return code == -signal.SIGKILL


def stage_failure(stage, hint, code, detail):
    if killed(code):
        return LaunchFailure(
            stage, MEMORY_HINT, f"{stage} failed: it ran out of memory and was stopped", OUT_OF_MEMORY_DETAIL
        )

    return LaunchFailure(stage, hint, f"{stage} failed: {detail}", detail)


class LaunchExit(Exception):
    def __init__(self, code):
        super().__init__(f"launcher exit {code}")
        self.code = code


class SnapshotRefused(Exception):
    pass


class SyncRefusal(Exception):
    def __init__(self, message, arabic):
        super().__init__(message)
        self.arabic = arabic


def say(line):
    print(f"serverk: {line}", flush=True)


def text(value):
    if not isinstance(value, str):
        return None

    trimmed = value.strip()

    return trimmed or None


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def parse_iso(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def short_commit(commit):
    return commit[:COMMIT_LENGTH] if commit else None


def one_line(detail):
    line = JS_SPACE.sub(" ", str(detail or "")).strip(JS_WHITESPACE)[:DETAIL_LIMIT]

    return line or "no detail"


def deployment_line(deployment, outcome, commit=None, stage=None, detail=None):
    if outcome == OUTCOME_READY:
        at = f" at {short_commit(commit)}" if commit else ""
        return f"serverk: deployment {deployment} ready{at}"

    return f"serverk: deployment {deployment} failed: {stage}: {one_line(detail)}"


def bot_environment(environment):
    return {key: value for key, value in environment.items() if key not in LAUNCHER_KEYS}


def read_text(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except (OSError, UnicodeDecodeError):
        return None


def read_text_replacing(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return None


def parse_object(raw):
    if raw is None:
        return None

    try:
        parsed = json.loads(raw)
    except ValueError:
        return None

    return parsed if isinstance(parsed, dict) else None


def read_json(path):
    return parse_object(read_text(path))


def write_json(path, value):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(value, indent="\t", ensure_ascii=False) + "\n")


def string_list(value):
    return value if isinstance(value, list) and all(isinstance(entry, str) for entry in value) else None


def positive_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def compiles(pattern):
    try:
        re.compile(pattern)
    except re.error:
        return False

    return True


def serverk_json_rules_of(rules):
    if not isinstance(rules, dict):
        return None

    limits = ("commandLengthLimit", "envLimit", "envKeyLengthLimit", "exampleLengthLimit")

    if (
        not isinstance(rules.get("file"), str)
        or not all(positive_int(rules.get(limit)) for limit in limits)
        or not string_list(rules.get("runtimes"))
        or not string_list(rules.get("platforms"))
        or not string_list(rules.get("frameworks"))
        or not isinstance(rules.get("envKey"), str)
        or not compiles(rules["envKey"])
    ):
        return None

    return {
        "file": rules["file"],
        "commandLengthLimit": rules["commandLengthLimit"],
        "runtimes": rules["runtimes"],
        "platforms": rules["platforms"],
        "frameworks": rules["frameworks"],
        "envLimit": rules["envLimit"],
        "envKey": rules["envKey"],
        "envKeyLengthLimit": rules["envKeyLengthLimit"],
        "exampleLengthLimit": rules["exampleLengthLimit"],
    }


def install_command_of(value):
    command = string_list(value)

    return command if command and all(command) and command[0] in INSTALL_TOOLS else None


def version_file_of(entry):
    if not isinstance(entry, dict) or not isinstance(entry.get("file"), str):
        return None

    spec = {"file": entry["file"]}

    for field in ("tool", "prefix", "key"):
        if field not in entry:
            continue

        if not isinstance(entry[field], str):
            return None

        spec[field] = entry[field]

    return spec if "key" not in spec or compiles(spec["key"]) else None


def python_rules_of(rules):
    if not isinstance(rules, dict):
        return None

    manifests = rules.get("manifests")
    commands = rules.get("installCommands")
    version_files = rules.get("versionFiles")

    if (
        not string_list(rules.get("startFiles"))
        or not isinstance(manifests, list)
        or not manifests
        or not all(
            isinstance(entry, dict) and isinstance(entry.get("file"), str) and isinstance(entry.get("manager"), str)
            for entry in manifests
        )
        or not isinstance(commands, dict)
        or not all(install_command_of(commands.get(entry["manager"])) for entry in manifests)
        or string_list(rules.get("unhonouredManagers")) is None
        or not isinstance(version_files, list)
        or not isinstance(rules.get("defaultVersion"), str)
    ):
        return None

    specs = [version_file_of(entry) for entry in version_files]

    if any(spec is None for spec in specs):
        return None

    return {
        "startFiles": rules["startFiles"],
        "manifests": [{"file": entry["file"], "manager": entry["manager"]} for entry in manifests],
        "installCommands": {entry["manager"]: commands[entry["manager"]] for entry in manifests},
        "unhonouredManagers": rules["unhonouredManagers"],
        "versionFiles": specs,
        "defaultVersion": rules["defaultVersion"],
    }


def table_of(raw):
    table = parse_object(raw)

    if not table or table.get("version") != DETECT_TABLE_VERSION:
        return None

    python = python_rules_of(table.get("python"))
    procfile = table.get("procfile")
    serverk_json = serverk_json_rules_of(table.get("serverkJson"))

    if (
        python is None
        or serverk_json is None
        or not isinstance(procfile, dict)
        or not isinstance(procfile.get("file"), str)
        or not isinstance(procfile.get("line"), str)
        or not compiles(procfile["line"])
        or not string_list(procfile.get("processes"))
    ):
        return None

    return {
        "version": DETECT_TABLE_VERSION,
        "procfile": {"file": procfile["file"], "line": procfile["line"], "processes": procfile["processes"]},
        "serverkJson": serverk_json,
        "python": python,
    }


def load_detect_table(env):
    return table_of(read_text(text(env.get("SERVERK_DETECT_TABLE")) or DETECT_TABLE_PATH)) or BUILT_IN_TABLE


def has_shell_operator(command):
    quote = None
    escaped = False

    for char in command:
        if escaped:
            escaped = False
            continue

        if char == "\\" and quote != "'":
            escaped = True
            continue

        if quote:
            if char == quote:
                quote = None
            continue

        if char in ("'", '"'):
            quote = char
            continue

        if char in SHELL_OPERATORS:
            return True

    return False


def command_words(command):
    words = []
    word = ""
    quote = None
    escaped = False
    started = False

    for char in command:
        if escaped:
            word += char
            escaped = False
            continue

        if char == "\\" and quote != "'":
            word += char
            escaped = True
            started = True
            continue

        if quote:
            word += char

            if char == quote:
                quote = None

            continue

        if char in ("'", '"'):
            word += char
            quote = char
            started = True
            continue

        if char in JS_WHITESPACE:
            if started:
                words.append(word)
                word = ""
                started = False

            continue

        word += char
        started = True

    if started:
        words.append(word)

    return words


def shell_command(command):
    if has_shell_operator(command):
        return ["sh", "-c", command]

    words = command_words(command)
    leading = next((index for index, word in enumerate(words) if not ASSIGNMENT_WORD.match(word)), None)

    if leading is None or words[leading] in NO_EXEC_WORDS:
        return ["sh", "-c", command]

    return ["sh", "-c", f"exec env {command}" if leading > 0 else f"exec {command}"]


def procfile_command(content, table=BUILT_IN_TABLE):
    pattern = re.compile(table["procfile"]["line"])
    entries = {}

    for line in content.split("\n"):
        match = pattern.match(line.strip(JS_WHITESPACE))

        if match and match.group(1) not in entries:
            entries[match.group(1)] = match.group(2).strip(JS_WHITESPACE)

    for process in table["procfile"]["processes"]:
        if entries.get(process):
            return entries[process]

    return None


def optional_choice(value, allowed):
    return value is None or (isinstance(value, str) and value in allowed)


def declared_command(value, limit):
    if value is None:
        return True, None

    command = value.strip(JS_WHITESPACE) if isinstance(value, str) else ""
    valid = bool(command) and len(command) <= limit and "\n" not in command

    return valid, command if valid else None


def declared_env_entry(entry, rules, env_key):
    def is_key(key):
        return isinstance(key, str) and len(key) <= rules["envKeyLengthLimit"] and env_key.fullmatch(key) is not None

    if isinstance(entry, str):
        return is_key(entry)

    if not isinstance(entry, dict):
        return False

    sensitive = entry.get("sensitive")
    example = entry.get("example")

    return (
        is_key(entry.get("key"))
        and (sensitive is None or isinstance(sensitive, bool))
        and (example is None or (isinstance(example, str) and len(example) <= rules["exampleLengthLimit"]))
    )


def refuse_constant(name):
    raise ValueError(f"{name} is not JSON")


def serverk_json_of(raw, table=BUILT_IN_TABLE):
    if raw is None:
        return None

    try:
        document = json.loads(raw, parse_constant=refuse_constant)
    except ValueError:
        return None

    if not isinstance(document, dict):
        return None

    rules = table["serverkJson"]
    env_key = re.compile(rules["envKey"])
    start_valid, start = declared_command(document.get("start"), rules["commandLengthLimit"])
    install_valid, install = declared_command(document.get("install"), rules["commandLengthLimit"])
    env = document.get("env")
    env_valid = env is None or (
        isinstance(env, list)
        and len(env) <= rules["envLimit"]
        and all(declared_env_entry(entry, rules, env_key) for entry in env)
    )

    if (
        not optional_choice(document.get("runtime"), rules["runtimes"])
        or not optional_choice(document.get("platform"), rules["platforms"])
        or not optional_choice(document.get("framework"), rules["frameworks"])
        or not start_valid
        or not install_valid
        or not env_valid
    ):
        return None

    return {"start": start, "install": install}


def bot_package_of(packages):
    names = sorted(
        {
            name
            for name in packages
            if PACKAGE_NAME_PATTERN.fullmatch(name) and name not in SKIPPED_FOLDERS and name not in NOT_A_BOT_PACKAGE
        }
    )

    return names[0] if len(names) == 1 else None


def detect_start(files, start_command=None, procfile=None, table=BUILT_IN_TABLE, serverk_json=None, packages=()):
    command = (start_command or "").strip()

    if command:
        return {"source": "start-command", "argv": shell_command(command)}

    declared = (serverk_json or {}).get("start")

    if declared:
        return {"source": "serverk-json", "argv": shell_command(declared)}

    declared = procfile_command(procfile, table) if procfile else None

    if declared:
        return {"source": "procfile", "argv": shell_command(declared)}

    for candidate in table["python"]["startFiles"]:
        if candidate in files:
            return {"source": "file", "argv": [VENV_PYTHON, "-u", candidate]}

    package = bot_package_of(packages)

    if package:
        return {"source": "package", "argv": [VENV_PYTHON, "-u", "-m", package]}

    return None


def version_from_file(content, spec):
    for raw in content.split("\n"):
        line = raw.strip(JS_WHITESPACE)

        if not line or line.startswith("#"):
            continue

        if "tool" in spec:
            words = JS_SPACE.split(line)

            if words[0] != spec["tool"]:
                continue

            line = words[1] if len(words) > 1 else ""

        if "key" in spec:
            match = re.match(f'^{spec["key"]}[{JS_SPACE_CHARS}]*=[{JS_SPACE_CHARS}]*"?([^"{JS_SPACE_CHARS}]+)', line)

            if not match:
                continue

            line = match.group(1)

        if "prefix" in spec:
            if not line.startswith(spec["prefix"]):
                return None

            line = line[len(spec["prefix"]) :]

        match = VERSION_NUMBER.match(line)

        return match.group(1) if match else None

    return None


def python_version_of(read, table=BUILT_IN_TABLE):
    for spec in table["python"]["versionFiles"]:
        content = read(spec["file"])

        if content is None:
            continue

        version = version_from_file(content, spec)

        if version is not None:
            return ".".join(version.split(".")[:PYTHON_VERSION_PARTS])

    return None


def managed_python_of(requested, running):
    if requested is None or running == requested or running.startswith(f"{requested}."):
        return None

    return requested


def detect_manager(files, table=BUILT_IN_TABLE):
    for entry in table["python"]["manifests"]:
        if entry["file"] in files:
            return {"manager": entry["manager"], "manifest": entry["file"]}

    return None


def dependency_hash(parts):
    return hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()


def sync_due(stamp, deploy, checkout, repo, branch, now):
    if deploy or not checkout or not stamp:
        return True

    if stamp.get("repo") != repo or stamp.get("branch") != branch:
        return True

    synced_at = parse_iso(stamp.get("syncedAt", ""))

    return synced_at is None or now - synced_at > SYNC_MAX_AGE_SECONDS


def parse_marker(raw):
    if raw is None:
        return None

    marker = parse_object(raw) or {}

    def valid(value, pattern):
        return value if isinstance(value, str) and pattern.fullmatch(value) else None

    return {
        "deployment": valid(marker.get("deployment"), ID_PATTERN),
        "ref": valid(marker.get("ref"), REPO_REF_PATTERN),
        "snapshot": valid(marker.get("snapshot"), ID_PATTERN),
        "reinstall": marker.get("reinstall") is True,
    }


def start_retry_of(request, stamp, synced):
    if (
        request["deploying"]
        or not isinstance(stamp, dict)
        or stamp.get("outcome") != OUTCOME_FAILED
        or stamp.get("stage") != STAGE_START
        or not isinstance(stamp.get("deployment"), str)
    ):
        return None

    synced = synced or {}

    if stamp.get("source") == SOURCE_GIT:
        return stamp if synced.get("source") == SOURCE_GIT and synced.get("commit") == stamp.get("commit") else None

    return stamp if synced.get("source") == SOURCE_LOCAL else None


def retry_start(context):
    stamp_path = os.path.join(context["state_dir"], DEPLOYMENT_STAMP)
    retry = start_retry_of(context["request"], read_json(stamp_path), context.get("synced"))

    if retry is None:
        return

    write_json(
        stamp_path,
        {**retry, "outcome": OUTCOME_READY, "stage": None, "detail": None, "finishedAt": now_iso(), "settled": False},
    )
    say(f"starting deployment {retry['deployment']} again, it goes live once the bot proves itself")


def resolve_request(env, marker, legacy_reinstall, stamp):
    marker_values = marker or {}
    deployment = text(env.get("SERVERK_DEPLOYMENT_ID")) or marker_values.get("deployment")
    implied = deployment is not None and (
        (stamp or {}).get("deployment") != deployment or (stamp or {}).get("outcome") != OUTCOME_READY
    )

    return {
        "deployment": deployment,
        "ref": text(env.get("SERVERK_REPO_REF")) or marker_values.get("ref"),
        "snapshot": text(env.get("SERVERK_SNAPSHOT_ID")) or marker_values.get("snapshot"),
        "reinstall": marker_values.get("reinstall") is True or legacy_reinstall,
        "deploying": marker is not None or legacy_reinstall or implied,
    }


def occupied_entries(entries):
    return [entry for entry in entries if entry not in DEPENDENCY_ENTRIES]


def take_marker(path):
    if not os.path.exists(path):
        return None

    raw = read_text(path) or ""

    try:
        os.remove(path)
    except FileNotFoundError:
        pass

    return raw


def redactor(secret):
    if not secret:
        return lambda line: line

    return lambda line: line.replace(secret, REDACTED)


NOISE_PREFIXES = (
    re.compile(r"npm (?:error|ERR!) A complete log of this run can be found in"),
    re.compile(r"npm notice\b"),
    re.compile(r"(?:note|hint):"),
    re.compile(r"\[notice\]"),
    re.compile(r"[╰│]"),
)

NOISE_LINES = (
    re.compile(r"npm (?:error|ERR!)"),
    re.compile(r"npm (?:error|ERR!)\s+\S*_logs/\S*\.log"),
    re.compile(r"\[end of output\]"),
    re.compile(r"\[\d+ lines? of output\]"),
)

NPM_CODE = re.compile(r"npm (?:error|ERR!) code \S+")

NPM_DESCRIBED = re.compile(r"npm (?:error|ERR!) (?:404 \S|ERESOLVE\b)")

NPM_BARE_404 = re.compile(r"npm (?:error|ERR!) 404")

NPM_PREFIX = re.compile(r"npm (?:error|ERR!) ")

PIP_ERROR = re.compile(r"ERROR: \S")

UV_HEADLINE = re.compile(r"× \S")

UV_CAUSE = re.compile(r"[├╰]─▶ (.+)")


class DetailPicker:
    def __init__(self):
        self.code = None
        self.reason = None
        self.described = None
        self.pip_error = None
        self.last = None
        self.headline = None
        self.uv = None
        self.continuing = False

    def read_uv(self, text):
        cause = UV_CAUSE.match(text)

        if cause and self.uv is None and self.headline is not None:
            self.uv = f"{self.headline.rstrip(':')}: {cause.group(1)}"
            self.continuing = True
            return True

        if (
            self.continuing
            and text
            and not cause
            and not UV_HEADLINE.match(text)
            and not any(pattern.match(text) for pattern in NOISE_PREFIXES)
        ):
            self.uv = f"{self.uv} {text}"
            return True

        self.continuing = False
        self.headline = text if UV_HEADLINE.match(text) else None

        return False

    def add(self, line):
        text = line.strip()

        if self.read_uv(text):
            return

        if (
            not text
            or any(pattern.match(text) for pattern in NOISE_PREFIXES)
            or any(pattern.fullmatch(text) for pattern in NOISE_LINES)
        ):
            return

        self.last = text

        if self.code is None:
            if NPM_CODE.fullmatch(text):
                self.code = text
            elif self.described is None and NPM_DESCRIBED.match(text):
                self.described = text
            elif self.pip_error is None and PIP_ERROR.match(text):
                self.pip_error = text

            return

        if self.reason is None and not NPM_BARE_404.fullmatch(text):
            self.reason = NPM_PREFIX.sub("", text, count=1)

    def pick(self):
        if self.code is not None:
            return self.code if self.reason is None else f"{self.code}: {self.reason}"

        return self.described or self.uv or self.pip_error or self.last


def failure_detail(lines):
    picker = DetailPicker()

    for line in lines:
        picker.add(line)

    return picker.pick()


def run(argv, cwd, env, secret=None, echo=True, capture=False):
    redact = redactor(secret)
    last = None

    try:
        child = subprocess.Popen(
            argv,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE if capture else subprocess.STDOUT,
            text=True,
            errors="replace",
        )
    except OSError as error:
        return 127, redact(str(error))[:DETAIL_LIMIT], ""

    if capture:
        output, errors = child.communicate()
        detail = failure_detail(redact(line) for line in (errors or "").splitlines())
        return child.returncode, (detail or f"{argv[0]} exited with code {child.returncode}")[:DETAIL_LIMIT], output

    picker = DetailPicker()

    for raw in child.stdout:
        shown = redact(raw.rstrip("\r\n"))

        if echo:
            print(shown, flush=True)

        picker.add(shown)

        if shown.strip():
            last = shown.strip()

    child.stdout.close()
    code = child.wait()
    detail = picker.pick() or f"{argv[0]} exited with code {code}"

    return code, detail[:DETAIL_LIMIT], last or ""


def repo_host(repo):
    return repo[len("https://") :].split("/")[0] if isinstance(repo, str) and repo.startswith("https://") else ""


def git_environment(env, git_token, repo):
    git_env = {key: env[key] for key in GIT_ENVIRONMENT_KEYS if isinstance(env.get(key), str)}
    git_env.update({"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0"})

    if git_token:
        git_env["GIT_ASKPASS"] = GIT_ASKPASS
        git_env["SERVERK_GIT_TOKEN"] = git_token
        git_env["SERVERK_GIT_HOST"] = repo_host(repo)

    return git_env


def git_argv(*args):
    return ["git", *GIT_HARDENING, *args]


def write_git_config(git_dir):
    with open(os.path.join(git_dir, "config"), "w", encoding="utf-8") as handle:
        handle.write(GIT_CONFIG)


def rev_parse(app_dir, env, name, git_dir=None):
    prefix = [f"--git-dir={git_dir}"] if git_dir else []
    code, _, output = run(git_argv(*prefix, "rev-parse", "--verify", "--quiet", name), app_dir, env, echo=False)

    return output if code == 0 and re.fullmatch(r"[0-9a-f]{40,64}", output) else None


def prune_empty_parents(app_dir, directory):
    current = directory

    while current != app_dir and current.startswith(app_dir + os.sep):
        try:
            os.rmdir(current)
        except OSError:
            return

        current = os.path.dirname(current)


def inside_of(base, path):
    return path == base or path.startswith(base + os.sep)


def remove_files(app_dir, files):
    base = os.path.realpath(app_dir)

    for name in files:
        path = os.path.normpath(os.path.join(app_dir, name))

        if not path.startswith(app_dir + os.sep):
            continue

        parent = os.path.realpath(os.path.dirname(path))

        if not inside_of(base, parent):
            continue

        target = os.path.join(parent, os.path.basename(path))

        if os.path.isdir(target) and not os.path.islink(target):
            continue

        try:
            os.remove(target)
        except FileNotFoundError:
            continue

        prune_empty_parents(app_dir, os.path.dirname(path))


def tree_files(app_dir, env, git_dir, treeish):
    prefix = [f"--git-dir={git_dir}"] if git_dir else []
    code, detail, output = run(git_argv(*prefix, "ls-tree", "-r", "-z", treeish), app_dir, env, echo=False, capture=True)

    if code != 0:
        raise RuntimeError(detail)

    entries = (entry.split("\t", 1) for entry in output.split("\0") if "\t" in entry)

    return [name for meta, name in entries if meta.split(" ")[1:2] == ["blob"]]


def owned_file(name):
    segments = name.split("/")

    return "\0" not in name and segments[0] != STATE_ENTRY and all(part not in ("", ".", "..", ".git") for part in segments)


def digest_of(path):
    try:
        info = os.lstat(path)
        digest = hashlib.sha256()

        if stat.S_ISLNK(info.st_mode):
            digest.update(f"link:{os.readlink(path)}".encode())
            return digest.hexdigest()

        if not stat.S_ISREG(info.st_mode):
            return None

        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(HASH_CHUNK_BYTES), b""):
                digest.update(chunk)

        return digest.hexdigest()
    except (OSError, ValueError):
        return None


def read_source_files(state_dir):
    files = (read_json(os.path.join(state_dir, SOURCE_FILES)) or {}).get("files")

    if not isinstance(files, dict):
        return None

    return {
        name: digest
        for name, digest in files.items()
        if owned_file(name) and isinstance(digest, str) and DIGEST_PATTERN.fullmatch(digest)
    }


def write_source_files(state_dir, app_dir, files):
    digests = ((name, digest_of(os.path.join(app_dir, name))) for name in sorted(set(files)))
    write_json(os.path.join(state_dir, SOURCE_FILES), {"files": {name: digest for name, digest in digests if digest}})


def dropped_files(app_dir, previous, carried):
    kept = set(carried)
    unchanged = []
    changed = 0

    for name, digest in previous.items():
        if name in kept:
            continue

        current = digest_of(os.path.join(app_dir, name))

        if current == digest:
            unchanged.append(name)
        elif current is not None:
            changed += 1

    return {"unchanged": unchanged, "changed": changed}


def clear_way(app_dir, carried):
    removed = 0

    for name in carried:
        segments = name.split("/")

        for depth in range(1, len(segments) + 1):
            path = os.path.join(app_dir, *segments[:depth])

            try:
                directory = stat.S_ISDIR(os.lstat(path).st_mode)
            except OSError:
                break

            if directory == (depth == len(segments)):
                if directory:
                    shutil.rmtree(path)
                else:
                    os.remove(path)

                removed += 1
                break

    if removed:
        say(f"removed {removed} {'path' if removed == 1 else 'paths'} in the way of the source's files")


def files_word(count):
    return "file" if count == 1 else "files"


def remove_dropped(app_dir, dropped):
    remove_files(app_dir, dropped["unchanged"])
    removed = sum(1 for name in dropped["unchanged"] if not os.path.lexists(os.path.join(app_dir, name)))

    if removed:
        say(f"removed {removed} {files_word(removed)} the source no longer carries")

    if dropped["changed"]:
        say(f"kept {dropped['changed']} changed {files_word(dropped['changed'])} the source no longer carries")


def leave_git_source(context):
    git_dir = os.path.join(context["app_dir"], ".git")

    if not os.path.isdir(git_dir):
        return

    say("switching from the repository to uploaded code")
    shutil.rmtree(git_dir, ignore_errors=True)


def leave_snapshot_source(context):
    history_dir = os.path.join(context["state_dir"], HISTORY_DIR)

    if not os.path.isdir(history_dir):
        return

    say("switching from uploaded code to the repository")
    shutil.rmtree(history_dir, ignore_errors=True)


def exclude_state_directory(app_dir):
    info = os.path.join(app_dir, ".git", "info")
    exclude = os.path.join(info, "exclude")
    current = read_text(exclude) or ""

    if f"/{STATE_ENTRY}/" in current.split("\n"):
        return

    os.makedirs(info, exist_ok=True)
    separator = "" if current == "" or current.endswith("\n") else "\n"

    with open(exclude, "w", encoding="utf-8") as handle:
        handle.write(f"{current}{separator}/{STATE_ENTRY}/\n")


def managed_source(stamp):
    return bool(stamp) and stamp.get("source") in (SOURCE_GIT, SOURCE_SNAPSHOT)


def sync_git(context):
    app_dir = context["app_dir"]
    state_dir = context["state_dir"]
    env = context["env"]
    request = context["request"]
    repo = text(env.get("SERVERK_REPO_URL"))
    branch = text(env.get("SERVERK_REPO_BRANCH")) or DEFAULT_BRANCH
    ref = request["ref"]

    if not REPO_URL_PATTERN.fullmatch(repo) or not REPO_BRANCH_PATTERN.fullmatch(branch):
        raise LaunchFailure(
            STAGE_SYNC,
            LINK_HINT,
            "sync failed: the repository link must be a full https link with no username or password, and the branch a valid Git branch name",
            "the repository link or branch is not valid",
            EXIT_CONFIG,
        )

    if ref is not None and not REPO_REF_PATTERN.fullmatch(ref):
        raise LaunchFailure(
            STAGE_SYNC,
            REQUEST_HINT,
            "sync failed: the commit to deploy is not a full commit hash",
            "the commit is not a full hash",
            EXIT_CONFIG,
        )

    git_token = text(env.get("SERVERK_GIT_TOKEN"))
    stamp_path = os.path.join(state_dir, SYNC_STAMP)
    stamp = read_json(stamp_path)
    git_dir = os.path.join(app_dir, ".git")
    checkout = os.path.isdir(git_dir)
    git_env = git_environment(env, git_token, repo)

    if checkout:
        write_git_config(git_dir)

    before = rev_parse(app_dir, git_env, "HEAD") if checkout else None
    now = datetime.now(timezone.utc).timestamp()

    if ref is not None:
        if not request["deploying"] and checkout and (stamp or {}).get("repo") == repo and before == ref:
            say(f"code is at {short_commit(ref)}")
            return {"source": SOURCE_GIT, "commit": before}
    elif not sync_due(stamp, request["deploying"], checkout, repo, branch, now):
        say("code synced a moment ago, skipping the pull")
        return {"source": SOURCE_GIT, "commit": before}

    if not checkout and not managed_source(stamp) and occupied_entries(os.listdir(app_dir)):
        raise LaunchFailure(
            STAGE_SYNC,
            OCCUPIED_HINT,
            "sync failed: your bot folder already holds files that are not a Git checkout. Delete them and deploy again",
            "the bot folder holds files that are not a Git checkout",
            EXIT_CONFIG,
        )

    def git(*args):
        code, detail, _ = run(git_argv(*args), app_dir, git_env, secret=git_token)

        if code != 0:
            raise RuntimeError(detail)

    def tracks_state(treeish):
        code, _, output = run(
            git_argv("ls-tree", "--name-only", treeish, "--", STATE_ENTRY), app_dir, git_env, echo=False, capture=True
        )

        return code == 0 and bool(output.strip())

    previous = read_source_files(state_dir) or {}

    say(f"fetching {repo} at {short_commit(ref)}" if ref else f"pulling {repo} ({branch})")

    created = False

    try:
        if not checkout:
            git("init", "--quiet", f"--initial-branch={branch}")
            created = True
            write_git_config(git_dir)

        exclude_state_directory(app_dir)

        target = "FETCH_HEAD"

        if ref is None:
            git("fetch", "--quiet", "--no-tags", "--depth", "1", repo, branch)
        elif before == ref:
            target = ref
        else:
            try:
                git("fetch", "--quiet", "--no-tags", "--depth", "1", repo, ref)
            except RuntimeError as pinned:
                git("fetch", "--quiet", "--no-tags", "--depth", "1", repo, branch)

                if rev_parse(app_dir, git_env, "FETCH_HEAD") != ref:
                    raise SyncRefusal(
                        f"commit {short_commit(ref)} is not in the repository ({one_line(pinned)})", PINNED_HINT
                    ) from pinned

        if tracks_state(target):
            raise SyncRefusal(STATE_TRACKED, TRACKED_STATE_HINT)

        carried = tree_files(app_dir, git_env, None, target)
        clear_way(app_dir, carried)
        dropped = dropped_files(app_dir, previous, carried)
        git("read-tree", "--empty")

        if ref is None:
            git("checkout", "--quiet", "--force", "-B", branch, "FETCH_HEAD")
        else:
            git("checkout", "--quiet", "--force", "--detach", target)
            landed = rev_parse(app_dir, git_env, "HEAD")

            if landed != ref:
                raise RuntimeError(f"the checkout landed on {short_commit(landed) or 'nothing'}, not {short_commit(ref)}")
    except (RuntimeError, SyncRefusal, OSError) as error:
        if created:
            shutil.rmtree(git_dir, ignore_errors=True)

        detail = str(error)

        if isinstance(error, SyncRefusal):
            raise LaunchFailure(STAGE_SYNC, error.arabic, f"sync failed: {detail}", detail) from error

        if ref is None and before:
            say(f"sync failed: {detail}. Starting the last pulled code ({short_commit(before)})")
            return {"source": SOURCE_GIT, "commit": before}

        raise LaunchFailure(STAGE_SYNC, SYNC_HINT, f"sync failed: {detail}", detail) from error

    leave_snapshot_source(context)
    remove_dropped(app_dir, dropped)
    write_source_files(state_dir, app_dir, carried)

    after = rev_parse(app_dir, git_env, "HEAD")

    write_json(
        stamp_path,
        {"source": SOURCE_GIT, "repo": repo, "branch": branch, "ref": ref, "commit": after, "syncedAt": now_iso()},
    )

    if before and after and before != after:
        say(f"updated {short_commit(before)} -> {short_commit(after)}")
    else:
        say(f"code is at {short_commit(after) or 'an unknown commit'}")

    return {"source": SOURCE_GIT, "commit": after}


def snapshot_plan(bundle, max_entries=SNAPSHOT_ENTRY_LIMIT, max_bytes=SNAPSHOT_EXPANDED_MAX_BYTES):
    kept = []

    for info in bundle.infolist():
        if info.is_dir():
            continue

        segments = info.filename.split("/")

        if segments[0] == "__MACOSX" or ".git" in segments or segments[-1] == ".DS_Store":
            continue

        kept.append((info, info.filename))

    names = [raw for _, raw in kept]
    first = {name.split("/")[0] for name in names}
    wrapper = ""

    if len(first) == 1 and names and all("/" in name for name in names):
        wrapper = next(iter(first)) + "/"

    if len(kept) > max_entries:
        raise SnapshotRefused(f"the archive holds more than {max_entries} files")

    entries = []
    total = 0

    for info, raw in kept:
        name = raw[len(wrapper) :]
        segments = name.split("/")

        if segments[0] == STATE_ENTRY:
            continue

        if raw.startswith("/") or "\\" in raw or "\0" in raw or any(part in ("", ".", "..") for part in segments):
            raise SnapshotRefused(f"the archive entry {raw!r} is not a plain relative path")

        if stat.S_ISLNK(info.external_attr >> 16):
            raise SnapshotRefused(f"the archive entry {raw!r} is a symlink")

        total += info.file_size

        if total > max_bytes:
            raise SnapshotRefused(f"the archive expands past {max_bytes} bytes")

        entries.append((info, name))

    return entries


def extract_snapshot(bundle, entries, destination):
    for info, name in entries:
        target = os.path.join(destination, name)
        os.makedirs(os.path.dirname(target), exist_ok=True)

        if os.path.islink(target):
            os.unlink(target)

        with bundle.open(info) as source, open(target, "wb") as sink:
            shutil.copyfileobj(source, sink, 1048576)

        os.chmod(target, 0o755 if (info.external_attr >> 16) & 0o111 else 0o644)


def clean_snapshots(snapshots_dir, keep, now=None):
    try:
        entries = os.listdir(snapshots_dir)
    except OSError:
        return

    now = time.time() if now is None else now
    kept = (f"{keep}.zip", f"{keep}.zip{PARTIAL_SUFFIX}") if keep else ()

    for entry in entries:
        if entry in kept or not (entry.endswith(".zip") or entry.endswith(f".zip{PARTIAL_SUFFIX}")):
            continue

        path = os.path.join(snapshots_dir, entry)

        try:
            info = os.lstat(path)
        except OSError:
            continue

        if not stat.S_ISREG(info.st_mode) or now - info.st_mtime < SNAPSHOT_STALE_SECONDS:
            continue

        try:
            os.remove(path)
        except FileNotFoundError:
            pass


def newest_first(records):
    parsed = []

    for line in records:
        parts = line.split(" ")
        name = parts[0] if parts else ""
        seconds = parts[1] if len(parts) > 1 else ""
        word = parts[2] if len(parts) > 2 else ""
        created = parts[3] if len(parts) > 3 else ""

        if word == "created" and created.isdigit():
            at = int(created)
        elif seconds.isdigit():
            at = int(seconds) * 1000
        else:
            at = 0

        if name:
            parsed.append((name, at))

    parsed.sort(key=lambda record: record[0])
    parsed.sort(key=lambda record: record[1], reverse=True)

    return [name for name, _ in parsed]


def doomed_tags(snapshot_tags, other_tags, current, keep=HISTORY_KEEP):
    doomed = []
    others = 0

    for name in snapshot_tags:
        if name == current:
            continue

        if others < keep:
            others += 1
            continue

        doomed.append(name)

    return [*doomed, *other_tags]


def prune_history(history, current):
    def lines(output):
        return [line.strip() for line in output.split("\n") if line.strip()]

    snapshot_tags = newest_first(
        lines(
            history(
                "for-each-ref",
                "--format=%(refname:short) %(committerdate:unix) %(contents:body)",
                "refs/tags/snapshot-*",
                capture=True,
            )
        )
    )
    other_tags = [
        name
        for name in lines(history("for-each-ref", "--format=%(refname:short)", "refs/tags/", capture=True))
        if not name.startswith("snapshot-")
    ]
    branches = lines(history("for-each-ref", "--format=%(refname)", "refs/heads/", capture=True))
    doomed = doomed_tags(snapshot_tags, other_tags, current)

    if doomed:
        history("tag", "--delete", *doomed)

    for branch in branches:
        history("update-ref", "-d", branch)

    history("reflog", "expire", "--expire=now", "--all")
    history(
        "-c",
        "pack.threads=1",
        "-c",
        "pack.windowMemory=64m",
        "-c",
        "core.bigFileThreshold=16m",
        "gc",
        "--quiet",
        "--prune=now",
    )


def sync_snapshot(context):
    app_dir = context["app_dir"]
    state_dir = context["state_dir"]
    env = context["env"]
    request = context["request"]
    snapshot_id = request["snapshot"]

    if not ID_PATTERN.fullmatch(snapshot_id):
        raise LaunchFailure(
            STAGE_SNAPSHOT,
            REQUEST_HINT,
            "snapshot failed: the snapshot id is not valid",
            "the snapshot id is not valid",
            EXIT_CONFIG,
        )

    history_dir = os.path.join(state_dir, HISTORY_DIR)
    snapshots_dir = os.path.join(state_dir, SNAPSHOTS_DIR)
    archive = os.path.join(snapshots_dir, f"{snapshot_id}.zip")
    stamp_path = os.path.join(state_dir, SYNC_STAMP)
    stamp = read_json(stamp_path) or {}
    git_env = git_environment(env, None, None)
    tag = f"snapshot-{snapshot_id}"

    def history(*args, capture=False):
        code, detail, output = run(
            git_argv(f"--git-dir={history_dir}", f"--work-tree={app_dir}", "--literal-pathspecs", *HISTORY_IDENTITY, *args),
            app_dir,
            git_env,
            echo=False,
            capture=capture,
        )

        if code != 0:
            raise RuntimeError(detail)

        return output

    has_history = os.path.isdir(history_dir)

    if has_history:
        write_git_config(history_dir)

    def tagged():
        return has_history and rev_parse(app_dir, git_env, f"refs/tags/{tag}", history_dir) is not None

    present = os.path.isfile(archive)
    stamped = stamp.get("source") == SOURCE_SNAPSHOT and stamp.get("snapshot") == snapshot_id

    if not present and stamped and (not request["deploying"] or not tagged()):
        say(f"code is at snapshot {snapshot_id}")
        return {"source": SOURCE_SNAPSHOT, "commit": stamp.get("commit")}

    def broken(error):
        detail = str(error)
        return LaunchFailure(STAGE_SNAPSHOT, SNAPSHOT_BROKEN_HINT, f"snapshot failed: {detail}", detail)

    incoming = None

    if present:
        try:
            if os.path.getsize(archive) > SNAPSHOT_MAX_BYTES:
                raise SnapshotRefused(f"the archive is larger than {SNAPSHOT_MAX_BYTES} bytes")

            with zipfile.ZipFile(archive) as bundle:
                incoming = {name for _, name in snapshot_plan(bundle)}
                corrupt = bundle.testzip()

                if corrupt is not None:
                    raise SnapshotRefused(f"the archive entry {corrupt!r} is corrupt")
        except (SnapshotRefused, OSError, zipfile.BadZipFile, zlib.error, EOFError, ValueError, RuntimeError) as error:
            raise broken(error) from error
    elif not tagged():
        raise LaunchFailure(
            STAGE_SNAPSHOT,
            SNAPSHOT_MISSING_HINT,
            f"snapshot failed: snapshot {snapshot_id} is not on this bot",
            f"snapshot {snapshot_id} is not on this bot",
        )

    previous = read_source_files(state_dir) or {}

    leave_git_source(context)

    message = f"deployment {request['deployment']}" if request["deployment"] else f"snapshot {snapshot_id}"

    try:
        if not os.path.isdir(history_dir):
            history("init", "--quiet")

        write_git_config(history_dir)

        if incoming is not None:
            say(f"unpacking snapshot {snapshot_id}")

            clear_way(app_dir, incoming)
            remove_dropped(app_dir, dropped_files(app_dir, previous, incoming))

            with zipfile.ZipFile(archive) as bundle:
                entries = snapshot_plan(bundle)
                extract_snapshot(bundle, entries, app_dir)

            written = [name for _, name in entries]
            listing = os.path.join(state_dir, "snapshot-files")

            with open(listing, "w", encoding="utf-8") as handle:
                handle.write("".join(f"{name}\0" for name in written))

            try:
                history("read-tree", "--empty")

                if written:
                    history("add", "--force", f"--pathspec-from-file={listing}", "--pathspec-file-nul")
            finally:
                try:
                    os.remove(listing)
                except FileNotFoundError:
                    pass

            tree = history("write-tree", capture=True).strip()
            commit = history("commit-tree", "-m", message, "-m", f"created {time.time_ns() // 1_000_000}", tree, capture=True).strip()
            history("update-ref", "--no-deref", "HEAD", commit)
            history("tag", "--force", tag, commit)
            os.remove(archive)
            carried = written
        else:
            say(f"restoring snapshot {snapshot_id}")
            carried = tree_files(app_dir, git_env, history_dir, tag)
            clear_way(app_dir, carried)
            dropped = dropped_files(app_dir, previous, carried)
            history("read-tree", "--empty")
            history("checkout", "--quiet", "--force", "--detach", tag)
            remove_dropped(app_dir, dropped)
    except LaunchFailure:
        raise
    except (SnapshotRefused, RuntimeError, OSError, zipfile.BadZipFile, zlib.error, EOFError, ValueError) as error:
        raise broken(error) from error

    write_source_files(state_dir, app_dir, carried)

    try:
        prune_history(history, tag)
    except (RuntimeError, OSError) as error:
        say(f"history cleanup skipped: {one_line(error)}")

    commit = rev_parse(app_dir, git_env, "HEAD", history_dir)

    write_json(stamp_path, {"source": SOURCE_SNAPSHOT, "snapshot": snapshot_id, "commit": commit, "syncedAt": now_iso()})
    say(f"code is at snapshot {snapshot_id}")

    return {"source": SOURCE_SNAPSHOT, "commit": commit}


def sync_from(context):
    if context["request"]["snapshot"] is not None:
        return sync_snapshot(context)

    if text(context["env"].get("SERVERK_REPO_URL")):
        return sync_git(context)

    say("no repository linked, running the files in your bot folder")

    return {"source": SOURCE_LOCAL, "commit": None}


def sync_source(context):
    synced = sync_from(context)

    if context["request"]["deploying"]:
        clean_snapshots(os.path.join(context["state_dir"], SNAPSHOTS_DIR), context["request"]["snapshot"])

    return synced


def is_root_directory(value):
    return len(value) <= ROOT_DIRECTORY_LENGTH_LIMIT and ROOT_DIRECTORY_PATTERN.fullmatch(value) is not None


def source_stage(request):
    return STAGE_SNAPSHOT if request["snapshot"] is not None else STAGE_SYNC


def resolve_project_dir(app_dir, root, stage):
    if root is None:
        return app_dir

    def refuse(detail):
        return LaunchFailure(stage, ROOT_HINT, f"{stage} failed: {detail}", detail, EXIT_CONFIG)

    if not is_root_directory(root):
        raise refuse(f"root directory {root} is not valid")

    joined = os.path.join(app_dir, root)

    if not os.path.lexists(joined):
        raise refuse(f"root directory {root} not found")

    resolved = os.path.realpath(joined)
    base = os.path.realpath(app_dir)

    if resolved != base and not resolved.startswith(base + os.sep):
        raise refuse(f"root directory {root} leaves the bot folder")

    segments = [] if resolved == base else resolved[len(base) + 1 :].split(os.sep)
    reserved = STATE_ENTRY if segments[:1] == [STATE_ENTRY] else ".git" if ".git" in segments else None

    if reserved is not None:
        raise refuse(f"root directory {root} points inside {reserved}")

    if not os.path.isdir(resolved):
        raise refuse(f"root directory {root} not found")

    return resolved


def tool_environment(env, state_dir):
    return {
        **bot_environment(env),
        "PIP_CACHE_DIR": env.get("PIP_CACHE_DIR") or os.path.join(state_dir, "cache", "pip"),
        "UV_CACHE_DIR": env.get("UV_CACHE_DIR") or os.path.join(state_dir, *UV_CACHE_DIR),
        "UV_PYTHON_INSTALL_DIR": env.get("UV_PYTHON_INSTALL_DIR") or os.path.join(state_dir, *UV_PYTHON_INSTALL_DIR),
        "PIPENV_CACHE_DIR": env.get("PIPENV_CACHE_DIR") or os.path.join(state_dir, *PIPENV_CACHE_DIR),
        "PIPENV_DONT_LOAD_ENV": "1",
        "UV_MANAGED_PYTHON": "1",
        "CI": "true",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PIP_NO_INPUT": "1",
        "PIP_PROGRESS_BAR": "off",
        "PYTHONUNBUFFERED": "1",
    }


def venv_environment(env, app_dir):
    venv_dir = os.path.join(app_dir, VENV)

    return {
        **env,
        "PATH": f"{os.path.join(venv_dir, 'bin')}:{env.get('PATH') or '/usr/local/bin:/usr/bin:/bin'}",
        "VIRTUAL_ENV": venv_dir,
        "PYTHONUNBUFFERED": "1",
    }


def minor_of(version):
    return ".".join(version.split(".")[:PYTHON_VERSION_PARTS])


def venv_version_of(project_dir):
    for line in (read_text(os.path.join(project_dir, VENV, VENV_CONFIG)) or "").splitlines():
        key, separator, value = line.partition("=")
        match = VERSION_NUMBER.match(value.strip())

        if separator and key.strip() in VENV_VERSION_KEYS and match:
            return minor_of(match.group(1))

    return None


def venv_argv(venv_dir, python):
    if python is None:
        return [sys.executable, "-I", "-m", "venv", venv_dir]

    return [TOOL_UV, "venv", "--seed", "--managed-python", "--python", python, venv_dir]


def ensure_venv(project_dir, env, rebuild, python=None):
    venv_dir = os.path.join(project_dir, VENV)

    if rebuild:
        shutil.rmtree(venv_dir, ignore_errors=True)

    if os.path.isfile(os.path.join(project_dir, VENV_PYTHON)):
        return False

    if python is None:
        say(f"creating {VENV} with Python {platform.python_version()}")
    else:
        shutil.rmtree(venv_dir, ignore_errors=True)
        say(f"creating {VENV} with Python {python} through uv")

    code, detail, _ = run(venv_argv(venv_dir, python), project_dir, env)

    if code != 0:
        raise stage_failure(STAGE_INSTALL, INSTALL_HINT, code, detail)

    return True


def source_listing(context):
    synced = context.get("synced") or {}
    app_dir = context["app_dir"]

    if synced.get("source") == SOURCE_SNAPSHOT:
        git_dir = os.path.join(context["state_dir"], HISTORY_DIR)
    elif synced.get("source") == SOURCE_GIT:
        git_dir = os.path.join(app_dir, ".git")
    else:
        return None

    if not os.path.isdir(git_dir):
        return None

    code, _, output = run(
        git_argv(f"--git-dir={git_dir}", f"--work-tree={app_dir}", "ls-files", "-z"),
        app_dir,
        git_environment(context["env"], None, None),
        echo=False,
        capture=True,
    )

    return {name for name in output.split("\0") if name} if code == 0 else None


def project_prefix(app_dir, project_dir):
    base = os.path.realpath(app_dir)
    project = os.path.realpath(project_dir)

    if project == base:
        return ""

    return project[len(base) + 1 :] + "/" if project.startswith(base + os.sep) else None


def carried_by(listing, prefix):
    return lambda name: listing is None or prefix is None or f"{prefix}{name}" in listing


def dependency_files(plan):
    if plan is None:
        return []

    companion = MANIFEST_COMPANIONS.get(plan["manifest"])

    return [plan["manifest"], companion] if companion else [plan["manifest"]]


def install_run_of(command, project_dir, env):
    venv_dir = os.path.join(project_dir, VENV)
    tool_env = {**env, "VIRTUAL_ENV": venv_dir}

    if command[0] == TOOL_UV:
        tool_env["UV_PROJECT_ENVIRONMENT"] = venv_dir

    return list(command), tool_env


def install_dependencies(context, reinstall, require_manifest):
    project_dir = context["project_dir"]
    state_dir = context["state_dir"]
    env = context["env"]
    table = context["table"]
    declared = serverk_json_of(read_text_replacing(os.path.join(project_dir, table["serverkJson"]["file"])), table)
    install_command = text(env.get("SERVERK_INSTALL_COMMAND")) or (declared or {}).get("install")
    carried = carried_by(source_listing(context), project_prefix(context["app_dir"], project_dir))
    present = {
        entry["file"]
        for entry in table["python"]["manifests"]
        if os.path.isfile(os.path.join(project_dir, entry["file"])) and carried(entry["file"])
    }
    plan = detect_manager(present, table)

    if plan is None and install_command is None and require_manifest:
        say(NO_MANIFEST_LINE)
        return

    def read(name):
        return read_text(os.path.join(project_dir, name)) if carried(name) else None

    command = None if install_command or plan is None else table["python"]["installCommands"][plan["manager"]]
    owned = command is not None and tuple(command[: len(UV_SYNC)]) == UV_SYNC
    python = managed_python_of(python_version_of(read, table), platform.python_version())
    runtime = python or platform.python_version()
    stamp_path = os.path.join(state_dir, DEPS_STAMP)
    stamp = read_json(stamp_path)
    current = None if owned else venv_version_of(project_dir)
    moved = current is not None and current != minor_of(runtime)

    if reinstall:
        say(f"reinstall requested, removing {VENV}")
    elif moved:
        say(f"Python changed to {runtime}, rebuilding {VENV}")

    tools = tool_environment(env, state_dir)

    if owned:
        if reinstall:
            shutil.rmtree(os.path.join(project_dir, VENV), ignore_errors=True)

        fresh = not os.path.isfile(os.path.join(project_dir, VENV_PYTHON))
    else:
        fresh = ensure_venv(project_dir, tools, reinstall or moved, python)

    if plan is None and install_command is None:
        say(NO_MANIFEST_LINE)
        return

    manager = "custom" if install_command else plan["manager"]
    root = text(env.get("SERVERK_ROOT_DIRECTORY")) or ""
    manifests = [read(name) or "" for name in dependency_files(plan)] or [""]
    digest = dependency_hash([install_command or plan["manager"], runtime, root, *manifests])

    if not reinstall and not fresh and stamp and stamp.get("hash") == digest:
        say(f"dependencies are up to date ({'custom' if install_command else command[0]})")
        return

    try:
        os.remove(stamp_path)
    except FileNotFoundError:
        pass

    if install_command:
        argv, run_env = shell_command(install_command), venv_environment(tools, project_dir)
        say(f"installing dependencies: {install_command}")
    else:
        argv, run_env = install_run_of(command, project_dir, tools)

        if plan["manager"] in table["python"]["unhonouredManagers"]:
            say(f"{plan['manifest']} is not used, installing from {PYPROJECT_FILE}")

        say(f"installing dependencies: {' '.join(command)}")

    code, detail, _ = run(argv, project_dir, run_env)

    if code != 0:
        raise stage_failure(STAGE_INSTALL, INSTALL_HINT, code, detail)

    write_json(stamp_path, {"hash": digest, "manager": manager, "runtime": runtime, "installedAt": now_iso()})
    say("dependencies installed")


def package_folders(project_dir):
    try:
        with os.scandir(project_dir) as entries:
            return [
                entry.name
                for entry in entries
                if entry.is_dir(follow_symlinks=False) and os.path.isfile(os.path.join(entry.path, PACKAGE_MAIN))
            ]
    except OSError:
        return []


def resolve_start(project_dir, env, table):
    files = {
        candidate for candidate in table["python"]["startFiles"] if os.path.isfile(os.path.join(project_dir, candidate))
    }

    return detect_start(
        files,
        serverk_json=serverk_json_of(read_text_replacing(os.path.join(project_dir, table["serverkJson"]["file"])), table),
        start_command=env.get("SERVERK_START_COMMAND"),
        procfile=read_text(os.path.join(project_dir, table["procfile"]["file"])),
        table=table,
        packages=package_folders(project_dir),
    )


def executable_of(app_dir, program):
    if program == "sh":
        return "/bin/sh"

    if program == VENV_PYTHON:
        return os.path.join(app_dir, VENV_PYTHON)

    return program


def intended_source(env, request):
    if request["snapshot"] is not None:
        return SOURCE_SNAPSHOT

    return SOURCE_GIT if text(env.get("SERVERK_REPO_URL")) else SOURCE_LOCAL


def record_deployment(context, outcome, source=None, commit=None, stage=None, detail=None):
    request = context.get("request")

    if not request or not request["deploying"] or request["deployment"] is None:
        return

    source = source or intended_source(context["env"], request)

    write_json(
        os.path.join(context["state_dir"], DEPLOYMENT_STAMP),
        {
            "deployment": request["deployment"],
            "source": source,
            "ref": request["ref"] if request["snapshot"] is None else None,
            "commit": commit,
            "snapshot": request["snapshot"],
            "outcome": outcome,
            "stage": stage,
            "detail": detail,
            "finishedAt": now_iso(),
            "settled": outcome == OUTCOME_FAILED,
        },
    )

    if outcome == OUTCOME_READY:
        return

    print(deployment_line(request["deployment"], outcome, stage=stage, detail=detail), flush=True)


def resume_state_of(raw):
    state = parse_object(raw if isinstance(raw, str) else None)

    if not state:
        return None

    request = state.get("request")
    synced = state.get("synced")

    def nullable(value, pattern):
        return value is None or (isinstance(value, str) and pattern.fullmatch(value) is not None)

    if (
        not isinstance(request, dict)
        or not nullable(request.get("deployment"), ID_PATTERN)
        or not nullable(request.get("ref"), REPO_REF_PATTERN)
        or not nullable(request.get("snapshot"), ID_PATTERN)
        or not isinstance(request.get("reinstall"), bool)
        or not isinstance(request.get("deploying"), bool)
        or not isinstance(synced, dict)
        or synced.get("source") not in (SOURCE_GIT, SOURCE_SNAPSHOT, SOURCE_LOCAL)
        or not nullable(synced.get("commit"), COMMIT_PATTERN)
    ):
        return None

    return {
        "request": {
            "deployment": request.get("deployment"),
            "ref": request.get("ref"),
            "snapshot": request.get("snapshot"),
            "reinstall": request["reinstall"],
            "deploying": request["deploying"],
        },
        "synced": {"source": synced["source"], "commit": synced.get("commit")},
    }


def resume_without_token(mode, context):
    env = {key: value for key, value in context["env"].items() if key != "SERVERK_GIT_TOKEN"}
    env[RESUME_KEY] = json.dumps({"request": context["request"], "synced": context["synced"]})

    sys.stdout.flush()
    sys.stderr.flush()

    os.execve(
        sys.executable,
        [sys.executable, "-I", os.path.abspath(__file__), *(["install"] if mode == "install" else [])],
        env,
    )


def launch(mode, context):
    env = dict(os.environ)
    app_dir = os.getcwd()
    state_dir = text(env.get("SERVERK_STATE_DIR")) or DEFAULT_STATE_DIR

    os.makedirs(state_dir, exist_ok=True)

    context.update({"env": env, "app_dir": app_dir, "state_dir": state_dir, "table": load_detect_table(env)})

    resumed = resume_state_of(env.get(RESUME_KEY))

    if resumed:
        context["request"] = resumed["request"]
        context["synced"] = resumed["synced"]
    else:
        if mode == "install":
            context["request"] = {**resolve_request(env, None, False, None), "deploying": False, "reinstall": False}
        else:
            marker = parse_marker(take_marker(os.path.join(state_dir, DEPLOY_MARKER)))
            legacy_reinstall = take_marker(os.path.join(state_dir, LEGACY_REINSTALL_MARKER)) is not None

            context["request"] = resolve_request(
                env, marker, legacy_reinstall, read_json(os.path.join(state_dir, DEPLOYMENT_STAMP))
            )

            if context["request"]["deploying"] and context["request"]["deployment"]:
                say(f"deploying {context['request']['deployment']}")

        context["stage"] = source_stage(context["request"])
        context["synced"] = sync_source(context)

        if "SERVERK_GIT_TOKEN" in env:
            resume_without_token(mode, context)

    context["stage"] = source_stage(context["request"])
    context["project_dir"] = resolve_project_dir(
        app_dir, text(env.get("SERVERK_ROOT_DIRECTORY")), source_stage(context["request"])
    )
    project_dir = context["project_dir"]
    context["stage"] = STAGE_INSTALL
    install_dependencies(context, reinstall=context["request"]["reinstall"], require_manifest=mode == "install")

    if mode == "install":
        raise LaunchExit(0)

    context["stage"] = STAGE_START

    start = resolve_start(project_dir, env, context["table"])

    if start is None:
        raise LaunchFailure(
            STAGE_START,
            START_HINT,
            "start failed: nothing to start. Add a main.py or bot.py, or set a start command in the bot's settings",
            "nothing to start",
            EXIT_CONFIG,
        )

    record_deployment(context, OUTCOME_READY, source=context["synced"]["source"], commit=context["synced"]["commit"])
    retry_start(context)

    program, *args = start["argv"]
    exec_env = venv_environment(bot_environment(env), project_dir)

    say(f"start command: {' '.join(start['argv'])}")
    print(READY_LINE, flush=True)

    os.chdir(project_dir)
    os.execve(executable_of(project_dir, program), [program, *args], exec_env)


def main(argv):
    context = {"request": None, "stage": STAGE_SYNC, "synced": None}

    try:
        launch("install" if argv[:1] == ["install"] else "start", context)
    except LaunchExit as done:
        sys.exit(done.code)
    except Exception as error:
        failure = (
            error
            if isinstance(error, LaunchFailure)
            else LaunchFailure(context["stage"], None, f"{context['stage']} failed: {error}", str(error))
        )

        if failure.arabic:
            say(failure.arabic)

        say(failure.english)

        if "state_dir" in context:
            synced = context.get("synced") or {}
            record_deployment(
                context,
                OUTCOME_FAILED,
                source=synced.get("source"),
                commit=synced.get("commit"),
                stage=failure.stage,
                detail=failure.detail,
            )

        sys.exit(failure.code)


if __name__ == "__main__":
    main(sys.argv[1:])
