# Frontend Dockerfile — Django Web UI
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8080

CMD ["gunicorn", "dj_frontend.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "2"]
