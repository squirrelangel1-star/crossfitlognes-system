FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    python -m playwright install chromium

COPY . .

CMD ["python", "main.py"]
