from app import create_app
from app.models import db, Member
import unittest
from datetime import datetime

from app.utils.util import encode_token


class TestMember(unittest.TestCase):
    def setUp(self):
        self.app = create_app("TestingConfig")
        self.member = Member(
            name="test_user",
            email="test@email.com",
            DOB=datetime.strptime("1900-01-01", "%Y-%m-%d").date(),
            password="test",
        )
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            db.session.add(self.member)
            db.session.commit()
            self.token = encode_token(1, "customer")
            self.client = self.app.test_client()

    def test_create_member(self):
        member_payload = {
            "name": "John Doe",
            "email": "jd@email.com",
            "DOB": "1900-01-01",
            "password": "123",
        }

        response = self.client.post("/members/", json=member_payload)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["name"], "John Doe")

    def test_login_member(self):
        credentials = {"email": "test@email.com", "password": "test"}

        response = self.client.post("/users/login", json=credentials)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["auth_token"], self.token)
        return response.json["auth_token"]

    def test_invalid_creation(self):
        member_payload = {
            "name": "John Doe",
            "phone": "123-456-7890",
            "password": "123",
        }

        response = self.client.post("/members/", json=member_payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json["email"], ["Missing data for required field."])

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_invalid_login(self):
        credentials = {"email": "bad_email@email.com", "password": "bad_pw"}

        response = self.client.post("/users/login", json=credentials)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json["error"], "Invalid email or password")

    def test_update_member(self):
        update_payload = {
            "name": "Peter",
            "phone": "",
            "email": "",
            "password": ""
        }

        headers = {'Authorization': "Bearer " + self.test_login_member()}

        response = self.client.put('/members/', json=update_payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['name'], 'Peter') 
        self.assertEqual(response.json['email'], 'test@email.com')
