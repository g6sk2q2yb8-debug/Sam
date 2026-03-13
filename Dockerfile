FROM python:3.11-alpine

WORKDIR /app

RUN apk add --no-cache ffmpeg

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY telegram_bot_modified.py .

CMD ["python", "telegram_bot_modified.py"]
