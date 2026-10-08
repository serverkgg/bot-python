## Folder or zip

On "Run your bot", or with **Upload a new version** in the **Deployments** tab, drop your bot's folder or a zip, or press **Choose a folder** or **Choose a zip file**.

- **A folder**: we pack it in your browser and leave out `.venv`, `__pycache__`, `.git` and `node_modules`. We don't compress it, so it counts at its full size.
- **A zip**: we upload it as it is, and it counts at its compressed size. When your folder is over the limit, zip it yourself and upload the zip.

@[open](overview)

## Limits

- 24 MB for the upload.
- 20,000 files and 512 MB once unpacked.
- An upload you haven't deployed expires after 24 hours. Upload it again.

We refuse a zip that is password-protected, holds a symlink, an absolute path or `..`, or holds the same path twice.

## The folder around your files

When every file in the zip sits inside one folder, we take them out of it, so `requirements.txt` lands at the top of your bot folder. We take out one folder only, so zip the folder that holds `requirements.txt` itself.

## Hidden files and what we leave out

Files whose names start with a dot, such as `.python-version` and `.env.example`, upload like any other file. We leave out:

- `.git`, `__MACOSX` and `.DS_Store`.
- A `.serverk` folder at the top of your code, a name Serverk keeps for itself.
- Every `.env` file, such as `.env` or `.env.local`. `.env.example`, `.env.sample` and `.env.template` stay.

`.venv` inside a zip uploads as it is, so take it out: we set up the Python environment ourselves.

## What happens to `.env`

On "Run your bot":

- From a folder, we offer **Add its values to the variables**, which fills in the names and values for you.
- From a zip, we add the names in the `.env` at the top of the zip to the suggested variables, and you paste their values.

Mark the token and every secret value **Sensitive**.

> [!warning] Never put your bot's data files, such as `bot.sqlite`, in an upload. Every file you upload replaces the file with the same name in your bot.
