from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    # Add other user fields as needed, e.g., registration date, last login
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(id):
    """User loader callback used by Flask-Login."""
    return User.query.get(int(id))

# --- Photo Model ---

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    # Store path relative to the configured PHOTO_LIBRARY_PATH
    relative_path = db.Column(db.String(1024), nullable=False, index=True, unique=True)
    # Extracted timestamp (from EXIF or file system) for timeline sorting
    timestamp = db.Column(db.DateTime, index=True)
    # Store basic metadata extracted during scan
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    filesize = db.Column(db.Integer) # In bytes
    # Store hash to detect duplicates?
    file_hash = db.Column(db.String(64), index=True, unique=True, nullable=True) # e.g., SHA256
    # Store thumbnail status/path? (or derive from ID/hash)
    thumbnail_generated = db.Column(db.Boolean, default=False)
    # Foreign key to user if photos are user-specific (optional for now)
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # user = db.relationship('User', backref=db.backref('photos', lazy=True))
    # Store raw EXIF data (consider JSON type if DB supports it)
    exif_data = db.Column(db.Text)
    # Fields for search/classification (to be added later)
    # description = db.Column(db.Text)
    # ocr_text = db.Column(db.Text)
    # scene_tags = db.Column(db.Text) # Or use a separate Tag model

    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Photo {self.filename} ({self.relative_path})>'

# Define other models here later (e.g., Album, Tag, Face)
