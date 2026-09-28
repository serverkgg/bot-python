## Create the application

1. Open the [Discord Developer Portal](https://discord.com/developers/applications) and sign in.
2. Press **New Application**, name it and accept the terms.

## Get the token

1. Pick **Bot** in the menu.
2. Press **Reset Token**, confirm, then **Copy**.
3. Add it to your bot's variables under the name your code reads, usually `DISCORD_TOKEN`, and mark it **Sensitive**.

> [!warning] Discord shows the token only once. If you lose it, press Reset Token again and use the new one; the old one stops working at once.

If you change the token later, update it in your variables and press **Redeploy**.

@[open](overview)

## Add the bot to your server

The token tells us your application's id, so your bot card shows an **Add it to a Discord server** button. Press it and pick the server.

If your bot reads message text, turn on **Message Content Intent** on the Bot page of the Developer Portal, or the text never reaches it.

@[open](panel:bot)

## Your personal account token? No

Running your personal account as a bot (a self-bot) breaks Discord's rules and can get the account banned. Always use the bot token from the Developer Portal.
