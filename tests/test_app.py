import unittest

from app import create_app


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "DEMO_USERNAME": "admin",
                "DEMO_PASSWORD": "welcome123",
            }
        ).test_client()

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "ok"})

    def test_welcome_requires_login(self):
        response = self.client.get("/welcome")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/"))

    def test_login_flow(self):
        response = self.client.post(
            "/login",
            data={"username": "admin", "password": "welcome123"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome, admin", response.data)

    def test_invalid_login(self):
        response = self.client.post(
            "/login", data={"username": "admin", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
