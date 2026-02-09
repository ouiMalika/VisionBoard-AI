import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from celery import current_app
from celery.result import AsyncResult
from .models import ClusterJob

logger = logging.getLogger(__name__)


class UploadView(APIView):
    def post(self, request):
        files = request.FILES.getlist("files")
        if not files:
            return Response(
                {"error": "No files provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.core.files.storage import default_storage
        urls = []
        for f in files:
            filename = default_storage.save(f"uploads/{f.name}", f)
            url = request.build_absolute_uri(f"/media/{filename}")
            urls.append(url)

        return Response({"image_urls": urls}, status=status.HTTP_200_OK)


class ClusterView(APIView):
    def post(self, request):
        urls = request.data.get("image_urls", [])
        n = request.data.get("n_clusters", 5)

        if not isinstance(urls, list) or len(urls) == 0:
            return Response(
                {"error": "image_urls must be a non-empty list."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not isinstance(n, int) or n < 1:
            return Response(
                {"error": "n_clusters must be a positive integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task = current_app.send_task("tasks.cluster_images", args=[urls, n])
        ClusterJob.objects.create(job_id=task.id, status="PENDING")
        return Response({"job_id": task.id}, status=status.HTTP_202_ACCEPTED)


class JobStatusView(APIView):
    def get(self, request, job_id):
        result = AsyncResult(job_id, app=current_app)
        job, _ = ClusterJob.objects.get_or_create(job_id=job_id)
        job.status = result.status
        if result.ready():
            try:
                job.result = result.result
            except Exception:
                logger.exception("Failed to read result for job %s", job_id)
                job.result = str(result.result)
        job.save()
        return Response({
            "job_id": job.job_id,
            "status": job.status,
            "result": job.result,
        })
