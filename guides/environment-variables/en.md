## Every variable arrives under its own name

The variables you add in your bot's settings reach your bot under exactly the same name, unchanged. If your code reads:

```python
bot.run(os.environ["DISCORD_TOKEN"])
```

add a variable named `DISCORD_TOKEN`. If it reads `os.getenv("TOKEN")`, name it `TOKEN`. When you create your bot we show you the names we found in your code and in `.env.example`, so you know what to add.

## Sensitive values are stored encrypted

Turn on **Sensitive** for any secret value, such as a token or a password. A sensitive value is stored encrypted and never shown again after you save it; to change it, type a new one. Even if your bot prints it by mistake, we hide it in the console and show `••••` instead.

> [!warning] Never put the token in your code or in a `.env` file inside your repository. Anyone who sees it can take over your bot.

## Paste a `.env` file

Have a `.env` file on your computer? Paste the whole file into the variables box and we split it line by line.

## After you change a variable

The change reaches your bot with the next deployment. Press **Redeploy** on your bot's page to apply it right away. Variables do not roll back when you roll back to an older deployment; they stay as they are.

@[open](overview)

## Reserved names

Some names belong to Serverk, so you cannot add them as variables:

- Any name that starts with `SERVERK_`.
- The names that carry your deployment settings: `REPO_URL`, `REPO_REF`, `REPO_BRANCH`, `START_COMMAND`, `INSTALL_COMMAND`, `ROOT_DIRECTORY`, `DEPLOYMENT_ID`, `SNAPSHOT_ID`, `BOT_PLATFORM` and `GIT_TOKEN`. Change these from your bot's settings instead.
- `PATH`, `HOME`, `TZ`, `VIRTUAL_ENV` and `PYTHONUNBUFFERED`, which your bot needs to run.

We give your bot these ourselves:

- `SERVERK_BOT` set to `1`, and `SERVERK_SERVER_CODE`, your bot's code.
- `BOT_PLATFORM`: `discord` or `telegram`.

> [!note] Your variables reach the dependency install too, so if you use a private package index, add `PIP_INDEX_URL` to your variables and mark it sensitive.
