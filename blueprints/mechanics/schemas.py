from app.extensions import ma
from app.models import Mechanic


class MechanicSchema(ma.SQLAlchemyAutoSchema):
    id = ma.auto_field(dump_only=True)

    class Meta:
        model = Mechanic


mechanic_schema = MechanicSchema()
mechanics_schema = MechanicSchema(many=True)