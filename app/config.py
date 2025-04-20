import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', '.env')) # Look for .env in the project root

class Config:
    """Base configuration settings."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess' # Change this in production!

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, '..', 'ohmyphoto.db') # DB in project root
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Paths for data storage (customize these)
    # Ensure these directories exist or are created by the app
    PHOTO_LIBRARY_PATH = os.environ.get('PHOTO_LIBRARY_PATH') or os.path.join(basedir, '..', 'photo_library')
    DATA_STORAGE_PATH = os.environ.get('DATA_STORAGE_PATH') or os.path.join(basedir, '..', 'data_storage') # For thumbnails, metadata db, etc.
    THUMBNAIL_DIR = os.path.join(DATA_STORAGE_PATH, 'thumbnails')
    METADATA_DB_PATH = os.path.join(DATA_STORAGE_PATH, 'metadata.db') # Example path for metadata DB

    # Add other configuration variables as needed
    # e.g., settings for extensions, API keys, etc.

# You might add other configurations like DevelopmentConfig, TestingConfig, ProductionConfig
# class DevelopmentConfig(Config):
#     DEBUG = True
#
# class ProductionConfig(Config):
#     # Production specific settings
#     pass
