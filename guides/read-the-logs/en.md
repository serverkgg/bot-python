Every line in the console shows when it was printed, who printed it and what it says. Find your line here, then what to do about it.

## Where the logs are

The **Console** tab shows every line as it's printed, from your bot and from us. On **Overview**, the **Latest logs** card shows the last lines your bot printed, and the **Deployments** tab keeps each deployment's log: open the menu at the end of its row and press **Open the log**.

![The Console tab in the bot's panel, with your bot's lines.](guides/read-the-logs/console-tab.webp)

@[open](console)

## Read a line

![Console lines with their three parts numbered: the time, who printed it and the line itself.](guides/read-the-logs/read-a-line.webp)

1. The time the line was printed.
2. Who printed it: `BOT` for what your bot prints, our `serverk:` lines included, `BRIDGE` for the program that starts and watches your bot, and `API` for Serverk itself, such as a new deployment starting.
3. The line itself, in red when it's an error.

## The serverk lines

Every line that starts with `serverk:` comes from us, not from your bot, and shows what we did before it started:

- `deploying ...`: a new deployment began.
- `fetching ... at ...` or `unpacking snapshot ...`: we pull the commit from your repository, or unpack the version you uploaded.
- `creating .venv ...`: we build your bot's own Python environment.
- `installing dependencies ...`: we install the dependencies.
- `dependencies are up to date`: nothing changed, so we didn't reinstall.
- `deployment ... ready at ...`: the deployment succeeded.
- `web address ... on port ...`: your bot's web address and the port it must listen on, while the web address is on.
- `port 1 ...` and `port 2 ...`: the number of each port that's on, with the address others connect to while the web address is on.
- `start command: ...`: the command we run your bot with.
- `bot process starting`: your bot started, and every line after it is printed by your bot itself.

## When your bot crashes

Errors show up in red. In Python, read the last line of the error:

```txt
Traceback (most recent call last):
  File "/home/container/main.py", line 12, in <module>
    bot.run(os.environ["DISCORD_TOKEN"])
KeyError: 'DISCORD_TOKEN'
```

The last line says what went wrong, and `File ... line 12` says where: the file `main.py`, line 12. This example means the variable `DISCORD_TOKEN` is missing from your bot's variables.

## The usual errors

When your bot stops on a cause we know, the deployment's page names it, and **Read the guide** opens its section in ["Your bot's errors and how to fix them"](/bots/bot-python/guides/errors).

![A failed deployment naming its cause, with the Read the guide link below it.](guides/read-the-logs/named-cause.webp)

- `deployment ... failed: sync: ...`: we couldn't pull the commit. Check that the repository and the branch exist and that the Serverk app on GitHub can reach the repository.
- `deployment ... failed: sync: repository tracks .serverk`: your repository has a `.serverk` folder, and that name is reserved for Serverk. Delete the folder from your repository and redeploy.
- `deployment ... failed: install: ...`: the dependency install failed and the line says why. Most often a library name is misspelled or a version in `requirements.txt` doesn't exist.
- `deployment ... failed: pre-deploy: ...`: [the pre-deploy command failed](/bots/bot-python/guides/errors#pre-deploy). Read the lines the command printed above this one, then redeploy.
- `deployment ... failed: start: nothing to start`: we found no file to run. Name your main file `main.py`, or set a start command in your bot's settings.
- `KeyError` with a variable name: [that variable is missing](/bots/bot-python/guides/errors#variable-missing). Add it to your variables under the same name and redeploy.
- `LoginFailure: Improper token has been passed` or `InvalidToken`: [the token is wrong](/bots/bot-python/guides/errors#token-invalid) or changed. Check the variable's name and value, then redeploy.
- `PrivilegedIntentsRequired`: turn on [the intent your bot asks for](/bots/bot-python/guides/errors#intents-disallowed) on the Bot page of the Developer Portal.
- `ModuleNotFoundError`: [the library is missing](/bots/bot-python/guides/errors#missing-dependency) from `requirements.txt`. Add it and redeploy.
- `MemoryError`: [your bot ran out of RAM](/bots/bot-python/guides/errors#out-of-memory). Move to a bigger plan or keep less in memory.

> [!note] If a deployment fails before your bot starts, we don't retry until you fix the cause. If your bot crashes after it started, we restart it, and after 3 crashes within 10 minutes we stop it so it doesn't loop. Fix the error and redeploy, or roll back to the last deployment that worked.
