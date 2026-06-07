from project import create_app, db
from project.models import User, Family
from bcrypt import hashpw, gensalt
import logging
from logging.handlers import RotatingFileHandler
import os

app = create_app()

# Настройка логирования
if not os.path.exists('logs'):
    os.mkdir('logs')

file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)

app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Application startup')

def init_db():
    """Инициализация базы данных и создание администратора по умолчанию"""
    with app.app_context():
        # Создаем все таблицы
        db.create_all()
        
        # Проверяем, есть ли уже администратор
        admin = User.query.filter_by(role='admin').first()
        
        if not admin:
            # Создаем администратора по умолчанию
            admin_password = 'admin123'  # В реальном проекте смени!
            admin = User(
                username='admin',
                email='admin@familybudget.com',
                role='admin',
                family_id=None
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            app.logger.info(f'Создан администратор: username="admin"')
            print(f'Создан администратор: username="admin", password="{admin_password}"')
            print('Пожалуйста, измените пароль администратора в настройках!')
        else:
            app.logger.info('Администратор уже существует')
            print('Администратор уже существует')
        
        print('База данных инициализирована')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)