import unittest

from sqlalchemy import select
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import Part, ServiceTicketPart, User


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

    def create_part(self, name="Brake Pad Set", sku="BR-100", stock_quantity=20):
        return self.client.post(
            "/inventory",
            headers=self.admin_headers,
            json={"name": name, "sku": sku, "stock_quantity": stock_quantity},
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

    def test_service_ticket_edit_route_adds_and_removes_mechanics(self):
        self.create_customer()
        self.create_mechanic()
        response = self.client.post(
            "/mechanics",
            headers=self.admin_headers,
            json={
                "name": "Second Mechanic",
                "specialty": "Brakes",
                "experience": "5 years",
                "certification": "ASE",
            },
        )
        self.assertEqual(response.status_code, 201)

        self.create_service_ticket()

        edit_response = self.client.put(
            "/service-tickets/1/edit",
            headers=self.admin_headers,
            json={"add_ids": [1, 2], "remove_ids": []},
        )
        self.assertEqual(edit_response.status_code, 200)
        self.assertEqual(
            {pair["id"] for pair in edit_response.get_json()["mechanics"]},
            {1, 2},
        )

        remove_response = self.client.put(
            "/service-tickets/1/edit",
            headers=self.admin_headers,
            json={"add_ids": [], "remove_ids": [1]},
        )
        self.assertEqual(remove_response.status_code, 200)
        self.assertEqual([pair["id"] for pair in remove_response.get_json()["mechanics"]], [2])

    def test_mechanics_endpoint_sorts_by_ticket_count(self):
        self.create_customer()
        self.create_mechanic()
        second_mechanic_response = self.client.post(
            "/mechanics",
            headers=self.admin_headers,
            json={
                "name": "Second Mechanic",
                "specialty": "Brakes",
                "experience": "5 years",
                "certification": "ASE",
            },
        )
        self.assertEqual(second_mechanic_response.status_code, 201)

        self.create_service_ticket()
        self.client.post("/service-tickets/1/mechanics/1", headers=self.admin_headers)
        self.client.post("/service-tickets/1/mechanics/2", headers=self.admin_headers)

        second_ticket_response = self.client.post(
            "/service-tickets",
            headers=self.admin_headers,
            json={"repair_date": "2026-08-02", "customer_id": 1},
        )
        self.assertEqual(second_ticket_response.status_code, 201)
        self.client.post("/service-tickets/2/mechanics/2", headers=self.admin_headers)

        response = self.client.get("/mechanics?sort=most_tickets", headers=self.admin_headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.get_json()], [2, 1])

    def test_customers_route_supports_pagination(self):
        for idx in range(3):
            response = self.client.post(
                "/customers",
                headers=self.admin_headers,
                json={
                    "name": f"Customer {idx + 1}",
                    "email": f"customer{idx + 1}@example.com",
                    "date_of_birth": "1990-01-01",
                },
            )
            self.assertEqual(response.status_code, 201)

        response = self.client.get(
            "/customers?limit=1&offset=1",
            headers=self.admin_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 1)
        self.assertEqual(response.get_json()[0]["id"], 2)

    def test_service_ticket_can_record_part_orders_with_metadata(self):
        self.create_customer()
        self.create_service_ticket()

        part = Part(name="Brake Pad Set", sku="BR-100", stock_quantity=20)
        db.session.add(part)
        db.session.commit()

        order = ServiceTicketPart(
            service_ticket_id=1,
            part_id=part.id,
            quantity=2,
            unit_cost=42.50,
        )
        db.session.add(order)
        db.session.commit()

        self.assertEqual(order.quantity, 2)
        self.assertEqual(order.unit_cost, 42.50)
        self.assertEqual(order.part.name, "Brake Pad Set")
        self.assertEqual(order.service_ticket.id, 1)

    def test_popular_parts_endpoint_sorts_by_total_quantity_with_lambda(self):
        self.create_customer()
        self.create_service_ticket()
        second_ticket_response = self.create_service_ticket()
        self.assertEqual(second_ticket_response.status_code, 201)

        brake_pads = Part(name="Brake Pad Set", sku="BR-100", stock_quantity=3)
        oil_filter = Part(name="Oil Filter", sku="OF-210", stock_quantity=10)
        unused_part = Part(name="Cabin Filter", sku="CF-300", stock_quantity=8)
        db.session.add_all([brake_pads, oil_filter, unused_part])
        db.session.flush()
        db.session.add_all(
            [
                ServiceTicketPart(
                    service_ticket_id=1,
                    part_id=brake_pads.id,
                    quantity=2,
                    unit_cost=42.50,
                ),
                ServiceTicketPart(
                    service_ticket_id=2,
                    part_id=brake_pads.id,
                    quantity=3,
                    unit_cost=42.50,
                ),
                ServiceTicketPart(
                    service_ticket_id=1,
                    part_id=oil_filter.id,
                    quantity=1,
                    unit_cost=18.99,
                ),
            ]
        )
        db.session.commit()

        response = self.client.get(
            "/service-tickets/parts/popular", headers=self.admin_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [(part["name"], part["total_used"]) for part in response.get_json()],
            [("Brake Pad Set", 5), ("Oil Filter", 1), ("Cabin Filter", 0)],
        )

    def test_inventory_part_can_be_created_and_retrieved(self):
        create_response = self.create_part()

        self.assertEqual(create_response.status_code, 201)
        part_id = create_response.get_json()["id"]

        get_response = self.client.get(
            f"/inventory/{part_id}", headers=self.admin_headers
        )
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.get_json()["sku"], "BR-100")

    def test_inventory_duplicate_sku_rejected(self):
        self.create_part()

        response = self.create_part(name="Different Part")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_inventory_part_can_be_updated(self):
        part_id = self.create_part().get_json()["id"]

        response = self.client.put(
            f"/inventory/{part_id}",
            headers=self.admin_headers,
            json={"stock_quantity": 5},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["stock_quantity"], 5)

    def test_inventory_part_with_orders_cannot_be_deleted(self):
        self.create_customer()
        self.create_service_ticket()
        part_id = self.create_part().get_json()["id"]
        db.session.add(
            ServiceTicketPart(
                service_ticket_id=1, part_id=part_id, quantity=1, unit_cost=10.0
            )
        )
        db.session.commit()

        response = self.client.delete(
            f"/inventory/{part_id}", headers=self.admin_headers
        )

        self.assertEqual(response.status_code, 409)

    def test_inventory_part_without_orders_can_be_deleted(self):
        part_id = self.create_part().get_json()["id"]

        response = self.client.delete(
            f"/inventory/{part_id}", headers=self.admin_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(db.session.get(Part, part_id))

    def test_inventory_supports_search_and_sort(self):
        self.create_part(name="Brake Pad Set", sku="BR-100", stock_quantity=20)
        self.create_part(name="Oil Filter", sku="OF-210", stock_quantity=5)

        response = self.client.get(
            "/inventory?sort=stock", headers=self.admin_headers
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["name"] for item in response.get_json()],
            ["Oil Filter", "Brake Pad Set"],
        )


if __name__ == "__main__":
    unittest.main()