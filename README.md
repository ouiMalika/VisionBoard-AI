# VisionBoard-AI

An AI-powered image clustering application that groups images by visual similarity using OpenAI's CLIP model.

## Architecture

| Service | Description |
|---------|-------------|
| **Backend** | Django REST API — handles uploads, creates jobs, serves results |
| **Worker** | Celery worker — runs CLIP embeddings + KMeans clustering |
| **PostgreSQL** | Stores job metadata |
| **Redis** | Message broker between Django and Celery |
| **AWS S3** | Image file storage |

## Prerequisites

- Python 3.11+
- PostgreSQL
- Redis
- AWS account with an S3 bucket (for image uploads)

### Installing prerequisites (macOS)

```bash
brew install postgresql@16 redis
brew services start postgresql@16
brew services start redis
```

Verify they're running:

```bash
pg_isready          # should print "accepting connections"
redis-cli ping      # should print "PONG"
```

### Database setup

Create the database and user PostgreSQL expects:

```bash
psql -d postgres
```

```sql
CREATE USER visionboard WITH PASSWORD 'visionboard';
CREATE DATABASE visionboard OWNER visionboard;
\q
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `visionboard` | Database name |
| `POSTGRES_USER` | `visionboard` | Database user |
| `POSTGRES_PASSWORD` | `visionboard` | Database password |
| `POSTGRES_HOST` | `postgres` | Database host — set to `localhost` for local dev |
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | Redis broker URL — set to `redis://localhost:6379/0` for local dev |
| `AWS_ACCESS_KEY_ID` | — | Your AWS access key |
| `AWS_SECRET_ACCESS_KEY` | — | Your AWS secret key |
| `AWS_STORAGE_BUCKET_NAME` | `visionboard-ai` | S3 bucket name |
| `AWS_S3_REGION_NAME` | `us-east-2` | S3 region |

> **Note:** The defaults for `POSTGRES_HOST` and `CELERY_BROKER_URL` use Docker service names. When running locally, you must override them to use `localhost`.

## Running Locally

You need **two terminals** — one for the backend, one for the worker.

### Terminal 1: Backend

```bash
cd backend
pip install -r requirements.txt
export POSTGRES_HOST=localhost
python manage.py migrate
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`.

### Terminal 2: Celery Worker

```bash
cd worker
pip install -r requirements.txt
export CELERY_BROKER_URL=redis://localhost:6379/0
celery -A tasks worker --loglevel=info
```

The worker will download the CLIP model on first run (~605 MB).

## Running with Docker

### Backend

```bash
cd backend
docker build -t visionboard-backend .
docker run -p 8000:8000 \
  -e POSTGRES_HOST=<db-host> \
  -e AWS_ACCESS_KEY_ID=<key> \
  -e AWS_SECRET_ACCESS_KEY=<secret> \
  visionboard-backend
```

### Worker

```bash
cd worker
docker build -t visionboard-worker .
docker run --gpus all \
  -e CELERY_BROKER_URL=redis://<redis-host>:6379/0 \
  visionboard-worker
```

The worker Dockerfile uses `nvidia/cuda:12.1.1` for GPU acceleration. Pass `--gpus all` if you have an NVIDIA GPU.

## API Endpoints

### Upload images

```
POST /api/upload/
Content-Type: multipart/form-data

file: <image file>
```

### Start a clustering job

```
POST /api/cluster/
Content-Type: application/json

{
  "image_urls": ["https://s3.amazonaws.com/.../img1.jpg", "..."],
  "n_clusters": 5
}
```

Returns: `{"job_id": "<task-id>"}`

### Check job status

```
GET /api/jobs/<job_id>/
```

Returns: `{"job_id": "...", "status": "...", "result": {"0": [...], "1": [...], ...}}`

## How It Works

1. User uploads images to S3 via `/api/upload/`
2. User sends image URLs to `/api/cluster/` — Django creates an async Celery task and returns a job ID
3. The Celery worker picks up the task, downloads each image, and extracts visual embeddings using the CLIP model
4. Embeddings are clustered with KMeans into the requested number of groups
5. User polls `/api/jobs/<job_id>/` until the result is ready

## Project Structure

```
VisionBoard-AI/
├── backend/
│   ├── boards/                    # Django app (models, views, urls)
│   ├── visionboard_backend/       # Django project config (settings, celery, wsgi)
│   ├── manage.py
│   ├── requirements.txt
│   └── Dockerfile
├── worker/
│   ├── tasks.py                   # Celery task: cluster_images
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                      # (not yet implemented)
└── infra/
```
