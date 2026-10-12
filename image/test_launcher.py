import contextlib
import hashlib
import io
import json
import os
import platform
import shutil
import stat
import subprocess
import tempfile
import unittest
import zipfile

import launcher

TEMPLATES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates")

SHA = "0123456789abcdef0123456789abcdef01234567"

REMOTE = "https://example.test/bots/sample"

RUNTIME_FILES = {"data/bot.sqlite": "rows", "cache.json": "{}"}

REMOVED_ONE = "serverk: removed 1 file the source no longer carries"

REMOVED_TWO = "serverk: removed 2 files the source no longer carries"

KEPT_ONE = "serverk: kept 1 changed file the source no longer carries"

IN_THE_WAY_ONE = "serverk: removed 1 path in the way of the source's files"


def sha(content):
    return hashlib.sha256(content.encode()).hexdigest()


def template_start(name):
    directory = os.path.join(TEMPLATES, name)
    files = {
        candidate
        for candidate in launcher.BUILT_IN_TABLE["python"]["startFiles"]
        if os.path.isfile(os.path.join(directory, candidate))
    }
    procfile = launcher.read_text(os.path.join(directory, "Procfile"))

    return launcher.detect_start(files, procfile=procfile)


def bundle_of(entries):
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content, mode in entries:
            info = zipfile.ZipInfo(name)
            info.external_attr = mode << 16
            archive.writestr(info, content)

    buffer.seek(0)

    return zipfile.ZipFile(buffer)


class TemplateStartTest(unittest.TestCase):
    def test_both_templates_run_main_py_unbuffered_from_the_venv(self):
        for name in ("discord-python", "telegram-python"):
            self.assertEqual(
                template_start(name),
                {"source": "file", "argv": [".venv/bin/python", "-u", "main.py"]},
            )

    def test_both_templates_pin_every_requirement(self):
        for name in ("discord-python", "telegram-python"):
            lines = launcher.read_text(os.path.join(TEMPLATES, name, "requirements.txt")).split()

            self.assertTrue(lines)
            self.assertTrue(all("==" in line for line in lines), name)
            self.assertEqual(
                launcher.detect_manager({"requirements.txt"}),
                {"manager": "requirements", "manifest": "requirements.txt"},
            )


class DetectStartTest(unittest.TestCase):
    def test_prefers_the_typed_start_command(self):
        self.assertEqual(
            launcher.detect_start({"main.py"}, start_command="  python -m mybot  "),
            {"source": "start-command", "argv": ["sh", "-c", "exec python -m mybot"]},
        )

    def test_walks_the_entry_files_in_order(self):
        self.assertEqual(launcher.detect_start({"src/bot.py", "app.py"})["argv"], [".venv/bin/python", "-u", "app.py"])
        self.assertEqual(
            launcher.detect_start({"src/main.py", "src/bot.py"})["argv"],
            [".venv/bin/python", "-u", "src/main.py"],
        )

    def test_reads_a_worker_or_bot_procfile_line_first_after_serverk_json(self):
        self.assertEqual(launcher.procfile_command("web: gunicorn app\nbot: python bot/run.py\n"), "python bot/run.py")
        self.assertEqual(launcher.procfile_command("bot: python a.py\nworker: python b.py"), "python b.py")
        self.assertIsNone(launcher.procfile_command("web: gunicorn app"))
        self.assertEqual(launcher.procfile_command("\ufeffworker: python main.py\r\n"), "python main.py")
        self.assertEqual(launcher.procfile_command("worker:\u00a0python main.py\u00a0\n"), "python main.py")
        self.assertIsNone(launcher.procfile_command("web: gunicorn app\rworker: python main.py\r"))
        self.assertEqual(
            launcher.detect_start({"main.py"}, procfile="worker: python -m bot\n", packages=["bot"]),
            {"source": "procfile", "argv": ["sh", "-c", "exec python -m bot"]},
        )
        self.assertEqual(
            launcher.detect_start(
                {"main.py"},
                procfile="worker: python -m bot\n",
                serverk_json=launcher.serverk_json_of(json.dumps({"start": "python run.py"})),
            )["source"],
            "serverk-json",
        )
        self.assertEqual(launcher.detect_start({"main.py"}, procfile="web: gunicorn app")["source"], "file")

    def test_runs_the_one_top_level_package_with_a_main_module_when_no_start_file_exists(self):
        self.assertEqual(
            launcher.detect_start(set(), packages=["mybot"]),
            {"source": "package", "argv": [".venv/bin/python", "-u", "-m", "mybot"]},
        )
        self.assertEqual(launcher.detect_start({"bot.py"}, packages=["mybot"])["argv"], [".venv/bin/python", "-u", "bot.py"])
        self.assertIsNone(launcher.detect_start(set(), packages=["mybot", "other"]))

    def test_skips_folders_that_are_not_the_bot_when_counting_packages(self):
        skipped = ["tests", "test", "docs", "examples", "scripts", "venv", "node_modules", "__pycache__", ".venv", "my-bot"]

        self.assertIsNone(launcher.detect_start(set(), packages=skipped))
        self.assertEqual(launcher.detect_start(set(), packages=[*skipped, "mybot"])["argv"][-1], "mybot")

    def test_finds_nothing_in_an_empty_folder(self):
        self.assertIsNone(launcher.detect_start(set()))
        self.assertIsNone(launcher.detect_start(set(), start_command="   "))

    def test_keeps_compound_commands_whole_and_reads_operators_outside_quotes(self):
        self.assertEqual(launcher.shell_command("pip check && python main.py"), ["sh", "-c", "pip check && python main.py"])
        self.assertFalse(launcher.has_shell_operator('python -c "print(1|2)"'))
        self.assertFalse(launcher.has_shell_operator("echo a\\;b"))
        self.assertTrue(launcher.has_shell_operator("python main.py | tee bot.log"))


class ShellCommandTest(unittest.TestCase):
    def test_execs_a_plain_command(self):
        self.assertEqual(launcher.shell_command("python main.py"), ["sh", "-c", "exec python main.py"])
        self.assertEqual(launcher.shell_command('python -c "run(1)"'), ["sh", "-c", 'exec python -c "run(1)"'])

    def test_puts_leading_assignments_behind_env(self):
        self.assertEqual(
            launcher.shell_command("PYTHONOPTIMIZE=1 python main.py"),
            ["sh", "-c", "exec env PYTHONOPTIMIZE=1 python main.py"],
        )
        self.assertEqual(
            launcher.shell_command('A=1 B="two words" python main.py'),
            ["sh", "-c", 'exec env A=1 B="two words" python main.py'],
        )

    def test_runs_compound_commands_subshells_and_builtins_without_exec(self):
        for command in (
            "pip check && python main.py",
            "python a.py || python b.py",
            "(cd app; python main.py)",
            "cd app",
            ". ./env.sh",
            "source ./env.sh",
            "export A=1",
            "exec python main.py",
            "A=1",
        ):
            self.assertEqual(launcher.shell_command(command), ["sh", "-c", command], command)

    def test_splits_words_outside_quotes_and_escapes(self):
        self.assertEqual(launcher.command_words("A=\"x y\" python 'a b' c\\ d"), ['A="x y"', "python", "'a b'", "c\\ d"])


