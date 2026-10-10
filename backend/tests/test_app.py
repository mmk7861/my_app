import unittest

from fastapi.testclient import TestClient

from backend.app import create_app


class AppTestCase(unittest.TestCase):
    def setUp(self):
        app = create_app(
            {
                "SECRET_KEY": "test-secret",
                "DATABASE_URL": "sqlite:///:memory:",
                "ADMIN_USERNAME": "admin",
                "ADMIN_PASSWORD": "welcome123",
            }
        )
        self.client_context = TestClient(app)
        self.client = self.client_context.__enter__()

    def tearDown(self):
        self.client_context.__exit__(None, None, None)

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "database": "connected"})

    def test_welcome_requires_login(self):
        response = self.client.get("/welcome", follow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "http://testserver/")

    def test_login_flow(self):
        response = self.client.post(
            "/login",
            data={"username": "admin", "password": "welcome123"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Welcome, admin", response.text)

    def test_invalid_login(self):
        response = self.client.post(
            "/login", data={"username": "admin", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 401)

    def test_registration_flow(self):
        response = self.client.post(
            "/register",
            data={
                "username": "new-user",
                "password": "securepass123",
                "confirm_password": "securepass123",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Welcome, new-user", response.text)

    def test_registration_rejects_duplicate_username(self):
        response = self.client.post(
            "/register",
            data={
                "username": "admin",
                "password": "securepass123",
                "confirm_password": "securepass123",
            },
        )
        self.assertEqual(response.status_code, 409)
        self.assertIn("already registered", response.text)

    def test_registration_validates_password_confirmation(self):
        response = self.client.post(
            "/register",
            data={
                "username": "new-user",
                "password": "securepass123",
                "confirm_password": "differentpass123",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("passwords do not match", response.text)


if __name__ == "__main__":
    unittest.main()
