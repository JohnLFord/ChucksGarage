from app.extensions import ma
from app.models import Lesson, Session, Student, Teacher


class StudentSummarySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Student
        fields = ("id", "name", "email")


class TeacherSummarySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Teacher
        fields = ("id", "name", "specialty")


class LessonSummarySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Lesson
        fields = ("id", "name", "sku")


class SessionSchema(ma.SQLAlchemyAutoSchema):
    id = ma.auto_field(dump_only=True)
    student = ma.Nested(StudentSummarySchema, dump_only=True)
    teacher = ma.Nested(TeacherSummarySchema, dump_only=True)
    lesson = ma.Nested(LessonSummarySchema, dump_only=True)

    class Meta:
        model = Session
        include_fk = True


session_schema = SessionSchema()
sessions_schema = SessionSchema(many=True)
