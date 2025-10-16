from celery import shared_task
from rest_framework.views import APIView
from rest_framework.response import Response
from celery.result import AsyncResult

from celery import current_app
from rest_framework import status
from .models import ClusterJob
import json

from storages.backends.s3 import S3Storage

class UploadView(APIView):
    def post(self, request):
        files = request.FILES.getlist("files")
        urls = []

        # Create an explicit S3Storage instance
        storage = S3Storage()

        for f in files:
            filename = storage.save(f.name, f)
            url = storage.url(filename)
            urls.append(url)

        return Response({"image_urls": urls}, status=200)

class ClusterView(APIView):
    def post(self, request):
        urls = request.data.get("image_urls", [])
        n = request.data.get("n_clusters", 5)

        # Send task to Celery worker by name
        task = current_app.send_task("tasks.cluster_images", args=[urls, n])
        return Response({"job_id": task.id})
    
class JobStatusView(APIView):
    def get(self, request, job_id):
        result = AsyncResult(job_id, app=current_app)
        job, _ = ClusterJob.objects.get_or_create(job_id=job_id)
        job.status = result.status
        if result.ready():
            try:
                job.result = result.result
            except Exception:
                job.result = str(result.result)
        job.save()
        return Response({
            "job_id": job.job_id,
            "status": job.status,
            "result": job.result
        })

class ClusterView(APIView):
    def post(self, request):
        urls = request.data.get("image_urls", [])
        n = request.data.get("n_clusters", 5)

        task = current_app.send_task("tasks.cluster_images", args=[urls, n])
        ClusterJob.objects.create(job_id=task.id, status="PENDING")
        return Response({"job_id": task.id})