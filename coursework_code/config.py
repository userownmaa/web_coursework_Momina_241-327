import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess-this-secret-key-2026'
    
    # Пока используем SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///family_budget.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Путь для загрузки файлов (чеков)
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max limit for uploads
    
    # Настройки администратора по умолчанию
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'admin123'  # В реальном проекте нужно сменить!