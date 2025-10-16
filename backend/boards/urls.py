from django.urls import path
from .views import UploadView, ClusterView, JobStatusView

urlpatterns = [
    path("upload/", UploadView.as_view()),
    path("cluster/", ClusterView.as_view()),
    path("jobs/<str:job_id>/", JobStatusView.as_view()),
]
