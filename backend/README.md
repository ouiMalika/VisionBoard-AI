---
title: VisionBoard AI API
emoji: 🖼️
colorFrom: blue
colorTo: cyan
sdk: docker
app_port: 7860
pinned: false
---
# VisionBoard AI — Django REST API
Handles authentication, image uploads, and clustering job management.

## Environment Variables (set as Space Secrets)

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | Set to `False` in production |
| `ALLOWED_HOSTS` | Your HF Space hostname, e.g. `username-visionboard-api.hf.space` |
| `DATABASE_URL` | Neon PostgreSQL connection string |
| `CELERY_BROKER_URL` | Upstash Redis URL (`rediss://...`) |
| `CELERY_RESULT_BACKEND` | Same as broker URL |
| `CORS_ALLOWED_ORIGINS` | Vercel frontend URL |
| `AWS_ACCESS_KEY_ID` | AWS S3 access key |
| `AWS_SECRET_ACCESS_KEY` | AWS S3 secret key |
| `AWS_STORAGE_BUCKET_NAME` | S3 bucket name |
| `AWS_S3_REGION_NAME` | S3 region (e.g. `us-east-1`) |
