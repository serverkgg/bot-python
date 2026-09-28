# بوت ديسكورد (discord.py)

قالب بوت ديسكورد بسيط بلغة بايثون: أمر `/ping` يرد عليك بسرعة الاتصال. سوّ منه ريبو وابنِ عليه.

A minimal Discord bot in Python: a `/ping` command that answers with the latency. Make it your own repository and build on top.

## شغّله على Serverk

[انشره على Serverk](https://serverk.gg/bots/start?template=discord-python)

1. اضغط الرابط فوق، أو اضغط **Use this template** في GitHub وبعدها اختر ريبوك الجديد من «شغّل بوتك».
2. حط التوكن في المتغيرات باسم `DISCORD_TOKEN` وخلّه حساس.
3. اضغط **ادفع وانشر**. نثبّت المكتبات من `requirements.txt` بنفسنا، وكل push على `main` ينشر بوتك من جديد.

## Use this template on Serverk

[Deploy it on Serverk](https://serverk.gg/bots/start?template=discord-python)

1. Open the link above, or press **Use this template** on GitHub and pick your new repository on «Run your bot».
2. Add the token to your variables as `DISCORD_TOKEN`, marked sensitive.
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
