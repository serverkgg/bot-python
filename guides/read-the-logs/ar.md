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

@[open](console)

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

- `deployment ... failed: sync: ...`: تعذّر سحب الـ commit. تأكد من وجود الريبو والفرع، ومن أن تطبيق Serverk على GitHub يصل إلى الريبو.
- `deployment ... failed: sync: repository tracks .serverk`: في الريبو مجلد `.serverk`، وهذا الاسم محجوز لمنصة سيرفرك. احذف المجلد من الريبو وانشر من جديد.
- `deployment ... failed: install: ...`: فشل تثبيت المكتبات، والسطر يوضح السبب. غالبًا يكون اسم مكتبة غير صحيح أو إصدار غير موجود في `requirements.txt`.
- `deployment ... failed: start: nothing to start`: لم نجد ملفًا لتشغيله. سمِّ ملفك الرئيسي `main.py`، أو اضبط أمر التشغيل من إعدادات بوتك.
- `KeyError` مع اسم متغير: المتغير غير موجود. أضفه إلى المتغيرات بالاسم نفسه، ثم انشر من جديد.
- `LoginFailure: Improper token has been passed` أو `InvalidToken`: التوكن غير صحيح أو تغيّر. تأكد من قيمته، ثم انشر من جديد.
- `PrivilegedIntentsRequired`: فعّل الـ intent الذي يطلبه بوتك من صفحة Bot في Developer Portal.
- `ModuleNotFoundError`: المكتبة غير موجودة في `requirements.txt`. أضفها، ثم انشر من جديد.
- `MemoryError`: استهلك بوتك الرام كاملة. انتقل إلى باقة أكبر، أو قلّل ما يحتفظ به بوتك في الذاكرة.

> [!note] إذا فشل النشر قبل أن يبدأ بوتك، فلا نعيد المحاولة حتى تصلح السبب. وإذا تعطّل بوتك بعد أن بدأ، نعمل له ريستارت، وإذا تعطّل 3 مرات خلال 10 دقائق نوقفه حتى لا يدخل في حلقة متكررة. أصلح الخطأ وانشر من جديد، أو ارجع إلى آخر نشر كان شغّالًا.
