import unittest

from app import create_app
from app.extensions import db
from app.models import User


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
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def test_app_starts_and_login_rejects_missing_credentials(self):
        response = self.client.post("/users/login", json={})

        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.is_json)
        self.assertEqual(response.get_json()["error"], "Email and password are required")

    def test_registration_creates_student_role_only(self):
        response = self.client.post(
            "/users/register",
            json={
                "name": "New Student",
                "email": "new.student@example.com",
                "password": "student-password",
                "date_of_birth": "2000-01-01",
                "role": "admin",
            },
        )

        self.assertEqual(response.status_code, 201)
        user = db.session.scalars(db.select(User)).one()
        self.assertEqual(user.role, "student")
        self.assertIsNotNone(user.student_id)


if __name__ == "__main__":
    unittest.main()
