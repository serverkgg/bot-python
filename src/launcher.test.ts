import { afterEach, beforeEach, describe, expect, it } from "bun:test";
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
	createBotReadiness,
	DEPLOYMENT_ID_PATTERN,
	DEPLOYMENT_LINE,
	DEPLOYMENT_STAGE_LINE,
	DEPLOYMENT_STATE_FILE,
	DETECT_TABLE,
	deploymentLine,
	deploymentStageLine,
	detect,
	detectWantedFiles,
	parseServerkJson,
	platformEnvironment,
	REPO_BRANCH_PATTERN,
	REPO_REF_PATTERN,
	REPO_URL_PATTERN,
	ROOT_DIRECTORY_PATTERN,
	renderDetectTable,
	SNAPSHOT_ID_PATTERN,
} from "@serverkgg/bridge/bot";
import { BridgeCrashCause, BridgeCrashPhase, BridgeEventName } from "@serverkgg/bridge/protocol";
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

const EXPOSED = platformEnvironment("bt7k2m9q4x", null, {
	web: 8080,
	webUrl: "https://mybot.srvk.gg",
	port1: 29_004,
	port2: 30_004,
});

const RAW_ONLY = platformEnvironment("bt7k2m9q4x", null, {
	web: null,
	webUrl: null,
	port1: null,
	port2: 30_004,
});

const QUIET = platformEnvironment("bt7k2m9q4x", null);

const INSTALL_ONLY_KEYS = [
	"CI",
	"PIPENV_DONT_LOAD_ENV",
	"PIPENV_CACHE_DIR",
	"UV_CACHE_DIR",
	"UV_PYTHON_INSTALL_DIR",
	"UV_MANAGED_PYTHON",
];

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

const UV_NO_SOLUTION_TRANSCRIPT = [
	"Using Python 3.12.3 environment at: .venv",
	"  × No solution found when resolving dependencies:",
	"  ╰─▶ Because serverk-no-such-package-e404-proof was not found in the package",
	"      registry and you require serverk-no-such-package-e404-proof==1.0, we can",
	"      conclude that your requirements are unsatisfiable.",
];

