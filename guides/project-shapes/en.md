## How we install the libraries

We give your bot its own Python environment (`.venv`) and install into it from the first file we find, in this order:

1. `requirements.txt`: `uv pip install -r requirements.txt`.
2. `uv.lock`: `uv sync --locked --no-dev`. Run `uv lock` after every change to `pyproject.toml`, because a lockfile that doesn't match stops the install.
3. `poetry.lock` or `pdm.lock`: we install the project from `pyproject.toml` with `uv pip install .`, without the lockfile, and the console says `poetry.lock is not used, installing from pyproject.toml`.
4. `Pipfile`: `pipenv install`.
5. `pyproject.toml` alone: `uv pip install .`.

To get the exact versions you tested with Poetry or PDM, add a `requirements.txt` with pinned versions, since it comes first. Pin every library with `==`, such as `discord.py==2.7.1`; "Run your bot" warns you when a library has no version.

We only install again when the install command, the Python version, the dependency file or its partner changes: `pyproject.toml` for a lockfile, `Pipfile.lock` for a `Pipfile`. Otherwise the console shows `dependencies are up to date (uv)`.

@[open](console)

## Python version

We read the version from the first file we find: `.python-version`, then `runtime.txt` such as `python-3.11.9`, then `python_version` in `Pipfile`, then `.tool-versions`. Without any of them, your bot runs on Python 3.12.

When your code asks for another version, we install it with uv on the first deployment that asks, and the console shows `creating .venv with Python 3.11 through uv`. When the version changes, we rebuild the environment: `Python changed to 3.11, rebuilding .venv`.

> [!note] Python 3.13 and later no longer include `audioop`. If your bot needs it, keep 3.12, or add `audioop-lts` to `requirements.txt`.

## How we start your bot

The first match wins:

1. The start command in your bot's settings.
2. The `start` field in `serverk.json`.
3. The `worker:` or `bot:` line of a `Procfile`.
4. `main.py`, then `bot.py`, `app.py`, `src/main.py` and `src/bot.py`.
5. `python -m` with the one folder at the top of your code that holds a `__main__.py`, such as `python -m mybot`. Folders named `tests`, `test`, `docs`, `examples` and `scripts` don't count.

A file starts as `.venv/bin/python -u main.py`. A command you write in the settings, in `serverk.json` or in a `Procfile` runs with `.venv/bin` first on the path, so `python` there is your bot's own Python.

## The pre-deploy command

The pre-deploy command is for a task such as a database migration. We run it once per deployment, after the install and before your bot starts. The first match wins:

1. The pre-deploy command in your bot's settings.
2. The `preDeploy` field in `serverk.json`.
3. `alembic.ini`: `alembic upgrade head`.
4. `manage.py`: `python manage.py migrate --noinput`.

Without any of them, nothing runs. To replace the command we find, write your own in the settings or in `serverk.json`.

The command runs in your bot's code folder with your bot's variables, and with `.venv/bin` first on the path, so `alembic` and `python` there come from your bot's own environment. The console shows `running the pre-deploy command: alembic upgrade head`.

A restart doesn't run it, only a deployment does. When it fails, the deployment stops at the `pre-deploy` step before your bot starts, and we run it again on the next start until the deployment completes. So make it a command that is safe to run twice, as the migration commands above are.

## A command you run from the console

The pre-deploy command runs on every deployment, so keep your migrations there. For a task you run once by hand, type its command in the console instead, such as:

- `python manage.py createsuperuser --noinput` to create a Django superuser. With `--noinput`, Django reads the account from `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL` and `DJANGO_SUPERUSER_PASSWORD`, so add them to your variables, mark the password **Sensitive**, and redeploy before you run the command.
- `python -m scripts.seed` to run one of your own scripts once, here `scripts/seed.py`.
- `pip list` to see which libraries your bot's environment has, and their versions.

We run it the way we run your bot: in your bot's code folder, as the same user your bot runs as, with your bot's variables and `.venv/bin` first on the path, so `python` and `pip` there come from your bot's own environment. It works even while your bot is stopped or has crashed. Its output prints in the console, then `serverk: command finished`, or `serverk: command failed (exit 1)`, where the number is the command's exit code. The next deployment puts back every file your code carries, so a lasting change, such as a new library in `requirements.txt`, belongs in your code.

One command runs at a time, for 10 minutes at most, and its output stops at 256 KiB. A command can't read input, so one that asks a question ends at once: add its flag that skips the questions, such as `--noinput`. Before your bot's first deployment, the console answers `serverk: deploy the bot first`.

@[open](console)

## What the runtime has

`ffmpeg`, `libopus` and `libsodium` for voice bots, and the build tools for libraries that build during the install. Everything your bot prints reaches the console at once, because `PYTHONUNBUFFERED=1` is set.
