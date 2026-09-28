# بوت تيليجرام (python-telegram-bot)

قالب بوت تيليجرام بسيط بلغة بايثون: يرحّب فيك على `/start` ويرجّع لك أي رسالة ترسلها. سوّ منه ريبو وابنِ عليه.

A minimal Telegram bot in Python: it greets you on `/start` and echoes every message back. Make it your own repository and build on top.

## شغّله على Serverk

[انشره على Serverk](https://serverk.gg/bots/start?template=telegram-python)

1. اضغط الرابط فوق، أو اضغط **Use this template** في GitHub وبعدها اختر ريبوك الجديد من «شغّل بوتك».
2. حط التوكن في المتغيرات باسم `TELEGRAM_TOKEN` وخلّه حساس.
3. اضغط **ادفع وانشر**. نثبّت المكتبات من `requirements.txt` بنفسنا، وكل push على `main` ينشر بوتك من جديد.

## Use this template on Serverk

[Deploy it on Serverk](https://serverk.gg/bots/start?template=telegram-python)

1. Open the link above, or press **Use this template** on GitHub and pick your new repository on «Run your bot».
2. Add the token to your variables as `TELEGRAM_TOKEN`, marked sensitive.
3. Press **Pay and deploy**. We install the dependencies from `requirements.txt`, and every push to `main` deploys your bot again.

## على جهازك / On your machine

```sh
cp .env.example .env
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
set -a && . ./.env && set +a
.venv/bin/python main.py
```

حط التوكن في `.env` على جهازك بس ولا ترفعه أبد. على Serverk مكانه متغيرات بوتك.

Keep the token in `.env` on your own machine only and never push it. On Serverk it belongs in your bot's variables.