class ServerkJsonTest(unittest.TestCase):
    def test_reads_start_and_install_and_ignores_a_file_it_cannot_trust(self):
        self.assertEqual(
            launcher.serverk_json_of(json.dumps({"start": " python -m bot ", "install": "pip install ."})),
            {"start": "python -m bot", "install": "pip install ."},
        )
        self.assertEqual(launcher.serverk_json_of("{}"), {"start": None, "install": None})

        for raw in ('{"runtime": "go"}', '{"start": "a\\nb"}', '{"start": NaN}', "[]", "not json", None):
            self.assertIsNone(launcher.serverk_json_of(raw), raw)

    def test_starts_from_the_file_after_the_typed_command_and_before_the_entry_files(self):
        declared = launcher.serverk_json_of(json.dumps({"start": "python -m bot"}))

        self.assertEqual(
            launcher.detect_start({"main.py"}, serverk_json=declared),
            {"source": "serverk-json", "argv": ["sh", "-c", "exec python -m bot"]},
        )
        self.assertEqual(
            launcher.detect_start({"main.py"}, start_command="python other.py", serverk_json=declared)["source"],
            "start-command",
        )


class GitTest(unittest.TestCase):
    def test_drops_inherited_git_variables_and_customer_variables(self):
        self.assertEqual(
            launcher.git_environment(
                {
                    "PATH": "/usr/bin",
                    "HOME": "/home/container",
                    "GIT_DIR": "/tmp/evil",
                    "GIT_CONFIG_COUNT": "1",
                    "HTTPS_PROXY": "http://evil:8080",
                    "TELEGRAM_TOKEN": "token",
                },
                None,
                None,
            ),
            {
                "PATH": "/usr/bin",
                "HOME": "/home/container",
                "GIT_CONFIG_GLOBAL": "/dev/null",
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_TERMINAL_PROMPT": "0",
            },
        )

    def test_binds_the_token_to_the_repository_host(self):
        environment = launcher.git_environment({}, "ghs_installation", "https://github.com:8443/you/bot")

        self.assertEqual(environment["GIT_ASKPASS"], "/serverk/git-askpass")
        self.assertEqual(environment["SERVERK_GIT_HOST"], "github.com:8443")
        self.assertEqual(
            launcher.git_argv("fetch"),
            [
                "git",
                "-c",
                "core.hooksPath=/dev/null",
                "-c",
                "core.fsmonitor=false",
                "-c",
                "protocol.allow=never",
                "-c",
                "protocol.https.allow=always",
                "fetch",
            ],
        )


class HistoryTest(unittest.TestCase):
    def test_keeps_the_current_snapshot_and_the_ten_newest_others(self):
        tags = [f"snapshot-s{index}" for index in range(14)]

        self.assertEqual(
            launcher.doomed_tags(tags, ["deployment-dep_1"], "snapshot-s12"),
            ["snapshot-s10", "snapshot-s11", "snapshot-s13", "deployment-dep_1"],
        )

    def test_orders_snapshots_by_when_they_were_made(self):
        self.assertEqual(
            launcher.newest_first(
                [
                    "snapshot-a 1790000000 created 1790000000100",
                    "snapshot-b 1790000000 created 1790000000900",
                    "snapshot-legacy 1789999000",
                    "snapshot-c 1790000000 created 1790000000500",
                ]
            ),
            ["snapshot-b", "snapshot-c", "snapshot-a", "snapshot-legacy"],
        )

    def test_drops_stale_zips_and_partials_but_never_the_requested_one_or_a_fresh_download(self):
        import shutil
        import tempfile
        import time

        directory = tempfile.mkdtemp(prefix="bot-python-snapshots-")
        now = time.time()
        old = now - launcher.SNAPSHOT_STALE_SECONDS - 60

        try:
            for name in ("snap_keep.zip", "snap_old.zip", "snap_old2.zip.partial", "snap_fresh.zip.partial", "notes.txt"):
                with open(os.path.join(directory, name), "w", encoding="utf-8") as handle:
                    handle.write("x")

            for name in ("snap_keep.zip", "snap_old.zip", "snap_old2.zip.partial", "notes.txt"):
                os.utime(os.path.join(directory, name), (old, old))

            launcher.clean_snapshots(directory, "snap_keep", now)

            self.assertEqual(sorted(os.listdir(directory)), ["notes.txt", "snap_fresh.zip.partial", "snap_keep.zip"])
        finally:
            shutil.rmtree(directory, ignore_errors=True)

    def test_carries_only_a_valid_resume_state(self):
        state = {
            "request": {"deployment": "dep_1", "ref": SHA, "snapshot": None, "reinstall": False, "deploying": True},
            "synced": {"source": "git", "commit": SHA},
        }

        self.assertEqual(launcher.resume_state_of(json.dumps(state)), state)
        self.assertIsNone(
            launcher.resume_state_of(json.dumps({**state, "request": {**state["request"], "deployment": "../x"}}))
        )
        self.assertIsNone(launcher.resume_state_of(None))


NPM_404_TRANSCRIPT = [
    "npm error code E404",
    "npm error 404 Not Found - GET https://registry.npmjs.org/serverk-no-such-package-e404-proof - Not found",
    "npm error 404",
    "npm error 404  The requested resource 'serverk-no-such-package-e404-proof@^1.0.0' could not be found or you do not have permission to access it.",
    "npm error 404",
    "npm error 404 Note that you can also install from a",
    "npm error 404 tarball, folder, http url, or git url.",
    "npm error A complete log of this run can be found in: /home/container/.serverk/cache/npm/_logs/2026-09-27T21_10_25_351Z-debug-0.log",
]

PIP_MISSING_TRANSCRIPT = [
    "Collecting serverk-no-such-package==1.0 (from -r requirements.txt (line 1))",
    "ERROR: Could not find a version that satisfies the requirement serverk-no-such-package==1.0 (from versions: none)",
    "ERROR: No matching distribution found for serverk-no-such-package==1.0",
]

PIP_BUILD_TRANSCRIPT = [
    "  error: subprocess-exited-with-error",
    "  ",
    "  × python setup.py egg_info did not run successfully.",
    "  │ exit code: 1",
    "  ╰─> [3 lines of output]",
    "      RuntimeError: this package cannot build here",
    "      [end of output]",
    "  ",
    "  note: This error originates from a subprocess, and is likely not a problem with pip.",
    "error: metadata-generation-failed",
    "",
    "× Encountered error while generating package metadata.",
    "╰─> See above for output.",
    "",
    "note: This is an issue with the package mentioned above, not pip.",
    "hint: See above for details.",
]


UV_NO_SOLUTION_TRANSCRIPT = [
    "  × No solution found when resolving dependencies:",
    "  ╰─▶ Because serverk-no-such-package-e404-proof was not found in the package",
    "      registry and you require serverk-no-such-package-e404-proof==1.0, we can",
    "      conclude that your requirements are unsatisfiable.",
]


class FailureDetailTest(unittest.TestCase):
    def test_names_npm_code_and_reason_never_the_debug_log(self):
        self.assertEqual(
            launcher.failure_detail(NPM_404_TRANSCRIPT),
            "npm error code E404: 404 Not Found - GET https://registry.npmjs.org/serverk-no-such-package-e404-proof - Not found",
        )

    def test_prefers_the_first_pip_error_line(self):
        self.assertEqual(
            launcher.failure_detail(PIP_MISSING_TRANSCRIPT),
            "ERROR: Could not find a version that satisfies the requirement serverk-no-such-package==1.0 (from versions: none)",
        )

    def test_skips_pip_trailers_after_a_build_failure(self):
        self.assertEqual(
            launcher.failure_detail(PIP_BUILD_TRANSCRIPT), "× Encountered error while generating package metadata."
        )

    def test_joins_uv_resolution_failure_with_its_wrapped_reason(self):
        self.assertEqual(
            launcher.failure_detail([*UV_NO_SOLUTION_TRANSCRIPT, "", "  hint: Packages were unavailable"]),
            "× No solution found when resolving dependencies: Because serverk-no-such-package-e404-proof was not "
            "found in the package registry and you require serverk-no-such-package-e404-proof==1.0, we can conclude "
            "that your requirements are unsatisfiable.",
        )
        self.assertEqual(
            launcher.failure_detail(["Resolved 1 package in 12ms", "  × Failed to build `bad==1.0`", "  ├─▶ boom"]),
            "× Failed to build `bad==1.0`: boom",
        )

    def test_keeps_the_last_informative_line_of_anything_else(self):
        self.assertEqual(
            launcher.failure_detail(["remote: Repository not found.", "fatal: repository 'https://github.com/you/bot/' not found"]),
            "fatal: repository 'https://github.com/you/bot/' not found",
        )
        self.assertIsNone(launcher.failure_detail([]))


