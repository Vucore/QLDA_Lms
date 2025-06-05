import os
import logging
from flask import Flask
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix
from extensions import db

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure upload folder
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max file size
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'courses')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///lms.db"
)
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database with app
db.init_app(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

# Import routes
from routes import *

# Import models and create tables
with app.app_context():
    import models
    db.create_all()

# Load user from session
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))