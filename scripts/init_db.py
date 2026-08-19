from flask_app import app
from app.extensions import db
from app.models import Part


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
    # Replaces the retired two-junction session model with one unified table.
    cascade = " CASCADE" if db.engine.dialect.name == "postgresql" else ""
    db.session.execute(db.text(f"DROP TABLE IF EXISTS mechanics_service_ticket{cascade}"))
    db.session.execute(db.text(f"DROP TABLE IF EXISTS service_ticket_parts{cascade}"))
    db.session.execute(db.text(f"DROP TABLE IF EXISTS service_tickets{cascade}"))
    db.session.commit()
    db.create_all()

    existing_skus = set(db.session.scalars(db.select(Part.sku)).all())
    db.session.add_all(
        Part(name=name, sku=sku, stock_quantity=24)
        for name, sku in LESSONS
        if sku not in existing_skus
    )
    db.session.commit()
