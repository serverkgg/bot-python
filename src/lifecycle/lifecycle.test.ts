import { describe, expect, it } from "bun:test";
import { BridgeLifecycleSubject } from "@serverkgg/bridge";
import {
	BOT_PLATFORM,
	BotDeploymentOutcome,
	BotDeploymentSource,
	BotDeploymentStage,
	BotPlatform,
	DEPLOYMENT_ID,
	DEPLOYMENT_STATE_FILE,
	GIT_TOKEN,
	IDENTITY_CACHE_FILE,
	INSTALL_COMMAND,
	LAUNCHER_DEPLOYMENT_ID,
	LAUNCHER_GIT_TOKEN,
	LAUNCHER_INSTALL_COMMAND,
	LAUNCHER_REPO_BRANCH,
	LAUNCHER_REPO_REF,
	LAUNCHER_REPO_URL,
	LAUNCHER_STATE_DIR,
	REPO_REF,
	REPO_URL,
} from "@serverkgg/bridge/bot";
import { BridgeCrashCause, BridgeCrashPhase, BridgeEventName } from "@serverkgg/bridge/protocol";
import { STATE_DIR } from "../shared";
import { fakeContext, SERVER_CODE } from "../testing";
import { lifecycle } from "./lifecycle";

const SHA = "0123456789abcdef0123456789abcdef01234567";

const TELEGRAM_TOKEN = "7123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw";

const environmentOf = async (context: ReturnType<typeof fakeContext>["context"]) => {
	return (await lifecycle.environment?.(context)) ?? {};
};

describe("the bot process environment", () => {
	it("hands the bot every vault key exactly as the customer named it", async () => {
		const { context } = fakeContext({
			variables: {
				MY_VAR: "plain",
				guild_id: "42",
			},
			secrets: {
				TELEGRAM_TOKEN,
			},
			memoryMb: 512,
		});

		expect(await environmentOf(context)).toEqual({
			TZ: "UTC",
			HOME: "/home/container",
			PYTHONUNBUFFERED: "1",
			PIP_CACHE_DIR: `${STATE_DIR}/cache/pip`,
			MY_VAR: "plain",
			guild_id: "42",
			TELEGRAM_TOKEN,
			[LAUNCHER_STATE_DIR]: STATE_DIR,
			SERVERK_BOT: "1",
			SERVERK_SERVER_CODE: SERVER_CODE,
			BOT_PLATFORM: BotPlatform.Telegram,
		});
	});

	it("lets the customer's own settings through and never lets a vault key shadow PATH, HOME or a platform key", async () => {
		const { context } = fakeContext({
			variables: {
				PIP_INDEX_URL: "https://pypi.example.com/simple",
				PYTHONUNBUFFERED: "0",
				VIRTUAL_ENV: "/tmp/venv",
				PATH: "/evil",
				HOME: "/tmp",
				SERVERK_BOT: "0",
				[BOT_PLATFORM]: BotPlatform.Discord,
				[REPO_URL]: "https://github.com/you/bot",
				[REPO_REF]: SHA,
				[DEPLOYMENT_ID]: "dep_a1b2c3d4",
				[INSTALL_COMMAND]: "pip install -r requirements-dev.txt",
			},
			secrets: {
				[GIT_TOKEN]: "ghs_installation",
			},
		});
		const environment = await environmentOf(context);

		expect(environment.PIP_INDEX_URL).toBe("https://pypi.example.com/simple");
		expect(environment.PYTHONUNBUFFERED).toBe("1");
		expect(environment.VIRTUAL_ENV).toBeUndefined();
		expect(environment.PATH).toBeUndefined();
		expect(environment.HOME).toBe("/home/container");
		expect(environment.SERVERK_BOT).toBe("1");
		expect(environment.BOT_PLATFORM).toBe(BotPlatform.Discord);
		expect(environment[REPO_URL]).toBeUndefined();
		expect(environment[GIT_TOKEN]).toBeUndefined();
		expect(environment).toMatchObject({
			[LAUNCHER_REPO_URL]: "https://github.com/you/bot",
			[LAUNCHER_REPO_REF]: SHA,
			[LAUNCHER_REPO_BRANCH]: "main",
			[LAUNCHER_GIT_TOKEN]: "ghs_installation",
			[LAUNCHER_DEPLOYMENT_ID]: "dep_a1b2c3d4",
			[LAUNCHER_INSTALL_COMMAND]: "pip install -r requirements-dev.txt",
		});
	});

	it("starts with no token at all, because nothing gates the start", async () => {
		const environment = await environmentOf(fakeContext().context);

		expect(environment.BOT_PLATFORM).toBeUndefined();
		expect(environment.SERVERK_BOT).toBe("1");
	});

	it("starts the launcher with python in isolated mode, so no PYTHON variable reaches it", async () => {
		expect(await lifecycle.command(fakeContext().context)).toEqual([
			"python3",
			"-I",
			"/serverk/launcher.py",
		]);
	});

	it("names the bot, not a game, in the bridge's lifecycle lines", () => {
		expect(lifecycle.subject).toBe(BridgeLifecycleSubject.Bot);
	});
});

