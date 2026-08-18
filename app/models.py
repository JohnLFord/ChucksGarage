from datetime import date

from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import Mapped, mapped_column

from .extensions import Base, db


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

    service_tickets: Mapped[list["Service_Ticket"]] = db.relationship(
        back_populates="customer"
    )
    user: Mapped["User | None"] = db.relationship(back_populates="customer")


class MechanicsServiceTicket(Base):
    __tablename__ = "mechanics_service_ticket"

    service_ticket_id: Mapped[int] = mapped_column(
        db.ForeignKey("service_tickets.id"), primary_key=True
    )
    mechanic_id: Mapped[int] = mapped_column(
        db.ForeignKey("mechanics.id"), primary_key=True
    )
    assignment_date: Mapped[date] = mapped_column(
        db.Date, nullable=False, default=date.today
    )
    part_ordered: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, default=False
    )

    service_ticket: Mapped["Service_Ticket"] = db.relationship(
        back_populates="mechanic_assignments"
    )
    mechanic: Mapped["Mechanic"] = db.relationship(back_populates="ticket_assignments")


class Service_Ticket(Base):
    __tablename__ = "service_tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    repair_date: Mapped[date] = mapped_column(db.Date)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey("customers.id"))

    customer: Mapped["Customer"] = db.relationship(back_populates="service_tickets")
    mechanic_assignments: Mapped[list["MechanicsServiceTicket"]] = db.relationship(
        back_populates="service_ticket", cascade="all, delete-orphan"
    )
    mechanics = association_proxy(
        "mechanic_assignments",
        "mechanic",
        creator=lambda mechanic: MechanicsServiceTicket(mechanic=mechanic),
    )
    part_orders: Mapped[list["ServiceTicketPart"]] = db.relationship(
        back_populates="service_ticket"
    )


class Part(Base):
    __tablename__ = "parts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    sku: Mapped[str] = mapped_column(db.String(100), nullable=False, unique=True)
    stock_quantity: Mapped[int] = mapped_column(default=0)

    service_ticket_parts: Mapped[list["ServiceTicketPart"]] = db.relationship(
        back_populates="part"
    )


class ServiceTicketPart(Base):
    __tablename__ = "service_ticket_parts"

    id: Mapped[int] = mapped_column(primary_key=True)
    service_ticket_id: Mapped[int] = mapped_column(
        db.ForeignKey("service_tickets.id"), nullable=False
    )
    part_id: Mapped[int] = mapped_column(db.ForeignKey("parts.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(default=1)
    unit_cost: Mapped[float] = mapped_column(db.Float, nullable=False, default=0.0)

    service_ticket: Mapped["Service_Ticket"] = db.relationship(
        back_populates="part_orders"
    )
    part: Mapped["Part"] = db.relationship(back_populates="service_ticket_parts")


class Mechanic(Base):
    __tablename__ = "mechanics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    specialty: Mapped[str] = mapped_column(db.String(255), nullable=False)
    experience: Mapped[str] = mapped_column(db.String(255), nullable=False)
    certification: Mapped[str] = mapped_column(db.String(255), nullable=False)

    ticket_assignments: Mapped[list["MechanicsServiceTicket"]] = db.relationship(
        back_populates="mechanic", cascade="all, delete-orphan"
    )
    service_tickets = association_proxy("ticket_assignments", "service_ticket")
    user: Mapped["User | None"] = db.relationship(back_populates="mechanic")


class Member(db.Model):
    __tablename__ = "members"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    DOB = db.Column(db.Date, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="customer")

    def __repr__(self):
        return f"<Member {self.name}>"
