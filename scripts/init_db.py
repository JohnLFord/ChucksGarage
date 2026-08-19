import os

from werkzeug.security import generate_password_hash

from flask_app import app
from app.extensions import db
from app.models import Lesson, User


LESSONS = [
    ("HTML", "HTML-101"),
    ("CSS", "CSS-101"),
    ("React", "REACT-101"),
    ("SQL", "SQL-101"),
    ("Python", "PYTHON-101"),
    ("JavaScript", "JAVASCRIPT-101"),
    ("TypeScript", "TYPESCRIPT-101"),
    ("Firebase", "FIREBASE-101"),
    ("Firestore", "FIRESTORE-101"),
    ("Auth0", "AUTH0-101"),
    ("Render", "RENDER-101"),
    ("Vercel", "VERCEL-101"),
    ("CI/CD", "CICD-101"),
    ("Project Planning", "PLAN-101"),
    ("Database Design", "DBDESIGN-101"),
]

with app.app_context():
    cascade = " CASCADE" if db.engine.dialect.name == "postgresql" else ""
    existing_admins = db.session.execute(
        db.text("SELECT email, password_hash FROM users WHERE role = 'admin'")
    ).mappings().all()
    db.session.execute(db.text(f"DROP TABLE IF EXISTS mechanics_service_ticket{cascade}"))
    db.session.execute(db.text(f"DROP TABLE IF EXISTS service_ticket_parts{cascade}"))
    db.session.execute(db.text(f"DROP TABLE IF EXISTS service_tickets{cascade}"))
    db.session.execute(db.text(f"DROP TABLE IF EXISTS one_to_one_sessions{cascade}"))
    db.session.execute(db.text(f"DROP TABLE IF EXISTS sessions{cascade}"))
    db.session.execute(db.text(f"DROP TABLE IF EXISTS users{cascade}"))
    db.session.execute(db.text(f"DROP TABLE IF EXISTS customers{cascade}"))
    db.session.execute(db.text(f"DROP TABLE IF EXISTS mechanics{cascade}"))
    db.session.execute(db.text(f"DROP TABLE IF EXISTS parts{cascade}"))
    db.session.execute(db.text(f"DROP TABLE IF EXISTS students{cascade}"))
    db.session.execute(db.text(f"DROP TABLE IF EXISTS teachers{cascade}"))
    db.session.execute(db.text(f"DROP TABLE IF EXISTS lessons{cascade}"))
    db.session.commit()
    db.create_all()

    existing_skus = set(db.session.scalars(db.select(Lesson.sku)).all())
    db.session.add_all(
        Lesson(name=name, sku=sku, stock_quantity=24)
        for name, sku in LESSONS
        if sku not in existing_skus
    )
    admin_email = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "").strip().lower()
    admin_password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "")
    if admin_email and admin_password:
        administrators = {admin_email: generate_password_hash(admin_password)}
    else:
        administrators = {
            administrator["email"]: administrator["password_hash"]
            for administrator in existing_admins
        }
    db.session.add_all(
        User(email=email, password_hash=password_hash, role="admin")
        for email, password_hash in administrators.items()
    )
    db.session.commit()