describe("learning the bot's name", () => {
	it("remembers the name from the bot's own login line once it is ready", async () => {
		const { context, stored, print, followers } = fakeContext({
			secrets: {
				TELEGRAM_TOKEN,
			},
		});

		await lifecycle.onReady?.(context);

		print("Logged in as @serverk_test_bot");

		await Bun.sleep(5);

		expect(JSON.parse(stored.get(IDENTITY_CACHE_FILE) ?? "{}")).toMatchObject({
			platform: BotPlatform.Telegram,
			name: "serverk_test_bot",
		});
		expect(followers).toHaveLength(0);
	});

	it("listens for nothing while it cannot tell the platform", async () => {
		const { context, followers } = fakeContext();

		await lifecycle.onReady?.(context);

		expect(followers).toHaveLength(0);
	});
});

const launchedDeployment = async () => {
	const fake = fakeContext();

	await lifecycle.command(fake.context);

	fake.stored.set(
		DEPLOYMENT_STATE_FILE,
		JSON.stringify({
			deployment: "dep_a1b2c3d4",
			source: BotDeploymentSource.Snapshot,
			ref: null,
			commit: null,
			snapshot: "snap_1",
			outcome: BotDeploymentOutcome.Ready,
			stage: null,
			detail: null,
			finishedAt: new Date().toISOString(),
		}),
	);

	await lifecycle.onReady?.(fake.context);

	return fake;
};

const reportOf = (cause: BridgeCrashCause, phase: BridgeCrashPhase) => {
	return {
		cause,
		exitCode: 1,
		outOfMemory: false,
		phase,
		uptimeSeconds: 5,
		restarting: false,
		looping: false,
		restarts: 0,
		lastLine: null,
	};
};

describe("telling the platform how the deployment went", () => {
	it("says nothing when the launcher hands over and reports ready once the bot is stable", async () => {
		const { context, emitted } = await launchedDeployment();

		expect(emitted).toEqual([]);

		await lifecycle.onStable?.(context);

		expect(emitted).toEqual([
			{
				event: BridgeEventName.ServerUpdated,
				payload: {
					kind: "deployment",
					deployment: "dep_a1b2c3d4",
					outcome: BotDeploymentOutcome.Ready,
					commit: null,
				},
			},
		]);
	});

	it("fails the deployment at the start stage with the cause when the bot exits before it is ready", async () => {
		const { context, emitted, stored } = await launchedDeployment();

		await lifecycle.onExit?.(context, reportOf(BridgeCrashCause.TokenInvalid, BridgeCrashPhase.Booting));

		expect(emitted).toEqual([
			{
				event: BridgeEventName.ServerUpdated,
				payload: {
					kind: "deployment",
					deployment: "dep_a1b2c3d4",
					outcome: BotDeploymentOutcome.Failed,
					stage: BotDeploymentStage.Start,
					detail: BridgeCrashCause.TokenInvalid,
				},
			},
		]);
		expect(JSON.parse(stored.get(DEPLOYMENT_STATE_FILE) ?? "{}")).toMatchObject({
			deployment: "dep_a1b2c3d4",
			outcome: BotDeploymentOutcome.Failed,
			stage: BotDeploymentStage.Start,
			detail: BridgeCrashCause.TokenInvalid,
		});
	});

	it("leaves a deployment from an earlier launch alone when the bot only restarted", async () => {
		const { context, emitted, stored } = await launchedDeployment();

		await Bun.sleep(5);
		await lifecycle.command(context);
		await lifecycle.onReady?.(context);
		await lifecycle.onExit?.(context, reportOf(BridgeCrashCause.Unknown, BridgeCrashPhase.Booting));

		expect(emitted).toEqual([]);
		expect(JSON.parse(stored.get(DEPLOYMENT_STATE_FILE) ?? "{}").outcome).toBe(BotDeploymentOutcome.Ready);
	});
});
