import type { Bridge } from "@serverkgg/bridge";
import { readStamp, writeStamp } from "@serverkgg/bridge/install";
import { INSTALL_STAMP } from "./botRuntime";

export interface InstallStamp {
	runtime: string | null;
	installedAt: string;
}

const text = (value: unknown) => {
	return typeof value === "string" && value.length > 0 ? value : null;
};

export const installStampOf = (raw: Record<string, unknown> | null): InstallStamp | null => {
	const installedAt = text(raw?.installedAt);

	if (!raw || !installedAt) {
		return null;
	}

	return {
		runtime: text(raw.runtime),
		installedAt,
	};
};

export const readInstallStamp = async (context: Bridge.Context) => {
	return installStampOf(await readStamp(context, INSTALL_STAMP));
};

export const writeInstallStamp = async (context: Bridge.Context, stamp: InstallStamp) => {
	await writeStamp<InstallStamp>(context, stamp, INSTALL_STAMP);
};
