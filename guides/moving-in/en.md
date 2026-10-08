## What to bring

- Your bot's code: a GitHub repository, its folder or a zip.
- Your dependency file, such as `requirements.txt` or `pyproject.toml`.
- The names and values of your variables, the token included.
- The data files your bot wrote, such as `bot.sqlite` or `data.json`.

## Stop the old copy first

On Telegram, one token runs only one bot at a time: the second copy gets `409 Conflict`. On Discord, both copies connect and both answer, so every reply comes twice. Stop your bot on the old host before the first deployment here, or give it a new token.

## What you don't need here

- **Keep-alive**: a small web server such as `keep_alive.py` with Flask, visited by a service such as UptimeRobot. Your bot publishes no port here, so nothing outside can reach it, and we keep your bot running without it.
- **pm2, nohup and screen**: start your bot directly, such as `python main.py`. We restart it ourselves after a crash, and we only see the crash when your bot's own process stops.
- **Telegram webhooks**: no webhook can reach your bot here, so use polling, such as `app.run_polling()` in python-telegram-bot, as our template does.

## Move your variables

Put every value from your `.env` file, your Replit Secrets or your old host's variables into your bot's variables under the same name, and mark the secret ones **Sensitive**. Have a `.env` file? Paste all of it into the variables box at once. Your code reads them with `os.environ` or `os.getenv` as before.

@[open](overview)

## What we read from your code

We read your dependency files, a `Procfile` and your Python version file, never your old host's own settings:

- **Heroku** and **Railway**: we run the `worker:` or `bot:` line of your `Procfile`. A `web:` line isn't read. We read the Python version from `runtime.txt`.
- **Replit**: the `.replit` file isn't read.
- **Discloud**: `discloud.config` isn't read, so if we don't find the `MAIN` file it names, put that file in your start command.
- **A Pterodactyl host**: the startup command in its panel isn't read, and you don't need a `git pull` at start. Link GitHub and turn on **Deploy on every push** instead.
- **A VPS**: you don't need systemd or screen, because we start your bot and restart it ourselves.

When we find no way to start your bot, set a start command in your bot's settings, or add a `serverk.json` at the top of your code:

```json
{
  "start": "python src/run.py"
}
```

The guide "How we install and start a Python project" lists the files we look for, in order.

## Bring your data

After the first deployment, upload your data files in the **Files** tab, to the path your code reads. Keep them out of your repository and out of every upload, so later deployments leave them as they are.

@[open](files)
