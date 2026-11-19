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
