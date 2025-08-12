from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from flask_migrate import Migrate
import re



# Initialize Flask app
app = Flask(__name__,static_folder=os.path.abspath('static'))

# Set configuration variables
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///homemade_cosmetics.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Redirect to 'login' route if not authenticated
login_manager.login_message_category = 'info'  # Flash message category for login required
# Initialize Flask-Migrate
migrate = Migrate(app, db)

@login_manager.user_loader
def load_user(user_id):
    # Import User here to avoid circular import
    from app.model import User
    return User.query.get(int(user_id))

# Import routes at the end to avoid circular imports
from app import routes

def youtube_id(value):
    """
    Extracts the YouTube video ID from a URL or ID string.
    Supports various YouTube URL formats.
    """
    # If it's already an 11-character ID, return as is
    if re.match(r'^[A-Za-z0-9_-]{11}$', value):
        return value
    # Try to extract from common YouTube URL patterns
    patterns = [
        r'youtu\.be/([A-Za-z0-9_-]{11})',
        r'youtube\.com/watch\\?v=([A-Za-z0-9_-]{11})',
        r'youtube\.com/embed/([A-Za-z0-9_-]{11})',
        r'youtube\.com/v/([A-Za-z0-9_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            return match.group(1)
    # Fallback: return the original value
    return value

app.jinja_env.filters['youtube_id'] = youtube_id