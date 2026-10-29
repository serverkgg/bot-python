يوضح كل سطر في الكونسول متى طُبع، ومن طبعه، وما يقوله. ابحث عن سطرك هنا، ثم اعرف ما يلزم فعله.

## أين تجد السجل

يعرض تبويب **الكونسول** كل سطر لحظة طباعته، من بوتك ومنّا. وتعرض بطاقة **آخر السجل** في **نظرة عامة** آخر الأسطر التي طبعها بوتك، ويحفظ تبويب **النشرات** سجل كل نشر: افتح القائمة في آخر صفه واضغط **افتح السجل**.

![تبويب «الكونسول» في لوحة البوت، وفيه أسطر بوتك.](guides/read-the-logs/console-tab.webp)

@[open](console)

## اقرأ السطر

![أسطر في الكونسول وأجزاؤها الثلاثة مرقّمة: الوقت، ومن طبعه، والسطر نفسه.](guides/read-the-logs/read-a-line.webp)

1. الوقت الذي طُبع فيه السطر.
2. من طبعه: `BOT` لما يطبعه بوتك، ومعه سطور `serverk:` التي نطبعها، و `BRIDGE` للبرنامج الذي يشغّل بوتك ويراقبه، و `API` لمنصة سيرفرك نفسها، مثل بدء نشر جديد.
3. السطر نفسه، ويظهر باللون الأحمر إذا كان خطأ.

## سطور serverk

كل سطر يبدأ بـ `serverk:` صادر منا وليس من بوتك، ويوضح ما نفّذناه قبل أن يبدأ:

- `deploying ...`: بدأ نشر جديد.
- `fetching ... at ...` أو `unpacking snapshot ...`: نسحب الـ commit من الريبو، أو نفك الكود الذي رفعته.
- `creating .venv ...`: ننشئ بيئة بايثون خاصة ببوتك.
- `installing dependencies ...`: نثبّت المكتبات.
- `dependencies are up to date`: لم يتغيّر شيء، فلم نعد التثبيت.
- `deployment ... ready at ...`: نجح النشر.
- `web address ... on port ...`: عنوان الويب لبوتك، والمنفذ الذي يلزم أن يستمع عليه، ما دام عنوان الويب مفعّلًا.
- `port 1 ...` و `port 2 ...`: رقم كل منفذ مفعّل، ومعه العنوان الذي يتصل به الآخرون إذا كان عنوان الويب مفعّلًا.
- `start command: ...`: الأمر الذي نشغّل به بوتك.
- `bot process starting`: بدأ بوتك، وكل سطر بعده يطبعه بوتك نفسه.

## عندما يتعطّل بوتك

تظهر الأخطاء باللون الأحمر. في بايثون اقرأ آخر سطر من الخطأ:

```txt
Traceback (most recent call last):
  File "/home/container/main.py", line 12, in <module>
    bot.run(os.environ["DISCORD_TOKEN"])
KeyError: 'DISCORD_TOKEN'
```

يوضح آخر سطر نوع الخطأ، ويوضح `File ... line 12` مكانه: الملف `main.py`، السطر 12. ومعنى هذا المثال أن المتغير `DISCORD_TOKEN` غير موجود في متغيرات بوتك.

## أشهر الأخطاء

عندما يتوقف بوتك على سبب نعرفه، تذكر صفحة النشر السبب، ويفتح **اقرأ الشرح** قسمه في شرح [«أخطاء بوتك وحلولها»](/bots/bot-python/guides/errors).

![نشر فاشل يذكر سببه، ورابط «اقرأ الشرح» تحته.](guides/read-the-logs/named-cause.webp)

- `deployment ... failed: sync: ...`: تعذّر سحب الـ commit. تأكد من وجود الريبو والفرع، ومن أن تطبيق Serverk على GitHub يصل إلى الريبو.
- `deployment ... failed: sync: repository tracks .serverk`: في الريبو مجلد `.serverk`، وهذا الاسم محجوز لمنصة سيرفرك. احذف المجلد من الريبو وانشر من جديد.
- `deployment ... failed: install: ...`: فشل تثبيت المكتبات، والسطر يوضح السبب. غالبًا يكون اسم مكتبة غير صحيح أو إصدار غير موجود في `requirements.txt`.
- `deployment ... failed: pre-deploy: ...`: [فشل أمر ما قبل النشر](/bots/bot-python/guides/errors#pre-deploy). اقرأ الأسطر التي طبعها الأمر فوق هذا السطر، ثم انشر من جديد.
- `deployment ... failed: start: nothing to start`: لم نجد ملفًا لتشغيله. سمِّ ملفك الرئيسي `main.py`، أو اضبط أمر التشغيل من إعدادات بوتك.
- `KeyError` مع اسم متغير: [المتغير غير موجود](/bots/bot-python/guides/errors#variable-missing). أضفه إلى المتغيرات بالاسم نفسه، ثم انشر من جديد.
- `LoginFailure: Improper token has been passed` أو `InvalidToken`: [التوكن غير صحيح](/bots/bot-python/guides/errors#token-invalid) أو تغيّر. تأكد من اسم المتغير وقيمته، ثم انشر من جديد.
- `PrivilegedIntentsRequired`: فعّل [الـ intent الذي يطلبه بوتك](/bots/bot-python/guides/errors#intents-disallowed) من صفحة Bot في Developer Portal.
- `ModuleNotFoundError`: [المكتبة غير موجودة](/bots/bot-python/guides/errors#missing-dependency) في `requirements.txt`. أضفها، ثم انشر من جديد.
- `MemoryError`: [استهلك بوتك الرام كاملة](/bots/bot-python/guides/errors#out-of-memory). انتقل إلى باقة أكبر، أو قلّل ما يحتفظ به بوتك في الذاكرة.

> [!note] إذا فشل النشر قبل أن يبدأ بوتك، فلا نعيد المحاولة حتى تصلح السبب. وإذا تعطّل بوتك بعد أن بدأ، ننفّذ له ريستارت، وإذا تعطّل 3 مرات خلال 10 دقائق نوقفه حتى لا يدخل في حلقة متكررة. أصلح الخطأ وانشر من جديد، أو رجّع آخر نشر كان شغّالًا.
