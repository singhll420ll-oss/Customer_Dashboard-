"""
Application Configuration
"""
import os

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Secret key
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 
    f'sqlite:///{os.path.join(BASE_DIR, "bitebuddy.db")}')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Upload settings
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# Create upload folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
