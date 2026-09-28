import { type Bridge, BridgeKind, BridgeUserError } from "@serverkgg/bridge";
import { BOT_STATE_DIR, DEPLOYMENT_COMMIT_LENGTH, readDeploymentState } from "@serverkgg/bridge/bot";
import {
	botPlatformOf,
	INSTALL_MODE,
	launcherCommand,
	processEnvironment,
	RUNTIME,
	readInstallStamp,
	writeInstallStamp,
} from "../shared";

export const INSTALL_TIMEOUT_MS = 840_000;

const LAUNCHER_PREFIX = "serverk: ";

const LAUNCHER_FAILURE = /^serverk: (?:sync|snapshot|install|start) failed: (.+)$/;

export const installFailure = (stdout: string, code: number) => {
	const detail = stdout
		.split("\n")
		.map((line) => line.trim().match(LAUNCHER_FAILURE)?.[1])
		.filter((line) => line !== undefined)
		.at(-1);

	return detail ?? `the bot install exited with code ${code}`;
};

const installFailed = (detail: string) => {
	return new BridgeUserError({
		ar: `ما قدرنا نجهّز بوتك: ${detail}`,
		en: `We could not get your bot ready: ${detail}`,
	});
};

const runtimeVersion = async (context: Bridge.Context) => {
	const result = await context.exec([
		RUNTIME,
		"--version",
	]);

	const version = result.stdout.trim();

	return result.code === 0 && version.length > 0 ? version : null;
};

export const install: Bridge.Install = {
	kind: BridgeKind.Install,
	async run(context) {
		await context.files.ensure(BOT_STATE_DIR);

		const result = await context.exec(launcherCommand(INSTALL_MODE), {
			timeoutMs: INSTALL_TIMEOUT_MS,
			environment: processEnvironment(context),
			onOutput(line) {
				if (line.startsWith(LAUNCHER_PREFIX)) {
					context.log(line.slice(LAUNCHER_PREFIX.length));
				}
			},
		});

		if (result.code !== 0) {
			throw installFailed(installFailure(result.stdout, result.code));
		}

		const runtime = await runtimeVersion(context);

		await writeInstallStamp(context, {
			runtime,
			installedAt: new Date().toISOString(),
		});

		context.log("the bot is installed", {
			runtime,
		});
	},
	async describe(context) {
		const stamp = await readInstallStamp(context);
		const deployment = await readDeploymentState(context.files);

		return {
			version: stamp?.runtime ?? null,
			variant: botPlatformOf(context),
			build: deployment?.commit?.slice(0, DEPLOYMENT_COMMIT_LENGTH) ?? null,
		};
	},
};
