from flask import render_template, Blueprint, flash, redirect, url_for, request, jsonify
from flask import current_app
from flask_login import login_required, current_user
from project import db
from project.models import User, Family, Category, Transaction, Receipt, CategoryLimit, UserBudget, DashboardStats
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import secrets
import string
from datetime import datetime, date, timedelta

main_bp = Blueprint('main', __name__)

def generate_invite_code():
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = 'FAM-' + ''.join(secrets.choice(alphabet) for _ in range(6))
        if not Family.query.filter_by(invite_code=code).first():
            return code

@main_bp.route('/generate_invite_code', methods=['POST'])
@login_required
def generate_invite_code_route():
    if current_user.role != 'owner':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('main.index'))
    
    if current_user.family:
        new_code = generate_invite_code()
        current_user.family.invite_code = new_code
        db.session.commit()
        flash(f'Новый код приглашения: {new_code}', 'success')
    
    return redirect(url_for('main.members'))


def update_dashboard_stats(user_id):
    from project.models import DashboardStats
    
    # Получаем пользователя
    user = User.query.get(user_id)
    if not user or not user.family:
        return
    
    # Получаем всех членов семьи
    family_member_ids = [member.id for member in user.family.users]
    
    # Получаем все транзакции семьи
    all_transactions = Transaction.query.filter(
        Transaction.user_id.in_(family_member_ids)
    ).order_by(Transaction.date.asc()).all()
    
    # Вычисляем баланс на каждый день
    daily_balance = {}
    running_balance = 0.0
    
    if all_transactions:
        start_date = all_transactions[0].date
        end_date = datetime.utcnow().date()
        
        current_date = start_date
        trans_index = 0
        
        while current_date <= end_date:
            day_transactions = []
            while trans_index < len(all_transactions) and all_transactions[trans_index].date == current_date:
                day_transactions.append(all_transactions[trans_index])
                trans_index += 1
            
            day_income = sum(float(t.amount) for t in day_transactions if t.amount > 0)
            day_expense = sum(float(t.amount) for t in day_transactions if t.amount < 0)
            running_balance += (day_income + day_expense)
            
            daily_balance[current_date.isoformat()] = running_balance
            current_date += timedelta(days=1)
    
    # Сохраняем или обновляем статистику пользователя
    stats = DashboardStats.query.filter_by(user_id=user_id).first()
    if stats:
        stats.daily_balance = daily_balance
        stats.last_calculated = datetime.utcnow()
    else:
        stats = DashboardStats(
            user_id=user_id,
            period='month',
            daily_balance=daily_balance
        )
        db.session.add(stats)
    
    db.session.commit()
    print(f"Статистика для пользователя {user_id} обновлена. Дней: {len(daily_balance)}")

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


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


