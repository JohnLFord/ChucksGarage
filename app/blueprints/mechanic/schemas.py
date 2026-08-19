from app.extensions import ma
from app.models import Teacher


class TeacherSchema(ma.SQLAlchemyAutoSchema):
    id = ma.auto_field(dump_only=True)

    class Meta:
        model = Teacher


teacher_schema = TeacherSchema()
teachers_schema = TeacherSchema(many=True)