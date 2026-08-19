from app.extensions import ma
from app.models import Student


class StudentSchema(ma.SQLAlchemyAutoSchema):
    id = ma.auto_field(dump_only=True)

    class Meta:
        model = Student


student_schema = StudentSchema()
students_schema = StudentSchema(many=True)