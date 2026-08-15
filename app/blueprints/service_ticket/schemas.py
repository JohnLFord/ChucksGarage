from app.extensions import ma
from app.models import (
    Mechanic,
    MechanicsServiceTicket,
    Part,
    ServiceTicketPart,
    Service_Ticket,
)


class MechanicSummarySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mechanic
        fields = ("id", "name", "specialty")


class PartSummarySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Part
        fields = ("id", "name", "sku", "stock_quantity")


class ServiceTicketPartSchema(ma.SQLAlchemyAutoSchema):
    id = ma.auto_field(dump_only=True)
    part = ma.Nested(PartSummarySchema, dump_only=True)

    class Meta:
        model = ServiceTicketPart
        include_fk = True


class MechanicAssignmentSchema(ma.SQLAlchemyAutoSchema):
    mechanic = ma.Nested(MechanicSummarySchema, dump_only=True)

    class Meta:
        model = MechanicsServiceTicket
        include_fk = True


class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    id = ma.auto_field(dump_only=True)
    mechanics = ma.Nested(MechanicSummarySchema, many=True, dump_only=True)
    mechanic_assignments = ma.Nested(MechanicAssignmentSchema, many=True, dump_only=True)
    part_orders = ma.Nested(ServiceTicketPartSchema, many=True, dump_only=True)

    class Meta:
        model = Service_Ticket
        include_fk = True


service_ticket_schema = ServiceTicketSchema()
service_tickets_schema = ServiceTicketSchema(many=True)
service_ticket_part_schema = ServiceTicketPartSchema()
service_ticket_parts_schema = ServiceTicketPartSchema(many=True)