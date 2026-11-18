from flask import Flask
from models import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///focusflow.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'focusflow-secret'

db.init_app(app)

@app.route('/')
def home():
    return {"message": "FocusFlow Backend is running!"}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database created!")
    app.run(debug=True)
