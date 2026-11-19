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

