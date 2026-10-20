## Find your line

When your bot stops on one of the lines below, its page names the cause and what to do. Find the line in the console, then read its section here. Each line is copied as the library prints it, and its start is enough to match.

@[open](console)

## The token is invalid {#token-invalid}

- discord.py: `discord.errors.LoginFailure: Improper token has been passed.`
- python-telegram-bot: `telegram.error.InvalidToken`
- aiogram: `aiogram.exceptions.TelegramUnauthorizedError: Telegram server says - Unauthorized`

Copy the token again from the Developer Portal or BotFather, update it in your variables, then redeploy.

## A variable is missing {#variable-missing}

- `KeyError: 'TELEGRAM_TOKEN'`

Your code reads the variable named between the quotes, as in `os.environ["TELEGRAM_TOKEN"]`, and your bot's variables have none by that name. Add it to your bot's variables under that exact name, in the same capital letters, then redeploy. If your code reads the token with `os.getenv` instead, it gets an empty value and your bot stops as in "The token is invalid" above.

## Privileged intents are off {#intents-disallowed}

- discord.py: `discord.errors.PrivilegedIntentsRequired: Shard ID None is requesting privileged intents that have not been explicitly enabled in the developer portal.`

Turn on the intents your code asks for on the Bot page of the Developer Portal, then start your bot again. The guide "Your Discord bot's token, intents and permissions" shows the switch each intent needs.

## Another bot is using the token {#token-in-use}

- python-telegram-bot: `telegram.error.Conflict: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running`

python-telegram-bot doesn't stop on this line: it prints it and keeps going beside the other copy. One token runs only one bot at a time, so stop the other copy, such as one on your computer, or send `/revoke` to BotFather for a new token, update it in your variables, then redeploy.

## A webhook is set on the token {#webhook-active}

- aiogram: `aiogram.exceptions.TelegramConflictError: Telegram server says - Conflict: can't use getUpdates method while webhook is active; use deleteWebhook to delete the webhook first`

Telegram answers this when your bot pulls messages by polling while its token still has a webhook set, from an old host or from when the web address was on. Pick one:

- Move your code to the webhook and turn on the web address, as the guide "Your bot's web address and ports" shows.
- Or delete the webhook: add `await bot.delete_webhook()` before `dp.start_polling(bot)`, or open `https://api.telegram.org/botTOKEN/deleteWebhook` in your browser once with your token in place of `TOKEN`, then start your bot again.

## A library is missing {#missing-dependency}

- `ModuleNotFoundError: No module named 'discord'`

Add the library to `requirements.txt`, then redeploy. The library's name can differ from the name you import: `discord` comes from `discord.py`, and `telegram` from `python-telegram-bot`. A voice bot on `discord.py` that stops on `RuntimeError: davey library needed in order to use voice` needs `discord.py[voice]` in `requirements.txt` instead of `discord.py`.

## The wrong Telegram library is installed {#wrong-telegram-package}

- `ImportError: cannot import name 'Update' from 'telegram'`

Replace `telegram` with `python-telegram-bot` in `requirements.txt`, then redeploy.

## The wrong Discord library is installed {#wrong-discord-package}

- `AttributeError: module 'discord' has no attribute 'Bot'`
- `ModuleNotFoundError: No module named 'discord.app_commands'`
- `ImportError: cannot import name 'app_commands' from 'discord'`

You import both `discord.py` and `py-cord` as `discord`, and your code was written for the one that isn't installed. Code that uses `discord.Bot` needs `py-cord`, and code that imports `discord.app_commands` needs `discord.py`. Keep only that one in `requirements.txt`, never both, then redeploy.

## A library couldn't be built {#build-tools}

- `error: command 'gcc' failed: No such file or directory`

The problem is on our side. [Contact us](/dashboard/support) and we'll add the tools the library needs.

## ffmpeg is missing {#ffmpeg-missing}

- discord.py: `discord.errors.ClientException: ffmpeg was not found.`

The problem is on our side. [Contact us](/dashboard/support) and we'll add ffmpeg to the runtime.

## This Python version has no audioop {#audioop-removed}

- `ModuleNotFoundError: No module named 'audioop'`

Python 3.13 and later no longer include `audioop`. Set Python 3.12 in `.python-version`, or add `audioop-lts` to `requirements.txt`, then redeploy.

## Your bot hit a rate limit {#rate-limited}

- discord.py: `discord.errors.HTTPException: 429 Too Many Requests (error code: 0)`
- Or the line `error code: 1015`

Give it a few minutes before you start it again, and check the code that sends requests in a loop.

## Your bot isn't listening on its web address {#web-not-listening}

The web address is on, but nothing answered on the port in `PORT`, so your bot's page warns you and the address shows "This bot isn't answering right now". Make your bot listen on `0.0.0.0` and `int(os.environ["PORT"])`, not on `localhost` or `127.0.0.1` and not on a fixed number such as `5000`, then redeploy. The guide "Your bot's web address and ports" shows how for each library. If your bot doesn't need the web address, turn it off in **Manage**.

## Your bot opens the same port twice {#port-busy}

- `OSError: [Errno 98] Address already in use`
- `OSError: [Errno 98] error while attempting to bind on address ('0.0.0.0', 8080): address already in use`

Nothing else uses your bot's ports, so this line means your code opens the same port twice, such as a server for your pages and the webhook server both on `PORT`, or an old keep-alive server beside them. Open one server on `PORT` and add every route to it, then redeploy.

## The pre-deploy command failed {#pre-deploy}

- `serverk: pre-deploy failed:`
- Then `serverk: deployment dep_a1b2c3d4 failed: pre-deploy:`

The pre-deploy command ended with an error, so the deployment stopped before your bot started. Read the lines the command printed above these two in the console. Check that the command is right and that the variables that connect to your database, such as `DATABASE_URL`, are in your bot's variables with the right values, then redeploy. The guide "How we install and start a Python project" shows where the command comes from and how to change it.

## Your bot stopped with exit code `137` {#oom-kill}

Your plan's RAM ran out while your bot was running. Nothing is printed: your bot stops at once with exit code `137`, and its page shows "Not enough RAM". Upgrade the plan for more RAM, or cut down what your bot keeps in memory.

## Not enough RAM to install or run {#out-of-memory}

- `MemoryError`
- `serverk: install failed: it ran out of memory and was stopped`
- Then `serverk: deployment dep_a1b2c3d4 failed: install: out-of-memory`

The first line ends the traceback when Python runs out of memory while your bot runs. The other two mean the install ran out of RAM; they say `pre-deploy` instead of `install` when the pre-deploy command ran out. Upgrade the plan for more RAM, then redeploy.

> [!note] Your line isn't here? The last line of the error still says what went wrong, and the guide "Read the console and work out what happened" shows how to read it.
