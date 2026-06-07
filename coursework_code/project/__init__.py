# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# from flask_login import LoginManager
# from config import Config
# import os

# db = SQLAlchemy()
# login_manager = LoginManager()
# login_manager.login_view = 'auth.login'  # куда перенаправлять неавторизованных
# login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'

# def create_app(config_class=Config):
#     app = Flask(__name__, template_folder='../templates', static_folder='../static')
#     app.config.from_object(config_class)
    
#     # Создаем папку для загрузки файлов, если её нет
#     if not os.path.exists(app.config['UPLOAD_FOLDER']):
#         os.makedirs(app.config['UPLOAD_FOLDER'])
    
#     db.init_app(app)
#     login_manager.init_app(app)

#     # В create_app() после инициализации добавьте:
#     @app.route('/uploads/<filename>')
#     def uploaded_file(filename):
#         from flask import send_from_directory
#         return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
#     # Регистрируем blueprint'ы
#     from project.auth import auth_bp
#     from project.admin import admin_bp
#     from project.main import main_bp
    
#     app.register_blueprint(auth_bp, url_prefix='/auth')
#     app.register_blueprint(admin_bp, url_prefix='/admin')
#     app.register_blueprint(main_bp)
    
#     return app


from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config_class)
    
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    db.init_app(app)
    login_manager.init_app(app)
    
    from project.models import User, Family, Category, Transaction, Receipt, CategoryLimit, UserBudget, DashboardStats

    from project.auth import auth_bp
    from project.admin import admin_bp
    from project.main import main_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(main_bp)
    
    # Создаем все таблицы
    with app.app_context():
        db.create_all()
    
    return app