from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.database import db
from app.models import Note, Project
from app.helpers import to_iso, utc_now, error, validation_error

notes_bp = Blueprint("notes", __name__)


def note_to_dict(note):
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "project_id": note.project_id,
        "task_id": note.task_id,
        "created_at": to_iso(note.created_at),
        "updated_at": to_iso(note.updated_at),
    }


def check_project(user_id, value):
    # returns (project_id, error_text). An empty value is fine, a note
    # does not need a project.
    if value is None or value == "":
        return None, None

    try:
        project_id = int(value)
    except (TypeError, ValueError):
        return None, "Must be a number"

    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    if project is None:
        return None, "Project not found"

    return project_id, None


@notes_bp.route("", methods=["GET"])
@jwt_required()
def get_notes():
    user_id = int(get_jwt_identity())

    query = Note.query.filter_by(user_id=user_id)

    # optional: /api/notes?project_id=3
    project_id = request.args.get("project_id", type=int)
    if project_id is not None:
        query = query.filter_by(project_id=project_id)

    notes = query.order_by(Note.updated_at.desc()).all()

    return jsonify([note_to_dict(n) for n in notes]), 200


@notes_bp.route("", methods=["POST"])
@jwt_required()
def create_note():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    title = (data.get("title") or "").strip()
    content = data.get("content") or ""
    errors = {}

    # a note needs at least a title or some content
    if title == "" and content.strip() == "":
        errors["title"] = "Add a title or some content"
    if len(title) > 150:
        errors["title"] = "Maximum 150 characters"

    project_id, project_error = check_project(user_id, data.get("project_id"))
    if project_error:
        errors["project_id"] = project_error

    if errors:
        return validation_error(errors)

    note = Note(
        user_id=user_id,
        title=title or None,
        content=content,
        project_id=project_id,
    )
    db.session.add(note)
    db.session.commit()

    return jsonify(note_to_dict(note)), 201


@notes_bp.route("/<int:note_id>", methods=["PUT"])
@jwt_required()
def update_note(note_id):
    user_id = int(get_jwt_identity())

    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if note is None:
        return error("Note not found", 404)

    data = request.get_json(silent=True) or {}
    errors = {}

    title = note.title
    content = note.content
    project_id = note.project_id

    if "title" in data:
        title = (data["title"] or "").strip()
        if len(title) > 150:
            errors["title"] = "Maximum 150 characters"

    if "content" in data:
        content = data["content"] or ""

    if "project_id" in data:
        project_id, project_error = check_project(user_id, data["project_id"])
        if project_error:
            errors["project_id"] = project_error

    if (title or "") == "" and content.strip() == "":
        errors["title"] = "Add a title or some content"

    if errors:
        return validation_error(errors)

    note.title = title or None
    note.content = content
    note.project_id = project_id
    note.updated_at = utc_now()
    db.session.commit()

    return jsonify(note_to_dict(note)), 200


@notes_bp.route("/<int:note_id>", methods=["DELETE"])
@jwt_required()
def delete_note(note_id):
    user_id = int(get_jwt_identity())

    note = Note.query.filter_by(id=note_id, user_id=user_id).first()
    if note is None:
        return error("Note not found", 404)

    db.session.delete(note)
    db.session.commit()

    return jsonify({"message": "Note deleted"}), 200
