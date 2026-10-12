## ماذا يفعل الزر؟

يفتح الزر صفحة «شغّل بوتك» على ريبو بوتك: نقرأ الكود ونحدد بيئة التشغيل والأوامر، ثم يختار من ضغط الزر الباقة وينشر البوت. يعمل الزر مع أي ريبو عام على GitHub، ويكفي من يضغطه حساب في سيرفرك، دون حساب GitHub.

## أضفه إلى README

الصق هذا السطر في ملف `README.md`، وضع ريبو بوتك مكان `owner/name`:

```md
[![Deploy on Serverk](https://serverk.gg/button.svg)](https://serverk.gg/bots/create?repo=https://github.com/owner/name)
```

وفي ملف README مكتوب بالعربية، استخدم الزر العربي `https://serverk.gg/button.ar.svg` مكان `button.svg`.

## اختر الفرع

ينشر الزر الفرع الافتراضي للريبو. ولنشر فرع آخر مثل `dev`، أضف `&ref=dev` إلى الرابط، أو ضع رابط صفحة الفرع نفسها `https://github.com/owner/name/tree/dev`. وتقبل قيمة `repo` الصيغة `owner/name` أو `github.com/owner/name` أو الرابط كاملًا.

## النشر مع كل push

البوت المنشور من ريبو عام يبدأ والنشر مع كل push موقوف، لأننا نقرأ الريبو دون تطبيق Serverk على GitHub. أما النشر من جديد والاسترجاع ورابط النشر فتعمل كالمعتاد. ولتفعيل النشر مع كل push، اربط GitHub من قسم Git في إعدادات بوتك واختر الريبو نفسه.

@[open](overview)
