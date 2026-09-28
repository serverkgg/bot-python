import io
import json
import os
import stat
import unittest
import zipfile

import launcher

TEMPLATES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates")

SHA = "0123456789abcdef0123456789abcdef01234567"


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

    def test_reads_a_worker_or_bot_procfile_line_last(self):
        self.assertEqual(launcher.procfile_command("web: gunicorn app\nbot: python bot/run.py\n"), "python bot/run.py")
        self.assertEqual(launcher.procfile_command("bot: python a.py\nworker: python b.py"), "python b.py")
        self.assertIsNone(launcher.procfile_command("web: gunicorn app"))

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


class TableTest(unittest.TestCase):
    def test_reads_a_table_and_refuses_a_broken_one(self):
        self.assertEqual(launcher.table_of(json.dumps(launcher.BUILT_IN_TABLE)), launcher.BUILT_IN_TABLE)
        self.assertIsNone(launcher.table_of("{}"))
        self.assertIsNone(launcher.table_of(json.dumps({**launcher.BUILT_IN_TABLE, "version": 2})))

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


if __name__ == "__main__":
    unittest.main()
