import type { Bridge } from "@serverkgg/bridge";
import {
	type BotPlatform,
	botExposureOf,
	botProcessEnvironment,
	customerEnvironment,
	inferBotPlatform,
	launcherEnvironment,
	platformEnvironment,
	readBotConfig,
} from "@serverkgg/bridge/bot";
import { STATE_DIR, toolEnvironment } from "./botRuntime";

export const botPlatformOf = (context: Bridge.Context): BotPlatform | null => {
	return (
		readBotConfig(context).platform
		?? inferBotPlatform({
			variables: context.variables(),
			secrets: context.secrets(),
		})
	);
};

export const processEnvironment = (context: Bridge.Context): Record<string, string> => {
	return botProcessEnvironment({
		tool: toolEnvironment(),
		customer: customerEnvironment(context.variables(), context.secrets()),
		launcher: launcherEnvironment(readBotConfig(context), STATE_DIR),
		platform: platformEnvironment(context.server.code, botPlatformOf(context), botExposureOf(context)),
	});
};
