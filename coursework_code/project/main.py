from flask import render_template, Blueprint, flash, redirect, url_for, request, jsonify
from flask import current_app
from flask_login import login_required, current_user
from project import db
from project.models import User, Family, Category, Transaction, Receipt
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import secrets
import string
from datetime import datetime, date, timedelta

main_bp = Blueprint('main', __name__)

def generate_invite_code():
    """Генерация уникального кода приглашения"""
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = 'FAM-' + ''.join(secrets.choice(alphabet) for _ in range(6))
        if not Family.query.filter_by(invite_code=code).first():
            return code

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.admin_dashboard'))
        elif current_user.role == 'owner':
            return redirect(url_for('main.owner_dashboard'))
        else:
            return redirect(url_for('main.member_dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
    return render_template('dashboard/admin_dashboard.html')


# @main_bp.route('/dashboard/owner')
# @login_required
# def owner_dashboard():
#     if current_user.role != 'owner':
#         flash('Доступ запрещен', 'danger')
#         return redirect(url_for('main.index'))
    
#     period = request.args.get('period', 'month')
    
#     # Получаем данные текущего пользователя
#     total_income = current_user.get_total_income(period)
#     total_expense = current_user.get_total_expense(period)
#     balance = current_user.get_balance(period)
    
#     # Получаем бюджет пользователя
#     user_budget = current_user.user_budgets[0] if current_user.user_budgets else None
#     budget_amount = float(user_budget.amount_limit) if user_budget else 0
    
#     # 1. Расходы по категориям для круговой диаграммы
#     expense_by_category = {}
#     if current_user.family:
#         # Получаем все транзакции семьи за период
#         family_member_ids = [user.id for user in current_user.family.users]
#         query = Transaction.query.filter(
#             Transaction.user_id.in_(family_member_ids),
#             Transaction.amount < 0  # Только расходы
#         )
        
#         # Фильтр по периоду
#         now = datetime.utcnow()
#         if period == 'day':
#             start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
#             query = query.filter(Transaction.date >= start_date)
#         elif period == 'week':
#             start_date = now - timedelta(days=now.weekday())
#             start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
#             query = query.filter(Transaction.date >= start_date)
#         elif period == 'month':
#             start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
#             query = query.filter(Transaction.date >= start_date)
#         elif period == 'year':
#             start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
#             query = query.filter(Transaction.date >= start_date)
        
#         transactions = query.all()
        
#         # Группируем по категориям
#         for transaction in transactions:
#             category_name = transaction.category.name
#             amount = abs(float(transaction.amount))
#             expense_by_category[category_name] = expense_by_category.get(category_name, 0) + amount
    
#     # Подготовка данных для круговой диаграммы
#     expense_categories = list(expense_by_category.keys())
#     expense_amounts = list(expense_by_category.values())
    
#     # 2. Динамика бюджета за период
#     budget_timeline = []
#     if current_user.family:
#         family_member_ids = [user.id for user in current_user.family.users]
        
#         # Определяем интервалы для группировки
#         if period == 'day':
#             # По часам
#             intervals = 24
#             date_format = '%H:00'
#             date_range = [(datetime.now().replace(hour=i, minute=0, second=0), 
#                           datetime.now().replace(hour=i+1, minute=0, second=0)) for i in range(24)]
#         elif period == 'week':
#             # По дням недели
#             intervals = 7
#             date_format = '%a'
#             start_of_week = datetime.now() - timedelta(days=datetime.now().weekday())
#             date_range = [(start_of_week + timedelta(days=i), 
#                           start_of_week + timedelta(days=i+1)) for i in range(7)]
#         elif period == 'month':
#             # По дням месяца
#             days_in_month = (datetime.now().replace(day=28) + timedelta(days=4)).day
#             intervals = days_in_month
#             date_format = '%d.%m'
#             start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)
#             date_range = [(start_of_month + timedelta(days=i), 
#                           start_of_month + timedelta(days=i+1)) for i in range(days_in_month)]
#         else:  # year
#             # По месяцам
#             intervals = 12
#             date_format = '%b'
#             start_of_year = datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0)
#             date_range = [(start_of_year.replace(month=i+1, day=1),
#                           (start_of_year.replace(month=i+2, day=1) if i < 11 else start_of_year.replace(year=start_of_year.year+1, month=1, day=1))) 
#                          for i in range(12)]
        
#         budget_labels = []
#         budget_income_data = []
#         budget_expense_data = []
#         budget_balance_data = []
        
#         for start_dt, end_dt in date_range:
#             # Получаем транзакции за интервал
#             interval_transactions = Transaction.query.filter(
#                 Transaction.user_id.in_(family_member_ids),
#                 Transaction.date >= start_dt,
#                 Transaction.date < end_dt
#             ).all()
            
#             income_sum = sum(float(t.amount) for t in interval_transactions if t.amount > 0)
#             expense_sum = sum(abs(float(t.amount)) for t in interval_transactions if t.amount < 0)
            
#             if period == 'day':
#                 label = start_dt.strftime(date_format)
#             elif period == 'week':
#                 label = start_dt.strftime(date_format)
#             elif period == 'month':
#                 label = start_dt.strftime(date_format)
#             else:
#                 label = start_dt.strftime(date_format)
            
#             budget_labels.append(label)
#             budget_income_data.append(income_sum)
#             budget_expense_data.append(expense_sum)
#             budget_balance_data.append(income_sum - expense_sum)
    
#     # 3. Сводная таблица по участникам
#     family_members_data = []
#     if current_user.family:
#         for member in current_user.family.users:
#             member_income = member.get_total_income(period)
#             member_expense = member.get_total_expense(period)
#             member_balance = member.get_balance(period)
#             member_budget = member.user_budgets[0] if member.user_budgets else None
#             member_budget_amount = float(member_budget.amount_limit) if member_budget else 0
            
#             family_members_data.append({
#                 'id': member.id,
#                 'username': member.username,
#                 'role': member.role,
#                 'income_amount': member_income,
#                 'expense_amount': member_expense,
#                 'balance': member_balance,
#                 'budget_limit': member_budget_amount
#             })
    
#     # Получаем последние транзакции
#     recent_transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).limit(5).all()
    
#     return render_template('dashboard/owner_dashboard.html',
#                          user=current_user,
#                          period=period,
#                          total_income=float(total_income) if total_income else 0,
#                          total_expense=float(total_expense) if total_expense else 0,
#                          balance=float(balance) if balance else 0,
#                          user_budget=budget_amount,
#                          expense_categories=expense_categories,
#                          expense_amounts=expense_amounts,
#                          budget_labels=budget_labels if 'budget_labels' in locals() else [],
#                          budget_income_data=budget_income_data if 'budget_income_data' in locals() else [],
#                          budget_expense_data=budget_expense_data if 'budget_expense_data' in locals() else [],
#                          budget_balance_data=budget_balance_data if 'budget_balance_data' in locals() else [],
#                          family_members=family_members_data,
#                          recent_transactions=recent_transactions)

@main_bp.route('/dashboard/owner')
@login_required
def owner_dashboard():
    if current_user.role != 'owner':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('main.index'))
    
    period = request.args.get('period', 'month')
    
    # Получаем данные текущего пользователя и конвертируем в float
    total_income = float(current_user.get_total_income(period) or 0)
    total_expense = float(abs(current_user.get_total_expense(period)) or 0)
    
    # Получаем бюджет пользователя
    user_budget = current_user.user_budgets[0] if current_user.user_budgets else None
    budget_amount = float(user_budget.amount_limit) if user_budget else 0.0
    
    # Остаток = бюджет - расходы
    balance = budget_amount - total_expense
    
    # 1. Расходы по категориям для круговой диаграммы
    expense_by_category = {}
    if current_user.family:
        family_member_ids = [user.id for user in current_user.family.users]
        query = Transaction.query.filter(
            Transaction.user_id.in_(family_member_ids),
            Transaction.amount < 0
        )
        
        now = datetime.utcnow()
        if period == 'day':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            query = query.filter(Transaction.date >= start_date, Transaction.date <= end_date)
        elif period == 'week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
            query = query.filter(Transaction.date >= start_date, Transaction.date <= end_date)
        elif period == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                end_date = now.replace(year=now.year+1, month=1, day=1) - timedelta(seconds=1)
            else:
                end_date = now.replace(month=now.month+1, day=1) - timedelta(seconds=1)
            query = query.filter(Transaction.date >= start_date, Transaction.date <= end_date)
        
        transactions = query.all()
        
        for transaction in transactions:
            category_name = transaction.category.name
            amount = float(abs(transaction.amount))
            expense_by_category[category_name] = expense_by_category.get(category_name, 0.0) + amount
    
    expense_categories = list(expense_by_category.keys())
    expense_amounts = list(expense_by_category.values())
    
    # 2. Динамика баланса за период
    budget_labels = []
    budget_balance_data = []
    
    if current_user.family:
        family_member_ids = [user.id for user in current_user.family.users]
        now = datetime.utcnow()
        
        if period == 'day':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            date_range = []
            for i in range(24):
                hour_start = start_date.replace(hour=i)
                hour_end = hour_start.replace(hour=i+1) if i < 23 else hour_start.replace(hour=23, minute=59, second=59)
                date_range.append((hour_start, hour_end))
            date_format = '%H:00'
            
        elif period == 'week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            date_range = []
            for i in range(7):
                day_start = start_date + timedelta(days=i)
                day_end = day_start.replace(hour=23, minute=59, second=59)
                date_range.append((day_start, day_end))
            date_format = '%d.%m'
            
        else:  # month
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                end_date = now.replace(year=now.year+1, month=1, day=1) - timedelta(seconds=1)
            else:
                end_date = now.replace(month=now.month+1, day=1) - timedelta(seconds=1)
            
            days_in_month = end_date.day
            date_range = []
            for i in range(days_in_month):
                day_start = start_date + timedelta(days=i)
                day_end = day_start.replace(hour=23, minute=59, second=59)
                date_range.append((day_start, day_end))
            date_format = '%d.%m'
        
        running_balance = 0.0
        for start_dt, end_dt in date_range:
            interval_transactions = Transaction.query.filter(
                Transaction.user_id.in_(family_member_ids),
                Transaction.date >= start_dt,
                Transaction.date <= end_dt
            ).all()
            
            income_sum = sum(float(t.amount) for t in interval_transactions if t.amount > 0)
            expense_sum = sum(float(abs(t.amount)) for t in interval_transactions if t.amount < 0)
            running_balance += (income_sum - expense_sum)
            
            budget_labels.append(start_dt.strftime(date_format))
            budget_balance_data.append(running_balance)
    
    # 3. Сводная таблица по участникам
    family_members_data = []
    if current_user.family:
        for member in current_user.family.users:
            member_income = float(member.get_total_income(period) or 0)
            member_expense = float(abs(member.get_total_expense(period)) or 0)
            member_balance = member_income - member_expense
            
            family_members_data.append({
                'id': member.id,
                'username': member.username,
                'role': member.role,
                'income_amount': member_income,
                'expense_amount': member_expense,
                'balance': member_balance
            })
    
    # Получаем последние транзакции
    recent_transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).limit(5).all()
    
    return render_template('dashboard/owner_dashboard.html',
                         user=current_user,
                         period=period,
                         total_income=total_income,
                         total_expense=total_expense,
                         balance=balance,
                         user_budget=budget_amount,
                         expense_categories=expense_categories,
                         expense_amounts=expense_amounts,
                         budget_labels=budget_labels,
                         budget_balance_data=budget_balance_data,
                         family_members=family_members_data,
                         recent_transactions=recent_transactions)


