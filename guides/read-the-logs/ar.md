## سطور serverk

كل سطر يبدأ بـ `serverk:` جاي منا، مو من بوتك، ويوريك وش سوينا قبل ما يبدأ:

- `deploying ...`: بدأ نشر جديد.
- `fetching ... at ...` أو `unpacking snapshot ...`: نسحب الكوميت من الريبو، أو نفك النسخة اللي رفعتها.
- `creating .venv ...`: نسوي بيئة بايثون خاصة ببوتك.
- `installing dependencies ...`: نثبّت المكتبات.
- `dependencies are up to date`: ما تغيّر شيء، فما ثبّتنا من جديد.
- `deployment ... ready at ...`: نجح النشر.
- `start command: ...`: الأمر اللي نشغّل فيه بوتك.
- `bot process starting`: بدأ بوتك، وكل سطر بعده يطبعه بوتك نفسه.

@[open](console)

## لما يتعطّل بوتك

الأخطاء تطلع باللون الأحمر. في بايثون اقرأ آخر سطر من الخطأ:

```txt
Traceback (most recent call last):
  File "/home/container/main.py", line 12, in <module>
    bot.run(os.environ["DISCORD_TOKEN"])
KeyError: 'DISCORD_TOKEN'
```

آخر سطر يقول وش الخطأ، و`File ... line 12` يقول وينه: الملف `main.py`، السطر 12. والمثال هذا معناه إن المتغير `DISCORD_TOKEN` مو موجود في متغيرات بوتك.

## أشهر الأخطاء

- `deployment ... failed: sync: ...`: ما قدرنا نسحب الكوميت. تأكد إن الريبو والفرع موجودين وإن تطبيق Serverk على GitHub يقدر يوصل للريبو.
- `deployment ... failed: sync: repository tracks .serverk`: الريبو فيه مجلد `.serverk`، وهذا الاسم محجوز لسيرفرك. احذف المجلد من الريبو وانشر من جديد.
- `deployment ... failed: install: ...`: فشل تثبيت المكتبات والسطر يقول السبب. غالباً اسم مكتبة غلط أو نسخة ما لها وجود في `requirements.txt`.
- `deployment ... failed: start: nothing to start`: ما لقينا ملف نشغّله. سمِّ ملفك الرئيسي `main.py`، أو حط أمر التشغيل من إعدادات بوتك.
- `KeyError` باسم متغير: المتغير مو موجود. أضفه في المتغيرات بنفس الاسم وانشر من جديد.
- `LoginFailure: Improper token has been passed` أو `InvalidToken`: التوكن غلط أو تغيّر. تأكد من قيمته وانشر من جديد.
- `PrivilegedIntentsRequired`: فعّل الـ intent اللي يطلبه بوتك من Developer Portal في صفحة Bot.
- `ModuleNotFoundError`: المكتبة مو في `requirements.txt`. أضفها وانشر من جديد.
- `MemoryError`: بوتك خلّص الرام. كبّر باقتك أو خفّف اللي يحفظه بوتك في الذاكرة.

> [!note] لو فشل النشر قبل ما يبدأ بوتك، ما نعيد المحاولة لين تصلّح السبب. ولو تعطّل بوتك بعد ما بدأ نعيد تشغيله، وإذا تعطّل 3 مرات خلال 10 دقايق نوقفه عشان ما يدور في حلقة. صلّح الخطأ وانشر من جديد، أو ارجع لآخر نشر كان شغّال.
