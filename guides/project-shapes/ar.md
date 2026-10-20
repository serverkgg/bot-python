## كيف نثبّت المكتبات

نعطي بوتك بيئة بايثون خاصة به (`.venv`)، ونثبّت فيها من أول ملف نجده بهذا الترتيب:

1. `requirements.txt`: بالأمر `uv pip install -r requirements.txt`.
2. `uv.lock`: بالأمر `uv sync --locked --no-dev`. حدّث ملف القفل بـ `uv lock` عند كل تغيير في `pyproject.toml`، لأن ملف القفل غير المتطابق يوقف التثبيت.
3. `poetry.lock` أو `pdm.lock`: نثبّت المشروع من `pyproject.toml` بالأمر `uv pip install .` دون ملف القفل، ويظهر في الكونسول `poetry.lock is not used, installing from pyproject.toml`.
4. `Pipfile`: بالأمر `pipenv install`.
5. `pyproject.toml` وحده: بالأمر `uv pip install .`.

لتثبيت الإصدارات نفسها التي جربتها مع Poetry أو PDM، أضف `requirements.txt` بإصدارات محددة، فهو يأتي أولًا. وحدّد إصدار كل مكتبة بـ `==`، مثل `discord.py==2.7.1`، وننبّهك في «شغّل بوتك» إذا وجدنا مكتبة دون إصدار.

ولا نعيد التثبيت إلا عند تغيّر أمر التثبيت أو إصدار بايثون أو ملف المكتبات أو الملف المرتبط به، وهو `pyproject.toml` مع ملف القفل، و `Pipfile.lock` مع `Pipfile`. وإلا يظهر في الكونسول `dependencies are up to date (uv)`.

@[open](console)

## إصدار بايثون

نقرأ الإصدار من أول ملف نجده: `.python-version`، ثم `runtime.txt` مثل `python-3.11.9`، ثم `python_version` في `Pipfile`، ثم `.tool-versions`. ودون أي منها يشتغل بوتك على بايثون 3.12.

إذا طلب كودك إصدارًا آخر، نثبّته بـ uv في أول نشر يطلبه، ويظهر في الكونسول `creating .venv with Python 3.11 through uv`. وإذا تغيّر الإصدار، نبني البيئة من جديد: `Python changed to 3.11, rebuilding .venv`.

> [!note] لم يعد `audioop` موجودًا في بايثون 3.13 وما بعده. إذا احتاجه بوتك، فأبقِ 3.12، أو أضف `audioop-lts` إلى `requirements.txt`.

## كيف نشغّل بوتك

أول تطابق هو المعتمد:

1. أمر التشغيل في إعدادات بوتك.
2. الحقل `start` في `serverk.json`.
3. سطر `worker:` أو `bot:` في `Procfile`.
4. `main.py` ثم `bot.py` ثم `app.py` ثم `src/main.py` ثم `src/bot.py`.
5. `python -m` مع المجلد الوحيد في أعلى الكود الذي فيه `__main__.py`، مثل `python -m mybot`. ولا نحسب المجلدات `tests` و `test` و `docs` و `examples` و `scripts`.

نشغّل الملف بالأمر `.venv/bin/python -u main.py`. أما الأمر الذي تكتبه في الإعدادات أو في `serverk.json` أو في `Procfile`، فيشتغل و `.venv/bin` أول المسار، فيكون `python` فيه بايثون بوتك نفسه.

## أمر ما قبل النشر

أمر ما قبل النشر لمهمة مثل تحديث جداول قاعدة البيانات، وننفّذه مرة واحدة مع كل نشر، بعد تثبيت المكتبات وقبل تشغيل بوتك. أول تطابق هو المعتمد:

1. أمر ما قبل النشر في إعدادات بوتك.
2. الحقل `preDeploy` في `serverk.json`.
3. `alembic.ini`: بالأمر `alembic upgrade head`.
4. `manage.py`: بالأمر `python manage.py migrate --noinput`.

ودون أي منها لا ننفّذ شيئًا. ولاستبدال الأمر الذي نجده، اكتب أمرك في الإعدادات أو في `serverk.json`.

يشتغل الأمر في مجلد كود بوتك ومعه متغيرات بوتك، و `.venv/bin` أول المسار، فيكون `alembic` و `python` فيه من بيئة بوتك نفسها. ويظهر في الكونسول `running the pre-deploy command: alembic upgrade head`.

لا ننفّذه عند الريستارت، بل مع كل نشر فقط. وإذا فشل، يتوقف النشر عند الخطوة `pre-deploy` قبل تشغيل بوتك، وننفّذه من جديد في التشغيل التالي حتى يكتمل النشر. لذلك اجعله أمرًا يمكن تكراره دون ضرر، مثل أوامر تحديث الجداول أعلاه.

## ما في بيئة التشغيل

فيها `ffmpeg` و `libopus` و `libsodium` لبوتات الصوت، وأدوات البناء للمكتبات التي تُبنى عند التثبيت. ويصل كل ما يطبعه بوتك إلى الكونسول فورًا، لأن `PYTHONUNBUFFERED=1` مضبوط.