@main_bp.route('/dashboard/member')
@login_required
def member_dashboard():
    if current_user.role != 'member':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('main.index'))
    
    period = request.args.get('period', 'month')
    
    total_income = current_user.get_total_income(period)
    total_expense = current_user.get_total_expense(period)
    balance = current_user.get_balance(period)
    
    # Получаем бюджет участника
    user_budget = current_user.user_budgets[0] if current_user.user_budgets else None
    budget_amount = user_budget.amount_limit if user_budget else 0
    
    # Получаем категории семьи
    categories = Category.query.filter_by(family_id=current_user.family_id).all()
    
    return render_template('dashboard/member_dashboard.html',
                         user=current_user,
                         period=period,
                         total_income=total_income,
                         total_expense=total_expense,
                         balance=balance,
                         budget_amount=budget_amount,
                         categories=categories)


# @main_bp.route('/transactions', methods=['GET'])
# @login_required
# def transactions():
#     # Получаем параметры фильтрации
#     search_term = request.args.get('search', '')
#     date_from = request.args.get('date_from', '')
#     date_to = request.args.get('date_to', '')
    
#     # Базовый запрос
#     if current_user.role == 'owner' and current_user.family:
#         family_member_ids = [user.id for user in current_user.family.users]
#         query = Transaction.query.filter(Transaction.user_id.in_(family_member_ids))
#     else:
#         query = Transaction.query.filter_by(user_id=current_user.id)
    
