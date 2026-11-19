
from datetime import datetime, timezone
from flask import jsonify


# Small helper functions used by other files.
# These include projects.py, notes.py, focus.py and analytics.py.


def utc_now():
    # Get the current UTC time.
    # Remove the timezone information because our models save dates without it.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_iso(value):
    # Convert the date to ISO format.
    # Add Z to show JavaScript that the time is in UTC.
    if value is None:
        return None

    return value.isoformat() + "Z"


def parse_datetime(value):
    # Convert a date string into a UTC datetime.
    # Return None if the value is empty or the date is invalid.

    if not value:
        return None

    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None

    # If the date has timezone information, convert it to UTC.
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)

    return parsed


# Error responses used in section 7.2 of the project documentation.


def error(message, status):
    return jsonify({"error": message}), status


def validation_error(details):
    return jsonify({
        "error": "Validation failed",
        "details": details
    }), 400
