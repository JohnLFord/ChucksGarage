from datetime import date

from sqlalchemy.orm import Mapped, mapped_column

from .extensions import Base, db


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        db.CheckConstraint(
            "role IN ('admin', 'teacher', 'student')", name="ck_users_role"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(db.String(360), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(db.String(255), nullable=False)
    role: Mapped[str] = mapped_column(db.String(50), nullable=False, default="student")
    student_id: Mapped[int | None] = mapped_column(
        db.ForeignKey("students.id"), nullable=True, unique=True
    )
    teacher_id: Mapped[int | None] = mapped_column(
        db.ForeignKey("teachers.id"), nullable=True, unique=True
    )

    student: Mapped["Student | None"] = db.relationship(back_populates="user")
    teacher: Mapped["Teacher | None"] = db.relationship(back_populates="user")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(360), nullable=False, unique=True)
    date_of_birth: Mapped[date] = mapped_column("DOB", db.Date)

    sessions: Mapped[list["Session"]] = db.relationship(
        back_populates="student"
    )
    user: Mapped["User | None"] = db.relationship(back_populates="student")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_date: Mapped[date] = mapped_column(db.Date, nullable=False, default=date.today)
    student_id: Mapped[int] = mapped_column(db.ForeignKey("students.id"), nullable=False)
    teacher_id: Mapped[int] = mapped_column(db.ForeignKey("teachers.id"), nullable=False)
    lesson_id: Mapped[int] = mapped_column(db.ForeignKey("lessons.id"), nullable=False)
    notes: Mapped[str | None] = mapped_column(db.String(500), nullable=True)

    student: Mapped["Student"] = db.relationship(back_populates="sessions")
    teacher: Mapped["Teacher"] = db.relationship(back_populates="sessions")
    lesson: Mapped["Lesson"] = db.relationship(back_populates="sessions")


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    sku: Mapped[str] = mapped_column(db.String(100), nullable=False, unique=True)
    stock_quantity: Mapped[int] = mapped_column(default=0)

    sessions: Mapped[list["Session"]] = db.relationship(
        back_populates="lesson"
    )


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    specialty: Mapped[str] = mapped_column(db.String(255), nullable=False)
    experience: Mapped[str] = mapped_column(db.String(255), nullable=False)
    certification: Mapped[str] = mapped_column(db.String(255), nullable=False)

    sessions: Mapped[list["Session"]] = db.relationship(
        back_populates="teacher"
    )
    user: Mapped["User | None"] = db.relationship(back_populates="teacher")


