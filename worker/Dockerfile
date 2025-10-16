FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y python3 python3-pip git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["celery", "-A", "tasks", "worker", "--loglevel=info"]