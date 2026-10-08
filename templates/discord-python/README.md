# بوت ديسكورد (discord.py)

قالب بوت ديسكورد بسيط بلغة بايثون: أمر `/ping` يرد بسرعة الاتصال. أنشئ منه ريبو خاصًا بك وابنِ عليه.

A minimal Discord bot in Python: a `/ping` command that answers with the latency. Make it your own repository and build on top.

## شغّله على Serverk

[انشره على Serverk](https://serverk.gg/bots/create?template=discord-python)

1. افتح الرابط أعلاه، أو اضغط **Use this template** في GitHub ثم اختر ريبوك الجديد من «شغّل بوتك».
2. أضف التوكن إلى المتغيرات باسم `DISCORD_TOKEN` واتركه حساسًا.
3. اضغط «ادفع وانشر». نثبّت المكتبات بالأمر `uv pip install -r requirements.txt`، ونشغّل البوت بالأمر `python main.py`، على Python 3.12. وكل push على `main` ينشر بوتك من جديد.

| المتغير | مطلوب | القيمة |
| --- | --- | --- |
| `DISCORD_TOKEN` | نعم | توكن البوت من Discord Developer Portal |

- يصل كل متغير إلى بوتك بالاسم الذي حفظته به تمامًا، دون بادئة أو أي تغيير، ويقرؤه الكود من `os.environ["DISCORD_TOKEN"]`.
- لا يصل ملف `.env` إلى Serverk أبدًا: يستبعده `.gitignore` من الريبو، ونحذفه من أي zip ترفعه ونقترح أسماء متغيراته دون قيمها. يحمل `.env.example` الأسماء فقط.
- يستخدم البوت `discord.Intents.default()`، ولا تشمل أيًّا من الـ Intents المميزة. إذا أضفت أحدها مثل Message Content ففعّله أولًا في Developer Portal، وإلا رفض ديسكورد تسجيل دخول البوت.

الشروحات: [شغّل بوتك أول مرة](https://serverk.gg/bots/bot-python/guides/getting-started)، [أضف التوكن والمتغيرات](https://serverk.gg/bots/bot-python/guides/environment-variables)، [أين تجد توكن بوت ديسكورد](https://serverk.gg/bots/bot-python/guides/discord-token).

## Run it on Serverk

[Deploy it on Serverk](https://serverk.gg/bots/create?template=discord-python)

1. Open the link above, or press **Use this template** on GitHub and pick your new repository on **Run your bot**.
2. Add the token to your variables as `DISCORD_TOKEN`, marked sensitive.
3. Press **Pay and deploy**. We install the dependencies with `uv pip install -r requirements.txt` and start the bot with `python main.py`, on Python 3.12. Every push to `main` deploys your bot again.

| Variable | Required | Value |
| --- | --- | --- |
| `DISCORD_TOKEN` | Yes | The bot token from the Discord Developer Portal |

- Every variable reaches your bot under exactly the name you saved it with, with no prefix and no renaming. The code reads it from `os.environ["DISCORD_TOKEN"]`.
- A `.env` file never reaches Serverk: `.gitignore` keeps it out of the repository, and we remove it from any zip you upload and suggest its variable names without the values. `.env.example` holds the names only.
- The bot uses `discord.Intents.default()`, which holds no privileged intent. If you add one such as Message Content, turn it on in the Developer Portal first, or Discord refuses the bot's login.

Guides: [Run your bot for the first time](https://serverk.gg/bots/bot-python/guides/getting-started), [Add the token and your variables](https://serverk.gg/bots/bot-python/guides/environment-variables), [Where to find your Discord bot token](https://serverk.gg/bots/bot-python/guides/discord-token).

## مع أداة ذكاء اصطناعي / With an AI tool

يشرح ملف `AGENTS.md` في هذا الريبو ما سبق لأداة الذكاء الاصطناعي التي تكتب بها بوتك. وتعلّمها `use-serverk` من Serverk طريقة النشر كاملة، ونذكر ريبو `use-serverk` ضمن `serverkgg` في https://serverk.gg/llms.txt فور نشره. لتنشر الأداة بوتك وتضبط متغيراته وتقرأ سجل النشر، اربطها بواجهة MCP على `https://api.serverk.gg/mcp`.

`AGENTS.md` tells the AI tool you write your bot with all of the above. Serverk's `use-serverk` skill teaches it the whole workflow; its repository under `serverkgg` is named in https://serverk.gg/llms.txt once published. To let it deploy your bot, set its variables and read the deployment log, connect it to the Serverk MCP server at `https://api.serverk.gg/mcp`.

## على جهازك / On your machine

```sh
cp .env.example .env
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
set -a && . ./.env && set +a
.venv/bin/python main.py
```

ضع التوكن في `.env` على جهازك فقط، ولا ترفعه أبدًا. مكانه على Serverk متغيرات بوتك.

Keep the token in `.env` on your own machine only and never push it. On Serverk it belongs in your bot's variables.
