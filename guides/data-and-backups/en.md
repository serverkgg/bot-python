## What a deployment replaces

Every deployment, whether it comes from a push, from **Redeploy** or from a new version you upload, treats your bot folder by one rule:

- Every file the code carries goes back to its state in the code, even if you changed it in the **Files** tab or your bot wrote to it while running.
- A file the previous code carried and the new code doesn't is deleted, unless it changed since the last deployment. Then it stays.
- A file the code never carried stays as it is, such as `.venv` and the data files your bot creates.

Here, the code is the commit we deploy, or the folder or zip you uploaded.

@[open](overview)

## Keep your data out of the code

Let your bot create its data files itself, such as a `data` folder or a `bot.sqlite` file, and keep them out of the code you deploy:

- With GitHub, add them to `.gitignore`. If the repository already carries the file, `.gitignore` alone isn't enough: take it out of the repository with `git rm --cached`.
- With an upload, leave them out of the folder or zip, because every file you upload replaces the file with the same name in your bot.

When you set up your bot on "Run your bot", we warn you if the code carries a database file (`.sqlite`, `.sqlite3` or `.db`).

> [!warning] Never put your bot's data in the code you deploy. The next deployment puts the file back to its state in the code, and everything your bot wrote to it since is lost.

## Roll back to an older deployment

A rollback is a new deployment with exactly the code of an older one, an older commit or a version you uploaded before, so the same rule applies: the old code's files come back, and the data files your bot created stay. A rollback doesn't change your variables; they stay as they are.

## What a backup holds

A backup holds every file in your bot folder except:

- `.venv`, `__pycache__` and `.cache`
- the `logs` folder and every file ending in `.log`
- the temporary files and uploaded versions we keep in `.serverk`

Sensitive variables never enter a backup.

> [!note] Don't keep your bot's data in the `logs` folder or in a `.log` file. Backups leave them out.

For an exact copy of a SQLite database, stop your bot first, then press **Back up now**. While the bot is running, its last few writes may be missing from the backup.

@[open](backups)

## Restore a backup

When you press **Restore**, we first take a backup of the current state, then put your bot folder back the way it was in the backup, and every file created after it is deleted. Files that backups leave out, such as `.venv`, stay as they are.

Then we deploy the current deployment again, so the code's files come from the current deployment and the rest from the backup.

## Reset

A reset, from **Manage** then **Danger zone**, deletes every file and all data in your bot folder. We take a backup right before it, which you'll find in the **Backups** tab if you need to go back.

Then we rebuild your bot from scratch and deploy the current deployment again. Your variables and repository link stay as they are.
