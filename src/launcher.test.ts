import { afterEach, beforeEach, describe, expect, test } from "bun:test";
import {
	existsSync,
	mkdirSync,
	mkdtempSync,
	readdirSync,
	readFileSync,
	realpathSync,
	rmSync,
	symlinkSync,
	writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
	BOT_STATE_DIR,
	BotDeploymentOutcome,
	BotDeploymentStage,
	BotFramework,
	BotPlatform,
	BotRuntime,
	DEPLOY_MARKER as BRIDGE_DEPLOY_MARKER,
	LAUNCHER_KEYS as BRIDGE_LAUNCHER_KEYS,
	botDeploymentStateSchema,
	DEPLOYMENT_ID_PATTERN,
	DEPLOYMENT_LINE,
	DEPLOYMENT_STATE_FILE,
	DETECT_TABLE,
	deploymentLine,
	detect,
	detectWantedFiles,
	parseServerkJson,
	REPO_BRANCH_PATTERN,
	REPO_REF_PATTERN,
	REPO_URL_PATTERN,
	ROOT_DIRECTORY_PATTERN,
	renderDetectTable,
	SNAPSHOT_ID_PATTERN,
} from "@serverkgg/bridge/bot";
import { READY_LINE } from "./lifecycle";
import { STATE_DIR } from "./shared";

const ROOT = new URL("..", import.meta.url).pathname;

const IMAGE = join(ROOT, "image");

const LAUNCHER = join(IMAGE, "launcher.py");

const TABLE_FILE = join(IMAGE, "detect.json");

const TEMPLATES = join(ROOT, "templates");

const PYTHON = Bun.which("python3") ?? "python3";

const SHA = "0123456789abcdef0123456789abcdef01234567";

const REMOTE = "https://example.test/bots/sample";

const RESUME_KEY = "SERVERK_LAUNCH_RESUME";

const NPM_404_TRANSCRIPT = [
	"npm error code E404",
	"npm error 404 Not Found - GET https://registry.npmjs.org/serverk-no-such-package-e404-proof - Not found",
	"npm error 404",
	"npm error 404  The requested resource 'serverk-no-such-package-e404-proof@^1.0.0' could not be found or you do not have permission to access it.",
	"npm error 404",
	"npm error 404 Note that you can also install from a",
	"npm error 404 tarball, folder, http url, or git url.",
	"npm error A complete log of this run can be found in: /home/container/.serverk/cache/npm/_logs/2026-09-27T21_10_25_351Z-debug-0.log",
];

const PIP_BUILD_TRANSCRIPT = [
	"  error: subprocess-exited-with-error",
	"  × python setup.py egg_info did not run successfully.",
	"  │ exit code: 1",
	"  ╰─> [3 lines of output]",
	"      RuntimeError: this package cannot build here",
	"      [end of output]",
	"  note: This error originates from a subprocess, and is likely not a problem with pip.",
	"error: metadata-generation-failed",
	"",
	"× Encountered error while generating package metadata.",
	"╰─> See above for output.",
	"",
	"note: This is an issue with the package mentioned above, not pip.",
	"hint: See above for details.",
];

const transcriptScript = (lines: string[]) => {
	return `#!/bin/sh\ncat >&2 <<'TRANSCRIPT'\n${lines.join("\n")}\nTRANSCRIPT\nexit 1\n`;
};

const SAMPLES = {
	links: [
		"https://github.com/you/bot",
		"https://gitlab.com/group/sub/bot.git",
		"https://user:pw@github.com/you/bot",
		"http://github.com/you/bot",
		"git@github.com:you/bot.git",
	],
	branches: [
		"main",
		"feature/login",
		"deps/HEAD",
		"a.locked",
		"-rf",
		"a b",
		".hidden",
		"HEAD",
		"a..b",
		"a//b",
		"/main",
		"main/",
		"main.",
		"a/.hidden",
		"main.lock",
		"a.lock/b",
		"a@{1}",
		"a~1",
		"main\n",
	],
	refs: [
		SHA,
		"a".repeat(64),
		SHA.slice(0, 12),
		SHA.toUpperCase(),
		"main",
	],
	ids: [
		"dep_a1b2c3d4",
		"snap-1",
		"../x",
		"a".repeat(65),
		"",
		"dep_1\n",
	],
	roots: [
		"bot",
		"apps/bot",
		"src.bot/v1.2",
		"/bot",
		"./bot",
		".bot",
		"..",
		"apps/../bot",
		"apps//bot",
		"apps/bot/",
		"apps bot",
	],
};

const python = (script: string) => {
	const result = Bun.spawnSync(
		[
			PYTHON,
			"-c",
			script,
		],
		{
			cwd: IMAGE,
			env: {
				...process.env,
				PYTHONDONTWRITEBYTECODE: "1",
			},
			stdout: "pipe",
			stderr: "pipe",
		},
	);

	return JSON.parse(result.stdout.toString());
};

