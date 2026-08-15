from datetime import date

from sqlalchemy import inspect, text

from app import create_app
from app.extensions import db
from app.models import Customer, Mechanic, Part, ServiceTicketPart, Service_Ticket


def seed_demo_repair_data():
    customers = [
        Customer(name="Alicia Green", email="alicia@example.com", date_of_birth=date(1990, 1, 15)),
        Customer(name="Marcus Lee", email="marcus@example.com", date_of_birth=date(1986, 5, 20)),
        Customer(name="Priya Shah", email="priya@example.com", date_of_birth=date(1992, 9, 3)),
        Customer(name="Daniel Ross", email="daniel@example.com", date_of_birth=date(1983, 3, 25)),
    ]
    db.session.add_all(customers)
    db.session.flush()

    mechanics = [
        Mechanic(name="Jordan Smith", specialty="Brakes", experience="5 years", certification="ASE Master"),
        Mechanic(name="Tara Nguyen", specialty="Electrical", experience="8 years", certification="EV Certified"),
        Mechanic(name="Luis Moreno", specialty="Engine", experience="10 years", certification="Diesel Specialist"),
        Mechanic(name="Chloe Martin", specialty="Suspension", experience="6 years", certification="Alignment Certified"),
    ]
    db.session.add_all(mechanics)
    db.session.flush()

    ticket_data = [
        (customers[0], "Brake repair", [mechanics[0], mechanics[3]]),
        (customers[1], "Oil change", [mechanics[0], mechanics[2]]),
        (customers[2], "Battery replacement", [mechanics[1]]),
        (customers[0], "Tire rotation", [mechanics[3]]),
        (customers[3], "Engine diagnostics", [mechanics[2], mechanics[0]]),
        (customers[1], "Windshield replacement", [mechanics[1], mechanics[3]]),
        (customers[2], "AC repair", [mechanics[1]]),
        (customers[3], "Suspension work", [mechanics[3], mechanics[0]]),
        (customers[0], "Transmission service", [mechanics[2]]),
        (customers[1], "Electrical issue", [mechanics[1], mechanics[2], mechanics[0]]),
    ]

    parts = [
        Part(name="Brake Pad Set", sku="BR-100", stock_quantity=25),
        Part(name="Oil Filter", sku="OF-210", stock_quantity=40),
        Part(name="Battery 12V", sku="BT-335", stock_quantity=12),
        Part(name="Tire Rotation Kit", sku="TR-88", stock_quantity=15),
        Part(name="Spark Plug Set", sku="SP-420", stock_quantity=30),
        Part(name="Windshield Wiper Pack", sku="WW-155", stock_quantity=18),
        Part(name="Cabin Air Filter", sku="CAF-76", stock_quantity=20),
        Part(name="Shock Absorber", sku="SA-555", stock_quantity=8),
        Part(name="Transmission Fluid", sku="TF-95", stock_quantity=21),
        Part(name="Fuse Kit", sku="FK-19", stock_quantity=50),
    ]
    db.session.add_all(parts)
    db.session.flush()

    for index, (customer, repair_name, assigned_mechanics) in enumerate(ticket_data, start=1):
        ticket = Service_Ticket(
            repair_date=date(2026, 8, index),
            customer_id=customer.id,
        )
        db.session.add(ticket)
        db.session.flush()
        ticket.mechanics.extend(assigned_mechanics)

        for part_index, part in enumerate(parts[: min(index, len(parts))], start=1):
            if part_index % 2 == 0 or index % 2 == 0:
                db.session.add(
                    ServiceTicketPart(
                        service_ticket_id=ticket.id,
                        part_id=part.id,
                        quantity=(part_index if index % 2 else 1),
                        unit_cost=round((part_index + 1) * 12.5, 2),
                    )
                )

    db.session.commit()
    print("Seeded 10 demo service tickets, mechanic assignments, and part orders.")


def seed_demo_part_orders_for_existing_tickets():
    tickets = db.session.execute(db.select(Service_Ticket)).scalars().all()
    if not tickets:
        raise RuntimeError("Create at least one service ticket before seeding part orders.")

    parts = [
        Part(name="Brake Pad Set", sku="BR-100", stock_quantity=25),
        Part(name="Oil Filter", sku="OF-210", stock_quantity=40),
        Part(name="Battery 12V", sku="BT-335", stock_quantity=12),
        Part(name="Tire Rotation Kit", sku="TR-88", stock_quantity=15),
        Part(name="Spark Plug Set", sku="SP-420", stock_quantity=30),
        Part(name="Windshield Wiper Pack", sku="WW-155", stock_quantity=18),
        Part(name="Cabin Air Filter", sku="CAF-76", stock_quantity=20),
        Part(name="Shock Absorber", sku="SA-555", stock_quantity=8),
        Part(name="Transmission Fluid", sku="TF-95", stock_quantity=21),
        Part(name="Fuse Kit", sku="FK-19", stock_quantity=50),
    ]
    db.session.add_all(parts)
    db.session.flush()

    for index, part in enumerate(parts, start=1):
        db.session.add(
            ServiceTicketPart(
                service_ticket_id=tickets[(index - 1) % len(tickets)].id,
                part_id=part.id,
                quantity=index,
                unit_cost=round((index + 1) * 12.5, 2),
            )
        )

    db.session.add(
        ServiceTicketPart(
            service_ticket_id=tickets[0].id,
            part_id=parts[0].id,
            quantity=5,
            unit_cost=25.0,
        )
    )
    db.session.commit()
    print("Seeded 10 demo parts and 11 part-order line items for existing tickets.")


app = create_app("config.DevelopmentConfig")

with app.app_context():
    db.create_all()

    if db.session.query(Part).count() == 0 and db.session.query(Service_Ticket).count() > 0:
        seed_demo_part_orders_for_existing_tickets()
    elif db.session.query(Customer).count() == 0 and db.session.query(Mechanic).count() == 0:
        seed_demo_repair_data()

    duplicates = db.session.execute(
        text(
            """
            SELECT service_ticket_id, mechanic_id, COUNT(*)
            FROM mechanics_service_ticket
            GROUP BY service_ticket_id, mechanic_id
            HAVING COUNT(*) > 1
            """
        )
    ).all()
    if duplicates:
        raise RuntimeError(f"Duplicate assignments found: {duplicates}")

    primary_key = inspect(db.engine).get_pk_constraint(
        "mechanics_service_ticket"
    )["constrained_columns"]
    if not primary_key:
        db.session.execute(
            text(
                """
                ALTER TABLE mechanics_service_ticket
                ADD PRIMARY KEY (service_ticket_id, mechanic_id)
                """
            )
        )

    db.session.commit()

    primary_key = inspect(db.engine).get_pk_constraint(
        "mechanics_service_ticket"
    )["constrained_columns"]
    print(f"Assignment primary key: {primary_key}")