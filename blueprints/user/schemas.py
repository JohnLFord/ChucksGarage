from app.extensions import ma
from app.models import User


class UserSchema(ma.SQLAlchemyAutoSchema):
    id = ma.auto_field(dump_only=True)
    password_hash = ma.auto_field(load_only=True)

    class Meta:
        model = User


user_schema = UserSchema()