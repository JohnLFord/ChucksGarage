import unittest

from app import create_app


class SmokeTestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "smoke-test-jwt-signing-key-at-least-32-bytes"
    RATELIMIT_ENABLED = False


class SmokeTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(SmokeTestConfig)
        self.context = self.app.app_context()
        self.context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        self.context.pop()

    def test_app_starts_and_login_rejects_missing_credentials(self):
        response = self.client.post("/users/login", json={})

        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.is_json)
        self.assertEqual(response.get_json()["error"], "Email and password are required")


if __name__ == "__main__":
    unittest.main()
