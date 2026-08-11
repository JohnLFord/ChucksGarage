from datetime import date

from sqlalchemy.orm import Mapped, mapped_column

from .extensions import Base, db

service_ticket_mechanics = db.Table(
    "service_ticket_mechanics",
    db.metadata,
    db.Column(
        "service_ticket_id", db.ForeignKey("service_tickets.id"), primary_key=True
    ),
    db.Column("mechanic_id", db.ForeignKey("mechanics.id"), primary_key=True),
)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(360), nullable=False, unique=True)
    DOB: Mapped[date] = mapped_column(db.Date)

    service_tickets: Mapped[list["Service_Ticket"]] = db.relationship(back_populates="customer")


class Service_Ticket(Base):
    __tablename__ = "service_tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    repair_date: Mapped[date] = mapped_column(db.Date)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey("customers.id"))

    customer: Mapped["Customer"] = db.relationship(back_populates="service_tickets")
    mechanics: Mapped[list["Mechanic"]] = db.relationship(
        "Mechanic",
        secondary=service_ticket_mechanics,
        back_populates="service_tickets",
    )


class Mechanic(Base):
    __tablename__ = "mechanics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    specialty: Mapped[str] = mapped_column(db.String(255), nullable=False)
    experience: Mapped[str] = mapped_column(db.String(255), nullable=False)
    certification: Mapped[str] = mapped_column(db.String(255), nullable=False)

    service_tickets: Mapped[list["Service_Ticket"]] = db.relationship(
        "Service_Ticket",
        secondary=service_ticket_mechanics,
        back_populates="mechanics",
    )


