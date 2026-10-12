## What the button does

The button opens "Run your bot" on your bot's repository: we read the code and fill in the runtime and the commands, then whoever pressed it picks a plan and deploys. It works with any public GitHub repository, and the person pressing it needs a Serverk account, not a GitHub account.

## Add it to your README

Paste this line into your `README.md`, with your bot's repository in place of `owner/name`:

```md
[![Deploy on Serverk](https://serverk.gg/button.svg)](https://serverk.gg/bots/create?repo=https://github.com/owner/name)
```

For a README written in Arabic, use the Arabic button, `https://serverk.gg/button.ar.svg`, in place of `button.svg`.

## Pick the branch

The button deploys the repository's default branch. To deploy another one, such as `dev`, add `&ref=dev` to the link, or link to the branch page itself, `https://github.com/owner/name/tree/dev`. The `repo` value takes `owner/name`, `github.com/owner/name` or the full link.

## Deploy on every push

A bot deployed from a public repository starts with deploys on push off, because we read the repository without the Serverk app on GitHub. Redeploy, rollback and the deploy hook work as usual. To deploy on every push, connect GitHub from the Git section of your bot's settings and pick the same repository.

@[open](overview)
