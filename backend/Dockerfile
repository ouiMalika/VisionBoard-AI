# ---------- backend/Dockerfile ----------
FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code
COPY . .

# Run migrations automatically when container starts
CMD ["sh", "-c", "python manage.py migrate && gunicorn visionboard_backend.wsgi:application --bind 0.0.0.0:8000"]
