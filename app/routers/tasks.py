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
