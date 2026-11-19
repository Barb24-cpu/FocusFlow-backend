# TODO: Implement this file
from flask import Blueprint, jsonify, request

from app.database import db
from app.deps import current_user, error_response, login_required
from app.models import task
from app.schemas import (
    validationError,
    normalize_priority,
    task_to_dict,
    validate_task,
)

try: # projects built in; don't crash if they aren't merged yet
    from app.models import Project
except ImportError:  # pragma: no cover
    Project = None

tasks_bp = Blueprint("tasks", __name__, url_prefix="/tasks")

def _json_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _utc_now():
    """Current UTC time as a naive datetime (matches plain DateTime columns)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _get_own_task(task_id):
    return Task.query.filter_by(id=task_id, user_id=current_user().id).first()


def _owns_project(project_id):
    if Project is None:
        return False
    return Project.query.filter_by(id=project_id, user_id=current_user().id).first() is not None


def _commit():
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


@tasks_bp.get("", strict_slashes=False)
@login_required
def list_tasks():
    query = Task.query.filter_by(user_id=current_user().id)

    status = request.args.get("status")
    if status:
        normalized = normalize_status(status)
        if normalized is None:
            return error_response("Invalid status filter", 400)
        query = query.filter_by(status=normalized)

    priority = request.args.get("priority")
    if priority:
        normalized = normalize_priority(priority)
        if normalized is None:
            return error_response("Invalid priority filter", 400)
        query = query.filter_by(priority=normalized)

    project_id = request.args.get("project_id")
    if project_id:
        try:
            query = query.filter_by(project_id=int(project_id))
        except ValueError:
            return error_response("Invalid project_id filter", 400)

    search = request.args.get("search", "").strip()
    if search:
        escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        query = query.filter(
            db.or_(
                Task.title.ilike(pattern, escape="\\"),
                Task.description.ilike(pattern, escape="\\"),
            )
        )

    tasks = query.all()
    # Newest first, then (stable sort) earliest due date first with undated tasks last
    tasks.sort(key=lambda t: t.created_at or datetime.min, reverse=True)
    tasks.sort(key=lambda t: (t.due_date is None, t.due_date or date.max))

    return jsonify({"tasks": [task_to_dict(t) for t in tasks]})
