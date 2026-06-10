from flask import render_template, redirect, url_for, flash, request, Blueprint
from flask_login import login_user, logout_user, current_user, login_required
from project import db
from project.models import User, Family, Category
import secrets
import string
from flask import current_app

auth_bp = Blueprint('auth', __name__)

def generate_invite_code():
    alphabet = string.ascii_uppercase + string.digits
    return 'FAM-' + ''.join(secrets.choice(alphabet) for _ in range(6))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            current_app.logger.info(f'User {user.id} ({user.username}) logged in successfully')
            flash(f'Вход успешен, {user.username}!', 'success')
            
            if user.role == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
            elif user.role == 'owner':
                return redirect(url_for('main.owner_dashboard'))
            else:
                return redirect(url_for('main.member_dashboard'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')
    
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')  
        password = request.form.get('password')
        role = request.form.get('role')
        invite_code = request.form.get('invite_code')
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Пользователь с таким именем уже существует', 'danger')
            return redirect(url_for('auth.register'))
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Пользователь с таким email уже существует', 'danger')
            return redirect(url_for('auth.register'))
        
        if role == 'owner':
            new_invite_code = generate_invite_code()
            family = Family(name=f"Семья {username}", invite_code=new_invite_code)
            db.session.add(family)
            db.session.flush()
            
            user = User(username=username, email=email, role='owner', family_id=family.id)
            user.set_password(password)
            db.session.add(user)
            db.session.flush()
            
            default_categories = [
                Category(name='Продукты', type='expense', color='#dc3545', description='Покупка продуктов питания', family_id=family.id),
                Category(name='Транспорт', type='expense', color='#ffc107', description='Проезд, такси, бензин', family_id=family.id),
                Category(name='Коммунальные услуги', type='expense', color='#17a2b8', description='Квартплата, свет, вода', family_id=family.id),
                Category(name='Зарплата', type='income', color='#28a745', description='Заработная плата', family_id=family.id),
                Category(name='Подработка', type='income', color='#20c997', description='Дополнительный доход', family_id=family.id),
                Category(name='Кафе и рестораны', type='expense', color='#fd7e14', description='Обеды вне дома', family_id=family.id),
                Category(name='Развлечения', type='expense', color='#6f42c1', description='Кино, игры, хобби', family_id=family.id),
                Category(name='Одежда', type='expense', color='#e83e8c', description='Покупка одежды и обуви', family_id=family.id),
            ]
            
            for cat in default_categories:
                db.session.add(cat)
            
            db.session.commit()
            flash(f'Семья "{family.name}" создана! Ваш код приглашения: {new_invite_code}', 'success')
            
        elif role == 'member':
            if not invite_code:
                flash('Для регистрации как участник нужен код приглашения', 'danger')
                return redirect(url_for('auth.register'))
            
            family = Family.query.filter_by(invite_code=invite_code).first()
            if not family:
                flash('Неверный код приглашения', 'danger')
                return redirect(url_for('auth.register'))
            
            user = User(username=username, email=email, role='member', family_id=family.id)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash(f'Вы присоединились к семье "{family.name}"!', 'success')
        
        login_user(user)
        current_app.logger.info(f'New user registered: {user.id} ({user.username}) with role {user.role}')
        flash('Регистрация успешно завершена!', 'success')
        
        if user.role == 'owner':
            return redirect(url_for('main.owner_dashboard'))
        else:
            return redirect(url_for('main.member_dashboard'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    current_app.logger.info(f'User logged out')
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('auth.login'))