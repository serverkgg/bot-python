import { BOT_STATE_DIR, LAUNCHER_STATE_DIR } from "@serverkgg/bridge/bot";

export const HOME_DIR = "/home/container";

export const STATE_DIR = `${HOME_DIR}/${BOT_STATE_DIR}`;

export const RUNTIME = "python3";

export const ISOLATED = "-I";

export const LAUNCHER_PATH = "/serverk/launcher.py";

export const INSTALL_MODE = "install";

export const INSTALL_STAMP = `${BOT_STATE_DIR}/install.json`;

export const launcherCommand = (...args: string[]) => {
	return [
		RUNTIME,
		ISOLATED,
		LAUNCHER_PATH,
		...args,
	];
};

export const toolEnvironment = (): Record<string, string> => {
	return {
		TZ: "UTC",
		HOME: HOME_DIR,
		PYTHONUNBUFFERED: "1",
		PIP_CACHE_DIR: `${STATE_DIR}/cache/pip`,
		[LAUNCHER_STATE_DIR]: STATE_DIR,
	};
};
