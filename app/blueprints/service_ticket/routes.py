from datetime import date

from flask import g, jsonify, request
from marshmallow import ValidationError

from app.extensions import cache, db
from app.csv_export import csv_response
from app.models import Lesson, Session, Student, Teacher
from app.utils.util import roles_required, token_required

from . import service_tickets_bp
from .schemas import session_schema, sessions_schema


def get_session_or_404(session_id):
    session = db.session.get(Session, session_id)
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

    if not db.session.get(Student, payload["student_id"]):
        return jsonify({"error": "Student not found"}), 404
    if not db.session.get(Teacher, payload["teacher_id"]):
        return jsonify({"error": "Teacher not found"}), 404
    if not db.session.get(Lesson, payload["lesson_id"]):
        return jsonify({"error": "Lesson not found"}), 404

    session = Session(**payload)
    db.session.add(session)
    db.session.commit()
    cache.clear()
    return session_schema.jsonify(session), 201


@service_tickets_bp.route("/", methods=["GET"])
@token_required
def get_sessions():
    query = db.select(Session)
    if g.current_user.role == "student":
        query = query.where(Session.student_id == g.current_user.student_id)
    elif g.current_user.role == "teacher":
        query = query.where(Session.teacher_id == g.current_user.teacher_id)
    elif g.current_user.role != "admin":
        return jsonify({"error": "Insufficient permissions"}), 403
    else:
        student_id = request.args.get("student_id", type=int)
        teacher_id = request.args.get("teacher_id", type=int)
        lesson_id = request.args.get("lesson_id", type=int)
        session_date = request.args.get("session_date", type=str)
        if student_id is not None:
            query = query.where(Session.student_id == student_id)
        if teacher_id is not None:
            query = query.where(Session.teacher_id == teacher_id)
        if lesson_id is not None:
            query = query.where(Session.lesson_id == lesson_id)
        if session_date:
            try:
                query = query.where(Session.session_date == date.fromisoformat(session_date))
            except ValueError:
                return jsonify({"error": "session_date must use YYYY-MM-DD format"}), 400
    return sessions_schema.jsonify(db.session.execute(query).scalars().all()), 200


@service_tickets_bp.route("/export.csv", methods=["GET"])
@token_required
def export_sessions():
    query = db.select(Session).order_by(Session.id)
    if g.current_user.role == "student":
        query = query.where(Session.student_id == g.current_user.student_id)
    elif g.current_user.role == "teacher":
        query = query.where(Session.teacher_id == g.current_user.teacher_id)
    elif g.current_user.role != "admin":
        return jsonify({"error": "Insufficient permissions"}), 403
    sessions = db.session.execute(query).scalars().all()
    rows = [
        {
            "id": session.id,
            "session_date": session.session_date.isoformat(),
            "student_id": session.student_id,
            "student_name": session.student.name,
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
    if g.current_user.role == "student" and session.student_id != g.current_user.student_id:
        return jsonify({"error": "Insufficient permissions"}), 403
    if g.current_user.role == "teacher" and session.teacher_id != g.current_user.teacher_id:
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
    for field, model in (("student_id", Student), ("teacher_id", Teacher), ("lesson_id", Lesson)):
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