class DependenciesTest(unittest.TestCase):
    def test_prefers_requirements_over_the_project_file(self):
        self.assertEqual(launcher.detect_manager({"requirements.txt", "pyproject.toml"})["manager"], "requirements")
        self.assertEqual(launcher.detect_manager({"pyproject.toml"})["manager"], "project")
        self.assertIsNone(launcher.detect_manager(set()))

    def test_hashes_the_manifest_with_the_runtime(self):
        first = launcher.dependency_hash(["requirements", "3.12.1", "discord.py==2.7.1"])

        self.assertEqual(first, launcher.dependency_hash(["requirements", "3.12.1", "discord.py==2.7.1"]))
        self.assertNotEqual(first, launcher.dependency_hash(["requirements", "3.13.0", "discord.py==2.7.1"]))

    def test_lets_a_checkout_land_over_dependency_folders_only(self):
        self.assertEqual(launcher.occupied_entries([".serverk", ".venv", "__pycache__", "node_modules"]), [])
        self.assertEqual(launcher.occupied_entries([".serverk", "main.py"]), ["main.py"])


class PythonVersionTest(unittest.TestCase):
    def version_of(self, files):
        return launcher.python_version_of(files.get)

    def test_reads_the_version_files_in_order_and_keeps_major_and_minor(self):
        everything = {
            ".python-version": "3.11.9\n",
            "runtime.txt": "python-3.10.4",
            "Pipfile": '[requires]\npython_version = "3.9"\n',
            ".tool-versions": "python 3.13.1\n",
        }

        self.assertEqual(self.version_of(everything), "3.11")
        self.assertEqual(self.version_of({**everything, ".python-version": None}), "3.10")
        self.assertEqual(self.version_of({".tool-versions": "nodejs 24\npython 3.13.1 3.12.0\n"}), "3.13")
        self.assertIsNone(self.version_of({}))

    def test_reads_runtime_txt_only_with_its_python_prefix(self):
        self.assertEqual(self.version_of({"runtime.txt": "python-3.12.7\n"}), "3.12")
        self.assertIsNone(self.version_of({"runtime.txt": "3.12.7\n"}))
        self.assertEqual(self.version_of({"runtime.txt": "3.12.7\n", "Pipfile": "[requires]\npython_version=3.10\n"}), "3.10")
        self.assertIsNone(self.version_of({"Pipfile": "python_version = 'x'\npython_version = 3.10\n"}))

    def test_reads_the_pipfile_python_version_key_and_nothing_like_it(self):
        pipfile = '[packages]\ndiscord-py = "*"\n\n[requires]\npython_full_version = "3.10.2"\npython_version = "3.11"\n'

        self.assertEqual(self.version_of({"Pipfile": pipfile}), "3.11")
        self.assertIsNone(self.version_of({"Pipfile": '[requires]\npython_full_version = "3.10.2"\n'}))

    def test_skips_comments_and_whitespace_and_stops_at_the_first_version_line(self):
        self.assertEqual(self.version_of({".python-version": "﻿# pinned\n\n  v3.12 \n"}), "3.12")
        self.assertEqual(self.version_of({".python-version": "3\n"}), "3")
        self.assertEqual(self.version_of({".python-version": "pypy3.10\n", "runtime.txt": "python-3.9.1"}), "3.9")

    def test_asks_uv_only_for_a_version_the_image_python_does_not_satisfy(self):
        self.assertIsNone(launcher.managed_python_of(None, "3.12.3"))
        self.assertIsNone(launcher.managed_python_of("3.12", "3.12.3"))
        self.assertIsNone(launcher.managed_python_of("3", "3.12.3"))
        self.assertEqual(launcher.managed_python_of("3.11", "3.12.3"), "3.11")
        self.assertEqual(launcher.managed_python_of("3.1", "3.12.3"), "3.1")


class InstallCommandTest(unittest.TestCase):
    TOOLS = {"PATH": "/usr/local/bin:/usr/bin:/bin", "DISCORD_TOKEN": "token"}

    def run_of(self, manager):
        return launcher.install_run_of(launcher.BUILT_IN_TABLE["python"]["installCommands"][manager], "/srv/bot", self.TOOLS)

    def test_runs_every_manifest_through_the_command_the_table_names(self):
        self.assertEqual(
            {manager: self.run_of(manager)[0] for manager in launcher.BUILT_IN_TABLE["python"]["installCommands"]},
            {
                "requirements": ["uv", "pip", "install", "-r", "requirements.txt"],
                "uv": ["uv", "sync", "--locked", "--no-dev"],
                "poetry": ["uv", "pip", "install", "."],
                "pdm": ["uv", "pip", "install", "."],
                "pipenv": ["pipenv", "install"],
                "project": ["uv", "pip", "install", "."],
            },
        )

    def test_points_uv_at_the_project_venv(self):
        _, environment = self.run_of("uv")

        self.assertEqual(
            environment,
            {**self.TOOLS, "VIRTUAL_ENV": "/srv/bot/.venv", "UV_PROJECT_ENVIRONMENT": "/srv/bot/.venv"},
        )

    def test_points_pipenv_at_the_project_venv_and_nothing_else(self):
        _, environment = self.run_of("pipenv")

        self.assertEqual(environment, {**self.TOOLS, "VIRTUAL_ENV": "/srv/bot/.venv"})

    def test_hashes_a_lockfile_with_the_file_it_installs_from(self):
        self.assertEqual(launcher.dependency_files({"manager": "requirements", "manifest": "requirements.txt"}), ["requirements.txt"])
        self.assertEqual(launcher.dependency_files({"manager": "uv", "manifest": "uv.lock"}), ["uv.lock", "pyproject.toml"])
        self.assertEqual(launcher.dependency_files({"manager": "poetry", "manifest": "poetry.lock"}), ["poetry.lock", "pyproject.toml"])
        self.assertEqual(launcher.dependency_files({"manager": "pipenv", "manifest": "Pipfile"}), ["Pipfile", "Pipfile.lock"])
        self.assertEqual(launcher.dependency_files(None), [])

    def test_keeps_the_cache_and_python_builds_in_the_state_folder(self):
        environment = launcher.tool_environment({}, "/home/container/.serverk")

        self.assertEqual(environment["UV_CACHE_DIR"], "/home/container/.serverk/cache/uv")
        self.assertEqual(environment["UV_PYTHON_INSTALL_DIR"], "/home/container/.serverk/cache/python")
        self.assertEqual(environment["PIPENV_CACHE_DIR"], "/home/container/.serverk/cache/pipenv")

    def test_marks_installs_as_ci_and_keeps_pipenv_away_from_the_bot_env_file(self):
        environment = launcher.tool_environment({"DISCORD_TOKEN": "token"}, "/home/container/.serverk")

        self.assertEqual(environment["CI"], "true")
        self.assertEqual(environment["PIPENV_DONT_LOAD_ENV"], "1")
        self.assertEqual(environment["UV_MANAGED_PYTHON"], "1")
        self.assertEqual(environment["DISCORD_TOKEN"], "token")


