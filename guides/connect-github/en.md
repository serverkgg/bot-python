## Connect your GitHub account

On "Run your bot", pick **GitHub repository** and install the Serverk app on your account or organization, choosing the repositories we may reach. Then pick the repository and the branch, and we handle the rest.

Private repositories work without giving us any token: the app hands us short-lived read access during a deployment only, and your bot never sees it.

A public repository needs no app: open `https://serverk.gg/bots/create?repo=owner/name` with your bot's repository in place of `owner/name` and deploy it right away. That bot starts with deploys on push off; connect GitHub from the Git section and pick the same repository to turn them on.

## Every push deploys your bot

Turn on **Deploy on every push** in the Git section of your bot's settings, and every push to the linked branch deploys your bot on its own. Each deployment pins exactly one commit, so you always know which code is running.

We also post the deployment's status on the commit itself in GitHub, as `serverk/deploy`: pending, success or failure.

## Deploy it yourself

Press **Redeploy** on your bot's page and we deploy the latest commit of the branch. To deploy from anywhere else, such as GitHub Actions, take the **Deploy hook** from the Git section: any `POST` request to it deploys your bot.

> [!warning] Treat the deploy hook like a password. Never share it, and rotate it from the Git section if it leaks.

@[open](overview)

## What changes during a deployment?

A deployment resets every file that exists in the repository to its version in the commit, so any change to those files is gone, whether you made it in the **Files** tab or your bot wrote it while running. Files the repository never carried, such as `.venv` and the data files your bot creates, stay as they are. Keep data files such as `data.json` or `bot.sqlite` out of the repository by adding them to `.gitignore`.
