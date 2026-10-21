import { describe, expect, it } from "bun:test";
import { type Bridge, BridgeStream } from "@serverkgg/bridge";
import { BOT_RUN_MODE, BOT_RUN_TIMEOUT_MS, LAUNCHER_RUN_COMMAND } from "@serverkgg/bridge/bot";
import { launcherCommand, processEnvironment } from "../shared";
import { fakeContext } from "../testing";
import { terminal } from "./terminal";

type ExecCall = Parameters<Bridge.Context["exec"]>;

const shellContext = () => {
	const calls: ExecCall[] = [];
	const printed: string[] = [];
	const finished = Promise.withResolvers<void>();

	const context: Bridge.Context = {
		...fakeContext({
			variables: {
				GREETING: "hello",
			},
		}).context,
		async exec(...call: ExecCall) {
			calls.push(call);
			call[1]?.onOutput?.("up to date", BridgeStream.Stdout);

			return {
				stdout: "up to date\n",
				stderr: "",
				code: 0,
			};
		},
		print(line: string) {
			printed.push(line);

			if (line.startsWith("serverk: command")) {
				finished.resolve();
			}
		},
	};

	return {
		context,
		calls,
		printed,
		finished: finished.promise,
	};
};

describe("the bot console", () => {
	it("runs what the customer types as a shell command instead of writing it to the bot", () => {
		expect(terminal.shell).toBe(true);
		expect(terminal.run).toBeDefined();
		expect(terminal.commands).toEqual([]);
	});

	it("hands the command to the launcher's run mode with the bot's own environment", async () => {
		const { context, calls, printed, finished } = shellContext();

		expect(await terminal.run?.(context, "  ls -la  ")).toEqual({
			sent: "ls -la",
			line: null,
			groups: {},
		});

		await finished;

		expect(calls).toHaveLength(1);

		const [command, options] = calls[0] ?? [];

		expect(command).toEqual(launcherCommand(BOT_RUN_MODE));
		expect(options?.timeoutMs).toBe(BOT_RUN_TIMEOUT_MS);
		expect(options?.environment).toEqual({
			...processEnvironment(context),
			[LAUNCHER_RUN_COMMAND]: "ls -la",
		});
		expect(options?.environment?.GREETING).toBe("hello");
		expect(printed).toEqual([
			"up to date",
			"serverk: command finished",
		]);
	});
});
