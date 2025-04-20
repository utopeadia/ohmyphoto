from flask import Flask
from .config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login' # Route name for the login page
migrate = Migrate()

def create_app(config_class=Config):
    """Creates and configures an instance of the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions here
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints here
    from .main import bp as main_bp
    app.register_blueprint(main_bp)

    # Register auth blueprint
    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Add other app setup code here, like logging

    return app

# Import models here at the bottom to avoid circular dependencies
# This ensures models are defined before being used by migrations or routes
from . import models