FAKE_TOOL = """#!/bin/sh
echo "$(basename "$0") $* venv=${VIRTUAL_ENV:-none} project=${UV_PROJECT_ENVIRONMENT:-none}"
if [ "$1" = venv ]; then
  for last; do [ "$previous" = --python ] && version=$last; previous=$last; done
  mkdir -p "$last/bin" && touch "$last/bin/python" && echo "version_info = $version.0" > "$last/pyvenv.cfg"
fi
exit ${FAKE_TOOL_EXIT:-0}
"""


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="bot-python-install-")
        self.project = os.path.join(self.root, "app")
        self.state = os.path.join(self.project, ".serverk")
        self.bin = os.path.join(self.root, "bin")
        self.venv = os.path.join(self.project, ".venv")

        for directory in (self.state, self.bin, os.path.join(self.venv, "bin")):
            os.makedirs(directory)

        for tool in ("uv", "pipenv"):
            path = os.path.join(self.bin, tool)

            with open(path, "w", encoding="utf-8") as handle:
                handle.write(FAKE_TOOL)

            os.chmod(path, 0o755)

        self.write(".venv/bin/python", "")
        self.write(".venv/pyvenv.cfg", f"home = /usr/local/bin\nversion = {platform.python_version()}\n")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def write(self, name, content):
        with open(os.path.join(self.project, name), "w", encoding="utf-8") as handle:
            handle.write(content)

    def install(self, reinstall=False, **env):
        context = {
            "project_dir": self.project,
            "app_dir": self.project,
            "state_dir": self.state,
            "env": {"PATH": f"{self.bin}:/usr/bin:/bin", **env},
            "table": launcher.BUILT_IN_TABLE,
            "synced": {"source": launcher.SOURCE_LOCAL, "commit": None},
        }
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            launcher.install_dependencies(context, reinstall=reinstall, require_manifest=False)

        return output.getvalue().splitlines()

    def stamp(self):
        return launcher.read_json(os.path.join(self.state, "deps.json"))

    def test_installs_requirements_with_uv_into_the_project_venv(self):
        self.write("requirements.txt", "discord.py==2.7.1\n")

        self.assertEqual(
            self.install(),
            [
                "serverk: installing dependencies: uv pip install -r requirements.txt",
                f"uv pip install -r requirements.txt venv={self.venv} project={self.venv}",
                "serverk: dependencies installed",
            ],
        )
        self.assertEqual(self.install(), ["serverk: dependencies are up to date (uv)"])

    def test_installs_a_pipfile_with_pipenv_into_the_project_venv(self):
        self.write("Pipfile", '[packages]\ndiscord-py = "==2.7.1"\n')

        self.assertIn(f"pipenv install venv={self.venv} project=none", self.install())

        self.write("Pipfile.lock", "{}")

        self.assertIn("serverk: installing dependencies: pipenv install", self.install())

    def test_says_the_lockfile_is_not_used_when_installing_the_project_instead(self):
        self.write("pyproject.toml", '[project]\nname = "bot"\nversion = "1"\n')
        self.write("poetry.lock", "# poetry\n")

        self.assertEqual(
            self.install()[:2],
            [
                "serverk: poetry.lock is not used, installing from pyproject.toml",
                "serverk: installing dependencies: uv pip install .",
            ],
        )

        self.write("uv.lock", "version = 1\n")

        self.assertEqual(
            self.install(),
            [
                "serverk: installing dependencies: uv sync --locked --no-dev",
                f"uv sync --locked --no-dev venv={self.venv} project={self.venv}",
                "serverk: dependencies installed",
            ],
        )

    def test_reinstalls_when_the_lockfile_or_the_project_beside_it_changes(self):
        self.write("pyproject.toml", '[project]\nname = "bot"\nversion = "1"\n')
        self.write("uv.lock", "version = 1\n")
        self.install()
        self.write("pyproject.toml", '[project]\nname = "bot"\nversion = "2"\n')

        self.assertIn("serverk: installing dependencies: uv sync --locked --no-dev", self.install())

        self.write("uv.lock", "version = 2\n")

        self.assertIn("serverk: installing dependencies: uv sync --locked --no-dev", self.install())
        self.assertEqual(self.install(), ["serverk: dependencies are up to date (uv)"])

    def test_builds_the_venv_with_uv_for_the_python_the_files_name_and_rebuilds_when_it_changes(self):
        self.write("requirements.txt", "discord.py==2.7.1\n")
        self.write(".python-version", "3.11\n")

        lines = self.install()

        self.assertEqual(
            lines[:3],
            [
                "serverk: Python changed to 3.11, rebuilding .venv",
                "serverk: creating .venv with Python 3.11 through uv",
                f"uv venv --seed --managed-python --python 3.11 {self.venv} venv=none project=none",
            ],
        )
        self.assertIn("serverk: installing dependencies: uv pip install -r requirements.txt", lines)
        self.assertEqual(self.stamp()["runtime"], "3.11")
        self.assertEqual(self.install(), ["serverk: dependencies are up to date (uv)"])

        os.remove(os.path.join(self.project, ".python-version"))
        self.write("runtime.txt", "python-3.10.4\n")

        self.assertEqual(
            self.install()[:3],
            [
                "serverk: Python changed to 3.10, rebuilding .venv",
                "serverk: creating .venv with Python 3.10 through uv",
                f"uv venv --seed --managed-python --python 3.10 {self.venv} venv=none project=none",
            ],
        )

    def test_keeps_the_image_python_when_the_files_name_it(self):
        self.write("requirements.txt", "discord.py==2.7.1\n")
        self.write(".python-version", ".".join(platform.python_version().split(".")[:2]))

        self.assertEqual(self.install()[0], "serverk: installing dependencies: uv pip install -r requirements.txt")
        self.assertEqual(self.stamp()["runtime"], platform.python_version())

    def test_rebuilds_a_venv_on_another_python_with_no_stamp_to_say_so(self):
        self.write(".venv/pyvenv.cfg", "home = /usr/local/bin\nversion = 3.12.3\n")
        self.write(".python-version", "3.11\n")
        self.write("requirements.txt", "needs-311==1.0\n")

        self.assertIsNone(self.stamp())
        self.assertEqual(
            self.install()[:3],
            [
                "serverk: Python changed to 3.11, rebuilding .venv",
                "serverk: creating .venv with Python 3.11 through uv",
                f"uv venv --seed --managed-python --python 3.11 {self.venv} venv=none project=none",
            ],
        )

    def test_rebuilds_after_a_failed_install_once_the_files_name_another_python(self):
        self.write("requirements.txt", "needs-311==1.0\n")

        with self.assertRaises(launcher.LaunchFailure):
            self.install(FAKE_TOOL_EXIT="1")

        self.assertIsNone(self.stamp())

        self.write(".python-version", "3.11\n")

        self.assertEqual(self.install()[0], "serverk: Python changed to 3.11, rebuilding .venv")

    def test_creates_the_venv_for_the_python_the_files_name_with_nothing_to_install(self):
        shutil.rmtree(self.venv)
        self.write(".python-version", "3.11\n")

        self.assertEqual(
            self.install(),
            [
                "serverk: creating .venv with Python 3.11 through uv",
                f"uv venv --seed --managed-python --python 3.11 {self.venv} venv=none project=none",
                "serverk: no requirements.txt, Pipfile or pyproject.toml, skipping dependencies",
            ],
        )
        self.assertEqual(launcher.venv_version_of(self.project), "3.11")

    def test_leaves_the_venv_of_a_uv_lock_project_to_uv_sync(self):
        self.write("pyproject.toml", '[project]\nname = "bot"\nversion = "1"\nrequires-python = ">=3.14"\n')
        self.write("uv.lock", "version = 1\n")
        sync = [
            "serverk: installing dependencies: uv sync --locked --no-dev",
            f"uv sync --locked --no-dev venv={self.venv} project={self.venv}",
            "serverk: dependencies installed",
        ]

        self.assertEqual(self.install(), sync)

        self.write(".venv/pyvenv.cfg", "home = /x/cpython-3.14.8/bin\nversion_info = 3.14.8\n")

        self.assertEqual(self.install(), ["serverk: dependencies are up to date (uv)"])

        self.write(".python-version", "3.11\n")

        self.assertEqual(self.install(), sync)
        self.assertTrue(os.path.isfile(os.path.join(self.venv, "pyvenv.cfg")))

    def test_syncs_a_uv_lock_project_again_when_its_venv_is_gone(self):
        self.write("pyproject.toml", '[project]\nname = "bot"\nversion = "1"\n')
        self.write("uv.lock", "version = 1\n")
        self.install()
        shutil.rmtree(self.venv)

        self.assertEqual(self.install()[0], "serverk: installing dependencies: uv sync --locked --no-dev")

    def test_keeps_a_venv_whose_python_it_cannot_read(self):
        os.remove(os.path.join(self.venv, "pyvenv.cfg"))
        self.write(".python-version", "3.11\n")
        self.write("requirements.txt", "discord.py==2.7.1\n")

        self.assertEqual(self.install()[0], "serverk: installing dependencies: uv pip install -r requirements.txt")


