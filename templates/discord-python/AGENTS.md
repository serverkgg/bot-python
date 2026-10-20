# AGENTS.md

This repository is a Discord bot in Python with discord.py, deployed on Serverk (serverk.gg). Serverk runs the bot and never writes it.

## Run on Serverk

- Install: `uv pip install -r requirements.txt`. Start: `python main.py`. Python 3.12, since no `.python-version` asks for another.
- `serverk.json` declares the runtime, platform, framework and variables. One invalid field rejects the whole file.
- A database migration goes in the `preDeploy` field of `serverk.json`, one line such as `alembic upgrade head`. Without it, an `alembic.ini` runs `alembic upgrade head` and a `manage.py` runs `python manage.py migrate --noinput`. It runs once per deployment, after the install and before the start, with the bot's variables and `.venv/bin` first on the path, never on a plain restart. Its failure fails the deployment at the `pre-deploy` stage, and the next start runs it again, so it must be safe to run twice.
- Keep the `Logged in as` line: Serverk marks the bot ready when it prints it, or after 20 seconds alive.
- The bot uses `discord.Intents.default()`, which holds no privileged intent. A privileged intent (`message_content`, `members`, `presences`) must be turned on in the Developer Portal first, or the login fails with `PrivilegedIntentsRequired`.
- The bot publishes no port until the web address is turned on in the bot's Manage page: the bot then gets `PORT`, `SERVERK_WEB_URL` and `SERVERK_WEB_HOST`, and must listen on `0.0.0.0` and `PORT`.

## Variables

- `DISCORD_TOKEN` (required, sensitive): the bot token from the Discord Developer Portal. The code reads `os.environ["DISCORD_TOKEN"]`.
- Serverk delivers every variable under exactly the name it was saved with, with no prefix and no alias.
- A new variable the code reads goes into `.env.example` and the `env` list of `serverk.json`; its value goes into the bot's variables on Serverk, never into the repository.
- Never commit `.env` or a token. `.env` is in `.gitignore` and is removed from an uploaded zip.

## Deploy and debug

- With auto deploy on, the default, a push to the connected branch deploys. A variable change reaches the bot with its next deployment.
- MCP server: `https://api.serverk.gg/mcp`, scopes `customer:read customer:write customer:destructive` (the variable tools need `customer:destructive`). Tools: `customer_server_env_keys`, `customer_server_env_set`, `customer_server_deploy`, `customer_server_deployments`, `customer_server_deployment_log`, `customer_server_terminal`, `customer_server_rollback`.
- `customer_server_env_set` takes one `key` and `value`, or `entries`, a list of `{ key, value, sensitive }` that sets several variables in one call. `sensitive` defaults to true.
- Serverk's `serverk-bot` skill teaches the whole workflow; its repository is https://github.com/serverkgg/serverk-skills. Guides: https://serverk.gg/bots/bot-python/guides
