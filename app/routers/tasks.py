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