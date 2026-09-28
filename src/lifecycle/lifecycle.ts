import { type Bridge, BridgeKind, BridgeLifecycleSubject, BridgeStopSignal } from "@serverkgg/bridge";
import { watchLoginLine } from "@serverkgg/bridge/bot";
import { botPlatformOf, launcherCommand, processEnvironment } from "../shared";

export const READY_LINE = /^serverk: bot process starting$/;

export const STOP_TIMEOUT_SECONDS = 15;

export const READY_TIMEOUT_SECONDS = 900;

export const lifecycle: Bridge.Lifecycle = {
	kind: BridgeKind.Lifecycle,
	ready: READY_LINE,
	stopTimeoutSeconds: STOP_TIMEOUT_SECONDS,
	readyTimeoutSeconds: READY_TIMEOUT_SECONDS,
	stopSignal: BridgeStopSignal.Term,
	subject: BridgeLifecycleSubject.Bot,
	async command() {
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
	},
};