const UV_NO_SOLUTION_DETAIL =
	"× No solution found when resolving dependencies: Because serverk-no-such-package-e404-proof was not found in the package registry and you require serverk-no-such-package-e404-proof==1.0, we can conclude that your requirements are unsatisfiable.";

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
	it("passes its own unit tests against the templates", () => {
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

	it("reads the table the bridge renders and falls back to the same table built in", () => {
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

	it("agrees with the driver and the bridge on every line, marker, key and pattern it reads", () => {
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
				`'exposed': launcher.exposure_lines(${JSON.stringify(EXPOSED)}),`,
				`'rawOnly': launcher.exposure_lines(${JSON.stringify(RAW_ONLY)}),`,
				`'quiet': launcher.exposure_lines(${JSON.stringify(QUIET)}),`,
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
		expect(answer.exposed).toEqual([
			"web address https://mybot.srvk.gg on port 8080",
			"port 1 at mybot.srvk.gg:29004",
			"port 2 at mybot.srvk.gg:30004",
		]);
		expect(answer.rawOnly).toEqual([
			"port 2 on 30004",
		]);
		expect(answer.quiet).toEqual([]);
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
		start: "python bot.py",
		preDeploy: " alembic upgrade head ",
	}),
	JSON.stringify({
		start: "python bot.py",
		preDeploy: "",
	}),
	JSON.stringify({
		start: "python bot.py",
		preDeploy: "a\nb",
	}),
	JSON.stringify({
		start: "python bot.py",
		preDeploy: [
			"alembic",
			"upgrade",
			"head",
		],
	}),
	JSON.stringify({
		start: "python bot.py",
		preDeploy: "x".repeat(1025),
	}),
	JSON.stringify({
		start: "python bot.py",
		build: true,
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
	it("agrees with the bridge's parser on every sample, broken files included", () => {
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
							preDeploy: parsed.preDeploy,
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

	it("detects each template cleanly and agrees with the launcher on how to start it", () => {
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
					command: "uv pip install -r requirements.txt",
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

const LAYOUTS: Record<string, string>[] = [
	{
		"main.py": "run()",
		Procfile: "worker: python -m bot\n",
		"requirements.txt": "discord.py==2.7.1\n",
	},
	{
		"mybot/__main__.py": "run()",
		"requirements.txt": "discord.py==2.7.1\n",
	},
	{
		"tests/__main__.py": "run()",
		"venv/__main__.py": "run()",
		"mybot/__main__.py": "run()",
		"pyproject.toml": '[project]\nname = "bot"\nversion = "1"\ndependencies = ["discord.py==2.7.1"]\n',
		"poetry.lock": "# lock\n",
	},
	{
		"bot.py": "run()",
		"pyproject.toml": '[project]\nname = "bot"\nversion = "1"\ndependencies = ["aiogram==3.22.0"]\n',
		"uv.lock": "version = 1\n",
		".python-version": "3.11.4\n",
	},
	{
		"app.py": "run()",
		Pipfile: '[packages]\ndiscord-py = "==2.7.1"\n\n[requires]\npython_version = "3.10"\n',
	},
	{
		"main.py": "run()",
		"requirements.txt": "discord.py==2.7.1\n",
		"runtime.txt": "python-3.9.18\n",
	},
	{
		"src/main.py": "run()",
		"requirements.txt": "discord.py==2.7.1\n",
		".tool-versions": "nodejs 24\npython 3.13.1\n",
	},
];

describe("deciding the way the panel shows it", () => {
	it("starts, installs and picks the Python version the way the bridge detects them", () => {
		const root = mkdtempSync(join(tmpdir(), "bot-python-layouts-"));

		try {
			const dirs = LAYOUTS.map((layout, index) => {
				const dir = join(root, String(index));

				for (const [file, content] of Object.entries(layout)) {
					mkdirSync(join(dir, file, ".."), {
						recursive: true,
					});
					writeFileSync(join(dir, file), content);
				}

				return dir;
			});

			const answer = python(
				[
					"import json, os, launcher",
					`dirs = ${JSON.stringify(dirs)}`,
					"table = launcher.BUILT_IN_TABLE",
					"def decide(folder):",
					"    read = lambda name: launcher.read_text(os.path.join(folder, name))",
					"    plan = launcher.detect_manager({entry['file'] for entry in table['python']['manifests'] if read(entry['file']) is not None})",
					"    argv = launcher.resolve_start(folder, {}, table)['argv']",
					"    start = ' '.join(['python', *argv[2:]]) if argv[0] == launcher.VENV_PYTHON else argv[2].removeprefix('exec ')",
					"    install = ' '.join(table['python']['installCommands'][plan['manager']])",
					"    return {'start': start, 'install': install, 'version': launcher.python_version_of(read)}",
					"print(json.dumps([decide(folder) for folder in dirs]))",
				].join("\n"),
			);

			const detected = LAYOUTS.map((layout) => {
				const files = Object.keys(layout).map((path) => ({
					path,
				}));
				const result = detect({
					files,
					contents: Object.fromEntries(
						detectWantedFiles(files).map((path) => [
							path,
							layout[path] ?? "",
						]),
					),
				});

				return {
					start: result.start?.command ?? null,
					install: result.install?.command ?? null,
					version: result.pythonVersion,
				};
			});

			expect(answer).toEqual(detected);
			expect(detected.map((entry) => entry.start)).toEqual([
				"python -m bot",
				"python -m mybot",
				"python -m mybot",
				"python bot.py",
				"python app.py",
				"python main.py",
				"python src/main.py",
			]);
		} finally {
			rmSync(root, {
				force: true,
				recursive: true,
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

	const stagesOf = (lines: string[]) => {
		return lines.filter((line) => DEPLOYMENT_STAGE_LINE.test(line));
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

	it("deploys an uploaded snapshot, drops what the next one deleted and rolls back without a download", () => {
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
		expect(first.lines.slice(-3)).toEqual([
			"serverk: start command: sh -c exec echo the bot ran",
			"serverk: bot process starting",
			"the bot ran",
		]);
		expect(first.lines.some((line) => DEPLOYMENT_LINE.test(line))).toBe(false);
		expect(stamp()).toMatchObject({
			deployment: "dep_1",
			outcome: "ready",
			settled: false,
		});
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

	it("prints each stage of a deployment once, the way the bridge reads it, and none on a start with nothing to deploy", () => {
		place(
			zipOf("one", {
				"main.py": "run()",
			}),
			"snap_1",
		);

		const deployed = launch({
			SERVERK_SNAPSHOT_ID: "snap_1",
			SERVERK_DEPLOYMENT_ID: "dep_1",
		});

		expect(deployed.code).toBe(0);
		expect(stagesOf(deployed.lines)).toEqual([
			deploymentStageLine("dep_1", BotDeploymentStage.Snapshot),
			deploymentStageLine("dep_1", BotDeploymentStage.Install),
			deploymentStageLine("dep_1", BotDeploymentStage.Start),
		]);
		expect(deployed.lines.indexOf(deploymentStageLine("dep_1", BotDeploymentStage.Start))).toBeLessThan(
			deployed.lines.findIndex((line) => READY_LINE.test(line)),
		);

		const again = launch({
			SERVERK_SNAPSHOT_ID: "snap_1",
			SERVERK_DEPLOYMENT_ID: "dep_1",
		});

		expect(again.code).toBe(0);
		expect(stagesOf(again.lines)).toEqual([]);

		const installMode = launch(
			{
				SERVERK_SNAPSHOT_ID: "snap_1",
				SERVERK_DEPLOYMENT_ID: "dep_2",
			},
			[
				"install",
			],
		);

		expect(stagesOf(installMode.lines)).toEqual([]);
	});

	it("prints the web address and each raw port right before the start line, and none of them while they are off", () => {
		place(
			zipOf("one", {
				"main.py": "one()",
			}),
			"snap_1",
		);

		const deployment = {
			SERVERK_SNAPSHOT_ID: "snap_1",
			SERVERK_DEPLOYMENT_ID: "dep_1",
		};
		const off = launch({
			...deployment,
			PORT: "3000",
		});

		expect(off.code).toBe(0);
		expect(off.lines.filter((line) => /^serverk: (?:web address|port \d) /.test(line))).toEqual([]);

		const on = launch({
			...deployment,
			PORT: "8080",
			SERVERK_WEB_URL: "https://mybot.srvk.gg",
			SERVERK_WEB_HOST: "mybot.srvk.gg",
			SERVERK_PORT_1: "29004",
			SERVERK_PORT_2: "30004",
		});

		expect(on.code).toBe(0);
		expect(on.lines.slice(-6)).toEqual([
			"serverk: web address https://mybot.srvk.gg on port 8080",
			"serverk: port 1 at mybot.srvk.gg:29004",
			"serverk: port 2 at mybot.srvk.gg:30004",
			"serverk: start command: sh -c exec echo the bot ran",
			"serverk: bot process starting",
			"the bot ran",
		]);

		const raw = launch({
			...deployment,
			SERVERK_PORT_1: "29004",
		});

		expect(raw.lines.slice(-4)).toEqual([
			"serverk: port 1 on 29004",
			"serverk: start command: sh -c exec echo the bot ran",
			"serverk: bot process starting",
			"the bot ran",
		]);
	});

	it("ends a failed deployment with the failure line and records it", () => {
		const { code, lines } = launch({
			SERVERK_SNAPSHOT_ID: "snap_missing",
			SERVERK_DEPLOYMENT_ID: "dep_9",
		});

		expect(code).toBe(1);
		expect(stagesOf(lines)).toEqual([
			deploymentStageLine("dep_9", BotDeploymentStage.Snapshot),
		]);
		expect(lines.at(-1)).toBe("serverk: deployment dep_9 failed: snapshot: snapshot snap_missing is not on this bot");
		expect(stamp()).toMatchObject({
			deployment: "dep_9",
			outcome: "failed",
			stage: "snapshot",
		});
	});

	const fakeAlembic = () => {
		writeFileSync(
			join(app, ".venv", "bin", "alembic"),
			'#!/bin/sh\necho "alembic $* for $DATABASE_URL token=$SERVERK_GIT_TOKEN ci=$CI"\n',
			{
				mode: 0o755,
			},
		);
		writeFileSync(join(app, "alembic.ini"), "[alembic]\n");
	};

	const preDeployHint = () => {
		return python("import json, launcher\nprint(json.dumps(launcher.PRE_DEPLOY_HINT))") as string;
	};

	it("runs the pre-deploy command once per deployment, after the install and before the start, with the bot's variables and the venv on the path", () => {
		fakeAlembic();

		const deployment = {
			SERVERK_DEPLOYMENT_ID: "dep_1",
			SERVERK_GIT_TOKEN: "ghs_secret",
			DATABASE_URL: "postgres://db",
		};
		const deployed = launch(deployment);

		expect(deployed.code).toBe(0);
		expect(stagesOf(deployed.lines)).toEqual([
			deploymentStageLine("dep_1", BotDeploymentStage.Sync),
			deploymentStageLine("dep_1", BotDeploymentStage.Install),
			deploymentStageLine("dep_1", BotDeploymentStage.PreDeploy),
			deploymentStageLine("dep_1", BotDeploymentStage.Start),
		]);

		const ran = deployed.lines.indexOf("serverk: running the pre-deploy command: alembic upgrade head");

		expect(ran).toBeGreaterThan(deployed.lines.indexOf(deploymentStageLine("dep_1", BotDeploymentStage.PreDeploy)));
		expect(deployed.lines.slice(ran + 1, ran + 3)).toEqual([
			"alembic upgrade head for postgres://db token= ci=",
			"serverk: pre-deploy command finished",
		]);
		expect(ran).toBeLessThan(deployed.lines.indexOf(deploymentStageLine("dep_1", BotDeploymentStage.Start)));
		expect(deployed.lines.at(-1)).toBe("the bot ran");

		const restart = launch(deployment);

		expect(restart.code).toBe(0);
		expect(restart.lines.filter((line) => line.includes("pre-deploy") || line.startsWith("alembic"))).toEqual([]);

		const installMode = launch(
			{
				...deployment,
				SERVERK_DEPLOYMENT_ID: "dep_2",
			},
			[
				"install",
			],
		);

		expect(installMode.code).toBe(0);
		expect(installMode.lines.filter((line) => line.includes("pre-deploy") || line.startsWith("alembic"))).toEqual([]);
	});

	it("prints no pre-deploy stage for a deployment with no pre-deploy command", () => {
		const deployed = launch({
			SERVERK_DEPLOYMENT_ID: "dep_1",
		});

		expect(deployed.code).toBe(0);
		expect(stagesOf(deployed.lines)).toEqual([
			deploymentStageLine("dep_1", BotDeploymentStage.Sync),
			deploymentStageLine("dep_1", BotDeploymentStage.Install),
			deploymentStageLine("dep_1", BotDeploymentStage.Start),
		]);
		expect(deployed.lines.filter((line) => line.includes("pre-deploy"))).toEqual([]);
	});

	it("fails a deployment at the pre-deploy stage and runs the command again on its next start", () => {
		const failed = launch({
			SERVERK_DEPLOYMENT_ID: "dep_1",
			SERVERK_PRE_DEPLOY_COMMAND: "echo relation users already exists; exit 1",
		});

		expect(failed.code).toBe(1);
		expect(failed.lines).not.toContain("serverk: bot process starting");
		expect(failed.lines.slice(-3)).toEqual([
			`serverk: ${preDeployHint()}`,
			"serverk: pre-deploy failed: relation users already exists",
			"serverk: deployment dep_1 failed: pre-deploy: relation users already exists",
		]);
		expect(stamp()).toMatchObject({
			deployment: "dep_1",
			outcome: "failed",
			stage: BotDeploymentStage.PreDeploy,
			detail: "relation users already exists",
		});

		const again = launch({
			SERVERK_DEPLOYMENT_ID: "dep_1",
			SERVERK_PRE_DEPLOY_COMMAND: "echo migrated",
		});

		expect(again.code).toBe(0);
		expect(again.lines).toContain("serverk: running the pre-deploy command: echo migrated");
		expect(again.lines).toContain("migrated");
		expect(stamp()).toMatchObject({
			deployment: "dep_1",
			outcome: "ready",
		});
	});

	it("fails a deployment whose pre-deploy command the memory limit killed with out-of-memory", () => {
		const { code, lines } = launch({
			SERVERK_DEPLOYMENT_ID: "dep_oom",
			SERVERK_PRE_DEPLOY_COMMAND: "echo Running upgrade; kill -9 $$",
		});

		expect(code).toBe(1);
		expect(lines.at(-1)).toBe("serverk: deployment dep_oom failed: pre-deploy: out-of-memory");
		expect(stamp()).toMatchObject({
			stage: BotDeploymentStage.PreDeploy,
			detail: BridgeCrashCause.OutOfMemory,
		});
	});

	it("takes the pre-deploy command from the settings, then serverk.json, then alembic.ini before manage.py", () => {
		writeFileSync(join(app, "manage.py"), "import sys\nprint('manage', *sys.argv[1:], flush=True)\n");

		const django = launch({
			SERVERK_DEPLOYMENT_ID: "dep_1",
		});

		expect(django.lines).toContain("serverk: running the pre-deploy command: python manage.py migrate --noinput");
		expect(django.lines).toContain("manage migrate --noinput");

		fakeAlembic();

		expect(
			launch({
				SERVERK_DEPLOYMENT_ID: "dep_2",
			}).lines,
		).toContain("serverk: running the pre-deploy command: alembic upgrade head");

		writeFileSync(
			join(app, "serverk.json"),
			JSON.stringify({
				preDeploy: "echo declared migration",
			}),
		);

		const declared = launch({
			SERVERK_DEPLOYMENT_ID: "dep_3",
		});

		expect(declared.lines).toContain("serverk: running the pre-deploy command: echo declared migration");
		expect(declared.lines).toContain("declared migration");

		const typed = launch({
			SERVERK_DEPLOYMENT_ID: "dep_4",
			SERVERK_PRE_DEPLOY_COMMAND: "echo typed migration",
		});

		expect(typed.lines).toContain("serverk: running the pre-deploy command: echo typed migration");
		expect(typed.lines.filter((line) => line.includes("declared migration"))).toEqual([]);
	});

	it("runs the customer's install command inside the venv and reinstalls when it changes", () => {
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

	it("runs a pinned commit from its root directory, never from the checkout root", () => {
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
		expect(stamp()).toMatchObject({
			deployment: "dep_1",
			outcome: "ready",
			commit: sha,
		});
		expect(lines).toContain("serverk: start command: .venv/bin/python -u main.py");
		expect(lines.at(-1)).toBe(`cwd ${realpathSync(join(app, "app"))}`);
		expect(readFileSync(join(app, "README.md"), "utf8")).toBe("sibling");
	});

	it("runs an uploaded snapshot from its root directory and fails the source stage on a missing one", () => {
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

	it("reinstalls when the root directory changes", () => {
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

	it("keeps the install-only variables away from the bot and out of the image", () => {
		const { code, lines } = launch({
			SERVERK_INSTALL_COMMAND: "sh -c 'echo install CI=$CI PIPENV_DONT_LOAD_ENV=$PIPENV_DONT_LOAD_ENV'",
			SERVERK_START_COMMAND: "env",
		});
		const dockerfile = readFileSync(join(IMAGE, "Dockerfile"), "utf8");

		expect(code).toBe(0);
		expect(lines).toContain("install CI=true PIPENV_DONT_LOAD_ENV=1");
		expect(lines.filter((line) => INSTALL_ONLY_KEYS.some((key) => line.startsWith(`${key}=`)))).toEqual([]);
		expect(INSTALL_ONLY_KEYS.filter((key) => dockerfile.includes(key))).toEqual([]);
	});

	it("runs a start command that sets a variable before the program", () => {
		const { code, lines } = launch({
			SERVERK_START_COMMAND: "GREETING=hello sh -c 'echo greeting $GREETING'",
		});

		expect(code).toBe(0);
		expect(lines).toContain("serverk: start command: sh -c exec env GREETING=hello sh -c 'echo greeting $GREETING'");
		expect(lines.at(-1)).toBe("greeting hello");
	});

	it("installs and starts with the commands serverk.json declares", () => {
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

	it("keeps the customer's PYTHON variables away from the launcher", () => {
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

	it("boots uploaded code after a restore that dropped the history and the zips, and rebuilds the history later", () => {
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

	it("keeps the repository's code when the zip that replaces it is corrupt", () => {
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

	it("keeps the uploaded code when the repository that replaces it cannot be fetched", () => {
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
		expect(failed.lines.some((line) => line.includes("تعذّر سحب كود بوتك"))).toBe(true);
		expect(failed.lines.join("\n")).not.toContain("ghs_expired_token");
		expect(readFileSync(join(app, "main.py"), "utf8")).toBe("one()");
		expect(existsSync(join(state, "history"))).toBe(true);
		expect(existsSync(join(app, ".git"))).toBe(false);
	});

	it("refuses a repository that tracks .serverk instead of letting it overwrite the stamps", () => {
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

	it("installs and starts with no git token left in the launcher's own environment", () => {
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
		expect(stagesOf(lines)).toEqual([
			deploymentStageLine("dep_1", BotDeploymentStage.Sync),
			deploymentStageLine("dep_1", BotDeploymentStage.Install),
			deploymentStageLine("dep_1", BotDeploymentStage.Start),
		]);
		expect(stamp()).toMatchObject({
			deployment: "dep_1",
			outcome: "ready",
			commit: remote.sha,
		});
		expect(lines.at(-1)).toBe("bot none");
	});

	const fakeUv = (script = '#!/bin/sh\necho "fake uv $* in $VIRTUAL_ENV"\nexit 0\n') => {
		const tools = join(root, "tools");

		mkdirSync(tools, {
			recursive: true,
		});
		writeFileSync(join(tools, "uv"), script, {
			mode: 0o755,
		});

		return `${tools}:${process.env.PATH ?? "/usr/bin:/bin"}`;
	};

	const deployWithUv = (name: string, files: Record<string, string>) => {
		place(zipOf(name, files), name);

		return launch({
			PATH: fakeUv(),
			SERVERK_SNAPSHOT_ID: name,
			SERVERK_DEPLOYMENT_ID: `dep_${name}`,
		});
	};

	it("drops a shipped requirements file with its snapshot and installs the next snapshot from its own manifest", () => {
		const first = deployWithUv("snap_a", {
			"main.py": "run()",
			"requirements.txt": "discord.py==2.7.1\n",
		});

		expect(first.code).toBe(0);
		expect(first.lines).toContain("serverk: installing dependencies: uv pip install -r requirements.txt");
		expect(first.lines).toContain(`fake uv pip install -r requirements.txt in ${join(app, ".venv")}`);

		const second = deployWithUv("snap_b", {
			"main.py": "run()",
			"pyproject.toml": '[project]\nname = "b"\nversion = "1"\n',
		});

		expect(second.code).toBe(0);
		expect(second.lines).toContain("serverk: installing dependencies: uv pip install .");
		expect(stamp()).toMatchObject({
			deployment: "dep_snap_b",
			outcome: "ready",
		});
		expect(second.lines.at(-1)).toBe("the bot ran");
	});

	it("ignores a requirements file the snapshot does not carry when it picks how to install", () => {
		const project = {
			"main.py": "run()",
			"pyproject.toml": '[project]\nname = "b"\nversion = "1"\n',
		};

		expect(deployWithUv("snap_a", project).code).toBe(0);

		writeFileSync(join(app, "requirements.txt"), "left==1.0\n");

		const second = deployWithUv("snap_b", {
			"main.py": "run_again()",
			"pyproject.toml": '[project]\nname = "b"\nversion = "2"\n',
		});

		expect(second.code).toBe(0);
		expect(second.lines).toContain("serverk: installing dependencies: uv pip install .");
		expect(second.lines).not.toContain("serverk: installing dependencies: uv pip install -r requirements.txt");
		expect(readFileSync(join(app, "requirements.txt"), "utf8")).toBe("left==1.0\n");
	});

	it("fails the install stage with uv's reason, not the last line it wrapped", () => {
		writeFileSync(join(app, "requirements.txt"), "serverk-no-such-package-e404-proof==1.0\n");

		const { code, lines } = launch({
			PATH: fakeUv(transcriptScript(UV_NO_SOLUTION_TRANSCRIPT)),
			SERVERK_DEPLOYMENT_ID: "dep_uv",
		});

		expect(code).toBe(1);
		expect(lines.at(-1)).toBe(`serverk: deployment dep_uv failed: install: ${UV_NO_SOLUTION_DETAIL.slice(0, 200)}`);
	});

	it("a start after a boot failure reports the same deployment ready when the bot survives", async () => {
		const emitted: {
			event: string;
			payload: unknown;
		}[] = [];
		const bridge = {
			files: {
				async exists(path: string) {
					return existsSync(join(app, path));
				},
				async read(path: string) {
					return readFileSync(join(app, path), "utf8");
				},
				async write(path: string, content: string) {
					writeFileSync(join(app, path), content);
				},
			},
			log: Object.assign(() => {}, {
				warn: () => {},
				error: () => {},
			}),
			emit(event: string, payload: unknown) {
				emitted.push({
					event,
					payload,
				});
			},
		} as unknown as Parameters<ReturnType<typeof createBotReadiness>["ready"]>[0];
		const readiness = createBotReadiness();

		place(
			zipOf("one", {
				"main.py": "run()",
			}),
			"snap_1",
		);
		readiness.launching();
		launch({
			SERVERK_SNAPSHOT_ID: "snap_1",
			SERVERK_DEPLOYMENT_ID: "dep_1",
		});
		await readiness.ready(bridge);
		await readiness.exit(bridge, {
			cause: BridgeCrashCause.TokenInvalid,
			exitCode: 1,
			outOfMemory: false,
			phase: BridgeCrashPhase.Booting,
			uptimeSeconds: 2,
			restarting: false,
			looping: false,
			restarts: 0,
			lastLine: null,
		});

		expect(stamp()).toMatchObject({
			deployment: "dep_1",
			outcome: "failed",
			stage: "start",
		});

		readiness.launching();

		const again = launch({});

		await readiness.ready(bridge);
		await readiness.stable(bridge);

		expect(again.code).toBe(0);
		expect(again.lines.at(-1)).toBe("the bot ran");
		expect(emitted.at(-1)).toEqual({
			event: BridgeEventName.ServerUpdated,
			payload: {
				kind: "deployment",
				deployment: "dep_1",
				outcome: "ready",
				commit: null,
			},
		});
		expect(stamp()).toMatchObject({
			deployment: "dep_1",
			outcome: "ready",
			settled: true,
		});
	});

	it("fails a deployment whose install the memory limit killed with out-of-memory, not its last line", () => {
		writeFileSync(join(app, "requirements.txt"), "discord.py==2.4.0\n");

		const { code, lines } = launch({
			PATH: fakeUv("#!/bin/sh\necho Resolved 12 packages\nkill -9 $$\n"),
			SERVERK_DEPLOYMENT_ID: "dep_oom",
		});

		expect(code).toBe(1);
		expect(lines.at(-1)).toBe("serverk: deployment dep_oom failed: install: out-of-memory");
		expect(stamp()).toMatchObject({
			deployment: "dep_oom",
			outcome: "failed",
			stage: "install",
			detail: BridgeCrashCause.OutOfMemory,
		});
	});

	it("fails the install stage with npm's reason, not the path of its debug log", () => {
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

	it("fails the install stage with pip's summary, not its closing hint", () => {
		const script = join(root, "pip-build.sh");

		writeFileSync(script, transcriptScript(PIP_BUILD_TRANSCRIPT), {
			mode: 0o755,
		});

		const { code, lines } = launch({
			SERVERK_INSTALL_COMMAND: `sh ${script}`,
			SERVERK_DEPLOYMENT_ID: "dep_pip",
		});

		expect(code).toBe(1);
		expect(lines.at(-1)).toBe(
			"serverk: deployment dep_pip failed: install: × Encountered error while generating package metadata.",
		);
	});

	it("keeps only the current snapshot and the ten before it", () => {
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
