from django.conf import settings
from django.db import models
from django.utils import timezone


class ClusterJob(models.Model):
    """Tracks an async image-clustering task."""

    job_id = models.CharField(max_length=128, unique=True)
    status = models.CharField(max_length=32, default="PENDING")
    result = models.JSONField(null=True, blank=True)
    board_name = models.CharField(max_length=256, default="Untitled Board")
    boards_created = models.BooleanField(default=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="cluster_jobs",
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.job_id} ({self.status})"


class Tag(models.Model):
    """A keyword or aesthetic label (e.g. 'minimalist', 'warm tones')."""

    name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name


class Board(models.Model):
    """A moodboard — a named collection of images with aesthetic tags."""

    name = models.CharField(max_length=256)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="boards",
    )
    cluster_job = models.ForeignKey(
        ClusterJob,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="boards",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="boards")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Image(models.Model):
    """An image belonging to a moodboard."""

    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name="images",
    )
    url = models.URLField(max_length=1024)
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Image {self.id} on {self.board.name}"
