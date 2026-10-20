# بوت بايثون (Python bot)

حزمة بوتات بايثون على منصة سيرفرك (`serverk.gg`). هذا المستودع فيه كل شيء يحتاجه بوت ديسكورد أو تيليجرام مكتوب بلغة بايثون عشان يشتغل على المنصة: ملف التعريف `serverk.yml`، الـ driver اللي يدير البوت، صورة الدوكر مع الـ launcher، القوالب الجاهزة، والشروحات.

The Python bot package for the Serverk platform (`serverk.gg`). This repo holds everything a Discord or Telegram bot written in Python needs to run on the platform: the `serverk.yml` manifest, the driver that manages the bot, the Docker image with its launcher, the starter templates, and the guides.

## Layout

- `serverk.yml` — the bot manifest: metadata, resources, no ports, the environment vault, backup rules, file notes, guides.
- `src/` — the bridge driver: install (the launcher's `install` mode), lifecycle and its layered process environment (tool defaults, then the customer's vault, then the launcher's internals), the passive identity card, the deploy module the platform invokes, query, terminal rules and the deployment event.
- `image/Dockerfile` — the runtime image; the compiled bridge binary is its entrypoint.
- `image/launcher.py` — what the bridge starts: it takes the deploy marker, puts the code in place (a pinned Git commit, an uploaded snapshot committed into `.serverk/history`, or the files already there), installs the dependencies into the bot's own `.venv` by hash, runs the pre-deploy command once per deployment, prints `serverk: deployment <id> ready` or `serverk: deployment <id> failed: <stage>: <detail>`, then `serverk: bot process starting`, and replaces itself with the bot's own start command.
- `image/detect.json` — the start and install table the launcher reads, rendered by `serverk-bridge detect-table` from the same kit the platform inspects code with.
- `image/test_launcher.py` — the launcher's unit tests, run with `python3 -m unittest` and from `bun run test`.
- `image/git-askpass` — hands Git the installation token from the environment, so it never lands on a command line or in a log.
- `templates/` — starter bots (discord.py and python-telegram-bot), each with a fully pinned `requirements.txt`, synced to the public `serverkgg/bot-template-*` repositories by `outdo templates`.
- `assets/` — logo and banner (webp).
- `guides/` — customer guides in Arabic and English.

## Develop

Everything runs on [Bun](https://bun.sh):

```sh
bun install
bun run check
bun run tsc
bun run test
bun run validate
bun run compile
```

`validate` checks the manifest, assets, driver wiring and the detection table with the exact validation the platform runs at publish. `compile` produces `dist/bridge`, an amd64 binary — serverk publishes package images for `linux/amd64` only. The launcher is tested with `python3 -m unittest` against `templates/`, and `bun run test` runs those tests, checks its tables and patterns against the bridge's, and drives its snapshot deployments end to end with `python3` and `git`.

The `pre-commit` hook is the gate: it runs `fix`, `tsc`, `test`, `validate`, `serverk-bridge schema --check` and `serverk-bridge detect-table --check`, and restages whatever the formatter touched. There is no CI workflow — a commit that passes the hook is a commit that is ready.

The driver is built on [`@serverkgg/bridge`](https://www.npmjs.com/package/@serverkgg/bridge) and its `@serverkgg/bridge/bot` helpers. `bun install` runs `serverk-bridge link`, which points `node_modules/@serverkgg/bridge` at `../serverk/modules/bridge` when that checkout exists — never commit a `file:` dependency.

## Contribute

- افتح issue لأي مشكلة أو اقتراح — بالعربي أو بالإنجليزي، كلها مرحّب فيها.
- Run `bun install` once so the `pre-commit` hook is wired, then let it gate every commit — lint, types, tests, package validation, and the schema check all run locally, with no secrets and nothing to configure.
- Releases are done by the Serverk team through the platform's central release pipeline; merged changes ride the next release.

## Arabic copy

Arabic is the source language of the platform. Customer-facing strings in `serverk.yml`, the launcher's hints and the guides use Gulf Arabic — the package's name is «بوت بايثون» ("Python bot" in English): it names the product a customer buys, so nothing adds «بوت» in front of it, and «بايثون» alone only ever names the runtime.