#     # Применяем фильтры
#     if search_term:
#         query = query.filter(Transaction.description.contains(search_term))
    
#     if date_from:
#         query = query.filter(Transaction.date >= datetime.strptime(date_from, '%Y-%m-%d'))
    
#     if date_to:
#         query = query.filter(Transaction.date <= datetime.strptime(date_to, '%Y-%m-%d'))
    
#     transactions_list = query.order_by(Transaction.date.desc()).all()
    
#     # Получаем участников семьи и категории
#     family_members = current_user.family.users if current_user.family and current_user.role == 'owner' else []
#     categories = Category.query.filter_by(family_id=current_user.family_id).all() if current_user.family else []
    
#     return render_template('transactions.html',
#                          transactions=transactions_list,
#                          family_members=family_members,
#                          categories=categories,
#                          current_user=current_user,
#                          search_term=search_term,
#                          date_from=date_from,
#                          date_to=date_to,
#                          user=current_user)

@main_bp.route('/transactions', methods=['GET'])
@login_required
def transactions():
    # Получаем параметры фильтрации
    search_term = request.args.get('search', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Базовый запрос
    if current_user.role == 'owner' and current_user.family:
        family_member_ids = [user.id for user in current_user.family.users]
        query = Transaction.query.filter(Transaction.user_id.in_(family_member_ids))
    else:
        query = Transaction.query.filter_by(user_id=current_user.id)
    
    # Применяем фильтры (включительно)
    if search_term:
        query = query.filter(Transaction.description.contains(search_term))
    
    if date_from:
        query = query.filter(Transaction.date >= datetime.strptime(date_from, '%Y-%m-%d'))
    
    if date_to:
        query = query.filter(Transaction.date <= datetime.strptime(date_to, '%Y-%m-%d'))
    
    transactions_list = query.order_by(Transaction.date.desc()).all()
    
    # Получаем участников семьи и категории
    family_members = current_user.family.users if current_user.family and current_user.role == 'owner' else []
    categories = Category.query.filter_by(family_id=current_user.family_id).all() if current_user.family else []
    
    return render_template('transactions.html',
                         transactions=transactions_list,
                         family_members=family_members,
                         categories=categories,
                         current_user=current_user,
                         search_term=search_term,
                         date_from=date_from,
                         date_to=date_to,
                         user=current_user,
                         today=date.today().isoformat())


@main_bp.route('/api/get_receipt/<int:id>')
@login_required
def get_receipt(id):
    """Получение чека для просмотра"""
    receipt = Receipt.query.get_or_404(id)
    transaction = receipt.transaction
    
    # Проверка прав
    if transaction.user_id != current_user.id and current_user.role not in ['owner', 'admin']:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    return jsonify({'url': f'/uploads/{os.path.basename(receipt.filepath)}'})

# @main_bp.route('/add_transaction', methods=['POST'])
# @login_required
# def add_transaction():
#     try:
#         description = request.form.get('description')
#         date_str = request.form.get('date')
#         amount = float(request.form.get('amount'))
#         category_id = int(request.form.get('category_id'))
#         user_id = int(request.form.get('user_id'))
        
#         # Проверка прав: только владелец может добавлять транзакции для других
#         if user_id != current_user.id and current_user.role != 'owner':
#             flash('У вас нет прав на добавление транзакций для других пользователей', 'danger')
#             return redirect(url_for('main.transactions'))
        
#         transaction = Transaction(
#             description=description,
#             date=datetime.strptime(date_str, '%Y-%m-%d'),
#             amount=amount,
#             category_id=category_id,
#             user_id=user_id
#         )
        
#         db.session.add(transaction)
#         db.session.flush()
        
#         # Обработка файла чека
#         if 'receipt' in request.files:
#             file = request.files['receipt']
#             if file and file.filename:
#                 filename = secure_filename(f"{transaction.id}_{file.filename}")
#                 filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
#                 file.save(filepath)
                
#                 receipt = Receipt(
#                     transaction_id=transaction.id,
#                     filename=file.filename,
#                     filepath=filepath
#                 )
#                 db.session.add(receipt)
        
#         db.session.commit()
#         flash('Транзакция успешно добавлена', 'success')
        
#     except Exception as e:
#         db.session.rollback()
#         flash(f'Ошибка при добавлении транзакции: {str(e)}', 'danger')
    
#     return redirect(url_for('main.transactions'))

# @main_bp.route('/edit_transaction', methods=['POST'])
# @login_required
# def edit_transaction():
#     try:
#         transaction_id = int(request.form.get('transaction_id'))
#         transaction = Transaction.query.get_or_404(transaction_id)
        
#         # Проверка прав
#         if transaction.user_id != current_user.id and current_user.role != 'owner':
#             flash('У вас нет прав на редактирование этой транзакции', 'danger')
#             return redirect(url_for('main.transactions'))
        
#         transaction.description = request.form.get('description')
#         transaction.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
#         transaction.amount = float(request.form.get('amount'))
#         transaction.category_id = int(request.form.get('category_id'))
#         transaction.user_id = int(request.form.get('user_id'))
        
#         # Обработка нового чека
#         if 'receipt' in request.files:
#             file = request.files['receipt']
#             if file and file.filename:
#                 # Удаляем старый чек если есть
#                 if transaction.receipt:
#                     if os.path.exists(transaction.receipt.filepath):
#                         os.remove(transaction.receipt.filepath)
#                     db.session.delete(transaction.receipt)
                
#                 filename = secure_filename(f"{transaction.id}_{file.filename}")
#                 filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
#                 file.save(filepath)
                
#                 receipt = Receipt(
#                     transaction_id=transaction.id,
#                     filename=file.filename,
#                     filepath=filepath
#                 )
#                 db.session.add(receipt)
        
#         db.session.commit()
#         flash('Транзакция успешно обновлена', 'success')
        
#     except Exception as e:
#         db.session.rollback()
#         flash(f'Ошибка при редактировании: {str(e)}', 'danger')
    
#     return redirect(url_for('main.transactions'))

@main_bp.route('/add_transaction', methods=['POST'])
@login_required
def add_transaction():
    try:
        description = request.form.get('description')
        date_str = request.form.get('date')
        amount = abs(float(request.form.get('amount')))  # Всегда положительное число
        category_id = int(request.form.get('category_id'))
        user_id = int(request.form.get('user_id'))
        
        # Получаем категорию, чтобы определить тип транзакции
        category = Category.query.get(category_id)
        if not category:
            flash('Категория не найдена', 'danger')
            return redirect(url_for('main.transactions'))
        
        # Для расходов делаем сумму отрицательной
        if category.type == 'expense':
            amount = -amount
        
        # Проверка прав
        if user_id != current_user.id and current_user.role != 'owner':
            flash('У вас нет прав на добавление транзакций для других пользователей', 'danger')
            return redirect(url_for('main.transactions'))
        
        transaction = Transaction(
            description=description,
            date=datetime.strptime(date_str, '%Y-%m-%d'),
            amount=amount,
            category_id=category_id,
            user_id=user_id
        )
        
        db.session.add(transaction)
        db.session.flush()
        
        # Обработка файла чека
        if 'receipt' in request.files:
            file = request.files['receipt']
            if file and file.filename:
                filename = secure_filename(f"{transaction.id}_{file.filename}")
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                receipt = Receipt(
                    transaction_id=transaction.id,
                    filename=file.filename,
                    filepath=filepath
                )
                db.session.add(receipt)
        
        db.session.commit()
        flash('Транзакция успешно добавлена', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при добавлении транзакции: {str(e)}', 'danger')
    
    return redirect(url_for('main.transactions'))

@main_bp.route('/edit_transaction', methods=['POST'])
@login_required
def edit_transaction():
    try:
        transaction_id = int(request.form.get('transaction_id'))
        transaction = Transaction.query.get_or_404(transaction_id)
        
        # Проверка прав
        if transaction.user_id != current_user.id and current_user.role != 'owner':
            flash('У вас нет прав на редактирование этой транзакции', 'danger')
            return redirect(url_for('main.transactions'))
        
        description = request.form.get('description')
        date_str = request.form.get('date')
        amount = abs(float(request.form.get('amount')))
        category_id = int(request.form.get('category_id'))
        user_id = int(request.form.get('user_id'))
        
        # Получаем категорию
        category = Category.query.get(category_id)
        if category.type == 'expense':
            amount = -amount
        
        transaction.description = description
        transaction.date = datetime.strptime(date_str, '%Y-%m-%d')
        transaction.amount = amount
        transaction.category_id = category_id
        transaction.user_id = user_id
        
        # Обработка нового чека
        if 'receipt' in request.files:
            file = request.files['receipt']
            if file and file.filename:
                # Удаляем старый чек если есть
                if transaction.receipt:
                    if os.path.exists(transaction.receipt.filepath):
                        os.remove(transaction.receipt.filepath)
                    db.session.delete(transaction.receipt)
                
                filename = secure_filename(f"{transaction.id}_{file.filename}")
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                receipt = Receipt(
                    transaction_id=transaction.id,
                    filename=file.filename,
                    filepath=filepath
                )
                db.session.add(receipt)
        
        db.session.commit()
        flash('Транзакция успешно обновлена', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при редактировании: {str(e)}', 'danger')
    
    return redirect(url_for('main.transactions'))

@main_bp.route('/api/get_transaction/<int:id>')
@login_required
def get_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    
    # Проверка прав
    if transaction.user_id != current_user.id and current_user.role != 'owner':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    return jsonify({
        'id': transaction.id,
        'description': transaction.description,
        'date': transaction.date.strftime('%Y-%m-%d'),
        'amount': float(transaction.amount),
        'category_id': transaction.category_id,
        'user_id': transaction.user_id
    })

@main_bp.route('/api/delete_transaction/<int:id>', methods=['POST'])
@login_required
def delete_transaction(id):
    try:
        transaction = Transaction.query.get_or_404(id)
        
        # Проверка прав
        if transaction.user_id != current_user.id and current_user.role != 'owner':
            return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
        
        # Удаляем чек если есть
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

@main_bp.route('/categories')
@login_required
def categories():
    # Только владелец может управлять категориями
    if current_user.role != 'owner':
        flash('Только владелец семьи может управлять категориями', 'danger')
        return redirect(url_for('main.index'))
    
    categories_list = Category.query.filter_by(family_id=current_user.family_id).all()
    
    return render_template('categories.html', 
                         categories=categories_list,
                         user=current_user)

@main_bp.route('/add_category', methods=['POST'])
@login_required
def add_category():
    """Добавление новой категории"""
    if current_user.role != 'owner':
        flash('Только владелец семьи может управлять категориями', 'danger')
        return redirect(url_for('main.categories'))
    
    try:
        name = request.form.get('name')
        category_type = request.form.get('type')
        color = request.form.get('color', '#007bff')
        description = request.form.get('description', '')
        
        category = Category(
            name=name,
            type=category_type,
            color=color,
            description=description,
            family_id=current_user.family_id
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash(f'Категория "{name}" успешно добавлена', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при добавлении категории: {str(e)}', 'danger')
    
    return redirect(url_for('main.categories'))

@main_bp.route('/edit_category', methods=['POST'])
@login_required
def edit_category():
    """Редактирование категории"""
    if current_user.role != 'owner':
        flash('Только владелец семьи может управлять категориями', 'danger')
        return redirect(url_for('main.categories'))
    
    try:
        category_id = int(request.form.get('category_id'))
        category = Category.query.get_or_404(category_id)
        
        # Проверка принадлежности категории семье
        if category.family_id != current_user.family_id:
            flash('Доступ запрещен', 'danger')
            return redirect(url_for('main.categories'))
        
        category.name = request.form.get('name')
        category.type = request.form.get('type')
        category.color = request.form.get('color')
        category.description = request.form.get('description')
        
        db.session.commit()
        flash(f'Категория "{category.name}" успешно обновлена', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при редактировании категории: {str(e)}', 'danger')
    
    return redirect(url_for('main.categories'))

@main_bp.route('/set_category_limit', methods=['POST'])
@login_required
def set_category_limit():
    """Установка лимита на категорию"""
    if current_user.role != 'owner':
        flash('Только владелец семьи может устанавливать лимиты', 'danger')
        return redirect(url_for('main.categories'))
    
    try:
        from project.models import CategoryLimit
        
        category_id = int(request.form.get('category_id'))
        amount_limit = float(request.form.get('amount_limit'))
        period = request.form.get('period')
        
        category = Category.query.get_or_404(category_id)
        
        # Проверка принадлежности категории семье
        if category.family_id != current_user.family_id:
            flash('Доступ запрещен', 'danger')
            return redirect(url_for('main.categories'))
        
        # Проверяем, есть ли уже лимит на эту категорию
        existing_limit = CategoryLimit.query.filter_by(category_id=category_id, period=period).first()
        
        if existing_limit:
            existing_limit.amount_limit = amount_limit
            flash(f'Лимит для категории "{category.name}" обновлен', 'success')
        else:
            new_limit = CategoryLimit(
                category_id=category_id,
                amount_limit=amount_limit,
                period=period
            )
            db.session.add(new_limit)
            flash(f'Лимит для категории "{category.name}" установлен', 'success')
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при установке лимита: {str(e)}', 'danger')
    
    return redirect(url_for('main.categories'))

@main_bp.route('/api/get_category/<int:id>')
@login_required
def get_category(id):
    """Получение данных категории для редактирования"""
    category = Category.query.get_or_404(id)
    
    # Проверка прав
    if category.family_id != current_user.family_id and current_user.role != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    return jsonify({
        'id': category.id,
        'name': category.name,
        'type': category.type,
        'color': category.color,
        'description': category.description
    })

@main_bp.route('/api/delete_category/<int:id>', methods=['POST'])
@login_required
def delete_category(id):
    """Удаление категории и всех связанных транзакций"""
    if current_user.role != 'owner':
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    try:
        category = Category.query.get_or_404(id)
        
        # Проверка принадлежности категории семье
        if category.family_id != current_user.family_id:
            return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
        
        # Удаляем все связанные транзакции и их чеки
        for transaction in category.transactions:
            if transaction.receipt:
                if os.path.exists(transaction.receipt.filepath):
                    os.remove(transaction.receipt.filepath)
                db.session.delete(transaction.receipt)
            db.session.delete(transaction)
        
        # Удаляем лимиты категории
        for limit in category.category_limits:
            db.session.delete(limit)
        
        # Удаляем саму категорию
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Категория удалена'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@main_bp.route('/members')
@login_required
def members():
    # Только владелец может управлять участниками
    if current_user.role != 'owner':
        flash('Только владелец семьи может управлять участниками', 'danger')
        return redirect(url_for('main.index'))
    
    family_members = current_user.family.users if current_user.family else []
    invite_code = current_user.family.invite_code if current_user.family else None
    
    return render_template('members.html',
                         members=family_members,
                         invite_code=invite_code,
                         user=current_user)

@main_bp.route('/api/delete_member/<int:id>', methods=['POST'])
@login_required
def delete_member(id):
    """Удаление участника из семьи"""
    if current_user.role != 'owner':
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    try:
        user_to_delete = User.query.get_or_404(id)
        
        # Нельзя удалить самого себя
        if user_to_delete.id == current_user.id:
            return jsonify({'success': False, 'message': 'Нельзя удалить самого себя'}), 400
        
        # Нельзя удалить владельца семьи
        if user_to_delete.role == 'owner':
            return jsonify({'success': False, 'message': 'Нельзя удалить владельца семьи'}), 400
        
        # Проверка, что участник из той же семьи
        if user_to_delete.family_id != current_user.family_id:
            return jsonify({'success': False, 'message': 'Участник из другой семьи'}), 400
        
        # Удаляем все транзакции участника и чеки
        for transaction in user_to_delete.transactions:
            if transaction.receipt:
                if os.path.exists(transaction.receipt.filepath):
                    os.remove(transaction.receipt.filepath)
                db.session.delete(transaction.receipt)
            db.session.delete(transaction)
        
        # Удаляем бюджеты участника
        for budget in user_to_delete.user_budgets:
            db.session.delete(budget)
        
        # Удаляем участника
        db.session.delete(user_to_delete)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Участник удален'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@main_bp.route('/api/get_user/<int:id>')
@login_required
def get_user(id):
    """Получение информации о пользователе"""
    user = User.query.get_or_404(id)
    
    # Проверка прав (только владелец своей семьи или админ)
    if user.family_id != current_user.family_id and current_user.role != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    # Получаем бюджет пользователя
    user_budget = user.user_budgets[0] if user.user_budgets else None
    budget_amount = float(user_budget.amount_limit) if user_budget else 0
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'budget': budget_amount
    })


@main_bp.route('/set_user_budget', methods=['POST'])
@login_required
def set_user_budget():
    """Установка бюджета участнику"""
    if current_user.role != 'owner':
        flash('Только владелец семьи может устанавливать бюджет', 'danger')
        return redirect(url_for('main.members'))
    
    try:
        from project.models import UserBudget
        
        user_id = int(request.form.get('user_id'))
        amount_limit = float(request.form.get('amount_limit'))
        period = request.form.get('period')
        description = request.form.get('description', '')
        
        user = User.query.get_or_404(user_id)
        
        # Проверка принадлежности семьи
        if user.family_id != current_user.family_id:
            flash('Доступ запрещен', 'danger')
            return redirect(url_for('main.members'))
        
        # Проверяем, есть ли уже бюджет
        existing_budget = UserBudget.query.filter_by(user_id=user_id, period=period).first()
        
        if existing_budget:
            existing_budget.amount_limit = amount_limit
            existing_budget.description = description
            flash(f'Бюджет для "{user.username}" обновлен', 'success')
        else:
            new_budget = UserBudget(
                user_id=user_id,
                amount_limit=amount_limit,
                period=period,
                description=description
            )
            db.session.add(new_budget)
            flash(f'Бюджет для "{user.username}" установлен', 'success')
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при установке бюджета: {str(e)}', 'danger')
    
    return redirect(url_for('main.members'))

# @main_bp.route('/api/get_user/<int:id>')
# @login_required
# def get_user(id):
#     """Получение информации о пользователе"""
#     user = User.query.get_or_404(id)
    
#     # Проверка прав
#     if user.family_id != current_user.family_id and current_user.role != 'admin':
#         return jsonify({'error': 'Доступ запрещен'}), 403
    
#     return jsonify({
#         'id': user.id,
#         'username': user.username,
#         'email': user.email,
#         'role': user.role
#     })


@main_bp.route('/profile')
@login_required
def profile():
    family_members = current_user.family.users if current_user.family else []
    return render_template('profile.html', user=current_user, family_members=family_members)

@main_bp.route('/generate_invite_code', methods=['POST'])
@login_required
def generate_invite_code_route():
    """Генерация нового кода приглашения"""
    if current_user.role != 'owner':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('main.index'))
    
    if current_user.family:
        new_code = generate_invite_code()
        current_user.family.invite_code = new_code
        db.session.commit()
        flash(f'Новый код приглашения: {new_code}', 'success')
    
    return redirect(url_for('main.members'))