describe("the python launcher", () => {
	test("passes its own unit tests against the templates", () => {
		const result = Bun.spawnSync(
			[
				PYTHON,
				"-m",
				"unittest",
				"discover",
				"-s",
				IMAGE,
				"-t",
				IMAGE,
				"-p",
				"test_*.py",
			],
			{
				cwd: IMAGE,
				env: {
					...process.env,
					PYTHONDONTWRITEBYTECODE: "1",
				},
				stdout: "pipe",
				stderr: "pipe",
			},
		);

		expect(result.stderr.toString()).toContain("OK");
		expect(result.exitCode).toBe(0);
	});

	test("reads the table the bridge renders and falls back to the same table built in", () => {
		expect(readFileSync(TABLE_FILE, "utf8")).toBe(renderDetectTable());

		const answer = python(
			[
				"import json, launcher",
				`table = launcher.table_of(open(${JSON.stringify(TABLE_FILE)}).read())`,
				"print(json.dumps({'loaded': table, 'builtIn': launcher.BUILT_IN_TABLE}))",
			].join("\n"),
		);

		const expected = {
			version: DETECT_TABLE.version,
			procfile: DETECT_TABLE.procfile,
			serverkJson: DETECT_TABLE.serverkJson,
			python: DETECT_TABLE.python,
		};

		expect(answer.loaded).toEqual(expected);
		expect(answer.builtIn).toEqual(expected);
	});

	test("agrees with the driver and the bridge on every line, marker, key and pattern it reads", () => {
		const answer = python(
			[
				"import json, launcher",
				`samples = ${JSON.stringify(SAMPLES)}`,
				"print(json.dumps({",
				"'ready': launcher.READY_LINE,",
				"'deploy': launcher.DEPLOY_MARKER,",
				"'state': launcher.DEFAULT_STATE_DIR,",
				"'keys': sorted(launcher.LAUNCHER_KEYS),",
				"'links': [bool(launcher.REPO_URL_PATTERN.fullmatch(value)) for value in samples['links']],",
				"'branches': [bool(launcher.REPO_BRANCH_PATTERN.fullmatch(value)) for value in samples['branches']],",
				"'refs': [bool(launcher.REPO_REF_PATTERN.fullmatch(value)) for value in samples['refs']],",
				"'ids': [bool(launcher.ID_PATTERN.fullmatch(value)) for value in samples['ids']],",
				"'roots': [launcher.is_root_directory(value) for value in samples['roots']],",
				`'readyLine': launcher.deployment_line('dep_1', launcher.OUTCOME_READY, commit=${JSON.stringify(SHA)}),`,
				"'plainLine': launcher.deployment_line('dep_1', launcher.OUTCOME_READY),",
				"'failedLine': launcher.deployment_line('dep_1', launcher.OUTCOME_FAILED, stage='install', detail='pip\\n  failed'),",
				"}))",
			].join("\n"),
		);

		expect(READY_LINE.test(answer.ready)).toBe(true);
		expect(`${BOT_STATE_DIR}/${answer.deploy}`).toBe(BRIDGE_DEPLOY_MARKER);
		expect(answer.state).toBe(STATE_DIR);
		expect(answer.keys).toEqual(
			[
				...BRIDGE_LAUNCHER_KEYS,
				RESUME_KEY,
			].sort(),
		);
		expect(answer.links).toEqual(SAMPLES.links.map((value) => REPO_URL_PATTERN.test(value)));
		expect(answer.branches).toEqual(SAMPLES.branches.map((value) => REPO_BRANCH_PATTERN.test(value)));
		expect(answer.refs).toEqual(SAMPLES.refs.map((value) => REPO_REF_PATTERN.test(value)));
		expect(answer.ids).toEqual(SAMPLES.ids.map((value) => DEPLOYMENT_ID_PATTERN.test(value)));
		expect(answer.ids).toEqual(SAMPLES.ids.map((value) => SNAPSHOT_ID_PATTERN.test(value)));
		expect(answer.roots).toEqual(SAMPLES.roots.map((value) => ROOT_DIRECTORY_PATTERN.test(value)));
		expect(answer.readyLine).toBe(
			deploymentLine({
				deployment: "dep_1",
				outcome: BotDeploymentOutcome.Ready,
				commit: SHA,
			}),
		);
		expect(answer.plainLine).toBe(
			deploymentLine({
				deployment: "dep_1",
				outcome: BotDeploymentOutcome.Ready,
				commit: null,
			}),
		);
		expect(answer.failedLine).toBe(
			deploymentLine({
				deployment: "dep_1",
				outcome: BotDeploymentOutcome.Failed,
				stage: BotDeploymentStage.Install,
				detail: "pip\n  failed",
			}),
		);
	});
});

