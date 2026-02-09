from django.urls import path
from .views import (
    UploadView,
    ClusterView,
    JobStatusView,
    BoardListView,
    BoardDetailView,
)
from .auth_views import RegisterView, LoginView

urlpatterns = [
    # Auth
    path("auth/register/", RegisterView.as_view()),
    path("auth/login/", LoginView.as_view()),
    # Core
    path("upload/", UploadView.as_view()),
    path("cluster/", ClusterView.as_view()),
    path("jobs/<str:job_id>/", JobStatusView.as_view()),
    path("boards/", BoardListView.as_view()),
    path("boards/<int:board_id>/", BoardDetailView.as_view()),
]
