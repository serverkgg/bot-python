## أنشئ التطبيق

1. افتح [Discord Developer Portal](https://discord.com/developers/applications) وسجّل الدخول.
2. اضغط **New Application**، وسمّه، ووافق على الشروط.

## انسخ التوكن

1. اختر **Bot** من القائمة.
2. اضغط **Reset Token** وأكّد، ثم **Copy**.
3. أضفه إلى متغيرات بوتك بالاسم الذي يقرأه كودك، وغالبًا `DISCORD_TOKEN`، وفعّل عليه **حساس**.

> [!warning] يعرض ديسكورد التوكن مرة واحدة فقط. إذا فقدته، فاضغط Reset Token مرة ثانية وضع التوكن الجديد، ويتوقف القديم فورًا.

إذا غيّرت التوكن لاحقًا، فحدّثه في المتغيرات واضغط **انشر من جديد**. وإذا شغّلت نسخة ثانية بالتوكن نفسه، مثل نسخة على جهازك، تتصل هي أيضًا وترد النسختان معًا، فيتكرر كل رد مرتين. لذلك وقّف أي نسخة أخرى من بوتك.

@[open](overview)

## فعّل الـ Intents التي يطلبها كودك

في صفحة **Bot** نفسها، تحت **Privileged Gateway Intents**، ثلاثة مفاتيح. فعّل منها فقط ما يطلبه كودك في `discord.Intents`، ثم اضغط **Save Changes**:

- `intents.presences = True` يحتاج **Presence Intent**.
- `intents.members = True` يحتاج **Server Members Intent**.
- `intents.message_content = True` يحتاج **Message Content Intent**. وبدونه تصل رسائل قنوات السيرفر إلى بوتك دون نصها، أما الرسائل الخاصة والرسائل التي تذكر البوت فيصل نصها حتى دونه.

أما `discord.Intents.all()` فيطلب الثلاثة معًا، و `discord.Intents.default()` لا يطلب أيًّا منها. إذا طلب كودك Intent غير مفعّل، يتوقف بوتك عند تسجيل الدخول، ويطبع discord.py هذا السطر:

```txt
discord.errors.PrivilegedIntentsRequired: Shard ID None is requesting privileged intents that have not been explicitly enabled in the developer portal.
```

فعّل الـ Intent الناقص، ثم شغّل بوتك من جديد، ولا تحتاج إلى تغيير التوكن.

@[open](console)

## أضف البوت إلى سيرفرك

نعرف رقم تطبيقك من التوكن، فيظهر في بطاقة البوت زر **أضفه إلى سيرفر ديسكورد**. اضغطه واختر السيرفر.

@[open](panel:bot)

يضيف هذا الزر البوت بالنطاقين `bot` و `applications.commands`، أي البوت وأوامر الـ slash، دون أي صلاحية خاصة به. لتعطيه الصلاحيات التي يحتاجها، اختر إحدى الطريقتين:

- من **Server Settings** في سيرفر ديسكورد، افتح **Roles**، وأنشئ رتبة بالصلاحيات التي يحتاجها البوت وأعطها له، أو امنحه الصلاحيات في كل قناة على حدة.
- أو أنشئ الرابط بنفسك من Developer Portal: افتح **OAuth2** ثم **URL Generator**، واختر `bot` و `applications.commands`، ثم الصلاحيات من **Bot Permissions**، وافتح الرابط الناتج.

إذا نقصت البوت صلاحية، يرد ديسكورد على طلبه بخطأ رمزه `50013`، وإذا لم يصل إلى القناة نفسها فرمزه `50001`.

## توكن حسابك الشخصي؟ لا

تشغيل حسابك الشخصي كبوت (self-bot) مخالف لقواعد ديسكورد، وقد يؤدي إلى حظر حسابك. استخدم دائمًا توكن البوت من Developer Portal.
