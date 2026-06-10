import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'my-most-secret-key-346381'
    
    DB_USER = os.environ.get('DB_USER', 'family_budget_user')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'web-coursework2026')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'family_budget_db')
    
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # SQLite (для отладки)
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///family_budget.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Путь для загрузки файлов
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'admin123'