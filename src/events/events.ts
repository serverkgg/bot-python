import { type Bridge, BridgeKind } from "@serverkgg/bridge";
import { DEPLOYMENT_EVENT_PATTERN } from "@serverkgg/bridge/bot";

export const events: Bridge.Events = {
	kind: BridgeKind.Events,
	patterns: [
		DEPLOYMENT_EVENT_PATTERN,
	],
};
