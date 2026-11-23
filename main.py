from flask_jwt_extended import JWTManager
from flask import Flask, jsonify
from flask_cors import CORS
from app.database import db

app = Flask(__name__)
jwt = JWTManager(app)
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///focusflow.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "focusflow-secret"
CORS(app, supports_credentials=True)
db.init_app(app)

# --- Register Flask Blueprints (SKIP github.py - it's FastAPI, will crash app) ---
from app.routers.auth import auth_bp
from app.routers.projects import projects_bp
from app.routers.tasks import tasks_bp
from app.routers.focus import focus_bp
from app.routers.notes import notes_bp
from app.routers.analytics import analytics_bp
from app.routers.subscriptions import subscription_bp

app.register_blueprint(auth_bp)
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
