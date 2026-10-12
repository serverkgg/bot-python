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

## Your bot stopped with exit code `137` {#oom-kill}

Your plan's RAM ran out while your bot was running. Nothing is printed: your bot stops at once with exit code `137`, and its page shows "Not enough RAM". Upgrade the plan for more RAM, or cut down what your bot keeps in memory.

## Not enough RAM to install or run {#out-of-memory}

- `MemoryError`
- `serverk: install failed: it ran out of memory and was stopped`
- Then `serverk: deployment dep_a1b2c3d4 failed: install: out-of-memory`

The first line ends the traceback when Python runs out of memory while your bot runs. The other two mean the install ran out of RAM. Upgrade the plan for more RAM, then redeploy.

> [!note] Your line isn't here? The last line of the error still says what went wrong, and the guide "Read the console and work out what happened" shows how to read it.
