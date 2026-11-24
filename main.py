from app.config import settings
from flask_jwt_extended import JWTManager
from flask import Flask, jsonify
from flask_cors import CORS
from app.database import db

app = Flask(__name__)
jwt = JWTManager(app)
app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies"]
app.config["JWT_COOKIE_CSRF_PROTECT"] = False
app.config["JWT_ACCESS_COOKIE_NAME"] = "token"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///focusflow.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = settings.JWT_SECRET_KEY
app.config["JWT_ALGORITHM"] = settings.JWT_ALGORITHM
CORS(app, supports_credentials=True)
db.init_app(app)

# --- Register Flask Blueprints (SKIP github.py - it's FastAPI, will crash app) ---
from app.routers.auth import auth_bp
from app.routers.github import github_bp
from app.routers.projects import projects_bp
from app.routers.tasks import tasks_bp
from app.routers.focus import focus_bp
from app.routers.notes import notes_bp
from app.routers.analytics import analytics_bp
from app.routers.subscriptions import subscription_bp

app.register_blueprint(auth_bp)
app.register_blueprint(github_bp)
app.register_blueprint(projects_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(focus_bp)
app.register_blueprint(notes_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(subscription_bp)
with app.app_context():
   from app import models
   db.create_all()

@app.route('/')
def home():
    return {"message": "FocusFlow Backend is running!"}


@app.before_request
def _handle_cors_preflight():
    from flask import request
    if request.method == "OPTIONS":
        resp = app.make_default_options_response()
        origin = request.headers.get("Origin")
        if origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Credentials"] = "true"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        return resp

if __name__ == '__main__':
    app.run(debug=True, port=5000)
