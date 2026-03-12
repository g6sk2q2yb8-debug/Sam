# استخدم صورة بايثون أساسية
FROM python:3.9-slim-buster

# تعيين دليل العمل داخل الحاوية
WORKDIR /app

# تثبيت ffmpeg والأدوات الأساسية
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملف requirements.txt وتثبيت المكتبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ ملف البوت الخاص بك
COPY telegram_bot_modified.py .

# تعريف متغير البيئة لتوكن البوت (مهم جداً للأمان)
# لا تضع التوكن هنا مباشرة، بل استخدم متغيرات البيئة في Render
ENV TOKEN="your_bot_token_here"

# الأمر الذي سيتم تشغيله عند بدء تشغيل الحاوية
CMD ["python", "telegram_bot_modified.py"]
