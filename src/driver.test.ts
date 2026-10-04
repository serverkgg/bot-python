import { describe, expect, it } from "bun:test";
import { readFileSync } from "node:fs";
import { BridgeKind, BridgeLayout, BridgeStopSignal } from "@serverkgg/bridge";
import {
	BOT_DEPLOY_MODULE,
	BOT_IDENTITY_MODULE,
	BOT_TAB,
	BotSection,
	LAUNCHER_RULES,
	PYTHON_RULES,
} from "@serverkgg/bridge/bot";
import { driver } from "./driver";
import { fakeContext } from "./testing";

const ROOT = new URL("..", import.meta.url).pathname;

const tabs = driver.panel?.tabs ?? [];

const LAUNCHER_READY_LINE = "serverk: bot process starting";

describe("validating the driver the way the platform does", () => {
	it("passes the same validate run that happens in the hook and at release", () => {
		const result = Bun.spawnSync(
			[
				`${ROOT}node_modules/.bin/serverk-bridge`,
				"validate",
			],
			{
				cwd: ROOT,
				stdout: "pipe",
				stderr: "pipe",
			},
		);
		const output = `${result.stdout.toString()}${result.stderr.toString()}`;

		expect(output).toContain("bot-python is valid");
		expect(output).toContain("manifest: BotPackage, 0 port(s)");
		expect(output).toContain("environment: vault on");
		expect(output).toContain("detect: image/detect.json matches this bridge");
		expect(output).toContain("setup: none");
		expect(result.exitCode).toBe(0);
	});

	it("ships the detection table the launcher reads inside the image", () => {
		expect(readFileSync(`${ROOT}image/Dockerfile`, "utf8")).toContain(
			"COPY image/launcher.py image/git-askpass image/detect.json /serverk/",
		);
	});
});

describe("assembling the bot driver", () => {
	it("never gates a start behind a setup flow", () => {
		expect(driver.setup).toBeUndefined();
	});

	it("keeps one bot tab with only the identity card on it", () => {
		expect(tabs.map((tab) => tab.id)).toEqual([
			BOT_TAB,
		]);
		expect(
			tabs[0]?.sections.map((section) => [
				section.id,
				section.layout,
			]),
		).toEqual([
			[
				BotSection.Identity,
				BridgeLayout.Detail,
			],
		]);
	});

	it("registers the identity module and the deploy module the platform invokes", () => {
		expect(driver.modules?.[BOT_IDENTITY_MODULE]?.kind).toBe(BridgeKind.Detail);

		const deploy = driver.modules?.[BOT_DEPLOY_MODULE];

		expect(deploy?.kind).toBe(BridgeKind.Actions);
		expect(deploy?.kind === BridgeKind.Actions && deploy.requiresRunning).toBe(false);
	});

	it("starts through the launcher, flips to running on its ready line and waits up to fifteen minutes for it", () => {
		expect(driver.lifecycle.ready?.test(LAUNCHER_READY_LINE)).toBe(true);
		expect(driver.lifecycle.ready?.test(`${LAUNCHER_READY_LINE} now`)).toBe(false);
		expect(driver.lifecycle.readyTimeoutSeconds).toBe(900);
		expect(driver.lifecycle.onReady).toBeDefined();
	});

	it("stops the bot with SIGTERM at once and kills it after fifteen seconds", () => {
		expect(driver.lifecycle.stopSignal).toBe(BridgeStopSignal.Term);
		expect(driver.lifecycle.stopTimeoutSeconds).toBe(15);
	});

	it("colours the launcher lines and python errors in the console", () => {
		expect(driver.terminal?.rules).toEqual([
			...LAUNCHER_RULES,
			...PYTHON_RULES,
		]);
		expect(driver.terminal?.commands).toEqual([]);
	});

	it("counts no players, because a bot has none", async () => {
		expect(await driver.query?.sample(fakeContext().context)).toEqual({
			online: null,
			max: null,
		});
	});
});