const SERVERK_JSON_SAMPLES = [
	"{}",
	JSON.stringify({
		start: " python -m bot ",
		install: "pip install -r requirements/prod.txt",
	}),
	JSON.stringify({
		runtime: "python",
		platform: "telegram",
		framework: "aiogram",
		start: "python bot.py",
		env: [
			"GUILD_ID",
			{
				key: "TELEGRAM_TOKEN",
				sensitive: true,
				example: "x",
			},
		],
	}),
	JSON.stringify({
		runtime: "go",
		start: "python bot.py",
	}),
	JSON.stringify({
		framework: "flask",
		start: "python bot.py",
	}),
	JSON.stringify({
		start: "",
	}),
	JSON.stringify({
		start: "a\nb",
	}),
	JSON.stringify({
		start: " python bot.py﻿",
	}),
	JSON.stringify({
		install: [
			"pip",
			"install",
		],
	}),
	JSON.stringify({
		start: "x".repeat(1024),
	}),
	JSON.stringify({
		start: "x".repeat(1025),
	}),
	JSON.stringify({
		start: `echo ${"🤖".repeat(1019)}`,
	}),
	JSON.stringify({
		start: "python bot.py",
		env: [
			"1BAD",
		],
	}),
	JSON.stringify({
		start: "python bot.py",
		env: [
			"KEY\n",
		],
	}),
	JSON.stringify({
		start: "python bot.py",
		env: [
			{
				key: "A",
				sensitive: "yes",
			},
		],
	}),
	JSON.stringify({
		start: "python bot.py",
		env: [
			{
				key: "A",
				example: "x".repeat(257),
			},
		],
	}),
	JSON.stringify({
		start: "python bot.py",
		env: Array.from(
			{
				length: 101,
			},
			(_, index) => `KEY_${index}`,
		),
	}),
	'{"start": "python bot.py", "n": NaN}',
	"[]",
	"null",
	"not json",
];

describe("reading serverk.json", () => {
	test("agrees with the bridge's parser on every sample, broken files included", () => {
		const answer = python(
			[
				"import json, launcher",
				`samples = json.loads(${JSON.stringify(JSON.stringify(SERVERK_JSON_SAMPLES))})`,
				"print(json.dumps([launcher.serverk_json_of(sample) for sample in samples]))",
			].join("\n"),
		);

		expect(answer).toEqual(
			SERVERK_JSON_SAMPLES.map((sample) => {
				const parsed = parseServerkJson(sample);

				return parsed
					? {
							start: parsed.start,
							install: parsed.install,
						}
					: null;
			}),
		);
	});
});

describe("the templates as the platform inspects them", () => {
	const inspect = (name: string) => {
		const dir = join(TEMPLATES, name);
		const files = readdirSync(dir).map((path) => ({
			path,
		}));
		const contents = Object.fromEntries(
			detectWantedFiles(files).map((path) => [
				path,
				readFileSync(join(dir, path), "utf8"),
			]),
		);

		return detect({
			files,
			contents,
		});
	};

	test("detects each template cleanly and agrees with the launcher on how to start it", () => {
		const expected = {
			"discord-python": {
				platform: BotPlatform.Discord,
				framework: BotFramework.DiscordPy,
				tokenKey: "DISCORD_TOKEN",
			},
			"telegram-python": {
				platform: BotPlatform.Telegram,
				framework: BotFramework.PythonTelegramBot,
				tokenKey: "TELEGRAM_TOKEN",
			},
		};

		for (const [name, wanted] of Object.entries(expected)) {
			expect(inspect(name)).toMatchObject({
				runtime: BotRuntime.Python,
				package: "bot-python",
				install: {
					command: "pip install -r requirements.txt",
				},
				start: {
					command: "python main.py",
				},
				warnings: [],
				...wanted,
			});
		}
	});
});

