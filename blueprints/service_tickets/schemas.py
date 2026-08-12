from app.extensions import ma
from app.models import Mechanic, Service_Ticket


class MechanicSummarySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mechanic
        fields = ("id", "name", "specialty")


class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    id = ma.auto_field(dump_only=True)
    mechanics = ma.Nested(MechanicSummarySchema, many=True, dump_only=True)

    class Meta:
        model = Service_Ticket
        include_fk = True


service_ticket_schema = ServiceTicketSchema()
service_tickets_schema = ServiceTicketSchema(many=True)