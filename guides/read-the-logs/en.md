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

@[open](console)

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

- `deployment ... failed: sync: ...`: we couldn't pull the commit. Check that the repository and the branch exist and that the Serverk app on GitHub can reach the repository.
- `deployment ... failed: sync: repository tracks .serverk`: your repository has a `.serverk` folder, and that name is reserved for Serverk. Delete the folder from your repository and redeploy.
- `deployment ... failed: install: ...`: the dependency install failed and the line says why. Most often a library name is misspelled or a version in `requirements.txt` doesn't exist.
- `deployment ... failed: start: nothing to start`: we found no file to run. Name your main file `main.py`, or set a start command in your bot's settings.
- `KeyError` with a variable name: that variable is missing. Add it to your variables under the same name and redeploy.
- `LoginFailure: Improper token has been passed` or `InvalidToken`: the token is wrong or changed. Check its value and redeploy.
- `PrivilegedIntentsRequired`: turn on the intent your bot asks for on the Bot page of the Developer Portal.
- `ModuleNotFoundError`: the library is missing from `requirements.txt`. Add it and redeploy.
- `MemoryError`: your bot ran out of RAM. Move to a bigger plan or keep less in memory.

> [!note] If a deployment fails before your bot starts, we don't retry until you fix the cause. If your bot crashes after it started, we restart it, and after 3 crashes within 10 minutes we stop it so it doesn't loop. Fix the error and redeploy, or roll back to the last deployment that worked.
