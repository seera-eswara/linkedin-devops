FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt && \
    apt-get update && apt-get install -y libnss3 libatk-bridge2.0-0 libgtk-3-0 libdrm2 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libasound2

RUN python -m playwright install

CMD ["python", "main.py"]
