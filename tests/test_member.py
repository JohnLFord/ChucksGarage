from app import create_app
from app.models import db, Member
import unittest
from datetime import datetime

class TestMember(unittest.TestCase):

    def setUp(self):
        # Load testing config
        self.app = create_app("TestingConfig")

        # Create fresh DB
        with self.app.app_context():
            db.drop_all()
            db.create_all()

        # Test client
        self.client = self.app.test_client()

    def test_create_member(self):
        member_payload = {
            "name": "John Doe",
            "email": "jd@email.com",
            "DOB": "1900-01-01",
            "password": "123"
        }

        response = self.client.post('/members/', json=member_payload)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['name'], "John Doe")