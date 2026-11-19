from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.database import db
from app.models import Project, Task, Note
from app.helpers import to_iso, error, validation_error

projects_bp = Blueprint("projects", __name__)


def project_to_dict(project):
    # the column in the database is called title, the frontend calls it name
    return {
        "id": project.id,
        "name": project.title,
        "description": project.description,
        "github_repo": project.github_repo,
        "status": project.status,
        "created_at": to_iso(project.created_at),
    }


def check_project_data(data):
    # returns a dict of errors, empty if everything is fine
    errors = {}

    name = (data.get("name") or "").strip()
    if name == "":
        errors["name"] = "Required"
    elif len(name) > 150:
        errors["name"] = "Maximum 150 characters"

    repo = (data.get("github_repo") or "").strip()
    if repo != "" and repo.count("/") != 1:
        errors["github_repo"] = "Use the format owner/repo"

    return errors


@projects_bp.route("", methods=["GET"])
@jwt_required()
def get_projects():
    user_id = int(get_jwt_identity())

    projects = (
        Project.query.filter_by(user_id=user_id)
        .order_by(Project.created_at.desc())
        .all()
    )

    return jsonify([project_to_dict(p) for p in projects]), 200


@projects_bp.route("", methods=["POST"])
@jwt_required()
def create_project():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    errors = check_project_data(data)
    if errors:
        return validation_error(errors)

    project = Project(
        user_id=user_id,
        title=data["name"].strip(),
        description=data.get("description"),
        github_repo=(data.get("github_repo") or "").strip() or None,
    )
    db.session.add(project)
    db.session.commit()

    return jsonify(project_to_dict(project)), 201


@projects_bp.route("/<int:project_id>", methods=["PUT"])
@jwt_required()
def update_project(project_id):
    user_id = int(get_jwt_identity())

    # filter by user_id too, so nobody can change another user's project
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    if project is None:
        return error("Project not found", 404)

    data = request.get_json(silent=True) or {}

    # keep the old values for anything that was not sent
    merged = {
        "name": data.get("name", project.title),
        "description": data.get("description", project.description),
        "github_repo": data.get("github_repo", project.github_repo),
    }
    errors = check_project_data(merged)
    if errors:
        return validation_error(errors)

    project.title = merged["name"].strip()
    project.description = merged["description"]
    project.github_repo = (merged["github_repo"] or "").strip() or None
    db.session.commit()

    return jsonify(project_to_dict(project)), 200


@projects_bp.route("/<int:project_id>", methods=["DELETE"])
@jwt_required()
def delete_project(project_id):
    user_id = int(get_jwt_identity())

    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    if project is None:
        return error("Project not found", 404)

    # tasks and notes can exist without a project, so we just unlink them
    Task.query.filter_by(project_id=project.id).update({"project_id": None})
    Note.query.filter_by(project_id=project.id).update({"project_id": None})

    db.session.delete(project)
    db.session.commit()

    return jsonify({"message": "Project deleted"}), 200
