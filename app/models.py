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


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        db.CheckConstraint(
            "role IN ('admin', 'mechanic', 'customer')", name="ck_users_role"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(db.String(360), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(db.String(255), nullable=False)
    role: Mapped[str] = mapped_column(db.String(50), nullable=False, default="customer")
    customer_id: Mapped[int | None] = mapped_column(
        db.ForeignKey("customers.id"), nullable=True, unique=True
    )
    mechanic_id: Mapped[int | None] = mapped_column(
        db.ForeignKey("mechanics.id"), nullable=True, unique=True
    )

    customer: Mapped["Customer | None"] = db.relationship(back_populates="user")
    mechanic: Mapped["Mechanic | None"] = db.relationship(back_populates="user")


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(360), nullable=False, unique=True)
    date_of_birth: Mapped[date] = mapped_column("DOB", db.Date)

    service_tickets: Mapped[list["Service_Ticket"]] = db.relationship(back_populates="customer")
    user: Mapped["User | None"] = db.relationship(back_populates="customer")


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
    user: Mapped["User | None"] = db.relationship(back_populates="mechanic")