describe("running the launcher", () => {
	let root = "";
	let app = "";
	let state = "";

	const zipOf = (name: string, files: Record<string, string>) => {
		const source = join(root, `${name}-source`, "bot");

		for (const [file, content] of Object.entries(files)) {
			mkdirSync(join(source, file, ".."), {
				recursive: true,
			});
			writeFileSync(join(source, file), content);
		}

		const archive = join(root, `${name}.zip`);

		Bun.spawnSync(
			[
				PYTHON,
				"-m",
				"zipfile",
				"-c",
				archive,
				"bot",
			],
			{
				cwd: join(root, `${name}-source`),
			},
		);

		return archive;
	};

	const place = (archive: string, snapshot: string) => {
		mkdirSync(join(state, "snapshots"), {
			recursive: true,
		});
		writeFileSync(join(state, "snapshots", `${snapshot}.zip`), readFileSync(archive));
	};

	const launch = (env: Record<string, string>, mode: string[] = []) => {
		const result = Bun.spawnSync(
			[
				PYTHON,
				LAUNCHER,
				...mode,
			],
			{
				cwd: app,
				env: {
					PATH: process.env.PATH ?? "/usr/bin:/bin",
					HOME: root,
					PYTHONDONTWRITEBYTECODE: "1",
					SERVERK_STATE_DIR: state,
					SERVERK_DETECT_TABLE: TABLE_FILE,
					SERVERK_START_COMMAND: "echo the bot ran",
					...env,
				},
				stdout: "pipe",
				stderr: "pipe",
			},
		);

		return {
			code: result.exitCode,
			lines: result.stdout.toString().trim().split("\n"),
		};
	};

	const historyCount = () => {
		const result = Bun.spawnSync(
			[
				"git",
				`--git-dir=${join(state, "history")}`,
				"rev-list",
				"--all",
				"--count",
			],
			{
				stdout: "pipe",
			},
		);

		return Number(result.stdout.toString().trim());
	};

	const stamp = () => {
		return botDeploymentStateSchema.parse(JSON.parse(readFileSync(join(app, DEPLOYMENT_STATE_FILE), "utf8")));
	};

	beforeEach(() => {
		root = mkdtempSync(join(tmpdir(), "bot-python-launcher-"));
		app = join(root, "app");
		state = join(app, BOT_STATE_DIR);

		mkdirSync(join(app, ".venv", "bin"), {
			recursive: true,
		});
		mkdirSync(state, {
			recursive: true,
		});
		symlinkSync(PYTHON, join(app, ".venv", "bin", "python"));
	});

	afterEach(() => {
		rmSync(root, {
			force: true,
			recursive: true,
		});
	});

	test("deploys an uploaded snapshot, drops what the next one deleted and rolls back without a download", () => {
		place(
			zipOf("one", {
				"main.py": "one()",
				".env.example": "TELEGRAM_TOKEN=",
				"lib/old.py": "old",
			}),
			"snap_1",
		);

		const first = launch({
			SERVERK_SNAPSHOT_ID: "snap_1",
			SERVERK_DEPLOYMENT_ID: "dep_1",
		});

		expect(first.code).toBe(0);
		expect(first.lines.slice(-4)).toEqual([
			"serverk: deployment dep_1 ready",
			"serverk: start command: sh -c exec echo the bot ran",
			"serverk: bot process starting",
			"the bot ran",
		]);
		expect(readFileSync(join(app, ".env.example"), "utf8")).toBe("TELEGRAM_TOKEN=");

		writeFileSync(join(app, "data.db"), "runtime");
		place(
			zipOf("two", {
				"main.py": "two()",
			}),
			"snap_2",
		);

		expect(
			launch({
				SERVERK_SNAPSHOT_ID: "snap_2",
				SERVERK_DEPLOYMENT_ID: "dep_2",
			}).code,
		).toBe(0);
		expect(existsSync(join(app, "lib"))).toBe(false);
		expect(readFileSync(join(app, "data.db"), "utf8")).toBe("runtime");
		expect(historyCount()).toBe(2);

		const rollback = launch({
			SERVERK_SNAPSHOT_ID: "snap_1",
			SERVERK_DEPLOYMENT_ID: "dep_3",
		});

		expect(rollback.lines).toContain("serverk: restoring snapshot snap_1");
		expect(readFileSync(join(app, "lib", "old.py"), "utf8")).toBe("old");
		expect(historyCount()).toBe(2);
		expect(stamp()).toMatchObject({
			deployment: "dep_3",
			source: "snapshot",
			outcome: "ready",
		});

		const again = launch({
			SERVERK_SNAPSHOT_ID: "snap_1",
			SERVERK_DEPLOYMENT_ID: "dep_3",
		});

		expect(again.lines.some((line) => DEPLOYMENT_LINE.test(line))).toBe(false);
		expect(historyCount()).toBe(2);

		expect(
			launch({
				SERVERK_SNAPSHOT_ID: "snap_2",
				SERVERK_DEPLOYMENT_ID: "dep_4",
			}).lines,
		).toContain("serverk: restoring snapshot snap_2");
		expect(existsSync(join(app, "lib"))).toBe(false);
		expect(historyCount()).toBe(2);
	});

	test("ends a failed deployment with the failure line and records it", () => {
		const { code, lines } = launch({
			SERVERK_SNAPSHOT_ID: "snap_missing",
			SERVERK_DEPLOYMENT_ID: "dep_9",
		});

		expect(code).toBe(1);
		expect(lines.at(-1)).toBe("serverk: deployment dep_9 failed: snapshot: snapshot snap_missing is not on this bot");
		expect(stamp()).toMatchObject({
			deployment: "dep_9",
			outcome: "failed",
			stage: "snapshot",
		});
	});

	test("runs the customer's install command inside the venv and reinstalls when it changes", () => {
		const first = launch({
			SERVERK_INSTALL_COMMAND: "echo custom install",
		});

		expect(first.lines).toContain("serverk: installing dependencies: echo custom install");
		expect(first.lines).toContain("custom install");
		expect(
			launch({
				SERVERK_INSTALL_COMMAND: "echo custom install",
			}).lines,
		).toContain("serverk: dependencies are up to date (custom)");
		expect(
			launch({
				SERVERK_INSTALL_COMMAND: "echo another install",
			}).lines,
		).toContain("serverk: installing dependencies: echo another install");

		const failing = launch(
			{
				SERVERK_INSTALL_COMMAND: "echo nope; exit 3",
				SERVERK_DEPLOYMENT_ID: "dep_1",
			},
			[
				"install",
			],
		);

		expect(failing.code).toBe(1);
		expect(failing.lines.at(-1)).toBe("serverk: install failed: nope");
		expect(failing.lines.some((line) => DEPLOYMENT_LINE.test(line))).toBe(false);
	});
	const fakeVenv = (folder: string) => {
		mkdirSync(join(app, folder, ".venv", "bin"), {
			recursive: true,
		});
		symlinkSync(PYTHON, join(app, folder, ".venv", "bin", "python"));
	};

	const MAIN = "import os\nprint(f'cwd {os.getcwd()}', flush=True)\n";

	const wrappedPath = (bare: string) => {
		const bin = join(root, "bin");
		const real = Bun.which("git") ?? "/usr/bin/git";

		mkdirSync(bin, {
			recursive: true,
		});
		writeFileSync(
			join(bin, "git"),
			`#!/bin/sh\nexec ${real} -c "url.file://${bare}.insteadOf=${REMOTE}" -c protocol.file.allow=always "$@"\n`,
			{
				mode: 0o755,
			},
		);

		return `${bin}:${process.env.PATH ?? "/usr/bin:/bin"}`;
	};

	const gitRemote = (files: Record<string, string>) => {
		const work = join(root, "remote-work");
		const bare = join(root, "sample.git");
		const git = (cwd: string, ...args: string[]) => {
			return Bun.spawnSync(
				[
					"git",
					"-c",
					"user.name=Serverk",
					"-c",
					"user.email=test@serverk.gg",
					...args,
				],
				{
					cwd,
					stdout: "pipe",
				},
			)
				.stdout.toString()
				.trim();
		};

		for (const [file, content] of Object.entries(files)) {
			mkdirSync(join(work, file, ".."), {
				recursive: true,
			});
			writeFileSync(join(work, file), content);
		}

		git(root, "init", "--quiet", "--bare", bare);
		git(work, "init", "--quiet", "-b", "main");
		git(work, "add", "--all");
		git(work, "commit", "--quiet", "-m", "one");
		git(work, "push", "--quiet", bare, "main");

		return {
			sha: git(work, "rev-parse", "HEAD"),
			env: {
				PATH: wrappedPath(bare),
				SERVERK_REPO_URL: REMOTE,
			},
		};
	};

	test("runs a pinned commit from its root directory, never from the checkout root", () => {
		const work = join(root, "remote-work");
		const bare = join(root, "sample.git");
		const git = (cwd: string, ...args: string[]) => {
			return Bun.spawnSync(
				[
					"git",
					"-c",
					"user.name=Serverk",
					"-c",
					"user.email=test@serverk.gg",
					...args,
				],
				{
					cwd,
					stdout: "pipe",
				},
			)
				.stdout.toString()
				.trim();
		};

		mkdirSync(join(work, "app"), {
			recursive: true,
		});
		writeFileSync(join(work, "app", "main.py"), MAIN);
		writeFileSync(join(work, "README.md"), "sibling");
		git(root, "init", "--quiet", "--bare", bare);
		git(work, "init", "--quiet", "-b", "main");
		git(work, "add", "--all");
		git(work, "commit", "--quiet", "-m", "one");
		git(work, "push", "--quiet", bare, "main");

		const sha = git(work, "rev-parse", "HEAD");

		fakeVenv("app");
		writeFileSync(
			join(state, "sync.json"),
			JSON.stringify({
				source: "snapshot",
			}),
		);

		const { code, lines } = launch({
			PATH: wrappedPath(bare),
			SERVERK_REPO_URL: REMOTE,
			SERVERK_REPO_REF: sha,
			SERVERK_START_COMMAND: "",
			SERVERK_DEPLOYMENT_ID: "dep_1",
			SERVERK_ROOT_DIRECTORY: "app",
		});

		expect(code).toBe(0);
		expect(lines).toContain(`serverk: deployment dep_1 ready at ${sha.slice(0, 12)}`);
		expect(lines).toContain("serverk: start command: .venv/bin/python -u main.py");
		expect(lines.at(-1)).toBe(`cwd ${realpathSync(join(app, "app"))}`);
		expect(readFileSync(join(app, "README.md"), "utf8")).toBe("sibling");
	});

	test("runs an uploaded snapshot from its root directory and fails the source stage on a missing one", () => {
		fakeVenv("app");
		place(
			zipOf("rooted", {
				"app/main.py": MAIN,
				"README.md": "sibling",
			}),
			"snap_r",
		);

		const rooted = launch({
			SERVERK_START_COMMAND: "",
			SERVERK_SNAPSHOT_ID: "snap_r",
			SERVERK_DEPLOYMENT_ID: "dep_r",
			SERVERK_ROOT_DIRECTORY: "app",
		});

		expect(rooted.code).toBe(0);
		expect(rooted.lines.at(-1)).toBe(`cwd ${realpathSync(join(app, "app"))}`);
		expect(readFileSync(join(app, "README.md"), "utf8")).toBe("sibling");

		const missing = launch({
			SERVERK_SNAPSHOT_ID: "snap_r",
			SERVERK_DEPLOYMENT_ID: "dep_m",
			SERVERK_ROOT_DIRECTORY: "nope",
		});

		expect(missing.code).toBe(78);
		expect(missing.lines.at(-1)).toBe("serverk: deployment dep_m failed: snapshot: root directory nope not found");
		expect(stamp()).toMatchObject({
			outcome: "failed",
			stage: "snapshot",
			detail: "root directory nope not found",
		});
		expect(
			launch({
				SERVERK_DEPLOYMENT_ID: "dep_c",
				SERVERK_ROOT_DIRECTORY: "..",
			}).lines.at(-1),
		).toBe("serverk: deployment dep_c failed: sync: root directory .. is not valid");
	});

	test("reinstalls when the root directory changes", () => {
		for (const folder of [
			"one",
			"two",
		]) {
			fakeVenv(folder);
		}

		const install = (folder: string) => {
			return launch({
				SERVERK_ROOT_DIRECTORY: folder,
				SERVERK_INSTALL_COMMAND: "echo custom install",
			}).lines;
		};

		expect(install("one")).toContain("serverk: installing dependencies: echo custom install");
		expect(install("one")).toContain("serverk: dependencies are up to date (custom)");
		expect(install("two")).toContain("serverk: installing dependencies: echo custom install");
	});

	const historyTags = () => {
		return Bun.spawnSync(
			[
				"git",
				`--git-dir=${join(state, "history")}`,
				"tag",
				"--list",
			],
			{
				stdout: "pipe",
			},
		)
			.stdout.toString()
			.split("\n")
			.filter((line) => line.length > 0);
	};

	const corrupted = (archive: string) => {
		const bytes = readFileSync(archive);
		const data = 30 + bytes.readUInt16LE(26) + bytes.readUInt16LE(28);

		bytes[data + 2] = (bytes[data + 2] ?? 0) ^ 0xff;
		bytes[data + 3] = (bytes[data + 3] ?? 0) ^ 0xff;

		const broken = `${archive}.broken`;

		writeFileSync(broken, bytes);

		return broken;
	};

	test("runs a start command that sets a variable before the program", () => {
		const { code, lines } = launch({
			SERVERK_START_COMMAND: "GREETING=hello sh -c 'echo greeting $GREETING'",
		});

		expect(code).toBe(0);
		expect(lines).toContain("serverk: start command: sh -c exec env GREETING=hello sh -c 'echo greeting $GREETING'");
		expect(lines.at(-1)).toBe("greeting hello");
	});

	test("installs and starts with the commands serverk.json declares", () => {
		writeFileSync(
			join(app, "serverk.json"),
			JSON.stringify({
				install: "echo declared install",
				start: "echo declared start",
			}),
		);

		const { code, lines } = launch({
			SERVERK_START_COMMAND: "",
		});

		expect(code).toBe(0);
		expect(lines).toContain("serverk: installing dependencies: echo declared install");
		expect(lines.at(-1)).toBe("declared start");
	});

	test("keeps the customer's PYTHON variables away from the launcher", () => {
		mkdirSync(join(root, "inject"), {
			recursive: true,
		});
		writeFileSync(join(root, "inject", "sitecustomize.py"), "print('injected', flush=True)\n");

		const result = Bun.spawnSync(
			[
				PYTHON,
				"-I",
				LAUNCHER,
			],
			{
				cwd: app,
				env: {
					PATH: process.env.PATH ?? "/usr/bin:/bin",
					HOME: root,
					PYTHONPATH: join(root, "inject"),
					SERVERK_STATE_DIR: state,
					SERVERK_DETECT_TABLE: TABLE_FILE,
					SERVERK_START_COMMAND: "echo the bot ran",
				},
				stdout: "pipe",
				stderr: "pipe",
			},
		);
		const lines = result.stdout.toString().trim().split("\n");

		expect(result.exitCode).toBe(0);
		expect(lines).not.toContain("injected");
		expect(lines.at(-1)).toBe("the bot ran");
	});

	test("boots uploaded code after a restore that dropped the history and the zips, and rebuilds the history later", () => {
		place(
			zipOf("one", {
				"main.py": "one()",
			}),
			"snap_1",
		);

		const env = {
			SERVERK_SNAPSHOT_ID: "snap_1",
			SERVERK_DEPLOYMENT_ID: "dep_1",
		};

		expect(launch(env).code).toBe(0);

		rmSync(join(state, "history"), {
			force: true,
			recursive: true,
		});
		rmSync(join(state, "snapshots"), {
			force: true,
			recursive: true,
		});

		expect(
			launch(env, [
				"install",
			]).code,
		).toBe(0);

		const start = launch(env);

		expect(start.code).toBe(0);
		expect(start.lines).toContain("serverk: code is at snapshot snap_1");
		expect(start.lines.slice(-2)).toEqual([
			"serverk: bot process starting",
			"the bot ran",
		]);
		expect(start.lines.some((line) => DEPLOYMENT_LINE.test(line))).toBe(false);
		expect(stamp()).toMatchObject({
			deployment: "dep_1",
			outcome: "ready",
		});

		place(
			zipOf("two", {
				"main.py": "two()",
			}),
			"snap_2",
		);

		expect(
			launch({
				SERVERK_SNAPSHOT_ID: "snap_2",
				SERVERK_DEPLOYMENT_ID: "dep_2",
			}).code,
		).toBe(0);
		expect(readFileSync(join(app, "main.py"), "utf8")).toBe("two()");
		expect(historyCount()).toBe(1);
	});

	test("keeps the repository's code when the zip that replaces it is corrupt", () => {
		const remote = gitRemote({
			"main.py": "print('from git')",
		});

		expect(
			launch({
				...remote.env,
				SERVERK_REPO_REF: remote.sha,
				SERVERK_DEPLOYMENT_ID: "dep_1",
			}).code,
		).toBe(0);

		place(
			corrupted(
				zipOf("broken", {
					"main.py": "x".repeat(4096),
				}),
			),
			"snap_bad",
		);

		const failed = launch({
			SERVERK_SNAPSHOT_ID: "snap_bad",
			SERVERK_DEPLOYMENT_ID: "dep_2",
		});

		expect(failed.code).toBe(1);
		expect(failed.lines.at(-1)).toStartWith("serverk: deployment dep_2 failed: snapshot: ");
		expect(existsSync(join(app, ".git"))).toBe(true);
		expect(readFileSync(join(app, "main.py"), "utf8")).toBe("print('from git')");
		expect(existsSync(join(state, "history"))).toBe(false);
	});

	test("keeps the uploaded code when the repository that replaces it cannot be fetched", () => {
		place(
			zipOf("one", {
				"main.py": "one()",
			}),
			"snap_1",
		);

		expect(
			launch({
				SERVERK_SNAPSHOT_ID: "snap_1",
				SERVERK_DEPLOYMENT_ID: "dep_1",
			}).code,
		).toBe(0);

		const failed = launch({
			PATH: wrappedPath(join(root, "missing.git")),
			SERVERK_REPO_URL: REMOTE,
			SERVERK_REPO_REF: SHA,
			SERVERK_DEPLOYMENT_ID: "dep_2",
			SERVERK_GIT_TOKEN: "ghs_expired_token",
		});

		expect(failed.code).toBe(1);
		expect(failed.lines.at(-1)).toStartWith("serverk: deployment dep_2 failed: sync: ");
		expect(failed.lines.some((line) => line.includes("ما قدرنا نسحب كود بوتك"))).toBe(true);
		expect(failed.lines.join("\n")).not.toContain("ghs_expired_token");
		expect(readFileSync(join(app, "main.py"), "utf8")).toBe("one()");
		expect(existsSync(join(state, "history"))).toBe(true);
		expect(existsSync(join(app, ".git"))).toBe(false);
	});

	test("refuses a repository that tracks .serverk instead of letting it overwrite the stamps", () => {
		const remote = gitRemote({
			"main.py": "run()",
			".serverk/deployment.json": "{}",
		});
		const failed = launch({
			...remote.env,
			SERVERK_REPO_REF: remote.sha,
			SERVERK_DEPLOYMENT_ID: "dep_1",
		});

		expect(failed.code).toBe(1);
		expect(failed.lines.at(-1)).toBe("serverk: deployment dep_1 failed: sync: repository tracks .serverk");
		expect(stamp()).toMatchObject({
			deployment: "dep_1",
			outcome: "failed",
			stage: "sync",
		});
		expect(existsSync(join(app, "main.py"))).toBe(false);
	});

	test("installs and starts with no git token left in the launcher's own environment", () => {
		const remote = gitRemote({
			"main.py": "import os\nprint('bot ' + os.environ.get('SERVERK_GIT_TOKEN', 'none'), flush=True)\n",
		});
		const { code, lines } = launch({
			...remote.env,
			SERVERK_REPO_REF: remote.sha,
			SERVERK_DEPLOYMENT_ID: "dep_1",
			SERVERK_GIT_TOKEN: "ghs_installation",
			SERVERK_INSTALL_COMMAND:
				"echo parent-token-$(tr '\\0' '\\n' < /proc/$PPID/environ | grep -c '^SERVERK_GIT_TOKEN=')",
			SERVERK_START_COMMAND: "",
		});

		expect(code).toBe(0);
		expect(lines).toContain("parent-token-0");
		expect(lines).toContain(`serverk: deployment dep_1 ready at ${remote.sha.slice(0, 12)}`);
		expect(lines.at(-1)).toBe("bot none");
	});

	const fakePip = () => {
		const python = join(app, ".venv", "bin", "python");

		rmSync(python, {
			force: true,
		});
		writeFileSync(python, '#!/bin/sh\necho "fake python $*"\nexit 0\n', {
			mode: 0o755,
		});
	};

	const deployWithPip = (name: string, files: Record<string, string>) => {
		place(zipOf(name, files), name);

		return launch({
			SERVERK_SNAPSHOT_ID: name,
			SERVERK_DEPLOYMENT_ID: `dep_${name}`,
		});
	};

	test("drops a shipped requirements file with its snapshot and installs the next snapshot from its own manifest", () => {
		fakePip();

		const first = deployWithPip("snap_a", {
			"main.py": "run()",
			"requirements.txt": "discord.py==2.7.1\n",
		});

		expect(first.code).toBe(0);
		expect(first.lines).toContain("serverk: installing dependencies: pip install -r requirements.txt");

		const second = deployWithPip("snap_b", {
			"main.py": "run()",
			"pyproject.toml": '[project]\nname = "b"\nversion = "1"\n',
		});

		expect(second.code).toBe(0);
		expect(second.lines).toContain("serverk: installing dependencies: pip install .");
		expect(second.lines).toContain("serverk: deployment dep_snap_b ready");
		expect(second.lines.at(-1)).toBe("the bot ran");
	});

	test("ignores a requirements file the snapshot does not carry when it picks how to install", () => {
		fakePip();

		const project = {
			"main.py": "run()",
			"pyproject.toml": '[project]\nname = "b"\nversion = "1"\n',
		};

		expect(deployWithPip("snap_a", project).code).toBe(0);

		writeFileSync(join(app, "requirements.txt"), "left==1.0\n");

		const second = deployWithPip("snap_b", {
			"main.py": "run_again()",
			"pyproject.toml": '[project]\nname = "b"\nversion = "2"\n',
		});

		expect(second.code).toBe(0);
		expect(second.lines).toContain("serverk: installing dependencies: pip install .");
		expect(second.lines).not.toContain("serverk: installing dependencies: pip install -r requirements.txt");
		expect(readFileSync(join(app, "requirements.txt"), "utf8")).toBe("left==1.0\n");
	});

	test("fails the install stage with npm's reason, not the path of its debug log", () => {
		const script = join(root, "npm404.sh");

		writeFileSync(script, transcriptScript(NPM_404_TRANSCRIPT), {
			mode: 0o755,
		});

		const { code, lines } = launch({
			SERVERK_INSTALL_COMMAND: `sh ${script}`,
			SERVERK_DEPLOYMENT_ID: "dep_404",
		});

		expect(code).toBe(1);
		expect(lines.at(-1)).toBe(
			"serverk: deployment dep_404 failed: install: npm error code E404: 404 Not Found - GET https://registry.npmjs.org/serverk-no-such-package-e404-proof - Not found",
		);
	});

	test("fails the install stage with pip's summary, not its closing hint", () => {
		const python = join(app, ".venv", "bin", "python");

		rmSync(python, {
			force: true,
		});
		writeFileSync(python, transcriptScript(PIP_BUILD_TRANSCRIPT), {
			mode: 0o755,
		});
		writeFileSync(join(app, "requirements.txt"), "broken-package==1.0\n");

		const { code, lines } = launch({
			SERVERK_DEPLOYMENT_ID: "dep_pip",
		});

		expect(code).toBe(1);
		expect(lines.at(-1)).toBe(
			"serverk: deployment dep_pip failed: install: × Encountered error while generating package metadata.",
		);
	});

	test("keeps only the current snapshot and the ten before it", () => {
		for (let index = 1; index <= 12; index += 1) {
			place(
				zipOf(`s${index}`, {
					"main.py": `v${index}()`,
				}),
				`snap_${index}`,
			);

			expect(
				launch({
					SERVERK_SNAPSHOT_ID: `snap_${index}`,
					SERVERK_DEPLOYMENT_ID: `dep_${index}`,
				}).code,
			).toBe(0);
		}

		expect(historyTags()).toHaveLength(11);
		expect(historyTags()).not.toContain("snapshot-snap_1");
		expect(historyCount()).toBe(11);
		expect(
			launch({
				SERVERK_SNAPSHOT_ID: "snap_1",
				SERVERK_DEPLOYMENT_ID: "dep_13",
			}).lines.at(-1),
		).toBe("serverk: deployment dep_13 failed: snapshot: snapshot snap_1 is not on this bot");
	}, 60_000);
});
