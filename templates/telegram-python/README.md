# بوت تيليقرام (python-telegram-bot)

قالب بوت تيليقرام بسيط بلغة بايثون: يرحّب بك عند `/start` ويرد على أي رسالة بنصها. أنشئ منه ريبو خاصًا بك وابنِ عليه.

A minimal Telegram bot in Python: it greets you on `/start` and echoes every message back. Make it your own repository and build on top.

## شغّله على Serverk

[![انشر على سيرفرك](https://serverk.gg/button.ar.svg)](https://serverk.gg/bots/create?template=telegram-python)

1. اضغط الزر أعلاه، أو اضغط **Use this template** في GitHub ثم اختر ريبوك الجديد من «شغّل بوتك».
2. أضف التوكن إلى المتغيرات باسم `TELEGRAM_TOKEN` واتركه حساسًا.
3. اضغط «ادفع وانشر». نثبّت المكتبات بالأمر `uv pip install -r requirements.txt`، ونشغّل البوت بالأمر `python main.py`، على Python 3.12. وكل push على `main` ينشر بوتك من جديد.

| المتغير | مطلوب | القيمة |
| --- | --- | --- |
| `TELEGRAM_TOKEN` | نعم | توكن البوت من BotFather |

- يصل كل متغير إلى بوتك بالاسم الذي حفظته به تمامًا، دون بادئة أو أي تغيير، ويقرؤه الكود من `os.environ["TELEGRAM_TOKEN"]`.
- لا يصل ملف `.env` إلى Serverk أبدًا: يستبعده `.gitignore` من الريبو، ونحذفه من أي zip ترفعه ونقترح أسماء متغيراته دون قيمها. يحمل `.env.example` الأسماء فقط.
- يستقبل البوت الرسائل بطريقة polling. ولاستخدام الـ webhook، فعّل عنوان الويب من **الإدارة**، فيصل إلى بوتك `PORT` و `SERVERK_WEB_URL` و `SERVERK_WEB_HOST`. والتوكن الواحد يشغّل بوتًا واحدًا، فأوقف أي نسخة أخرى شغّالة بالتوكن نفسه قبل النشر.

الشروحات: [شغّل بوتك أول مرة](https://serverk.gg/bots/bot-python/guides/getting-started)، [أضف التوكن والمتغيرات](https://serverk.gg/bots/bot-python/guides/environment-variables)، [أين تجد توكن بوت تيليقرام](https://serverk.gg/bots/bot-python/guides/telegram-token).

## Run it on Serverk

[![Deploy on Serverk](https://serverk.gg/button.svg)](https://serverk.gg/bots/create?template=telegram-python)

1. Press the button above, or press **Use this template** on GitHub and pick your new repository on **Run your bot**.
2. Add the token to your variables as `TELEGRAM_TOKEN`, marked sensitive.
3. Press **Pay and deploy**. We install the dependencies with `uv pip install -r requirements.txt` and start the bot with `python main.py`, on Python 3.12. Every push to `main` deploys your bot again.

| Variable | Required | Value |
| --- | --- | --- |
| `TELEGRAM_TOKEN` | Yes | The bot token from BotFather |

- Every variable reaches your bot under exactly the name you saved it with, with no prefix and no renaming. The code reads it from `os.environ["TELEGRAM_TOKEN"]`.
- A `.env` file never reaches Serverk: `.gitignore` keeps it out of the repository, and we remove it from any zip you upload and suggest its variable names without the values. `.env.example` holds the names only.
- The bot receives messages by long polling. For a webhook, turn on the web address in **Manage**: your bot then gets `PORT`, `SERVERK_WEB_URL` and `SERVERK_WEB_HOST`. One token runs one bot, so stop any other copy that uses the same token before you deploy.

Guides: [Run your bot for the first time](https://serverk.gg/bots/bot-python/guides/getting-started), [Add the token and your variables](https://serverk.gg/bots/bot-python/guides/environment-variables), [Where to find your Telegram bot token](https://serverk.gg/bots/bot-python/guides/telegram-token).

## مع أداة ذكاء اصطناعي / With an AI tool

يشرح ملف `AGENTS.md` في هذا الريبو ما سبق لأداة الذكاء الاصطناعي التي تكتب بها بوتك. وتعلّمها `serverk-bot` من Serverk طريقة النشر كاملة، وريبوها هو https://github.com/serverkgg/serverk-skills. لتنشر الأداة بوتك وتضبط متغيراته وتقرأ سجل النشر، اربطها بواجهة MCP على `https://api.serverk.gg/mcp`.

`AGENTS.md` tells the AI tool you write your bot with all of the above. Serverk's `serverk-bot` skill teaches it the whole workflow; its repository is https://github.com/serverkgg/serverk-skills. To let it deploy your bot, set its variables and read the deployment log, connect it to the Serverk MCP server at `https://api.serverk.gg/mcp`.

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
