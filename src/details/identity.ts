import { type Bridge, BridgeDetailFormat, BridgeIcon } from "@serverkgg/bridge";
import {
	type BotIdentity,
	BotPlatform,
	createBotIdentityModule,
	inviteLink,
	resolveBotIdentity,
} from "@serverkgg/bridge/bot";

export const IDENTITY_DETAIL = "identity";

export const IDENTITY_ICON = BridgeIcon.Command;

const PLATFORM_LABELS: Record<BotPlatform, Bridge.Text> = {
	[BotPlatform.Discord]: {
		ar: "بوت ديسكورد",
		en: "Discord bot",
	},
	[BotPlatform.Telegram]: {
		ar: "بوت تيليجرام",
		en: "Telegram bot",
	},
};

const INVITE_LABELS: Record<BotPlatform, Bridge.Text> = {
	[BotPlatform.Discord]: {
		ar: "ضيفه لسيرفر ديسكورد",
		en: "Add it to a Discord server",
	},
	[BotPlatform.Telegram]: {
		ar: "افتحه في تيليجرام",
		en: "Open it in Telegram",
	},
};

const NAME_PENDING: Bridge.Text = {
	ar: "بيطلع اسم بوتك هنا أول ما يشتغل ويسجّل دخوله.",
	en: "Your bot's name shows up here once it runs and logs in.",
};

const identityStats = (identity: BotIdentity): Bridge.DetailStat[] => {
	return [
		...(identity.id
			? [
					{
						key: "id",
						label: {
							ar: "معرّف البوت",
							en: "Bot ID",
						},
						value: identity.id,
						format: BridgeDetailFormat.Text,
					},
				]
			: []),
		...(identity.seenAt
			? [
					{
						key: "seen",
						label: {
							ar: "آخر تسجيل دخول",
							en: "Last login",
						},
						value: identity.seenAt,
						format: BridgeDetailFormat.Date,
					},
				]
			: []),
	];
};

export const identityDetail = (identity: BotIdentity): Bridge.DetailResult => {
	const link = inviteLink(identity);

	return {
		id: IDENTITY_DETAIL,
		title: identity.name ?? PLATFORM_LABELS[identity.platform],
		subtitle: identity.name ? PLATFORM_LABELS[identity.platform] : null,
		description: identity.name ? null : NAME_PENDING,
		image: null,
		icon: IDENTITY_ICON,
		badges: [],
		stats: identityStats(identity),
		links: link
			? [
					{
						label: INVITE_LABELS[identity.platform],
						url: link,
					},
				]
			: [],
		stale: false,
		actions: [],
	};
};

export const readIdentity = async (context: Bridge.Context): Promise<Bridge.DetailResult | null> => {
	const identity = await resolveBotIdentity(context);

	return identity ? identityDetail(identity) : null;
};

export const identity = createBotIdentityModule(readIdentity);
