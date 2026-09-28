import { describe, expect, test } from "bun:test";
import { BridgeDetailFormat } from "@serverkgg/bridge";
import { BotPlatform, IDENTITY_CACHE_FILE } from "@serverkgg/bridge/bot";
import { fakeContext } from "../testing";
import { IDENTITY_DETAIL, IDENTITY_ICON, identity, readIdentity } from "./identity";

const DISCORD_ID = "1136470478027245683";

const DISCORD_TOKEN = `${btoa(DISCORD_ID).replaceAll("=", "")}.GxYz12.${"a".repeat(38)}`;

const TELEGRAM_TOKEN = "7123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw";

describe("the identity card", () => {
	test("shows nothing until the bot names a platform or holds a token", async () => {
		expect(await readIdentity(fakeContext().context)).toBeNull();
	});

	test("shows the id from the token and waits for the name, with an invite link already", async () => {
		const detail = await readIdentity(
			fakeContext({
				secrets: {
					DISCORD_TOKEN,
				},
			}).context,
		);

		expect(detail).toMatchObject({
			id: IDENTITY_DETAIL,
			title: {
				ar: "بوت ديسكورد",
				en: "Discord bot",
			},
			subtitle: null,
			image: null,
			icon: IDENTITY_ICON,
			stats: [
				{
					key: "id",
					value: DISCORD_ID,
					format: BridgeDetailFormat.Text,
				},
			],
			links: [
				{
					url: `https://discord.com/oauth2/authorize?client_id=${DISCORD_ID}&scope=bot+applications.commands`,
				},
			],
		});
		expect(detail?.description).not.toBeNull();
	});

	test("names the bot from its own login line and opens it in Telegram", async () => {
		const detail = await readIdentity(
			fakeContext({
				secrets: {
					TELEGRAM_TOKEN,
				},
				files: {
					[IDENTITY_CACHE_FILE]: JSON.stringify({
						platform: BotPlatform.Telegram,
						name: "serverk_test_bot",
						seenAt: "2026-09-27T10:00:00.000Z",
					}),
				},
			}).context,
		);

		expect(detail).toMatchObject({
			title: "serverk_test_bot",
			subtitle: {
				ar: "بوت تيليجرام",
				en: "Telegram bot",
			},
			description: null,
			links: [
				{
					label: {
						ar: "افتحه في تيليجرام",
						en: "Open it in Telegram",
					},
					url: "https://t.me/serverk_test_bot",
				},
			],
		});
		expect(detail?.stats.map((stat) => stat.key)).toEqual([
			"id",
			"seen",
		]);
	});

	test("reads while the bot is stopped and makes no network call", () => {
		expect(identity.requiresRunning).toBe(false);
	});
});
