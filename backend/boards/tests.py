from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from .models import ClusterJob, Board, Image, Tag


DATABASES_OVERRIDE = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}


@override_settings(DATABASES=DATABASES_OVERRIDE)
class ModelTests(TestCase):
    def test_create_cluster_job(self):
        job = ClusterJob.objects.create(job_id="test-123", board_name="Test")
        self.assertEqual(job.status, "PENDING")
        self.assertFalse(job.boards_created)
        self.assertEqual(str(job), "test-123 (PENDING)")

    def test_create_board_with_images_and_tags(self):
        job = ClusterJob.objects.create(job_id="j1")
        tag = Tag.objects.create(name="minimalist")
        board = Board.objects.create(name="My Board", cluster_job=job)
        board.tags.add(tag)
        Image.objects.create(board=board, url="https://example.com/img.jpg")

        self.assertEqual(board.images.count(), 1)
        self.assertIn(tag, board.tags.all())
        self.assertEqual(str(board), "My Board")

    def test_tag_uniqueness(self):
        Tag.objects.create(name="cozy")
        with self.assertRaises(Exception):
            Tag.objects.create(name="cozy")

    def test_board_cascade_deletes_images(self):
        board = Board.objects.create(name="Temp")
        Image.objects.create(board=board, url="https://example.com/1.jpg")
        Image.objects.create(board=board, url="https://example.com/2.jpg")
        self.assertEqual(Image.objects.count(), 2)
        board.delete()
        self.assertEqual(Image.objects.count(), 0)


@override_settings(DATABASES=DATABASES_OVERRIDE)
class AuthAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register(self):
        response = self.client.post(
            "/api/auth/register/",
            {"username": "alice", "password": "pass1234"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["username"], "alice")

    def test_register_duplicate(self):
        User.objects.create_user(username="bob", password="pass1234")
        response = self.client.post(
            "/api/auth/register/",
            {"username": "bob", "password": "pass1234"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_login(self):
        User.objects.create_user(username="carol", password="pass1234")
        response = self.client.post(
            "/api/auth/login/",
            {"username": "carol", "password": "pass1234"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)

    def test_login_bad_creds(self):
        response = self.client.post(
            "/api/auth/login/",
            {"username": "nobody", "password": "wrong"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)


@override_settings(DATABASES=DATABASES_OVERRIDE)
class BoardAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.board = Board.objects.create(name="Test Board", owner=self.user)
        tag = Tag.objects.create(name="warm tones")
        self.board.tags.add(tag)
        Image.objects.create(board=self.board, url="https://example.com/a.jpg")

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        response = client.get("/api/boards/")
        self.assertEqual(response.status_code, 401)

    def test_list_boards(self):
        response = self.client.get("/api/boards/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Test Board")
        self.assertEqual(response.data[0]["tags"], ["warm tones"])
        self.assertEqual(len(response.data[0]["images"]), 1)

    def test_boards_scoped_to_user(self):
        other_user = User.objects.create_user(username="other", password="pass")
        Board.objects.create(name="Other Board", owner=other_user)
        response = self.client.get("/api/boards/")
        self.assertEqual(len(response.data), 1)

    def test_get_board_detail(self):
        response = self.client.get(f"/api/boards/{self.board.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Test Board")

    def test_get_board_not_found(self):
        response = self.client.get("/api/boards/9999/")
        self.assertEqual(response.status_code, 404)

    def test_update_board_name(self):
        response = self.client.patch(
            f"/api/boards/{self.board.id}/",
            {"name": "Renamed"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.board.refresh_from_db()
        self.assertEqual(self.board.name, "Renamed")

    def test_update_board_tags(self):
        response = self.client.patch(
            f"/api/boards/{self.board.id}/",
            {"tags": ["bold", "modern"]},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.board.refresh_from_db()
        tag_names = sorted(self.board.tags.values_list("name", flat=True))
        self.assertEqual(tag_names, ["bold", "modern"])

    def test_delete_board(self):
        response = self.client.delete(f"/api/boards/{self.board.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Board.objects.count(), 0)

    def test_upload_no_files_returns_400(self):
        response = self.client.post("/api/upload/", {}, format="multipart")
        self.assertEqual(response.status_code, 400)

    def test_cluster_no_urls_returns_400(self):
        response = self.client.post(
            "/api/cluster/", {"image_urls": []}, format="json"
        )
        self.assertEqual(response.status_code, 400)
