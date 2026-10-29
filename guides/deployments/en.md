Deploy your bot again, follow each deployment, and roll back to an older version when a new one stops your bot.

## Before you start

- A bot that deployed at least once, as in ["Run your bot for the first time"](/bots/bot-python/guides/getting-started).
- To roll back: a deployment that succeeded before.

## 1. Open the Deployments tab

Each time you deploy, a push arrives, or you roll back, a new deployment shows up in the **Deployments** tab: the commit or the uploaded version, who started it, when, how long it took, and its log. The deployment running right now carries the **Current** mark.

![The Deployments tab listing the deployments, with the current one marked.](guides/deployments/deployments-tab.webp)

## 2. Deploy again

Press **Redeploy**, and a new deployment shows up at the top of the list. Every deployment walks the same steps:

![The Redeploy button, and a new deployment running at the top of the list.](guides/deployments/redeploy.webp)

1. We pull the commit from your repository, or unpack the version you uploaded.
2. We install the dependencies if they changed.
3. We run your pre-deploy command when your bot has one, such as your database migrations, on every deployment.
4. We start your bot and print the success line:

```txt
serverk: deployment dep_a1b2c3d4 ready at 3f2a9c1b7d10
```

@[open](overview)

## 3. Roll back to an older version

In the **Deployments** tab, open the menu at the end of the row of any deployment that succeeded before, and press **Roll back to this deployment**.

![An older deployment's menu open, showing Roll back to this deployment.](guides/deployments/rollback.webp)

We run a new deployment with exactly that old code, and files deleted since then come back.

> [!note] A rollback restores the code only. Your variables stay as they are, so if the old code needs a variable you changed, change it back yourself.

## When a deployment fails

If a step fails, the deployment stops and the last line in the console says where and why:

```txt
serverk: deployment dep_a1b2c3d4 failed: install: ERROR: No matching distribution found for discord.py==9.9
```

The step is one of `sync` (pulling the code), `snapshot` (unpacking an uploaded version), `install` (the dependencies), `pre-deploy` (the pre-deploy command) or `start` (starting the bot). Fix the cause and redeploy, or roll back to the last deployment that worked.

To read a failed deployment's lines, open the menu at the end of its row and press **Open the log**. When we know the cause, we name it above the lines with a link to its fix.

![A failed deployment's log: the step that failed, the cause and the Read the guide link.](guides/deployments/failed-log.webp)

@[open](console)

## Next

[Read the console and work out what happened](/bots/bot-python/guides/read-the-logs): what the serverk lines mean, and how to find the cause when a deployment fails or your bot crashes.
