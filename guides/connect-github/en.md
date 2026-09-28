## Connect your GitHub account

On «Run your bot», pick **GitHub** and install the Serverk app on your account or organization, choosing the repositories we may reach. Then pick the repository and the branch, and we handle the rest.

Private repositories work without giving us any token: the app hands us short-lived read access during a deployment only, and your bot never sees it.

## Every push deploys your bot

Turn on **Auto-deploy** in the Git section of your bot's settings, and every push to the linked branch deploys your bot on its own. Each deployment pins exactly one commit, so you always know which code is running.

We also post the deployment's status on the commit itself in GitHub, as `serverk/deploy`: pending, success or failure.

## Deploy on your own terms

Press **Redeploy** on your bot's page and we deploy the latest commit of the branch. To deploy from anywhere else, such as GitHub Actions, take the **deploy hook** from the Git section: any `POST` request to it deploys your bot.

> [!warning] Treat the deploy hook like a password. Never share it, and rotate it from the Git section if it leaks.

@[open](overview)

## What changes during a deployment?

A deployment resets every file that exists in the repository to its version in the commit, so any change you made in the file manager to a file from the repository is gone. Files that are not in the repository, such as `.venv` or your bot's data files, stay as they are.
