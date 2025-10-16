from django.db import models
from django.utils import timezone

class ClusterJob(models.Model):
    job_id = models.CharField(max_length=128, unique=True)
    status = models.CharField(max_length=32, default="PENDING")
    result = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.job_id} ({self.status})"
