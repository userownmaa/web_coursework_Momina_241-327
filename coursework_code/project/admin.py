from flask import render_template, Blueprint, flash, redirect, url_for, request, jsonify, Response
from flask_login import login_required, current_user
from project import db
from project.models import User, Family, Transaction, Receipt, Category, DashboardStats
from datetime import datetime
import os
import subprocess

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('У вас нет доступа к административной панели', 'danger')
        return redirect(url_for('main.index'))
    
    users = User.query.all()
    families = Family.query.all()
    return render_template('dashboard/admin_dashboard.html', users=users, families=families)

@admin_bp.route('/view_all_transactions')
@login_required
def view_all_transactions():
    if current_user.role != 'admin':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('main.index'))
    
    search = request.args.get('search', '')
    user_id = request.args.get('user_id', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = Transaction.query
    
    if search:
        query = query.filter(Transaction.description.contains(search))
    
    if user_id:
        query = query.filter(Transaction.user_id == int(user_id))
    
    if date_from:
        query = query.filter(Transaction.date >= datetime.strptime(date_from, '%Y-%m-%d'))
    
    if date_to:
        query = query.filter(Transaction.date <= datetime.strptime(date_to, '%Y-%m-%d'))
    
    transactions = query.order_by(Transaction.date.desc()).all()
    users = User.query.all()
    categories = Category.query.all()
    
    return render_template('admin/all_transactions.html',
                         transactions=transactions,
                         users=users,
                         categories=categories,
                         user=current_user,
                         search=search,
                         user_id=user_id,
                         date_from=date_from,
                         date_to=date_to)

@admin_bp.route('/view_all_files')
@login_required
def view_all_files():
    if current_user.role != 'admin':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('main.index'))
    
    receipts = Receipt.query.all()
    return render_template('admin/all_files.html', receipts=receipts)


@admin_bp.route('/api/get_user/<int:id>')
@login_required
def api_get_user(id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    user = User.query.get_or_404(id)
    user_budget = user.user_budgets[0] if user.user_budgets else None
    
    return jsonify({
        'success': True,
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'family_name': user.family.name if user.family else '—',
        'budget': float(user_budget.amount_limit) if user_budget else 0,
        'budget_period': user_budget.period if user_budget else 'month'
    })


@admin_bp.route('/api/reset_password/<int:id>', methods=['POST'])
@login_required
def api_reset_password(id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    data = request.get_json()
    new_password = data.get('password')
    
    if not new_password or len(new_password) < 4:
        return jsonify({'success': False, 'message': 'Пароль должен содержать минимум 4 символа'}), 400
    
    user = User.query.get_or_404(id)
    user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Пароль для {user.username} успешно изменен'})


@admin_bp.route('/api/delete_user/<int:id>', methods=['POST'])
@login_required
def api_delete_user(id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    user = User.query.get_or_404(id)
    
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Нельзя удалить самого себя'}), 400
    
    username = user.username
    
    for transaction in user.transactions:
        if transaction.receipt:
            if os.path.exists(transaction.receipt.filepath):
                os.remove(transaction.receipt.filepath)
            db.session.delete(transaction.receipt)
        db.session.delete(transaction)
    
    for budget in user.user_budgets:
        db.session.delete(budget)
    
    stats = DashboardStats.query.filter_by(user_id=user.id).first()
    if stats:
        db.session.delete(stats)
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Пользователь {username} удален'})


@admin_bp.route('/add_user', methods=['POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('admin.admin_dashboard'))
    
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')
    family_id = request.form.get('family_id')
    
    if User.query.filter_by(username=username).first():
        flash('Пользователь с таким логином уже существует', 'danger')
        return redirect(url_for('admin.admin_dashboard'))
    
    if User.query.filter_by(email=email).first():
        flash('Пользователь с таким email уже существует', 'danger')
        return redirect(url_for('admin.admin_dashboard'))
    
    user = None
    
    if role == 'owner':
        new_invite_code = generate_invite_code()
        family = Family(name=f"Семья {username}", invite_code=new_invite_code)
        db.session.add(family)
        db.session.flush()
        
        user = User(username=username, email=email, role='owner', family_id=family.id)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash(f'Создан владелец "{username}" с новой семьей "{family.name}". Код приглашения: {new_invite_code}', 'success')
        
    elif role == 'member':
        if not family_id:
            flash('Для создания участника необходимо выбрать семью', 'danger')
            return redirect(url_for('admin.admin_dashboard'))
        
        family = Family.query.get(family_id)
        if not family:
            flash('Выбранная семья не найдена', 'danger')
            return redirect(url_for('admin.admin_dashboard'))
        
        user = User(username=username, email=email, role='member', family_id=family.id)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash(f'Создан участник "{username}" в семье "{family.name}"', 'success')
    
    return redirect(url_for('admin.admin_dashboard'))

def generate_invite_code():
    import secrets
    import string
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = 'FAM-' + ''.join(secrets.choice(alphabet) for _ in range(6))
        if not Family.query.filter_by(invite_code=code).first():
            return code


@admin_bp.route('/api/backup', methods=['POST'])
@login_required
def api_backup():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    try:
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.sql')
        
        from config import Config
        db_user = Config.DB_USER
        db_password = Config.DB_PASSWORD
        db_host = Config.DB_HOST
        db_port = Config.DB_PORT
        db_name = Config.DB_NAME
        
        cmd = f'PGPASSWORD={db_password} pg_dump -h {db_host} -p {db_port} -U {db_user} -d {db_name} -f {backup_file}'
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({'success': True, 'filename': f'backup_{timestamp}.sql'})
        else:
            return jsonify({'success': False, 'message': f'Ошибка: {result.stderr}'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/api/get_receipt/<int:id>')
@login_required
def api_get_receipt(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    receipt = Receipt.query.get_or_404(id)
    return jsonify({'url': url_for('main.uploaded_file', filename=os.path.basename(receipt.filepath))})


@admin_bp.route('/api/delete_transaction/<int:id>', methods=['POST'])
@login_required
def api_delete_transaction(id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    try:
        transaction = Transaction.query.get_or_404(id)
        
        if transaction.receipt:
            if os.path.exists(transaction.receipt.filepath):
                os.remove(transaction.receipt.filepath)
            db.session.delete(transaction.receipt)
        
        db.session.delete(transaction)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Транзакция удалена'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/api/delete_receipt/<int:id>', methods=['POST'])
@login_required
def api_delete_receipt(id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    try:
        receipt = Receipt.query.get_or_404(id)
        
        if os.path.exists(receipt.filepath):
            os.remove(receipt.filepath)
        
        db.session.delete(receipt)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Чек удален'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_bp.route('/logs')
@login_required
def view_logs():
    if current_user.role != 'admin':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('main.index'))
    
    log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'app.log')
    
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            logs = f.read()
    else:
        logs = "Лог-файл не найден"
    
    return Response(logs, mimetype='text/plain')


@admin_bp.route('/files')
@login_required
def view_files():
    if current_user.role != 'admin':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('main.index'))
    
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    files = []
    
    if os.path.exists(upload_dir):
        for filename in os.listdir(upload_dir):
            filepath = os.path.join(upload_dir, filename)
            files.append({
                'name': filename,
                'size': os.path.getsize(filepath),
                'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
            })
    
    return render_template('admin/files_list.html', files=files)