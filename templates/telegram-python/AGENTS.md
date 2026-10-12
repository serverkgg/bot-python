# AGENTS.md

This repository is a Telegram bot in Python with python-telegram-bot, deployed on Serverk (serverk.gg). Serverk runs the bot and never writes it.

## Run on Serverk

- Install: `uv pip install -r requirements.txt`. Start: `python main.py`. Python 3.12, since no `.python-version` asks for another.
- `serverk.json` declares the runtime, platform, framework and variables. One invalid field rejects the whole file.
- Keep the `Logged in as` line: Serverk marks the bot ready when it prints it, or after 20 seconds alive.
- The bot long-polls; webhook mode is not offered, since a bot publishes no port. One token runs one bot: a second copy polling the same token gets `409 Conflict`.

## Variables

- `TELEGRAM_TOKEN` (required, sensitive): the bot token from BotFather. The code reads `os.environ["TELEGRAM_TOKEN"]`.
- Serverk delivers every variable under exactly the name it was saved with, with no prefix and no alias.
- A new variable the code reads goes into `.env.example` and the `env` list of `serverk.json`; its value goes into the bot's variables on Serverk, never into the repository.
- Never commit `.env` or a token. `.env` is in `.gitignore` and is removed from an uploaded zip.

## Deploy and debug

- With auto deploy on, the default, a push to the connected branch deploys. A variable change reaches the bot with its next deployment.
- MCP server: `https://api.serverk.gg/mcp`, scopes `customer:read customer:write customer:destructive` (the variable tools need `customer:destructive`). Tools: `customer_server_env_keys`, `customer_server_env_set`, `customer_server_deploy`, `customer_server_deployments`, `customer_server_deployment_log`, `customer_server_terminal`, `customer_server_rollback`.
- `customer_server_env_set` takes one `key` and `value`, or `entries`, a list of `{ key, value, sensitive }` that sets several variables in one call. `sensitive` defaults to true.
- Serverk's `serverk-bot` skill teaches the whole workflow; its repository is https://github.com/serverkgg/serverk-skills. Guides: https://serverk.gg/bots/bot-python/guides
