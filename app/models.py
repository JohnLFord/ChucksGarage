from datetime import date

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

    sessions: Mapped[list["OneToOneSession"]] = db.relationship(
        back_populates="customer"
    )
    user: Mapped["User | None"] = db.relationship(back_populates="customer")


class OneToOneSession(Base):
    __tablename__ = "one_to_one_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_date: Mapped[date] = mapped_column(db.Date, nullable=False, default=date.today)
    student_id: Mapped[int] = mapped_column(db.ForeignKey("customers.id"), nullable=False)
    teacher_id: Mapped[int] = mapped_column(db.ForeignKey("mechanics.id"), nullable=False)
    lesson_id: Mapped[int] = mapped_column(db.ForeignKey("parts.id"), nullable=False)
    notes: Mapped[str | None] = mapped_column(db.String(500), nullable=True)

    customer: Mapped["Customer"] = db.relationship(back_populates="sessions")
    teacher: Mapped["Mechanic"] = db.relationship(back_populates="sessions")
    lesson: Mapped["Part"] = db.relationship(back_populates="sessions")


class Part(Base):
    __tablename__ = "parts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    sku: Mapped[str] = mapped_column(db.String(100), nullable=False, unique=True)
    stock_quantity: Mapped[int] = mapped_column(default=0)

    sessions: Mapped[list["OneToOneSession"]] = db.relationship(
        back_populates="lesson"
    )


class Mechanic(Base):
    __tablename__ = "mechanics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    specialty: Mapped[str] = mapped_column(db.String(255), nullable=False)
    experience: Mapped[str] = mapped_column(db.String(255), nullable=False)
    certification: Mapped[str] = mapped_column(db.String(255), nullable=False)

    sessions: Mapped[list["OneToOneSession"]] = db.relationship(
        back_populates="teacher"
    )
    user: Mapped["User | None"] = db.relationship(back_populates="mechanic")