@main_bp.route('/dashboard/owner')
@login_required
def owner_dashboard():
    if current_user.role != 'owner':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('main.index'))

    current_app.logger.info(f'User {current_user.id} ({current_user.username}) viewed owner dashboard')
    
    period = request.args.get('period', 'month')
    
    # Определяем даты для периода
    now = datetime.utcnow().date()
    
    if period == 'day':
        start_date = now
        end_date = now
    elif period == 'week':
        start_date = now - timedelta(days=now.weekday())
        end_date = now
    else:  # month
        start_date = now.replace(day=1)
        end_date = now
    
    # Получаем расходы семьи за период
    family_expense = 0
    if current_user.family:
        family_member_ids = [user.id for user in current_user.family.users]
        family_transactions = Transaction.query.filter(
            Transaction.user_id.in_(family_member_ids),
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.amount < 0
        ).all()
        family_expense = sum(abs(float(t.amount)) for t in family_transactions)
    
    # Получаем доходы семьи за период
    family_income = 0
    if current_user.family:
        family_transactions_income = Transaction.query.filter(
            Transaction.user_id.in_(family_member_ids),
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.amount > 0
        ).all()
        family_income = sum(float(t.amount) for t in family_transactions_income)
    
    # Сначала считаем сумму всех личных бюджетов участников (приводим к месяцу)
    total_monthly_budget = 0
    if current_user.family:
        for member in current_user.family.users:
            member_budget = member.user_budgets[0] if member.user_budgets else None
            if member_budget:
                budget_amount = float(member_budget.amount_limit)
                budget_period = member_budget.period
                
                # Приводим к месячному бюджету
                if budget_period == 'day':
                    monthly_budget = budget_amount * 30
                elif budget_period == 'week':
                    monthly_budget = budget_amount * 4
                else: 
                    monthly_budget = budget_amount
                
                total_monthly_budget += monthly_budget
    
    # Теперь пересчитываем семейный бюджет под выбранный период
    if period == 'day':
        family_budget = total_monthly_budget / 30
    elif period == 'week':
        family_budget = total_monthly_budget / 4
    else:  # month
        family_budget = total_monthly_budget
    
    # Остаток семейного бюджета
    family_balance = family_budget - family_expense

    # расходы по категориям за период (для круговой диаграммы)
    expense_by_category = {}
    if current_user.family:
        family_member_ids = [user.id for user in current_user.family.users]
        family_transactions_all = Transaction.query.filter(
            Transaction.user_id.in_(family_member_ids),
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.amount < 0
        ).all()
        
        for transaction in family_transactions_all:
            category_name = transaction.category.name
            amount = float(abs(transaction.amount))
            expense_by_category[category_name] = expense_by_category.get(category_name, 0.0) + amount
    
    expense_categories = list(expense_by_category.keys())
    expense_amounts = list(expense_by_category.values())
    
    # Получаем данные для столбчатой диаграммы
    chart_labels = []
    chart_balance_data = []

    stats = DashboardStats.query.filter_by(user_id=current_user.id).first()
    now = datetime.utcnow().date()

    if period == 'day':
        # Показываем позавчера, вчера, сегодня
        dates = [now - timedelta(days=2), now - timedelta(days=1), now]
        date_format = '%d.%m'
    elif period == 'week':
        # Показываем все дни недели (с понедельника)
        start_date = now - timedelta(days=now.weekday())
        dates = [start_date + timedelta(days=i) for i in range(7)]
        date_format = '%d.%m'
    else: 
        # Показываем все дни месяца
        start_date = now.replace(day=1)
        if now.month == 12:
            end_date = now.replace(year=now.year+1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = now.replace(month=now.month+1, day=1) - timedelta(days=1)
        dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
        date_format = '%d.%m'

    for date in dates:
        date_str = date.isoformat()
        chart_labels.append(date.strftime(date_format))

        if date > now:
            chart_balance_data.append(0)
        elif stats and stats.daily_balance and date_str in stats.daily_balance:
            chart_balance_data.append(stats.daily_balance[date_str])
        elif stats and stats.daily_balance:
            last_balance = 0
            for d in sorted(stats.daily_balance.keys()):
                if d <= date_str:
                    last_balance = stats.daily_balance[d]
            chart_balance_data.append(last_balance)
        else:
            chart_balance_data.append(0)
    
    # Сводная таблица по участникам за период
    family_members_data = []
    if current_user.family:
        for member in current_user.family.users:
            member_transactions = Transaction.query.filter_by(user_id=member.id).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).all()
            
            member_income = sum(float(t.amount) for t in member_transactions if t.amount > 0)
            member_expense = sum(abs(float(t.amount)) for t in member_transactions if t.amount < 0)
            member_balance = member_income - member_expense
            
            family_members_data.append({
                'id': member.id,
                'username': member.username,
                'role': member.role,
                'income_amount': member_income,
                'expense_amount': member_expense,
                'balance': member_balance
            })
    
    recent_transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).limit(5).all()
    
    return render_template('dashboard/owner_dashboard.html',
                         user=current_user,
                         period=period,
                         total_income=family_income,  
                         total_expense=family_expense,  
                         balance=family_balance,  
                         user_budget=family_budget, 
                         expense_categories=expense_categories,
                         expense_amounts=expense_amounts,
                         chart_labels=chart_labels,
                         chart_balance_data=chart_balance_data,
                         family_members=family_members_data,
                         recent_transactions=recent_transactions)


