from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework.test import APIClient


class UploadViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_upload_no_files_returns_400(self):
        response = self.client.post("/api/upload/")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "No files provided.")

    def test_upload_files_returns_urls(self):
        mock_storage = MagicMock()
        mock_storage.save.return_value = "test.jpg"
        mock_storage.url.return_value = "https://s3.amazonaws.com/bucket/test.jpg"
        mock_cls = MagicMock(return_value=mock_storage)

        from django.core.files.uploadedfile import SimpleUploadedFile
        f = SimpleUploadedFile("test.jpg", b"fakecontent", content_type="image/jpeg")

        with patch.dict("sys.modules", {"storages.backends.s3": MagicMock(S3Storage=mock_cls)}):
            response = self.client.post("/api/upload/", {"files": f}, format="multipart")
        self.assertEqual(response.status_code, 200)
        self.assertIn("image_urls", response.json())
        self.assertEqual(len(response.json()["image_urls"]), 1)


class ClusterViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_cluster_empty_urls_returns_400(self):
        response = self.client.post(
            "/api/cluster/", {"image_urls": [], "n_clusters": 3},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_cluster_missing_urls_returns_400(self):
        response = self.client.post("/api/cluster/", {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_cluster_invalid_n_clusters_returns_400(self):
        response = self.client.post(
            "/api/cluster/",
            {"image_urls": ["http://example.com/img.jpg"], "n_clusters": -1},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_cluster_n_clusters_zero_returns_400(self):
        response = self.client.post(
            "/api/cluster/",
            {"image_urls": ["http://example.com/img.jpg"], "n_clusters": 0},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    @patch("boards.views.current_app")
    def test_cluster_valid_request_returns_202(self, mock_celery):
        mock_task = MagicMock()
        mock_task.id = "fake-task-id"
        mock_celery.send_task.return_value = mock_task

        response = self.client.post(
            "/api/cluster/",
            {"image_urls": ["http://example.com/img.jpg"], "n_clusters": 3},
            format="json",
        )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["job_id"], "fake-task-id")
        mock_celery.send_task.assert_called_once_with(
            "tasks.cluster_images",
            args=[["http://example.com/img.jpg"], 3],
        )


class JobStatusViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("boards.views.AsyncResult")
    def test_job_status_pending(self, mock_async_result):
        mock_result = mock_async_result.return_value
        mock_result.status = "PENDING"
        mock_result.ready.return_value = False

        response = self.client.get("/api/jobs/fake-job-id/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["job_id"], "fake-job-id")
        self.assertEqual(data["status"], "PENDING")
        self.assertIsNone(data["result"])

    @patch("boards.views.AsyncResult")
    def test_job_status_success(self, mock_async_result):
        mock_result = mock_async_result.return_value
        mock_result.status = "SUCCESS"
        mock_result.ready.return_value = True
        mock_result.result = {"0": ["img1.jpg"], "1": ["img2.jpg"]}

        response = self.client.get("/api/jobs/another-job-id/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["result"], {"0": ["img1.jpg"], "1": ["img2.jpg"]})
