## ابحث عن السطر

عندما يتوقف بوتك عند أحد السطور التالية، تعرض صفحته السبب وما يلزم فعله. ابحث عن السطر في الكونسول، ثم اقرأ قسمه هنا. نسخنا كل سطر كما تطبعه المكتبة، ويكفي أوله للمطابقة.

@[open](console)

## التوكن غير صحيح

- في discord.py: `discord.errors.LoginFailure: Improper token has been passed.`
- في python-telegram-bot: `telegram.error.InvalidToken`
- في aiogram: `aiogram.exceptions.TelegramUnauthorizedError: Telegram server says - Unauthorized`

انسخ التوكن من جديد من Developer Portal أو BotFather، وحدّثه في المتغيرات، ثم انشر من جديد.

## الـ Intents المطلوبة غير مفعّلة

- في discord.py: `discord.errors.PrivilegedIntentsRequired: Shard ID None is requesting privileged intents that have not been explicitly enabled in the developer portal.`

فعّل الـ Intents التي يطلبها كودك من صفحة Bot في Developer Portal، ثم شغّل بوتك من جديد. ويوضح شرح «توكن بوت ديسكورد والـ Intents والصلاحيات» المفتاح الذي يحتاجه كل Intent.

## التوكن مستخدم في بوت آخر

- في python-telegram-bot: `telegram.error.Conflict: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running`

لا يتوقف python-telegram-bot عند هذا السطر، بل يطبعه ويستمر بجانب النسخة الأخرى. التوكن الواحد يشغّل بوتًا واحدًا فقط في الوقت نفسه، فوقّف النسخة الأخرى، مثل نسخة على جهازك، أو أرسل `/revoke` إلى BotFather لتأخذ توكنًا جديدًا، وحدّثه في المتغيرات، ثم انشر من جديد.

## مكتبة ناقصة

- `ModuleNotFoundError: No module named 'discord'`

أضف المكتبة إلى `requirements.txt`، ثم انشر من جديد. وقد يختلف اسم المكتبة عن الاسم الذي تستورده: `discord` من المكتبة `discord.py`، و `telegram` من `python-telegram-bot`.

## مكتبة تيليقرام المثبّتة غير صحيحة

- `ImportError: cannot import name 'Update' from 'telegram'`

استبدل `telegram` بـ `python-telegram-bot` في `requirements.txt`، ثم انشر من جديد.

## تعذّر بناء إحدى المكتبات

- `error: command 'gcc' failed: No such file or directory`

هذا خلل من جهتنا، [تواصل معنا](/dashboard/support) لنضيف الأدوات التي تحتاجها المكتبة.

## ffmpeg غير متوفر

- في discord.py: `discord.errors.ClientException: ffmpeg was not found.`

هذا خلل من جهتنا، [تواصل معنا](/dashboard/support) لنضيف ffmpeg إلى بيئة التشغيل.

## إصدار بايثون لا يحتوي audioop

- `ModuleNotFoundError: No module named 'audioop'`

لم يعد `audioop` موجودًا في بايثون 3.13 وما بعده. حدّد بايثون 3.12 في ملف `.python-version`، أو أضف `audioop-lts` إلى `requirements.txt`، ثم انشر من جديد.

## تجاوز بوتك حد الطلبات

- في discord.py: `discord.errors.HTTPException: 429 Too Many Requests (error code: 0)`
- أو السطر `error code: 1015`

عطه بضع دقائق قبل أن تشغّله من جديد، وراجع الكود الذي يرسل الطلبات في حلقة متكررة.

## الرام غير كافية أثناء التشغيل

لا تطبع المكتبة سطرًا لهذا السبب: يتوقف بوتك فورًا عندما يتجاوز رام باقتك، برمز الخروج `137`، وتعرض صفحته «الرام غير كافية». ارفع الباقة للحصول على رام أكثر، أو خفّف ما يحتفظ به بوتك في الذاكرة.

## الرام غير كافية أثناء التثبيت

- `serverk: install failed: it ran out of memory and was stopped`
- ثم `serverk: deployment dep_a1b2c3d4 failed: install: out-of-memory`

ارفع الباقة للحصول على رام أكثر، ثم انشر من جديد.

> [!note] سطر غير موجود هنا؟ ما زال آخر سطر في الخطأ يوضح ما الذي حدث، ويشرح «اقرأ الكونسول وافهم ما حدث» طريقة قراءته.
