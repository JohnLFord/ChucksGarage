from app.extensions import ma
from app.models import Customer, Mechanic, OneToOneSession, Part


class StudentSummarySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Customer
        fields = ("id", "name", "email")


class TeacherSummarySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mechanic
        fields = ("id", "name", "specialty")


class LessonSummarySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Part
        fields = ("id", "name", "sku")


class OneToOneSessionSchema(ma.SQLAlchemyAutoSchema):
    id = ma.auto_field(dump_only=True)
    customer = ma.Nested(StudentSummarySchema, dump_only=True)
    teacher = ma.Nested(TeacherSummarySchema, dump_only=True)
    lesson = ma.Nested(LessonSummarySchema, dump_only=True)

    class Meta:
        model = OneToOneSession
        include_fk = True


session_schema = OneToOneSessionSchema()
sessions_schema = OneToOneSessionSchema(many=True)
