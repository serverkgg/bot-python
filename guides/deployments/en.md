## Every deployment is on record

Each time you deploy, a push arrives, or you roll back, a new deployment shows up in the **Deployments** tab: the commit or the uploaded version, who started it, when, how long it took, and its log. The deployment running right now carries the **Current** mark.

Every deployment walks the same steps:

1. We pull the commit from your repository, or unpack the version you uploaded.
2. We install the dependencies if they changed.
3. We start your bot and print the success line:

```txt
serverk: deployment dep_a1b2c3d4 ready at 3f2a9c1b7d10
```

@[open](overview)

## When a deployment fails

If a step fails, the deployment stops and the last line in the console says where and why:

```txt
serverk: deployment dep_a1b2c3d4 failed: install: ERROR: No matching distribution found for discord.py==9.9
```

The step is one of `sync` (pulling the code), `snapshot` (unpacking an uploaded version), `install` (the dependencies) or `start` (starting the bot). Fix the cause and redeploy, or roll back to the last deployment that worked.

@[open](console)

## Roll back to an older version

In the **Deployments** tab, pick any deployment that succeeded before and press **Rollback**. We run a new deployment with exactly that old code, and files deleted since then come back.

> [!note] A rollback restores the code only. Your variables stay as they are, so if the old code needs a variable you changed, change it back yourself.
