from functools import wraps

from flask import g, jsonify, request

from app.models import User
from app.security import decode_access_token

COOKIE_NAME = "access_token"