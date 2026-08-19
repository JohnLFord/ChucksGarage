from flask import g, jsonify, request
from marshmallow import ValidationError

from app.extensions import cache, db
from app.csv_export import csv_response
from app.models import Customer, Mechanic, OneToOneSession, Part
from app.utils.util import roles_required, token_required

from . import service_tickets_bp
from .schemas import session_schema, sessions_schema


def get_session_or_404(session_id):
    session = db.session.get(OneToOneSession, session_id)
    if not session:
        return None, (jsonify({"error": "Session not found"}), 404)
    return session, None


@service_tickets_bp.route("/", methods=["POST"])
@roles_required("admin")
def create_session():
    try:
        payload = session_schema.load(request.json)
    except ValidationError as error:
        return jsonify(error.messages), 400

    if not db.session.get(Customer, payload["student_id"]):
        return jsonify({"error": "Student not found"}), 404
    if not db.session.get(Mechanic, payload["teacher_id"]):
        return jsonify({"error": "Teacher not found"}), 404
    if not db.session.get(Part, payload["lesson_id"]):
        return jsonify({"error": "Lesson not found"}), 404

    session = OneToOneSession(**payload)
    db.session.add(session)
    db.session.commit()
    cache.clear()
    return session_schema.jsonify(session), 201


@service_tickets_bp.route("/", methods=["GET"])
@token_required
def get_sessions():
    query = db.select(OneToOneSession)
    if g.current_user.role == "customer":
        query = query.where(OneToOneSession.student_id == g.current_user.customer_id)
    elif g.current_user.role == "mechanic":
        query = query.where(OneToOneSession.teacher_id == g.current_user.mechanic_id)
    elif g.current_user.role != "admin":
        return jsonify({"error": "Insufficient permissions"}), 403
    return sessions_schema.jsonify(db.session.execute(query).scalars().all()), 200


@service_tickets_bp.route("/export.csv", methods=["GET"])
@token_required
def export_sessions():
    query = db.select(OneToOneSession).order_by(OneToOneSession.id)
    if g.current_user.role == "customer":
        query = query.where(OneToOneSession.student_id == g.current_user.customer_id)
    elif g.current_user.role == "mechanic":
        query = query.where(OneToOneSession.teacher_id == g.current_user.mechanic_id)
    elif g.current_user.role != "admin":
        return jsonify({"error": "Insufficient permissions"}), 403
    sessions = db.session.execute(query).scalars().all()
    rows = [
        {
            "id": session.id,
            "session_date": session.session_date.isoformat(),
            "student_id": session.student_id,
            "student_name": session.customer.name,
            "teacher_id": session.teacher_id,
            "teacher_name": session.teacher.name,
            "lesson_id": session.lesson_id,
            "lesson_name": session.lesson.name,
            "notes": session.notes or "",
        }
        for session in sessions
    ]
    return csv_response(
        "sessions.csv",
        rows,
        ["id", "session_date", "student_id", "student_name", "teacher_id", "teacher_name", "lesson_id", "lesson_name", "notes"],
    )


@service_tickets_bp.route("/<int:session_id>", methods=["GET"])
@token_required
def get_session(session_id):
    session, error = get_session_or_404(session_id)
    if error:
        return error
    if g.current_user.role == "customer" and session.student_id != g.current_user.customer_id:
        return jsonify({"error": "Insufficient permissions"}), 403
    if g.current_user.role == "mechanic" and session.teacher_id != g.current_user.mechanic_id:
        return jsonify({"error": "Insufficient permissions"}), 403
    return session_schema.jsonify(session), 200


@service_tickets_bp.route("/<int:session_id>", methods=["PUT"])
@roles_required("admin")
def update_session(session_id):
    session, error = get_session_or_404(session_id)
    if error:
        return error
    try:
        payload = session_schema.load(request.json, partial=True)
    except ValidationError as error:
        return jsonify(error.messages), 400
    for field, model in (("student_id", Customer), ("teacher_id", Mechanic), ("lesson_id", Part)):
        if field in payload and not db.session.get(model, payload[field]):
            return jsonify({"error": f"{field.replace('_id', '').title()} not found"}), 404
    for key, value in payload.items():
        setattr(session, key, value)
    db.session.commit()
    cache.clear()
    return session_schema.jsonify(session), 200


@service_tickets_bp.route("/<int:session_id>", methods=["DELETE"])
@roles_required("admin")
def delete_session(session_id):
    session, error = get_session_or_404(session_id)
    if error:
        return error
    db.session.delete(session)
    db.session.commit()
    cache.clear()
    return jsonify({"message": f"Session id: {session_id} deleted"}), 200
