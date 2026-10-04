## Upload your code

On "Run your bot", pick **Upload the code** and drop your bot folder or a zip. We zip the folder ourselves and leave out `.venv`, `__pycache__`, `.git` and `.env`, because we install the dependencies ourselves and your variables belong on the variables page.

If every file in the zip sits inside one folder, we lift them out so `requirements.txt` lands at the top of your bot folder.

> [!warning] Found a `.env` file in your code? Put its values in your variables, marked sensitive, and never upload it with the code.

## Ship a new version

Changed your code? In the **Deployments** tab press **Upload a new version** and upload the folder or the zip again. It becomes a new deployment, and files you deleted from your copy are deleted from your bot too.

@[open](overview)

## Editing in the file manager

You can edit any file in the file manager and restart your bot to run it. Keep in mind that the next deployment puts the uploaded version's files back exactly as you uploaded them, so a lasting change belongs in a new version you upload.

@[open](files)
