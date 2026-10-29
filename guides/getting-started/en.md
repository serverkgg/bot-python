Go from one page, "Run your bot", to the first line your bot prints in the console.

## Before you start

- A Serverk account, since we ask you to sign in before we read your code.
- Your bot's code: a GitHub repository, your bot's folder, or a zip file.
- Your bot's token, and every other variable your code reads.

No bot yet? We keep templates with a `/ping` or `/start` command that works right away: the [Discord template](https://github.com/serverkgg/bot-template-discord-python) and the [Telegram template](https://github.com/serverkgg/bot-template-telegram-python).

## 1. Pick where the code is

Open ["Run your bot"](/bots/create), and under **Where is the code?** pick a GitHub repository, upload your bot folder or a zip, or start from a template. With a template, we create it as a repository in your own GitHub or copy it straight into your bot.

![The three places for the code on "Run your bot": GitHub repository, Upload the code and Start from a template.](guides/getting-started/where-is-the-code.webp)

Once you pick, we read the code, and what we found shows up below the choices.

## 2. Check what we found in the code

Under **What we found in the code**, we work out that it's Python, the library (discord.py, python-telegram-bot and others) and the platform. Under **Commands**, we fill in the install and start commands. Change anything before you go on.

![The "What we found in the code" section showing the runtime, the library and the platform, which you can change.](guides/getting-started/what-we-found.webp)

Once the runtime is set, the plans show up under **Choose a plan**.

## 3. Add the token and your variables

Under **Variables**, add the token and every variable your code reads. We suggest the names we found in the code and in `.env.example`: press a name, then type its value.

![DISCORD_TOKEN added under "Variables", with its value field ready to fill.](guides/getting-started/add-the-token.webp)

Sensitive values are stored encrypted and never shown after saving.

## 4. Choose a plan and pay

Under **Choose a plan**, pick a plan and press **Pay and deploy**. After you pay, your bot's page opens and the first deployment starts.

## 5. Follow the first deployment

Your bot's page shows the deployment line by line:

![The "Deploying your bot" card on the bot's page, with the deployment's lines in the console below it.](guides/getting-started/first-deployment.webp)

- We pull the code from your repository, or unpack what you uploaded.
- We give your bot a Python environment of its own (`.venv`) and install the dependencies into it from the first of these we find: `requirements.txt`, `uv.lock`, `poetry.lock`, `pdm.lock`, `Pipfile`, then `pyproject.toml`. We only reinstall when the dependencies change.
- When your bot has a pre-deploy command, such as `alembic upgrade head`, we run it after the install and before your bot starts, on every deployment.
- We start your bot with the first of these we find: the start command in your bot's settings, `start` in `serverk.json`, the `worker:` or `bot:` line of a `Procfile`, then `main.py`, `bot.py`, `app.py`, `src/main.py` and `src/bot.py`, then `python -m` with the one folder that holds a `__main__.py`.

The moment these two lines show up in the console, your bot has started:

```txt
serverk: deployment dep_a1b2c3d4 ready at 3f2a9c1b7d10
serverk: bot process starting
```

@[open](overview)

## 6. Check that your bot signed in

Once your bot signs in and prints a line such as `Logged in as MyBot`, its name appears on the bot card together with its link: **Add it to a Discord server** for a Discord bot, or **Open it in Telegram** for a Telegram bot.

![The bot card showing the bot's name and ID, and the "Add it to a Discord server" link.](guides/getting-started/bot-signed-in.webp)

## The token is invalid {#token-invalid}

We start your bot even when its token has a problem, and the error shows up in the console exactly as your bot prints it. When your bot stops on it, the deployment fails and your bot's page names the cause:

![A failed deployment in the Deployments tab, with its cause below it: the token is invalid.](guides/getting-started/token-rejected.webp)

Copy the token again from the Developer Portal or BotFather, update it in your variables, then redeploy. The guide ["Your bot's errors and how to fix them"](/bots/bot-python/guides/errors#token-invalid) lists the line each library prints.

@[open](console)

## Next

[Deployments and rolling back](/bots/bot-python/guides/deployments): what happens in each deployment, and how to roll your bot back to the last deployment that worked.