@main_bp.route('/dashboard/member')
@login_required
def member_dashboard():
    if current_user.role != 'member':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('main.index'))

    current_app.logger.info(f'User {current_user.id} ({current_user.username}) viewed member dashboard')
    
    period = request.args.get('period', 'month')
    
    now = datetime.utcnow().date()
    
    if period == 'day':
        start_date = now
        end_date = now
    elif period == 'week':
        start_date = now - timedelta(days=now.weekday())
        end_date = now
    else:  # month
        start_date = now.replace(day=1)
        end_date = now
    
    # Получаем расходы и доходы участника за период
    member_transactions = Transaction.query.filter_by(user_id=current_user.id).filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).all()
    
    total_income = sum(float(t.amount) for t in member_transactions if t.amount > 0)
    total_expense = sum(abs(float(t.amount)) for t in member_transactions if t.amount < 0)
    
    # Получаем бюджет участника
    user_budget = current_user.user_budgets[0] if current_user.user_budgets else None
    budget_amount_raw = float(user_budget.amount_limit) if user_budget else 0.0
    budget_period = user_budget.period if user_budget else 'month'
    
    # Пересчет бюджета под выбранный период
    if budget_amount_raw > 0:
        if budget_period == 'day' and period == 'week':
            budget_amount = budget_amount_raw * 7
        elif budget_period == 'day' and period == 'month':
            budget_amount = budget_amount_raw * 30
        elif budget_period == 'week' and period == 'day':
            budget_amount = budget_amount_raw / 7
        elif budget_period == 'week' and period == 'month':
            budget_amount = budget_amount_raw * 4
        elif budget_period == 'month' and period == 'day':
            budget_amount = budget_amount_raw / 30
        elif budget_period == 'month' and period == 'week':
            budget_amount = budget_amount_raw / 4
        else:
            budget_amount = budget_amount_raw
    else:
        budget_amount = 0
    
    balance = budget_amount - total_expense
    
    # Расходы по категориям для участника
    expense_by_category = {}
    for transaction in member_transactions:
        if transaction.amount < 0:
            category_name = transaction.category.name
            amount = float(abs(transaction.amount))
            expense_by_category[category_name] = expense_by_category.get(category_name, 0.0) + amount
    
    expense_categories = list(expense_by_category.keys())
    expense_amounts = list(expense_by_category.values())
    
    # Данные для графика участника
    chart_labels = []
    chart_balance_data = []
    
    stats = DashboardStats.query.filter_by(user_id=current_user.id).first()
    now_date = datetime.utcnow().date()

    if period == 'day':
        dates = [now - timedelta(days=2), now - timedelta(days=1), now]
        date_format = '%d.%m'
    elif period == 'week':
        start_date = now - timedelta(days=now.weekday())
        dates = [start_date + timedelta(days=i) for i in range(7)]
        date_format = '%d.%m'
    else: 
        start_date = now.replace(day=1)
        if now.month == 12:
            end_date = now.replace(year=now.year+1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = now.replace(month=now.month+1, day=1) - timedelta(days=1)
        dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
        date_format = '%d.%m'

    for date in dates:
        date_str = date.isoformat()
        chart_labels.append(date.strftime(date_format))

        if date > now:
            chart_balance_data.append(0)
        elif stats and stats.daily_balance and date_str in stats.daily_balance:
            chart_balance_data.append(stats.daily_balance[date_str])
        else:
            # Считаем баланс участника на эту дату
            day_transactions = Transaction.query.filter_by(user_id=current_user.id).filter(
                Transaction.date >= date,
                Transaction.date <= date
            ).all()
            day_balance = sum(float(t.amount) for t in day_transactions)
            chart_balance_data.append(day_balance)


    # Последние транзакции участника
    recent_transactions = member_transactions[-5:] if len(member_transactions) > 5 else member_transactions
    
    return render_template('dashboard/member_dashboard.html',
                         user=current_user,
                         period=period,
                         total_income=total_income,
                         total_expense=total_expense,
                         balance=balance,
                         user_budget=budget_amount,
                         expense_categories=expense_categories,
                         expense_amounts=expense_amounts,
                         chart_labels=chart_labels,
                         chart_balance_data=chart_balance_data,
                         recent_transactions=recent_transactions)


@main_bp.route('/member_stats/<int:member_id>')
@login_required
def member_stats(member_id):
    if current_user.role != 'owner':
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('main.index'))
    
    member = User.query.get_or_404(member_id)
    
    if member.family_id != current_user.family_id:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('main.index'))
    
    period = request.args.get('period', 'month')
    
    now = datetime.utcnow().date()
    
    if period == 'day':
        start_date = now
        end_date = now
    elif period == 'week':
        start_date = now - timedelta(days=now.weekday())
        end_date = now
    else: 
        start_date = now.replace(day=1)
        end_date = now
    
    member_transactions = Transaction.query.filter_by(user_id=member.id).filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).all()
    
    total_income = sum(float(t.amount) for t in member_transactions if t.amount > 0)
    total_expense = sum(abs(float(t.amount)) for t in member_transactions if t.amount < 0)
    
    user_budget = member.user_budgets[0] if member.user_budgets else None
    budget_amount_raw = float(user_budget.amount_limit) if user_budget else 0.0
    budget_period = user_budget.period if user_budget else 'month'
    
    if budget_amount_raw > 0:
        if budget_period == 'day' and period == 'week':
            budget_amount = budget_amount_raw * 7
        elif budget_period == 'day' and period == 'month':
            budget_amount = budget_amount_raw * 30
        elif budget_period == 'week' and period == 'day':
            budget_amount = budget_amount_raw / 7
        elif budget_period == 'week' and period == 'month':
            budget_amount = budget_amount_raw * 4
        elif budget_period == 'month' and period == 'day':
            budget_amount = budget_amount_raw / 30
        elif budget_period == 'month' and period == 'week':
            budget_amount = budget_amount_raw / 4
        else:
            budget_amount = budget_amount_raw
    else:
        budget_amount = 0
    
    balance = budget_amount - total_expense
    
    expense_by_category = {}
    for transaction in member_transactions:
        if transaction.amount < 0:
            category_name = transaction.category.name
            amount = float(abs(transaction.amount))
            expense_by_category[category_name] = expense_by_category.get(category_name, 0.0) + amount
    
    expense_categories = list(expense_by_category.keys())
    expense_amounts = list(expense_by_category.values())

    chart_labels = []
    chart_balance_data = []
    
    stats = DashboardStats.query.filter_by(user_id=member.id).first()
    now_date = datetime.utcnow().date()

    if period == 'day':
        dates = [now - timedelta(days=2), now - timedelta(days=1), now]
        date_format = '%d.%m'
    elif period == 'week':
        start_date = now - timedelta(days=now.weekday())
        dates = [start_date + timedelta(days=i) for i in range(7)]
        date_format = '%d.%m'
    else: 
        start_date = now.replace(day=1)
        if now.month == 12:
            end_date = now.replace(year=now.year+1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = now.replace(month=now.month+1, day=1) - timedelta(days=1)
        dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
        date_format = '%d.%m'


    for date in dates:
        date_str = date.isoformat()
        chart_labels.append(date.strftime(date_format))

        if date > now:
            chart_balance_data.append(0)
        elif stats and stats.daily_balance and date_str in stats.daily_balance:
            chart_balance_data.append(stats.daily_balance[date_str])
        else:
            day_transactions = Transaction.query.filter_by(user_id=member.id).filter(
                Transaction.date >= date,
                Transaction.date <= date
            ).all()
            day_balance = sum(float(t.amount) for t in day_transactions)
            chart_balance_data.append(day_balance)
    
    return render_template('dashboard/member_stats.html',
                         member=member,
                         period=period,
                         total_income=total_income,
                         total_expense=total_expense,
                         balance=balance,
                         user_budget=budget_amount,
                         expense_categories=expense_categories,
                         expense_amounts=expense_amounts,
                         chart_labels=chart_labels,
                         chart_balance_data=chart_balance_data)


@main_bp.route('/transactions', methods=['GET'])
@login_required
def transactions():
    search_term = request.args.get('search', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    if current_user.role == 'owner' and current_user.family:
        family_member_ids = [user.id for user in current_user.family.users]
        query = Transaction.query.filter(Transaction.user_id.in_(family_member_ids))
    else:
        query = Transaction.query.filter_by(user_id=current_user.id)
    
    if search_term:
        query = query.filter(Transaction.description.contains(search_term))
    
    if date_from:
        query = query.filter(Transaction.date >= datetime.strptime(date_from, '%Y-%m-%d'))
    
    if date_to:
        query = query.filter(Transaction.date <= datetime.strptime(date_to, '%Y-%m-%d'))
    
    transactions_list = query.order_by(Transaction.date.desc()).all()
    
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

@main_bp.route('/add_transaction', methods=['POST'])
@login_required
def add_transaction():
    try:
        description = request.form.get('description')
        date_str = request.form.get('date')
        amount = abs(float(request.form.get('amount'))) 
        category_id = int(request.form.get('category_id'))
        user_id = int(request.form.get('user_id'))
        
        category = Category.query.get(category_id)
        if not category:
            flash('Категория не найдена', 'danger')
            return redirect(url_for('main.transactions'))
        
        if category.type == 'expense':
            amount = -amount
        
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
        
        if 'receipt' in request.files:
            file = request.files['receipt']
            if file and file.filename:
                if not allowed_file(file.filename):
                    flash('Неподдерживаемый формат файла. Разрешены: JPG, JPEG, PNG, PDF', 'danger')
                    return redirect(url_for('main.transactions'))
                
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
        if current_user.id:
            update_dashboard_stats(current_user.id)
        current_app.logger.info(f'User {current_user.id} ({current_user.username}) added transaction {transaction.id}: {amount} ₽, category: {category.name}')
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
        
        if transaction.user_id != current_user.id and current_user.role != 'owner':
            flash('У вас нет прав на редактирование этой транзакции', 'danger')
            return redirect(url_for('main.transactions'))
        
        description = request.form.get('description')
        date_str = request.form.get('date')
        amount = abs(float(request.form.get('amount')))
        category_id = int(request.form.get('category_id'))
        user_id = int(request.form.get('user_id'))
        
        category = Category.query.get(category_id)
        if category.type == 'expense':
            amount = -amount
        
        transaction.description = description
        transaction.date = datetime.strptime(date_str, '%Y-%m-%d')
        transaction.amount = amount
        transaction.category_id = category_id
        transaction.user_id = user_id
        
        if 'receipt' in request.files:
            file = request.files['receipt']
            if file and file.filename:
                # Проверка формата
                if not allowed_file(file.filename):
                    flash('Неподдерживаемый формат файла. Разрешены: JPG, JPEG, PNG, PDF', 'danger')
                    return redirect(url_for('main.transactions'))
                
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
        if current_user.id:
            update_dashboard_stats(current_user.id)
        current_app.logger.info(f'User {current_user.id} ({current_user.username}) edited transaction {transaction_id}')
        flash('Транзакция успешно обновлена', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при редактировании: {str(e)}', 'danger')
    
    return redirect(url_for('main.transactions'))

@main_bp.route('/api/get_transaction/<int:id>')
@login_required
def get_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    
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
        
        if transaction.user_id != current_user.id and current_user.role != 'owner':
            return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
        
        if transaction.receipt:
            if os.path.exists(transaction.receipt.filepath):
                os.remove(transaction.receipt.filepath)
            db.session.delete(transaction.receipt)
        
        db.session.delete(transaction)
        db.session.commit()
        if current_user.id:
            update_dashboard_stats(current_user.id)
        current_app.logger.info(f'User {current_user.id} ({current_user.username}) deleted transaction {id}')
        
        return jsonify({'success': True, 'message': 'Транзакция удалена'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@main_bp.route('/api/get_receipt/<int:id>')
@login_required
def get_receipt(id):
    receipt = Receipt.query.get_or_404(id)
    transaction = receipt.transaction
    
    if transaction.user_id != current_user.id and current_user.role not in ['owner', 'admin']:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    file_url = url_for('main.uploaded_file', filename=os.path.basename(receipt.filepath))
    return jsonify({'url': file_url})


@main_bp.route('/categories')
@login_required
def categories():
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
        current_app.logger.info(f'User {current_user.id} ({current_user.username}) added category {category.id}: category: {category.name}')
        
        flash(f'Категория "{name}" успешно добавлена', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при добавлении категории: {str(e)}', 'danger')
    
    return redirect(url_for('main.categories'))

@main_bp.route('/edit_category', methods=['POST'])
@login_required
def edit_category():
    if current_user.role != 'owner':
        flash('Только владелец семьи может управлять категориями', 'danger')
        return redirect(url_for('main.categories'))
    
    try:
        category_id = int(request.form.get('category_id'))
        category = Category.query.get_or_404(category_id)
        
        if category.family_id != current_user.family_id:
            flash('Доступ запрещен', 'danger')
            return redirect(url_for('main.categories'))
        
        category.name = request.form.get('name')
        category.type = request.form.get('type')
        category.color = request.form.get('color')
        category.description = request.form.get('description')
        
        db.session.commit()
        current_app.logger.info(f'User {current_user.id} ({current_user.username}) edited category {category.id}: category: {category.name}')
        flash(f'Категория "{category.name}" успешно обновлена', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при редактировании категории: {str(e)}', 'danger')
    
    return redirect(url_for('main.categories'))

@main_bp.route('/set_category_limit', methods=['POST'])
@login_required
def set_category_limit():
    if current_user.role != 'owner':
        flash('Только владелец семьи может устанавливать лимиты', 'danger')
        return redirect(url_for('main.categories'))
    
    try:
        from project.models import CategoryLimit
        
        category_id = int(request.form.get('category_id'))
        amount_limit = float(request.form.get('amount_limit'))
        period = request.form.get('period')
        
        category = Category.query.get_or_404(category_id)
        
        if category.family_id != current_user.family_id:
            flash('Доступ запрещен', 'danger')
            return redirect(url_for('main.categories'))
        
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
    category = Category.query.get_or_404(id)
    
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
    if current_user.role != 'owner':
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    try:
        category = Category.query.get_or_404(id)
        
        if category.family_id != current_user.family_id:
            return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
        
        for transaction in category.transactions:
            if transaction.receipt:
                if os.path.exists(transaction.receipt.filepath):
                    os.remove(transaction.receipt.filepath)
                db.session.delete(transaction.receipt)
            db.session.delete(transaction)
        
        for limit in category.category_limits:
            db.session.delete(limit)
        
        db.session.delete(category)
        db.session.commit()
        current_app.logger.info(f'User {current_user.id} ({current_user.username}) deleted category {category.id}: category: {category.name}')
        
        return jsonify({'success': True, 'message': 'Категория удалена'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@main_bp.route('/members')
@login_required
def members():
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
    if current_user.role != 'owner':
        return jsonify({'success': False, 'message': 'Доступ запрещен'}), 403
    
    try:
        user_to_delete = User.query.get_or_404(id)
        
        if user_to_delete.id == current_user.id:
            return jsonify({'success': False, 'message': 'Нельзя удалить самого себя'}), 400
        
        if user_to_delete.role == 'owner':
            return jsonify({'success': False, 'message': 'Нельзя удалить владельца семьи'}), 400
        
        if user_to_delete.family_id != current_user.family_id:
            return jsonify({'success': False, 'message': 'Участник из другой семьи'}), 400
        
        for transaction in user_to_delete.transactions:
            if transaction.receipt:
                if os.path.exists(transaction.receipt.filepath):
                    os.remove(transaction.receipt.filepath)
                db.session.delete(transaction.receipt)
            db.session.delete(transaction)
        
        for budget in user_to_delete.user_budgets:
            db.session.delete(budget)
        
        db.session.delete(user_to_delete)
        db.session.commit()
        current_app.logger.info(f'User {current_user.id} ({current_user.username}) deleted user {user_to_delete.id}: name: {user_to_delete.name}')
        
        return jsonify({'success': True, 'message': 'Участник удален'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@main_bp.route('/api/get_user/<int:id>')
@login_required
def get_user(id):
    user = User.query.get_or_404(id)
    
    if user.family_id != current_user.family_id and current_user.role != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
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
        
        if user.family_id != current_user.family_id:
            flash('Доступ запрещен', 'danger')
            return redirect(url_for('main.members'))
        
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


@main_bp.route('/profile')
@login_required
def profile():
    family_members = current_user.family.users if current_user.family else []
    return render_template('profile.html', user=current_user, family_members=family_members)

@main_bp.route('/edit_profile', methods=['POST'])
@login_required
def edit_profile():
    try:
        new_username = request.form.get('username')
        new_email = request.form.get('email')
        new_password = request.form.get('password')
        new_password2 = request.form.get('password2')
        
        if new_username != current_user.username:
            existing_user = User.query.filter_by(username=new_username).first()
            if existing_user:
                flash('Пользователь с таким логином уже существует', 'danger')
                return redirect(url_for('main.profile'))
        
        if new_email != current_user.email:
            existing_email = User.query.filter_by(email=new_email).first()
            if existing_email:
                flash('Пользователь с таким email уже существует', 'danger')
                return redirect(url_for('main.profile'))
        
        current_user.username = new_username
        current_user.email = new_email
        
        if new_password:
            if new_password != new_password2:
                flash('Пароли не совпадают', 'danger')
                return redirect(url_for('main.profile'))
            if len(new_password) < 4:
                flash('Пароль должен содержать минимум 4 символа', 'danger')
                return redirect(url_for('main.profile'))
            current_user.set_password(new_password)
        
        db.session.commit()
        flash('Профиль успешно обновлен', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при обновлении профиля: {str(e)}', 'danger')
    
    return redirect(url_for('main.profile'))


@main_bp.route('/export_report')
@login_required
def export_report():
    import csv
    from io import StringIO
    from flask import Response
    
    period = request.args.get('period', 'month')
    
    if current_user.role == 'owner' and current_user.family:
        family_member_ids = [user.id for user in current_user.family.users]
        transactions = Transaction.query.filter(
            Transaction.user_id.in_(family_member_ids)
        ).order_by(Transaction.date.desc()).all()
    else:
        transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
    
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['Дата', 'Описание', 'Категория', 'Сумма', 'Тип', 'Участник'])
    
    for t in transactions:
        writer.writerow([
            t.date.strftime('%d.%m.%Y'),
            t.description,
            t.category.name,
            f"{abs(float(t.amount)):.2f}",
            'Доход' if t.amount > 0 else 'Расход',
            t.user.username
        ])
    
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers.set('Content-Disposition', 'attachment', filename=f'report_{period}_{datetime.now().strftime("%Y%m%d")}.csv')
    
    return response