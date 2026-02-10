import logging

from django.core.files.storage import default_storage

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny


from celery import current_app
from celery.result import AsyncResult

from .models import ClusterJob, Board, Image, Tag

logger = logging.getLogger(__name__)


class UploadView(APIView):
    """Upload images to storage (S3 via django-storages) and return URLs."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        files = request.FILES.getlist("files")

        if not files:
            return Response(
                {"error": "No files provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        urls = []
        for f in files:
            filename = default_storage.save(f"uploads/{f.name}", f)
            url = default_storage.url(filename)
            urls.append(url)

        return Response(
            {"image_urls": urls},
            status=status.HTTP_200_OK,
        )


class ClusterView(APIView):
    """Trigger async image clustering to generate moodboards."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        urls = request.data.get("image_urls")
        n = request.data.get("n_clusters", 5)
        board_name = request.data.get("board_name", "Untitled Board")

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

        task = current_app.send_task(
            "tasks.cluster_images",
            args=[urls, n],
        )

        ClusterJob.objects.create(
            job_id=task.id,
            status="PENDING",
            board_name=board_name,
            owner=request.user,
        )

        return Response(
            {"job_id": task.id, "board_name": board_name},
            status=status.HTTP_202_ACCEPTED,
        )


class JobStatusView(APIView):
    """Poll a clustering job and persist moodboards when complete."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        try:
            job = ClusterJob.objects.get(job_id=job_id, owner=request.user)
        except ClusterJob.DoesNotExist:
            return Response(
                {"error": "Job not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        result = AsyncResult(job_id, app=current_app)
        job.status = result.status

        if result.ready():
            try:
                job.result = result.result
            except Exception:
                logger.exception("Failed to read result for job %s", job_id)
                job.result = str(result.result)

            if result.successful() and not job.boards_created:
                self._create_boards(job, request.user)

        job.save()

        return Response({
            "job_id": job.job_id,
            "status": job.status,
            "result": job.result,
        })


    def _create_boards(self, job, user):
        """Turn cluster results into Board + Image + Tag objects."""
        clusters = job.result

        if not isinstance(clusters, dict) or "error" in clusters:
            return

        for cluster_id, data in clusters.items():
            image_urls = data.get("images", [])
            tags = data.get("tags", [])

            board = Board.objects.create(
                name=f"{job.board_name} — Group {int(cluster_id) + 1}",
                cluster_job=job,
                owner=user,
            )

            for url in image_urls:
                Image.objects.create(board=board, url=url)

            for tag_name in tags:
                tag, _ = Tag.objects.get_or_create(name=tag_name.lower())
                board.tags.add(tag)

        job.boards_created = True


class BoardListView(APIView):
    """List the current user's moodboards."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        boards = (
            Board.objects.filter(owner=request.user)
            .prefetch_related("images", "tags")
            .order_by("-created_at")
        )

        data = []
        for board in boards:
            data.append({
                "id": board.id,
                "name": board.name,
                "created_at": board.created_at.isoformat(),
                "images": [
                    {"id": img.id, "url": img.url}
                    for img in board.images.all()
                ],
                "tags": [tag.name for tag in board.tags.all()],
            })

        return Response(data)


class BoardDetailView(APIView):
    """Get, update, or delete a single moodboard owned by the user."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _get_board(self, user, board_id):
        try:
            return Board.objects.prefetch_related("images", "tags").get(
                id=board_id,
                owner=user,
            )
        except Board.DoesNotExist:
            return None

    def get(self, request, board_id):
        board = self._get_board(request.user, board_id)
        if not board:
            return Response(
                {"error": "Board not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({
            "id": board.id,
            "name": board.name,
            "created_at": board.created_at.isoformat(),
            "images": [
                {"id": img.id, "url": img.url}
                for img in board.images.all()
            ],
            "tags": [tag.name for tag in board.tags.all()],
        })

    def patch(self, request, board_id):
        board = self._get_board(request.user, board_id)
        if not board:
            return Response(
                {"error": "Board not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if "name" in request.data:
            board.name = request.data["name"]

        if "tags" in request.data:
            board.tags.clear()
            for tag_name in request.data["tags"]:
                tag, _ = Tag.objects.get_or_create(name=tag_name.lower())
                board.tags.add(tag)

        board.save()
        return Response({"id": board.id, "name": board.name})

    def delete(self, request, board_id):
        board = self._get_board(request.user, board_id)
        if not board:
            return Response(
                {"error": "Board not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        board.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class AnonymousTokenView(APIView):
    """
    Issue a token for an anonymous demo user.
    Safe for public demo deployments.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        user, _ = User.objects.get_or_create(
            username="demo_user",
            defaults={"is_active": True},
        )

        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {"token": token.key},
            status=status.HTTP_200_OK,
        )