import { type Bridge, BridgeKind } from "@serverkgg/bridge";

export const QUERY_REFRESH_SECONDS = 60;

export const query: Bridge.Query = {
	kind: BridgeKind.Query,
	refreshSeconds: QUERY_REFRESH_SECONDS,
	async sample() {
		return {
			online: null,
			max: null,
		};
	},
};
