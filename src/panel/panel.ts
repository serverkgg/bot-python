import type { Bridge } from "@serverkgg/bridge";
import { createBotPanel } from "@serverkgg/bridge/bot";

export const panel: Bridge.Panel = {
	tabs: [
		createBotPanel(),
	],
};