class VenvVersionTest(unittest.TestCase):
    def test_reads_major_and_minor_from_the_venv_config_of_venv_uv_and_virtualenv(self):
        root = tempfile.mkdtemp(prefix="bot-python-venv-")

        try:
            os.makedirs(os.path.join(root, ".venv"))

            for content, version in (
                ("home = /usr/local/bin\ninclude-system-site-packages = false\nversion = 3.12.3\n", "3.12"),
                ("home = /x/cpython-3.11.16/bin\nimplementation = CPython\nuv = 0.12.23\nversion_info = 3.11.16\n", "3.11"),
                ("home = /usr/bin\nversion_info = 3.10.9.final.0\n", "3.10"),
                ("home = /usr/bin\n", None),
            ):
                with open(os.path.join(root, ".venv", "pyvenv.cfg"), "w", encoding="utf-8") as handle:
                    handle.write(content)

                self.assertEqual(launcher.venv_version_of(root), version, content)

            self.assertIsNone(launcher.venv_version_of(os.path.join(root, "missing")))
        finally:
            shutil.rmtree(root, ignore_errors=True)


class PackageFoldersTest(unittest.TestCase):
    def test_lists_top_level_folders_holding_a_main_module_and_no_symlinks(self):
        root = tempfile.mkdtemp(prefix="bot-python-packages-")

        try:
            for folder in ("mybot", "tests", "lib", "nested/inner"):
                os.makedirs(os.path.join(root, folder))

            for name in ("mybot/__main__.py", "tests/__main__.py", "nested/inner/__main__.py", "__main__.py"):
                with open(os.path.join(root, name), "w", encoding="utf-8") as handle:
                    handle.write("run()")

            os.symlink(os.path.join(root, "mybot"), os.path.join(root, "linked"))

            self.assertEqual(sorted(launcher.package_folders(root)), ["mybot", "tests"])
            self.assertEqual(
                launcher.resolve_start(root, {}, launcher.BUILT_IN_TABLE),
                {"source": "package", "argv": [".venv/bin/python", "-u", "-m", "mybot"]},
            )
            self.assertEqual(launcher.package_folders(os.path.join(root, "missing")), [])
        finally:
            shutil.rmtree(root, ignore_errors=True)


class TableTest(unittest.TestCase):
    def python_table(self, **changes):
        return json.dumps({**launcher.BUILT_IN_TABLE, "python": {**launcher.BUILT_IN_TABLE["python"], **changes}})

    def test_reads_a_table_and_refuses_a_broken_one(self):
        self.assertEqual(launcher.BUILT_IN_TABLE["version"], 2)
        self.assertEqual(launcher.table_of(json.dumps(launcher.BUILT_IN_TABLE)), launcher.BUILT_IN_TABLE)
        self.assertIsNone(launcher.table_of("{}"))
        self.assertIsNone(launcher.table_of(json.dumps({**launcher.BUILT_IN_TABLE, "version": 1})))
        self.assertIsNone(launcher.table_of(json.dumps({**launcher.BUILT_IN_TABLE, "version": 3})))

    def test_refuses_a_version_one_python_table(self):
        version_one = {
            "startFiles": ["main.py"],
            "manifests": [{"file": "requirements.txt", "manager": "requirements"}],
            "installArguments": {"requirements": ["install", "-r", "requirements.txt"]},
        }

        self.assertIsNone(launcher.table_of(json.dumps({**launcher.BUILT_IN_TABLE, "version": 1, "python": version_one})))
        self.assertIsNone(launcher.table_of(json.dumps({**launcher.BUILT_IN_TABLE, "python": version_one})))

    def test_refuses_install_commands_it_cannot_run(self):
        commands = launcher.BUILT_IN_TABLE["python"]["installCommands"]

        for broken in (
            {**commands, "uv": []},
            {**commands, "uv": ["uv", ""]},
            {**commands, "pipenv": "pipenv install"},
            {**commands, "requirements": ["sh", "-c", "pip install -r requirements.txt"]},
            {**commands, "requirements": ["pip", "install", "-r", "requirements.txt"]},
            {key: value for key, value in commands.items() if key != "pdm"},
        ):
            self.assertIsNone(launcher.table_of(self.python_table(installCommands=broken)), broken)

    def test_refuses_broken_version_files_and_lists(self):
        for changes in (
            {"versionFiles": [{"file": ".python-version", "prefix": 3}]},
            {"versionFiles": [{"tool": "python"}]},
            {"versionFiles": [{"file": "Pipfile", "key": "("}]},
            {"versionFiles": None},
            {"unhonouredManagers": None},
            {"defaultVersion": 3.12},
            {"manifests": []},
        ):
            self.assertIsNone(launcher.table_of(self.python_table(**changes)), changes)

        self.assertEqual(
            launcher.table_of(self.python_table(unhonouredManagers=[], versionFiles=[]))["python"]["versionFiles"], []
        )

    def test_falls_back_to_the_built_in_table(self):
        self.assertIs(
            launcher.load_detect_table({"SERVERK_DETECT_TABLE": "/nonexistent/detect.json"}),
            launcher.BUILT_IN_TABLE,
        )


