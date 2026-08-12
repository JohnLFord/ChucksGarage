import unittest

from sqlalchemy import select
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import User


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test-only-jwt-signing-key-at-least-32-bytes"
    RATELIMIT_ENABLED = False


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.client = self.app.test_client()
        admin = User(
            email="admin@example.com",
            password_hash=generate_password_hash("admin-password"),
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()
        login_response = self.client.post(
            "/users/login",
            json={"email": "admin@example.com", "password": "admin-password"},
        )
        self.admin_headers = {
            "Authorization": f"Bearer {login_response.get_json()['auth_token']}"
        }

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.context.pop()

    def create_customer(self):
        return self.client.post(
            "/customers",
            headers=self.admin_headers,
            json={
                "name": "Test Customer",
                "email": "customer@example.com",
                "date_of_birth": "1990-01-01",
            },
        )

    def create_mechanic(self):
        return self.client.post(
            "/mechanics",
            headers=self.admin_headers,
            json={
                "name": "Test Mechanic",
                "specialty": "Transmission",
                "experience": "3 years",
                "certification": "Degree",
            },
        )

    def create_service_ticket(self, customer_id=1):
        return self.client.post(
            "/service-tickets",
            headers=self.admin_headers,
            json={"repair_date": "2026-08-01", "customer_id": customer_id},
        )

    def test_customer_can_be_created_without_password(self):
        response = self.create_customer()

        self.assertEqual(response.status_code, 201)
        self.assertNotIn("password", response.get_json())

    def test_client_cannot_choose_primary_key(self):
        response = self.client.post(
            "/mechanics",
            headers=self.admin_headers,
            json={
                "id": 99,
                "name": "Test Mechanic",
                "specialty": "Transmission",
                "experience": "3 years",
                "certification": "Degree",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("id", response.get_json())

    def test_customer_with_ticket_cannot_be_deleted(self):
        self.create_customer()
        self.create_service_ticket()

        response = self.client.delete("/customers/1", headers=self.admin_headers)

        self.assertEqual(response.status_code, 409)

    def test_assignment_is_visible_and_cannot_be_duplicated(self):
        self.create_customer()
        self.create_mechanic()
        self.create_service_ticket()

        assignment_url = "/service-tickets/1/mechanics/1"
        first_response = self.client.post(assignment_url, headers=self.admin_headers)
        duplicate_response = self.client.post(assignment_url, headers=self.admin_headers)
        ticket_response = self.client.get(
            "/service-tickets/1", headers=self.admin_headers
        )

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(duplicate_response.status_code, 409)
        self.assertEqual(ticket_response.get_json()["mechanics"][0]["id"], 1)

    def test_malformed_json_returns_json_error(self):
        response = self.client.post(
            "/mechanics",
            data="{bad json",
            content_type="application/json",
            headers=self.admin_headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.is_json)
        self.assertEqual(response.get_json()["error"], "Invalid request")

    def test_user_can_register_login_and_access_profile(self):
        credentials = {
            "email": "Driver@example.com",
            "password": "strong-password",
            "name": "Test Driver",
            "date_of_birth": "1990-01-01",
        }

        register_response = self.client.post("/users/register", json=credentials)
        user = db.session.execute(
            select(User).where(User.email == "driver@example.com")
        ).scalar_one()
        login_response = self.client.post("/users/login", json=credentials)
        token = login_response.get_json()["auth_token"]
        profile_response = self.client.get(
            "/users/me", headers={"Authorization": f"Bearer {token}"}
        )

        self.assertEqual(register_response.status_code, 201)
        self.assertEqual(register_response.get_json()["email"], "driver@example.com")
        self.assertNotIn("password_hash", register_response.get_json())
        self.assertNotEqual(user.password_hash, credentials["password"])
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.get_json()["id"], user.id)

    def test_auth_rejects_duplicate_user_and_missing_token(self):
        credentials = {
            "email": "duplicate@example.com",
            "password": "strong-password",
            "name": "Duplicate Driver",
            "date_of_birth": "1990-01-01",
        }
        self.client.post("/users/register", json=credentials)

        duplicate_response = self.client.post("/users/register", json=credentials)
        profile_response = self.client.get("/users/me")

        self.assertEqual(duplicate_response.status_code, 409)
        self.assertEqual(profile_response.status_code, 401)


if __name__ == "__main__":
    unittest.main()