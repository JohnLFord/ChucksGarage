from app.extensions import ma
from app.models import Lesson


class LessonSchema(ma.SQLAlchemyAutoSchema):
    id = ma.auto_field(dump_only=True)

    class Meta:
        model = Lesson


lesson_schema = LessonSchema()
lessons_schema = LessonSchema(many=True)
