from project import create_app, db
from project.models import User, Family, Category
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
    with app.app_context():

        db.create_all()
        app.logger.info('Database tables created')
        
        admin = User.query.filter_by(role='admin').first()
        
        if not admin:
            admin_password = 'admin123'
            admin = User(
                username='admin',
                email='admin@familybudget.com',
                role='admin',
                family_id=None
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            app.logger.info(f'Created admin user: username="admin"')
            print(f'Создан администратор: username="admin", password="{admin_password}"')
            print('Пожалуйста, измените пароль администратора в настройках!')
        else:
            app.logger.info('Admin user already exists')
            print('Администратор уже существует')
        
        print('База данных инициализирована')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)