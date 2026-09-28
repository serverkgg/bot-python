import { describe, expect, test } from "bun:test";
import { installFailure } from "./install";

describe("reading a failed install", () => {
	test("takes the launcher's last failure line, whichever stage failed", () => {
		expect(
			installFailure(
				[
					"serverk: installing dependencies: npm ci",
					"npm error code EUSAGE",
					"serverk: ما قدرنا نثبّت مكتبات بوتك.",
					"serverk: install failed: npm error `npm ci` can only install with an existing package-lock.json",
				].join("\n"),
				1,
			),
		).toBe("npm error `npm ci` can only install with an existing package-lock.json");
		expect(
			installFailure(
				"serverk: fetching https://github.com/you/bot at 0123456789ab\nserverk: sync failed: commit 0123456789ab is not in the repository",
				1,
			),
		).toBe("commit 0123456789ab is not in the repository");
	});

	test("falls back to the exit code when the launcher printed nothing", () => {
		expect(installFailure("", 137)).toBe("the bot install exited with code 137");
	});
});
