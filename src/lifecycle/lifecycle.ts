import { type Bridge, BridgeKind, BridgeLifecycleSubject, BridgeStopSignal } from "@serverkgg/bridge";
import { BOT_READY_GRACE_SECONDS, createBotReadiness, LOGIN_LINE, watchLoginLine } from "@serverkgg/bridge/bot";
import { botPlatformOf, launcherCommand, processEnvironment } from "../shared";

export const READY_LINE = /^serverk: bot process starting$/;

export const STOP_TIMEOUT_SECONDS = 15;

export const READY_TIMEOUT_SECONDS = 900;

const readiness = createBotReadiness();

export const lifecycle: Bridge.Lifecycle = {
	kind: BridgeKind.Lifecycle,
	ready: READY_LINE,
	graceSeconds: BOT_READY_GRACE_SECONDS,
	stableLine: LOGIN_LINE,
	stopTimeoutSeconds: STOP_TIMEOUT_SECONDS,
	readyTimeoutSeconds: READY_TIMEOUT_SECONDS,
	stopSignal: BridgeStopSignal.Term,
	subject: BridgeLifecycleSubject.Bot,
	async command() {
		readiness.launching();

		return launcherCommand();
	},
	async environment(context) {
		return processEnvironment(context);
	},
	async onReady(context) {
		const platform = botPlatformOf(context);

		if (platform) {
			watchLoginLine(context, platform);
		}

		await readiness.ready(context);
	},
	async onStable(context) {
		await readiness.stable(context);
	},
	async onExit(context, report) {
		await readiness.exit(context, report);
	},
};
