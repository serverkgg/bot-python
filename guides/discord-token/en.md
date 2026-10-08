## Create the application

1. Open the [Discord Developer Portal](https://discord.com/developers/applications) and sign in.
2. Press **New Application**, name it and accept the terms.

## Get the token

1. Pick **Bot** in the menu.
2. Press **Reset Token**, confirm, then **Copy**.
3. Add it to your bot's variables under the name your code reads, usually `DISCORD_TOKEN`, and mark it **Sensitive**.

> [!warning] Discord shows the token only once. If you lose it, press Reset Token again and use the new one; the old one stops working at once.

If you change the token later, update it in your variables and press **Redeploy**. A second copy on the same token, such as one on your computer, connects too, and both copies answer, so every reply comes twice. Stop any other copy of your bot.

@[open](overview)

## Turn on the intents your code asks for

On the same **Bot** page, under **Privileged Gateway Intents**, there are three switches. Turn on only the ones your code asks for in `discord.Intents`, then press **Save Changes**:

- `intents.presences = True` needs **Presence Intent**.
- `intents.members = True` needs **Server Members Intent**.
- `intents.message_content = True` needs **Message Content Intent**. Without it, messages in server channels reach your bot without their text. Direct messages and messages that mention the bot still carry it.

`discord.Intents.all()` asks for all three, and `discord.Intents.default()` asks for none of them. If your code asks for an intent that is off, your bot stops at sign-in and discord.py prints this line:

```txt
discord.errors.PrivilegedIntentsRequired: Shard ID None is requesting privileged intents that have not been explicitly enabled in the developer portal.
```

Turn on the missing intent, then start your bot again. You don't need a new token.

@[open](console)

## Add the bot to your server

The token tells us your application's id, so your bot card shows an **Add it to a Discord server** button. Press it and pick the server.

@[open](panel:bot)

This button adds the bot with the scopes `bot` and `applications.commands`, so the bot and its slash commands, with no permissions of its own. To give it the permissions it needs, pick one way:

- In your Discord server's **Server Settings**, open **Roles**, create a role with the permissions the bot needs and give it to the bot, or grant the permissions channel by channel.
- Or build the link yourself in the Developer Portal: open **OAuth2**, then **URL Generator**, tick `bot` and `applications.commands`, pick the permissions under **Bot Permissions**, and open the link it gives you.

When the bot lacks a permission, Discord answers its request with error code `50013`, and with `50001` when it can't reach the channel at all.

## Your personal account token? No

Running your personal account as a bot (a self-bot) breaks Discord's rules and can get the account banned. Always use the bot token from the Developer Portal.
