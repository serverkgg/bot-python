import type { BridgeDriver } from "@serverkgg/bridge";
import { BOT_DEPLOY_MODULE, BOT_IDENTITY_MODULE } from "@serverkgg/bridge/bot";
import { deploy } from "./actions";
import { identity } from "./details";
import { events } from "./events";
import { install } from "./install";
import { lifecycle } from "./lifecycle";
import { panel } from "./panel";
import { query } from "./query";
import { terminal } from "./terminal";

export const driver: BridgeDriver = {
	install,
	lifecycle,
	events,
	query,
	terminal,
	panel,
	modules: {
		[BOT_IDENTITY_MODULE]: identity,
		[BOT_DEPLOY_MODULE]: deploy,
	},
};
