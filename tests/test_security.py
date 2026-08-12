import unittest
from datetime import date

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import Customer, Mechanic, Service_Ticket, User


class SecurityTestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "security-test-jwt-signing-key-at-least-32-bytes"
    RATELIMIT_ENABLED = False


class SecurityTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(SecurityTestConfig)
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
        self.admin_headers = self.login("admin@example.com", "admin-password")

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.context.pop()

    def login(self, email, password):
        response = self.client.post(
            "/users/login", json={"email": email, "password": password}
        )
        return {"Authorization": f"Bearer {response.get_json()['auth_token']}"}

    def register_customer(self, email, name):
        password = "strong-password"
        response = self.client.post(
            "/users/register",
            json={
                "email": email,
                "password": password,
                "name": name,
                "date_of_birth": "1990-01-01",
                "role": "admin",
            },
        )
        self.assertEqual(response.status_code, 201)
        return response.get_json(), self.login(email, password)

    def create_mechanic_user(self):
        mechanic = Mechanic(
            name="Assigned Mechanic",
            specialty="Transmission",
            experience="3 years",
            certification="ASE",
        )
        user = User(
            email="mechanic@example.com",
            password_hash=generate_password_hash("mechanic-password"),
            role="mechanic",
            mechanic=mechanic,
        )
        db.session.add(user)
        db.session.commit()
        return mechanic, self.login("mechanic@example.com", "mechanic-password")

    def test_anonymous_requests_cannot_access_business_data(self):
        for method, path in (
            (self.client.get, "/customers"),
            (self.client.get, "/mechanics"),
            (self.client.get, "/service-tickets"),
        ):
            with self.subTest(path=path):
                self.assertEqual(method(path).status_code, 401)

    def test_registration_links_customer_and_ignores_requested_role(self):
        profile, headers = self.register_customer("owner@example.com", "Owner")
        user = db.session.get(User, profile["id"])

        self.assertEqual(user.role, "customer")
        self.assertIsNotNone(user.customer_id)
        self.assertEqual(
            self.client.get(f"/customers/{user.customer_id}", headers=headers).status_code,
            200,
        )

    def test_customer_cannot_access_another_customer(self):
        first, first_headers = self.register_customer("first@example.com", "First")
        second, _ = self.register_customer("second@example.com", "Second")
        first_user = db.session.get(User, first["id"])
        second_user = db.session.get(User, second["id"])

        own_response = self.client.get(
            f"/customers/{first_user.customer_id}", headers=first_headers
        )
        other_response = self.client.get(
            f"/customers/{second_user.customer_id}", headers=first_headers
        )

        self.assertEqual(own_response.status_code, 200)
        self.assertEqual(other_response.status_code, 403)

    def test_customer_sees_only_own_tickets(self):
        first, first_headers = self.register_customer("first@example.com", "First")
        second, second_headers = self.register_customer("second@example.com", "Second")
        first_user = db.session.get(User, first["id"])
        second_user = db.session.get(User, second["id"])

        own_ticket = self.client.post(
            "/service-tickets",
            headers=first_headers,
            json={"repair_date": "2026-08-01", "customer_id": first_user.customer_id},
        )
        other_ticket = self.client.post(
            "/service-tickets",
            headers=second_headers,
            json={"repair_date": "2026-08-02", "customer_id": second_user.customer_id},
        )
        listed = self.client.get("/service-tickets", headers=first_headers).get_json()

        self.assertEqual(own_ticket.status_code, 201)
        self.assertEqual(other_ticket.status_code, 201)
        self.assertEqual([ticket["id"] for ticket in listed], [own_ticket.get_json()["id"]])

    def test_mechanic_sees_only_assigned_tickets(self):
        mechanic, mechanic_headers = self.create_mechanic_user()
        customer_one = Customer(
            name="One", email="one@example.com", date_of_birth=date(1990, 1, 1)
        )
        customer_two = Customer(
            name="Two", email="two@example.com", date_of_birth=date(1990, 1, 1)
        )
        assigned = Service_Ticket(repair_date=date(2026, 8, 1), customer=customer_one)
        unassigned = Service_Ticket(
            repair_date=date(2026, 8, 2), customer=customer_two
        )
        assigned.mechanics.append(mechanic)
        db.session.add_all([assigned, unassigned])
        db.session.commit()

        response = self.client.get("/service-tickets", headers=mechanic_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([ticket["id"] for ticket in response.get_json()], [assigned.id])

    def test_only_admin_can_mutate_mechanics(self):
        _, customer_headers = self.register_customer("owner@example.com", "Owner")
        payload = {
            "name": "New Mechanic",
            "specialty": "Electrical",
            "experience": "2 years",
            "certification": "ASE",
        }

        forbidden = self.client.post(
            "/mechanics", headers=customer_headers, json=payload
        )
        created = self.client.post(
            "/mechanics", headers=self.admin_headers, json=payload
        )

        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(created.status_code, 201)

    def test_invalid_token_is_rejected(self):
        response = self.client.get(
            "/users/me", headers={"Authorization": "Bearer invalid-token"}
        )

        self.assertEqual(response.status_code, 401)