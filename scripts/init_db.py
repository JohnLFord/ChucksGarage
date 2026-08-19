from flask_app import app
from app.extensions import db

with app.app_context():
    # Replaces the retired two-junction session model with one unified table.
    db.session.execute(db.text("DROP TABLE IF EXISTS mechanics_service_ticket CASCADE"))
    db.session.execute(db.text("DROP TABLE IF EXISTS service_ticket_parts CASCADE"))
    db.session.execute(db.text("DROP TABLE IF EXISTS service_tickets CASCADE"))
    db.session.commit()
    db.create_all()
