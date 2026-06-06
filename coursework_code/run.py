from project import create_app, db
from project.models import User, Family
from bcrypt import hashpw, gensalt

app = create_app()

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
            print(f'Создан администратор: username="admin", password="{admin_password}"')
            print('Пожалуйста, измените пароль администратора в настройках!')
        else:
            print('Администратор уже существует')
        
        print('База данных инициализирована')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)