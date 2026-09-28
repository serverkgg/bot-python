import { type Bridge, BridgeKind } from "@serverkgg/bridge";
import { LAUNCHER_RULES, PYTHON_RULES } from "@serverkgg/bridge/bot";

export const terminal: Bridge.Terminal = {
	kind: BridgeKind.Terminal,
	commands: [],
	rules: [
		...LAUNCHER_RULES,
		...PYTHON_RULES,
	],
};
