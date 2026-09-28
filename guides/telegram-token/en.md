## Create your bot with BotFather

1. Open [@BotFather](https://t.me/BotFather) in Telegram.
2. Send it `/newbot`.
3. Type the bot's name, then its username. It must end in `bot`, like `my_shop_bot`.
4. BotFather replies with the token, which looks like this:

```txt
123456789:AAH-your-token-here
```

5. Copy all of it and add it to your bot's variables under the name your code reads, usually `TELEGRAM_TOKEN`, marked **Sensitive**.

@[open](overview)

## Lost or leaked the token?

Send `/revoke` to BotFather and pick your bot. It gives you a new token and the old one stops working at once. Put the new one in your variables and press **Redeploy**.

## Only one copy at a time

Telegram lets only one copy of a bot receive messages. If you run it on your computer while it runs here, you get a `409 Conflict` error. Stop the other copy and everything goes back to normal.

@[open](console)
