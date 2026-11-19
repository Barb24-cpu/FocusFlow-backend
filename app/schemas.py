import re
from datetime import date, timezone


class ValidationError(Exception):
    """Raised when request data is invalid. `errors` maps field -> message."""

    def __init__(self, errors):
        self.errors = errors
        self.message = next(iter(errors.values())) if errors else "Invalid data"
        super().__init__(self.message)


# --- Auth schemas ---

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

def _clean_email(value):
    return value.strip().lower() if isinstance(value, str) else ""


def validate_register(data):
    """Expects {name | username, email, password}. Returns {name, email, password}."""
    errors = {}

    name = data.get("name") or data.get("username")  # frontend uses both names
    name = name.strip() if isinstance(name, str) else ""
    if not name:
        errors["name"] = "Name is required"
    elif len(name) > 100:
        errors["name"] = "Name must be 100 characters or fewer"

    email = _clean_email(data.get("email"))
    if not email:
        errors["email"] = "Email is required"
    elif len(email) > 254 or not EMAIL_RE.match(email):
        errors["email"] = "Enter a valid email address"

    password = data.get("password")
    if not isinstance(password, str) or not password:
        errors["password"] = "Password is required"
    elif len(password) < MIN_PASSWORD_LENGTH:
        errors["password"] = f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
    elif len(password) > MAX_PASSWORD_LENGTH:
        errors["password"] = f"Password must be {MAX_PASSWORD_LENGTH} characters or fewer"

    if errors:
        raise ValidationError(errors)
    return {"name": name, "email": email, "password": password}


def validate_login(data):
    """Expects {email, password}. Returns {email, password}."""
    errors = {}
    email = _clean_email(data.get("email"))
    password = data.get("password")

    if not email:
        errors["email"] = "Email is required"
    if not isinstance(password, str) or not password:
        errors["password"] = "Password is required"

    if errors:
        raise ValidationError(errors)
    return {"email": email, "password": password}



# --- Task schemas ---

PRIORITIES = ("low", "medium", "high")
STATUSES = ("todo", "in_progress", "done")

_STATUS_ALIASES = {
    "todo": "todo",
    "to_do": "todo",
    "pending": "todo",
    "in_progress": "in_progress",
    "inprogress": "in_progress",
    "doing": "in_progress",
    "done": "done",
    "complete": "done",
    "completed": "done",
}


def normalize_status(value):
    """'To do' / 'in-progress' / 'DONE' -> 'todo' / 'in_progress' / 'done'. None if invalid."""
    if not isinstance(value, str):
        return None
    key = value.strip().lower().replace("-", "_").replace(" ", "_")
    return _STATUS_ALIASES.get(key)


def normalize_priority(value):
    """'High' -> 'high'. None if invalid."""
    if not isinstance(value, str):
        return None
    key = value.strip().lower()
    return key if key in PRIORITIES else None


def parse_due_date(value):
    """'2026-11-20' (or a full ISO timestamp) -> date. None/'' -> None. Raises ValueError."""
    if value is None or value == "":
        return None
    if not isinstance(value, str) or len(value) < 10:
        raise ValueError("bad date")
    return date.fromisoformat(value[:10])


def parse_project_id(value):
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError("bad project id")
    return int(value)


def _present(data, *names):
    """(True, value) for the first key found in data, else (False, None)."""
    for name in names:
        if name in data:
            return True, data[name]
    return False, None


def validate_task(data, partial=False):
    """
    Create: validate_task(data)                -> every field filled (with defaults)
    Update: validate_task(data, partial=True)  -> only the fields that were sent

    Accepts due_date or dueDate, project_id or projectId.
    """
    cleaned, errors = {}, {}

    found, title = _present(data, "title")
    if found or not partial:
        title = title.strip() if isinstance(title, str) else ""
        if not title:
            errors["title"] = "Title is required"
        elif len(title) > 200:
            errors["title"] = "Title must be 200 characters or fewer"
        else:
            cleaned["title"] = title