import unittest
from datetime import date

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import Lesson, Session, Student, Teacher, User


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test-only-jwt-signing-key-at-least-32-bytes"
    RATELIMIT_ENABLED = False


class SessionTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        db.session.add(User(email="admin@example.com", password_hash=generate_password_hash("admin-password"), role="admin"))
        db.session.add(Student(name="Student One", email="student@example.com", date_of_birth=date(1990, 1, 1)))
        db.session.add(Teacher(name="Teacher One", specialty="React", experience="5 years", certification="Instructor"))
        db.session.add(Lesson(name="React", sku="REACT-101", stock_quantity=24))
        db.session.commit()
        self.client = self.app.test_client()
        login = self.client.post("/users/login", json={"email": "admin@example.com", "password": "admin-password"})
        self.headers = {"Authorization": f"Bearer {login.get_json()['auth_token']}"}

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def test_session_unifies_student_teacher_and_lesson(self):
        response = self.client.post(
            "/sessions/",
            headers=self.headers,
            json={"session_date": "2026-08-18", "student_id": 1, "teacher_id": 1, "lesson_id": 1, "notes": "Worked on components."},
        )
        self.assertEqual(response.status_code, 201)
        session = response.get_json()
        self.assertEqual(session["student_id"], 1)
        self.assertEqual(session["teacher"]["name"], "Teacher One")
        self.assertEqual(session["lesson"]["name"], "React")
        self.assertEqual(db.session.query(Session).count(), 1)

    def test_session_requires_existing_links(self):
        response = self.client.post(
            "/sessions/",
            headers=self.headers,
            json={"session_date": "2026-08-18", "student_id": 1, "teacher_id": 99, "lesson_id": 1},
        )
        self.assertEqual(response.status_code, 404)

    def test_admin_can_filter_session_history(self):
        db.session.add(Student(name="Student Two", email="student-two@example.com", date_of_birth=date(1991, 1, 1)))
        db.session.add(Teacher(name="Teacher Two", specialty="Python", experience="3 years", certification="Instructor"))
        db.session.add(Lesson(name="Python", sku="PYTHON-101", stock_quantity=24))
        db.session.commit()
        for payload in (
            {"session_date": "2026-08-18", "student_id": 1, "teacher_id": 1, "lesson_id": 1},
            {"session_date": "2026-08-19", "student_id": 2, "teacher_id": 2, "lesson_id": 2},
        ):
            response = self.client.post("/sessions/", headers=self.headers, json=payload)
            self.assertEqual(response.status_code, 201)

        response = self.client.get("/sessions/?student_id=2&teacher_id=2", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 1)
        self.assertEqual(response.get_json()[0]["student"]["name"], "Student Two")

    def test_linked_student_and_teacher_cannot_be_deleted(self):
        self.client.post(
            "/sessions/",
            headers=self.headers,
            json={"session_date": "2026-08-18", "student_id": 1, "teacher_id": 1, "lesson_id": 1},
        )

        student_response = self.client.delete("/students/1", headers=self.headers)
        teacher_response = self.client.delete("/teachers/1", headers=self.headers)

        self.assertEqual(student_response.status_code, 409)
        self.assertEqual(teacher_response.status_code, 409)

    def test_student_updates_through_students_endpoint(self):
        response = self.client.put(
            "/students/1",
            headers=self.headers,
            json={"name": "Gail Darm", "email": "student@example.com", "date_of_birth": "1949-08-18"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["name"], "Gail Darm")

    def test_csv_exports_return_downloadable_data(self):
        response = self.client.get("/students/export.csv", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/csv")
        self.assertIn("attachment; filename=\"students.csv\"", response.headers["Content-Disposition"])
        self.assertIn("Student One", response.get_data(as_text=True))