class RequestTest(unittest.TestCase):
    def test_reads_the_json_marker_and_drops_unsafe_values(self):
        self.assertEqual(
            launcher.parse_marker(json.dumps({"deployment": "dep_1", "ref": SHA, "reinstall": True})),
            {"deployment": "dep_1", "ref": SHA, "snapshot": None, "reinstall": True},
        )
        self.assertEqual(
            launcher.parse_marker(json.dumps({"deployment": "../x", "ref": "main"})),
            {"deployment": None, "ref": None, "snapshot": None, "reinstall": False},
        )
        self.assertEqual(
            launcher.parse_marker("2026-09-27T10:00:00.000Z\n"),
            {"deployment": None, "ref": None, "snapshot": None, "reinstall": False},
        )
        self.assertIsNone(launcher.parse_marker(None))

    def test_trusts_the_configured_deployment_and_implies_one_the_bot_has_not_run(self):
        env = {"SERVERK_DEPLOYMENT_ID": "dep_new", "SERVERK_REPO_REF": SHA}
        marker = {"deployment": "dep_old", "ref": "f" * 40, "snapshot": None, "reinstall": False}

        self.assertEqual(
            launcher.resolve_request(env, marker, False, None),
            {"deployment": "dep_new", "ref": SHA, "snapshot": None, "reinstall": False, "deploying": True},
        )
        self.assertFalse(launcher.resolve_request(env, None, False, {"deployment": "dep_new", "outcome": "ready"})["deploying"])
        self.assertTrue(launcher.resolve_request(env, None, False, {"deployment": "dep_new", "outcome": "failed"})["deploying"])
        self.assertTrue(launcher.resolve_request({}, None, True, None)["reinstall"])


class SnapshotTest(unittest.TestCase):
    def test_lifts_a_single_wrapper_folder_and_skips_junk(self):
        bundle = bundle_of(
            [
                ("bot/main.py", "run()", 0o644),
                ("bot/.env.example", "TOKEN=", 0o644),
                ("bot/.git/config", "[core]", 0o644),
                ("bot/.serverk/deploy-requested", "{}", 0o644),
                ("__MACOSX/bot/._main.py", "x", 0o644),
            ]
        )

        self.assertEqual([name for _, name in launcher.snapshot_plan(bundle)], ["main.py", ".env.example"])

    def test_marker_values_must_match_whole(self):
        self.assertEqual(
            launcher.parse_marker(json.dumps({"deployment": "dep_1\n", "snapshot": "snap_1\n"})),
            {"deployment": None, "ref": None, "snapshot": None, "reinstall": False},
        )

    def test_refuses_escapes_and_symlinks(self):
        with self.assertRaises(launcher.SnapshotRefused):
            launcher.snapshot_plan(bundle_of([("../evil.py", "x", 0o644), ("main.py", "x", 0o644)]))

        with self.assertRaises(launcher.SnapshotRefused):
            launcher.snapshot_plan(bundle_of([("link", "/etc/passwd", stat.S_IFLNK | 0o777), ("main.py", "x", 0o644)]))

    def test_caps_the_expanded_size(self):
        with self.assertRaises(launcher.SnapshotRefused):
            launcher.snapshot_plan(bundle_of([("a.py", "x" * 10, 0o644), ("b.py", "y" * 10, 0o644)]), max_bytes=15)


class SourceFilesTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="bot-python-source-")
        self.app = os.path.join(self.root, "app")
        self.state = os.path.join(self.app, launcher.STATE_ENTRY)
        self.work = os.path.join(self.root, "remote-work")
        self.bare = os.path.join(self.root, "sample.git")
        self.bin = os.path.join(self.root, "bin")

        for directory in (self.state, self.work, self.bin):
            os.makedirs(directory)

        wrapper = os.path.join(self.bin, "git")

        with open(wrapper, "w", encoding="utf-8") as handle:
            handle.write(
                f'#!/bin/sh\nexec {shutil.which("git")} -c "url.file://{self.bare}.insteadOf={REMOTE}" '
                '-c protocol.file.allow=always "$@"\n'
            )

        os.chmod(wrapper, 0o755)
        self.git(self.root, "init", "--quiet", "--bare", self.bare)
        self.git(self.work, "init", "--quiet", "-b", "main")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def git(self, cwd, *args):
        result = subprocess.run(
            ["git", "-c", "user.name=Serverk", "-c", "user.email=test@serverk.gg", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )

        return result.stdout.strip()

    def commit(self, tree):
        if self.git(self.work, "ls-files"):
            self.git(self.work, "rm", "--quiet", "-r", ".")

        for name, content in tree.items():
            path = os.path.join(self.work, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)

            with open(path, "w", encoding="utf-8") as handle:
                handle.write(content)

        self.git(self.work, "add", "--all")
        self.git(self.work, "commit", "--quiet", "-m", "next")
        self.git(self.work, "push", "--quiet", self.bare, "main")

        return self.git(self.work, "rev-parse", "HEAD")

    def place(self, snapshot, tree):
        snapshots = os.path.join(self.state, launcher.SNAPSHOTS_DIR)
        os.makedirs(snapshots, exist_ok=True)

        with zipfile.ZipFile(os.path.join(snapshots, f"{snapshot}.zip"), "w") as archive:
            for name, content in tree.items():
                archive.writestr(f"bot/{name}", content)

    def sync(self, deployment, ref=None, snapshot=None, **env):
        context = {
            "app_dir": self.app,
            "state_dir": self.state,
            "env": {"PATH": f"{self.bin}:{os.environ.get('PATH', '/usr/bin:/bin')}", "HOME": self.root, **env},
            "request": {
                "deployment": deployment,
                "ref": ref,
                "snapshot": snapshot,
                "reinstall": False,
                "deploying": True,
            },
        }
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            launcher.sync_source(context)

        return output.getvalue().splitlines()

    def deploy(self, deployment, ref=None, **env):
        return self.sync(deployment, ref=ref, SERVERK_REPO_URL=REMOTE, **env)

    def read(self, name):
        with open(os.path.join(self.app, name), encoding="utf-8") as handle:
            return handle.read()

    def write(self, name, content):
        path = os.path.join(self.app, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)

    def write_runtime(self):
        for name, content in RUNTIME_FILES.items():
            self.write(name, content)

    def assert_runtime_kept(self):
        for name, content in RUNTIME_FILES.items():
            self.assertEqual(self.read(name), content)

    def lose_history(self):
        for directory in (launcher.HISTORY_DIR, launcher.SNAPSHOTS_DIR):
            shutil.rmtree(os.path.join(self.state, directory), ignore_errors=True)

    def recorded(self):
        return sorted(launcher.read_source_files(self.state) or {})

    def removed_any(self, lines):
        return any(line.startswith("serverk: removed") for line in lines)

    def test_reads_back_the_hash_of_each_file_it_wrote_and_none_outside_the_bots_own_files(self):
        manifest = os.path.join(self.state, launcher.SOURCE_FILES)

        self.assertIsNone(launcher.read_source_files(self.state))

        self.write("a.py", "a")
        self.write("src/b.py", "b")
        launcher.write_source_files(self.state, self.app, ["src/b.py", "a.py", "src/b.py", "missing.py"])
        self.assertEqual(launcher.read_source_files(self.state), {"a.py": sha("a"), "src/b.py": sha("b")})

        with open(manifest, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "files": {
                        "kept.py": sha("kept"),
                        ".gitignore": sha("ignore"),
                        "short.py": "abc",
                        "number.py": 7,
                        ".serverk/deployment.json": sha("x"),
                        ".git/config": sha("x"),
                        "lib/.git/HEAD": sha("x"),
                        "../outside.py": sha("x"),
                        "lib/../up.py": sha("x"),
                        "/etc/passwd": sha("x"),
                        "lib//double.py": sha("x"),
                        "./here.py": sha("x"),
                    }
                },
                handle,
            )

        self.assertEqual(launcher.read_source_files(self.state), {"kept.py": sha("kept"), ".gitignore": sha("ignore")})

        with open(manifest, "w", encoding="utf-8") as handle:
            json.dump({"files": ["a.py"]}, handle)

        self.assertIsNone(launcher.read_source_files(self.state))

    def test_keeps_the_bots_files_and_the_dropped_files_it_changed_replaces_what_a_commit_carries_and_drops_the_rest(
        self,
    ):
        one = self.commit({"main.py": "one()", "config.json": "one", "cogs/old.py": "old", "cogs/tuned.py": "tuned"})
        two = self.commit({"main.py": "two()", "config.json": "two"})

        self.deploy("dep_1", ref=one)
        self.write_runtime()
        self.write("config.json", "edited")
        self.write("cogs/tuned.py", "mine")

        second = self.deploy("dep_2", ref=two)

        self.assertIn(REMOVED_ONE, second)
        self.assertIn(KEPT_ONE, second)
        self.assertFalse(os.path.exists(os.path.join(self.app, "cogs", "old.py")))
        self.assertEqual(self.read("cogs/tuned.py"), "mine")
        self.assertEqual(self.read("main.py"), "two()")
        self.assertEqual(self.read("config.json"), "two")
        self.assertEqual(self.recorded(), ["config.json", "main.py"])
        self.assert_runtime_kept()

        self.write("config.json", "edited")
        rollback = self.deploy("dep_3", ref=one)

        self.assertFalse(self.removed_any(rollback))
        self.assertEqual(self.read("cogs/old.py"), "old")
        self.assertEqual(self.read("cogs/tuned.py"), "tuned")
        self.assertEqual(self.read("config.json"), "one")
        self.assert_runtime_kept()

        pull = self.deploy("dep_4", SERVERK_REPO_BRANCH="main")

        self.assertIn(REMOVED_TWO, pull)
        self.assertEqual(launcher.read_json(os.path.join(self.state, launcher.SYNC_STAMP))["commit"], two)
        self.assertFalse(os.path.exists(os.path.join(self.app, "cogs")))
        self.assert_runtime_kept()
        self.assertNotIn("data/bot.sqlite", launcher.read_source_files(self.state))

    def test_keeps_the_bots_files_and_the_dropped_files_it_changed_replaces_what_a_snapshot_carries_and_drops_the_rest(
        self,
    ):
        self.place("snap_1", {"main.py": "one()", "config.json": "one", "cogs/old.py": "old", "cogs/tuned.py": "tuned"})
        self.sync("dep_1", snapshot="snap_1")
        self.write_runtime()
        self.write("config.json", "edited")
        self.write("cogs/tuned.py", "mine")
        self.place("snap_2", {"main.py": "two()", "config.json": "two"})

        second = self.sync("dep_2", snapshot="snap_2")

        self.assertIn(REMOVED_ONE, second)
        self.assertIn(KEPT_ONE, second)
        self.assertFalse(os.path.exists(os.path.join(self.app, "cogs", "old.py")))
        self.assertEqual(self.read("cogs/tuned.py"), "mine")
        self.assertEqual(self.read("main.py"), "two()")
        self.assertEqual(self.read("config.json"), "two")
        self.assertEqual(self.recorded(), ["config.json", "main.py"])
        self.assert_runtime_kept()

        self.write("config.json", "edited")
        rollback = self.sync("dep_3", snapshot="snap_1")

        self.assertIn("serverk: restoring snapshot snap_1", rollback)
        self.assertFalse(self.removed_any(rollback))
        self.assertEqual(self.read("cogs/old.py"), "old")
        self.assertEqual(self.read("cogs/tuned.py"), "tuned")
        self.assertEqual(self.read("config.json"), "one")
        self.assert_runtime_kept()

        forward = self.sync("dep_4", snapshot="snap_2")

        self.assertIn("serverk: restoring snapshot snap_2", forward)
        self.assertIn(REMOVED_TWO, forward)
        self.assertFalse(os.path.exists(os.path.join(self.app, "cogs")))
        self.assert_runtime_kept()

    def test_lets_a_snapshots_folder_replace_a_file_the_author_changed_at_its_path_and_its_file_replace_a_folder(self):
        self.place("snap_1", {"main.py": "one()", "extras": "file"})
        self.sync("dep_1", snapshot="snap_1")
        self.write_runtime()
        self.write("extras", "mine")
        self.place("snap_2", {"main.py": "two()", "extras/a.py": "a"})

        second = self.sync("dep_2", snapshot="snap_2")

        self.assertIn(IN_THE_WAY_ONE, second)
        self.assertFalse(any(line.startswith("serverk: kept") for line in second))
        self.assertEqual(self.read("extras/a.py"), "a")
        self.assertEqual(self.recorded(), ["extras/a.py", "main.py"])

        self.write("extras/a.py", "mine")
        self.place("snap_3", {"main.py": "three()", "extras": "file again"})

        self.assertIn(IN_THE_WAY_ONE, self.sync("dep_3", snapshot="snap_3"))
        self.assertEqual(self.read("extras"), "file again")
        self.assert_runtime_kept()

    def test_lets_a_commits_folder_replace_a_file_the_author_changed_at_its_path(self):
        one = self.commit({"main.py": "one()", "extras": "file"})
        two = self.commit({"main.py": "two()", "extras/a.py": "a"})

        self.deploy("dep_1", ref=one)
        self.write_runtime()
        self.write("extras", "mine")

        second = self.deploy("dep_2", ref=two)

        self.assertIn(IN_THE_WAY_ONE, second)
        self.assertFalse(any(line.startswith("serverk: kept") for line in second))
        self.assertEqual(self.read("extras/a.py"), "a")
        self.assertEqual(self.recorded(), ["extras/a.py", "main.py"])
        self.assert_runtime_kept()

    def test_drops_what_the_last_deployment_wrote_after_a_restore_lost_the_history_or_the_git_folder(self):
        self.place("snap_1", {"main.py": "one()", "cogs/old.py": "old"})
        self.sync("dep_1", snapshot="snap_1")
        self.write_runtime()

        self.assertEqual(self.recorded(), ["cogs/old.py", "main.py"])

        self.lose_history()
        self.place("snap_2", {"main.py": "two()", "extra.py": "extra"})

        self.assertIn(REMOVED_ONE, self.sync("dep_2", snapshot="snap_2"))
        self.assertFalse(os.path.exists(os.path.join(self.app, "cogs")))
        self.assertEqual(self.recorded(), ["extra.py", "main.py"])
        self.assert_runtime_kept()

        self.lose_history()
        one = self.commit({"main.py": "git()", "config.json": "one"})

        self.assertIn(REMOVED_ONE, self.deploy("dep_3", ref=one))
        self.assertFalse(os.path.exists(os.path.join(self.app, "extra.py")))
        self.assertEqual(self.recorded(), ["config.json", "main.py"])
        self.assert_runtime_kept()

        shutil.rmtree(os.path.join(self.app, ".git"))
        two = self.commit({"main.py": "git2()"})

        self.assertIn(REMOVED_ONE, self.deploy("dep_4", ref=two))
        self.assertFalse(os.path.exists(os.path.join(self.app, "config.json")))
        self.assertEqual(self.read("main.py"), "git2()")
        self.assertEqual(self.recorded(), ["main.py"])
        self.assert_runtime_kept()


