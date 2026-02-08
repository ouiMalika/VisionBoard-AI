from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from celery import current_app
from celery.result import AsyncResult

from .models import ClusterJob, Board, Image, Tag


class UploadView(APIView):
    """Upload images to S3 and return their URLs."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        files = request.FILES.getlist("files")
        if not files:
            return Response(
                {"error": "No files provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from storages.backends.s3 import S3Storage
        storage = S3Storage()
        urls = []
        for f in files:
            filename = storage.save(f.name, f)
            url = storage.url(filename)
            urls.append(url)

        return Response({"image_urls": urls}, status=status.HTTP_200_OK)


class ClusterView(APIView):
    """Trigger async image clustering to generate moodboards."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        urls = request.data.get("image_urls", [])
        n = request.data.get("n_clusters", 5)
        board_name = request.data.get("board_name", "Untitled Board")

        if not urls:
            return Response(
                {"error": "No image URLs provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task = current_app.send_task(
            "tasks.cluster_images", args=[urls, n]
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
                id=board_id, owner=user
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
