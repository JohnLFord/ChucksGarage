import unittest

from app import create_app
from app.extensions import db


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def create_customer(self):
        return self.client.post(
            "/customers",
            json={
                "name": "Test Customer",
                "email": "customer@example.com",
                "DOB": "1990-01-01",
            },
        )

    def create_mechanic(self):
        return self.client.post(
            "/mechanics",
            json={
                "name": "Test Mechanic",
                "specialty": "Transmission",
                "experience": "3 years",
                "certification": "Degree",
            },
        )

    def create_service_ticket(self):
        return self.client.post(
            "/service_tickets",
            json={"repair_date": "2026-08-01", "customer_id": 1},
        )

    def test_customer_can_be_created_without_password(self):
        response = self.create_customer()

        self.assertEqual(response.status_code, 201)
        self.assertNotIn("password", response.get_json())

    def test_client_cannot_choose_primary_key(self):
        response = self.client.post(
            "/mechanics",
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

        response = self.client.delete("/customers/1")

        self.assertEqual(response.status_code, 409)

    def test_assignment_is_visible_and_cannot_be_duplicated(self):
        self.create_customer()
        self.create_mechanic()
        self.create_service_ticket()

        first_response = self.client.post("/service_tickets/1/mechanics/1")
        duplicate_response = self.client.post("/service_tickets/1/mechanics/1")
        ticket_response = self.client.get("/service_tickets/1")

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(duplicate_response.status_code, 409)
        self.assertEqual(ticket_response.get_json()["mechanics"][0]["id"], 1)

    def test_malformed_json_returns_json_error(self):
        response = self.client.post(
            "/mechanics", data="{bad json", content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.is_json)
        self.assertEqual(response.get_json()["error"], "Invalid request")


if __name__ == "__main__":
    unittest.main()