class RootDirectoryTest(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.root = tempfile.mkdtemp(prefix="bot-python-root-")
        os.makedirs(os.path.join(self.root, "apps", "bot"))

        with open(os.path.join(self.root, "file.txt"), "w", encoding="utf-8") as handle:
            handle.write("not a folder")

    def tearDown(self):
        import shutil

        shutil.rmtree(self.root, ignore_errors=True)

    def detail_of(self, root, stage="sync"):
        with self.assertRaises(launcher.LaunchFailure) as raised:
            launcher.resolve_project_dir(self.root, root, stage)

        return f"{raised.exception.stage}: {raised.exception.detail}"

    def test_takes_only_plain_relative_folder_paths(self):
        for root in ("bot", "apps/bot", "src.bot/v1.2", "a" * 255):
            self.assertTrue(launcher.is_root_directory(root), root)

        for root in ("", "/bot", "./bot", ".bot", "..", "apps/../bot", "apps//bot", "apps/bot/", "apps\\bot", "a" * 256):
            self.assertFalse(launcher.is_root_directory(root), root)

    def test_keeps_the_checkout_root_or_resolves_a_nested_folder(self):
        self.assertEqual(launcher.resolve_project_dir(self.root, None, "sync"), self.root)
        self.assertEqual(
            launcher.resolve_project_dir(self.root, "apps/bot", "sync"),
            os.path.realpath(os.path.join(self.root, "apps", "bot")),
        )

    def test_refuses_a_root_inside_serverk_or_a_git_folder(self):
        os.makedirs(os.path.join(self.root, ".serverk", "history"))
        os.makedirs(os.path.join(self.root, "apps", ".git"))
        os.symlink(os.path.join(self.root, ".serverk"), os.path.join(self.root, "state"))

        self.assertEqual(self.detail_of("state"), "sync: root directory state points inside .serverk")
        self.assertEqual(self.detail_of("apps/.git"), "sync: root directory apps/.git points inside .git")

    def test_names_a_missing_root_a_file_a_climbing_path_and_an_escaping_symlink(self):
        os.symlink("/tmp", os.path.join(self.root, "outside"))

        self.assertEqual(self.detail_of("apps/nope", "snapshot"), "snapshot: root directory apps/nope not found")
        self.assertEqual(self.detail_of("file.txt"), "sync: root directory file.txt not found")
        self.assertEqual(self.detail_of("apps/../.."), "sync: root directory apps/../.. is not valid")
        self.assertEqual(self.detail_of("outside"), "sync: root directory outside leaves the bot folder")


class LinesTest(unittest.TestCase):
    def test_prints_the_deployment_lines(self):
        self.assertEqual(
            launcher.deployment_line("dep_1", launcher.OUTCOME_READY, commit=SHA),
            "serverk: deployment dep_1 ready at 0123456789ab",
        )
        self.assertEqual(launcher.deployment_line("dep_1", launcher.OUTCOME_READY), "serverk: deployment dep_1 ready")
        self.assertEqual(
            launcher.deployment_line("dep_1", launcher.OUTCOME_FAILED, stage="install", detail="pip\n  failed"),
            "serverk: deployment dep_1 failed: install: pip failed",
        )

    def test_strips_every_launcher_internal(self):
        self.assertEqual(
            launcher.bot_environment(
                {
                    "SERVERK_GIT_TOKEN": "ghs_installation",
                    "SERVERK_REPO_REF": SHA,
                    "SERVERK_INSTALL_COMMAND": "pip install .",
                    "TELEGRAM_TOKEN": "token",
                    "SERVERK_BOT": "1",
                }
            ),
            {"TELEGRAM_TOKEN": "token", "SERVERK_BOT": "1"},
        )

    def test_prints_the_ready_line_the_lifecycle_waits_for(self):
        self.assertEqual(launcher.READY_LINE, "serverk: bot process starting")

    def test_records_a_ready_deployment_without_announcing_it(self):
        state_dir = tempfile.mkdtemp(prefix="bot-python-record-")
        self.addCleanup(shutil.rmtree, state_dir, True)
        context = {
            "env": {},
            "state_dir": state_dir,
            "request": {"deployment": "dep_1", "ref": None, "snapshot": "snap_1", "deploying": True},
        }
        printed = io.StringIO()

        with contextlib.redirect_stdout(printed):
            launcher.record_deployment(context, launcher.OUTCOME_READY, source=launcher.SOURCE_SNAPSHOT)

        self.assertEqual(printed.getvalue(), "")

        with open(os.path.join(state_dir, launcher.DEPLOYMENT_STAMP), encoding="utf-8") as stamp:
            written = json.load(stamp)

        self.assertEqual(written["outcome"], launcher.OUTCOME_READY)
        self.assertFalse(written["settled"])

        with contextlib.redirect_stdout(printed):
            launcher.record_deployment(
                context, launcher.OUTCOME_FAILED, source=launcher.SOURCE_SNAPSHOT, stage="install", detail="nope"
            )

        self.assertEqual(printed.getvalue(), "serverk: deployment dep_1 failed: install: nope\n")


class EnterStageTest(unittest.TestCase):
    def enter(self, request, stage):
        context = {"request": request, "stage": launcher.STAGE_SYNC}
        printed = io.StringIO()

        with contextlib.redirect_stdout(printed):
            launcher.enter_stage(context, stage)

        return context["stage"], printed.getvalue()

    def test_prints_the_stage_a_deployment_enters(self):
        self.assertEqual(
            self.enter({"deployment": "dep_1", "deploying": True}, launcher.STAGE_INSTALL),
            (launcher.STAGE_INSTALL, "serverk: deployment dep_1 stage install\n"),
        )

    def test_prints_nothing_without_a_deployment_in_flight(self):
        self.assertEqual(
            self.enter({"deployment": "dep_1", "deploying": False}, launcher.STAGE_START),
            (launcher.STAGE_START, ""),
        )
        self.assertEqual(
            self.enter({"deployment": None, "deploying": True}, launcher.STAGE_START),
            (launcher.STAGE_START, ""),
        )
        self.assertEqual(self.enter(None, launcher.STAGE_SNAPSHOT), (launcher.STAGE_SNAPSHOT, ""))


class StartRetryTest(unittest.TestCase):
    FAILED = {"deployment": "dep_1", "source": "git", "commit": SHA, "outcome": "failed", "stage": "start"}

    def test_claims_a_failed_start_only_while_the_code_on_disk_is_its_own(self):
        request = {"deploying": False}

        self.assertEqual(launcher.start_retry_of(request, self.FAILED, {"source": "git", "commit": SHA}), self.FAILED)
        self.assertIsNone(launcher.start_retry_of(request, self.FAILED, {"source": "git", "commit": "f" * 40}))
        self.assertIsNone(launcher.start_retry_of({"deploying": True}, self.FAILED, {"source": "git", "commit": SHA}))
        self.assertIsNone(
            launcher.start_retry_of(request, {**self.FAILED, "stage": "install"}, {"source": "git", "commit": SHA})
        )
        self.assertEqual(
            launcher.start_retry_of(request, {**self.FAILED, "source": "snapshot"}, {"source": "local", "commit": None}),
            {**self.FAILED, "source": "snapshot"},
        )


class StageFailureTest(unittest.TestCase):
    def test_names_an_install_the_memory_limit_killed_out_of_memory(self):
        failure = launcher.stage_failure(launcher.STAGE_INSTALL, launcher.INSTALL_HINT, -9, "Resolved 12 packages")

        self.assertEqual(failure.stage, launcher.STAGE_INSTALL)
        self.assertEqual(failure.detail, "out-of-memory")
        self.assertEqual(failure.arabic, launcher.MEMORY_HINT)

    def test_keeps_the_reason_of_an_install_that_exited_137_on_its_own(self):
        failure = launcher.stage_failure(launcher.STAGE_INSTALL, launcher.INSTALL_HINT, 137, "Killed")

        self.assertEqual(failure.detail, "Killed")

    def test_keeps_the_reason_of_an_install_that_failed_on_its_own(self):
        failure = launcher.stage_failure(launcher.STAGE_INSTALL, launcher.INSTALL_HINT, 1, "No solution found")

        self.assertEqual(failure.detail, "No solution found")
        self.assertEqual(failure.english, "install failed: No solution found")


if __name__ == "__main__":
    unittest.main()
