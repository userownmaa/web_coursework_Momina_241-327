from flask import render_template, Blueprint, flash, redirect, url_for, request, jsonify, Response
from flask_login import login_required, current_user
from project import db
from project.models import User, Family, Transaction, Receipt
from datetime import datetime
import os
import json
import sqlite3
from werkzeug.utils import secure_filename

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

# @admin_bp.route('/view_all_transactions')
# @login_required
# def view_all_transactions():
#     if current_user.role != 'admin':
#         flash('Доступ запрещен', 'danger')
#         return redirect(url_for('main.index'))
    
#     transactions = Transaction.query.order_by(Transaction.date.desc()).all()
#     return render_template('admin/all_transactions.html', transactions=transactions)

@admin_bp.route('/view_all_transactions')
@login_required
def view_all_transactions():
    if current_user.role != 'admin':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('main.index'))
    
    # Получаем ВСЕ транзакции из базы
    transactions = Transaction.query.order_by(Transaction.date.desc()).all()
    
    # Получаем всех пользователей для фильтра
    users = User.query.all()
    
    # Получаем все категории
    categories = Category.query.all()
    
    return render_template('admin/all_transactions.html',
                         transactions=transactions,
                         users=users,
                         categories=categories,
                         user=current_user)

@admin_bp.route('/view_all_files')
@login_required
def view_all_files():
    if current_user.role != 'admin':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('main.index'))
    
    receipts = Receipt.query.all()
    return render_template('admin/all_files.html', receipts=receipts)

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
        transaction = receipt.transaction
        
        if os.path.exists(receipt.filepath):
            os.remove(receipt.filepath)
        
        db.session.delete(receipt)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Чек удален'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/get_user/<int:id>')
@login_required
def get_user(id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    user = User.query.get_or_404(id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'family_name': user.family.name if user.family else None
    })

@admin_bp.route('/api/reset_password/<int:id>', methods=['POST'])
@login_required
def reset_password(id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    data = request.get_json()
    new_password = data.get('password')
    
    if not new_password or len(new_password) < 4:
        return jsonify({'success': False, 'message': 'Пароль должен содержать минимум 4 символа'}), 400
    
    user = User.query.get_or_404(id)
    user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Пароль изменен'})

@admin_bp.route('/api/delete_user/<int:id>', methods=['POST'])
@login_required
def delete_user(id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    user = User.query.get_or_404(id)
    
    # Нельзя удалить самого себя
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Нельзя удалить самого себя'}), 400
    
    # Удаляем транзакции и чеки
    for transaction in user.transactions:
        if transaction.receipt:
            if os.path.exists(transaction.receipt.filepath):
                os.remove(transaction.receipt.filepath)
            db.session.delete(transaction.receipt)
        db.session.delete(transaction)
    
    # Удаляем бюджеты
    for budget in user.user_budgets:
        db.session.delete(budget)
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Пользователь удален'})

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
    
    user = User(username=username, email=email, role=role)
    if family_id and role != 'owner':
        user.family_id = int(family_id)
    
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    flash(f'Пользователь {username} создан', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/api/backup', methods=['POST'])
@login_required
def backup():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    try:
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.db')
        
        # Копируем базу данных
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'family_budget.db')
        
        import shutil
        shutil.copy2(db_path, backup_file)
        
        return jsonify({'success': True, 'filename': f'backup_{timestamp}.db'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/restore', methods=['POST'])
@login_required
def restore():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    data = request.get_json()
    filename = data.get('filename')
    
    if not filename:
        return jsonify({'success': False, 'message': 'Не указан файл'}), 400
    
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
    backup_file = os.path.join(backup_dir, filename)
    
    if not os.path.exists(backup_file):
        return jsonify({'success': False, 'message': 'Файл не найден'}), 404
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'family_budget.db')
    
    import shutil
    shutil.copy2(backup_file, db_path)
    
    return jsonify({'success': True, 'message': 'База данных восстановлена'})

@admin_bp.route('/api/cleanup_files', methods=['POST'])
@login_required
def cleanup_files():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    try:
        upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
        if not os.path.exists(upload_dir):
            return jsonify({'success': True, 'deleted': 0})
        
        # Получаем все файлы, привязанные к транзакциям
        used_files = set()
        receipts = Receipt.query.all()
        for receipt in receipts:
            if receipt.filepath and os.path.exists(receipt.filepath):
                used_files.add(os.path.basename(receipt.filepath))
        
        # Удаляем неиспользуемые файлы
        deleted = 0
        for filename in os.listdir(upload_dir):
            if filename not in used_files:
                filepath = os.path.join(upload_dir, filename)
                try:
                    os.remove(filepath)
                    deleted += 1
                except:
                    pass
        
        return jsonify({'success': True, 'deleted': deleted})
    except Exception as e:
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