from sqlalchemy import inspect, text

from app import create_app
from app.extensions import db


app = create_app("config.DevelopmentConfig")

with app.app_context():
    duplicates = db.session.execute(
        text(
            """
            SELECT service_ticket_id, mechanic_id, COUNT(*)
            FROM service_ticket_mechanics
            GROUP BY service_ticket_id, mechanic_id
            HAVING COUNT(*) > 1
            """
        )
    ).all()
    if duplicates:
        raise RuntimeError(f"Duplicate assignments found: {duplicates}")

    primary_key = inspect(db.engine).get_pk_constraint(
        "service_ticket_mechanics"
    )["constrained_columns"]
    if not primary_key:
        db.session.execute(
            text(
                """
                ALTER TABLE service_ticket_mechanics
                ADD PRIMARY KEY (service_ticket_id, mechanic_id)
                """
            )
        )

    db.session.commit()

    primary_key = inspect(db.engine).get_pk_constraint(
        "service_ticket_mechanics"
    )["constrained_columns"]
    print(f"Assignment primary key: {primary_key}")