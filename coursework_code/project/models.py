from flask_login import UserMixin
from project import db, login_manager
from datetime import datetime, timedelta
from sqlalchemy import JSON

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Family(db.Model):
    __tablename__ = 'family'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    invite_code = db.Column(db.String(20), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    
    users = db.relationship('User', back_populates='family', lazy=True)
    categories = db.relationship('Category', back_populates='family', lazy=True)
    
    def get_members(self):
        return self.users
    
    def get_owner(self):
        return User.query.filter_by(family_id=self.id, role='owner').first()
    
    def __repr__(self):
        return f'<Family {self.name}>'

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='member')
    family_id = db.Column(db.Integer, db.ForeignKey('family.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    
    family = db.relationship('Family', back_populates='users')
    transactions = db.relationship('Transaction', back_populates='user', lazy=True, order_by="Transaction.date.desc()")
    user_budgets = db.relationship('UserBudget', back_populates='user', lazy=True)
    dashboard_stats = db.relationship('DashboardStats', back_populates='user', lazy=True, uselist=False)
    
    def set_password(self, password):
        from bcrypt import hashpw, gensalt
        self.password_hash = hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')
    
    def check_password(self, password):
        from bcrypt import checkpw
        return checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def get_transactions(self, period='all'):
        now = datetime.utcnow()
        
        if period == 'day':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            return Transaction.query.filter_by(user_id=self.id).filter(
                Transaction.date >= start_date, 
                Transaction.date <= end_date
            ).all()
        elif period == 'week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            return Transaction.query.filter_by(user_id=self.id).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).all()
        elif period == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                end_date = now.replace(year=now.year+1, month=1, day=1) - timedelta(seconds=1)
            else:
                end_date = now.replace(month=now.month+1, day=1) - timedelta(seconds=1)
            return Transaction.query.filter_by(user_id=self.id).filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).all()
        else:
            return Transaction.query.filter_by(user_id=self.id).all()
    
    def get_total_income(self, period='all'):
        transactions = self.get_transactions(period)
        total = sum(float(t.amount) for t in transactions if t.amount > 0)
        return total
    
    def get_total_expense(self, period='all'):
        transactions = self.get_transactions(period)
        total = sum(float(t.amount) for t in transactions if t.amount < 0)
        return total
    
    def get_balance(self, period='all'):
        return self.get_total_income(period) + self.get_total_expense(period)
    
    def get_category_breakdown(self, period='all'):
        from collections import defaultdict
        transactions = self.get_transactions(period)
        
        breakdown = defaultdict(float)
        for t in transactions:
            if t.amount < 0:
                breakdown[t.category.name] += abs(float(t.amount))
        
        return dict(breakdown)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    __tablename__ = 'category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(10), nullable=False)
    color = db.Column(db.String(20), default='#007bff')
    description = db.Column(db.Text, nullable=True)
    family_id = db.Column(db.Integer, db.ForeignKey('family.id'), nullable=False)
    
    family = db.relationship('Family', back_populates='categories')
    transactions = db.relationship('Transaction', back_populates='category', lazy=True)
    category_limits = db.relationship('CategoryLimit', back_populates='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Transaction(db.Model):
    __tablename__ = 'transaction'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    description = db.Column(db.Text, nullable=True)
    
    user = db.relationship('User', back_populates='transactions')
    category = db.relationship('Category', back_populates='transactions')
    receipt = db.relationship('Receipt', uselist=False, back_populates='transaction', lazy=True)
    
    @property
    def is_income(self):
        return self.amount > 0
    
    def __repr__(self):
        return f'<Transaction {self.amount} on {self.date}>'

class Receipt(db.Model):
    __tablename__ = 'receipt'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), unique=True, nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    transaction = db.relationship('Transaction', back_populates='receipt')
    
    def __repr__(self):
        return f'<Receipt for transaction {self.transaction_id}>'

class CategoryLimit(db.Model):
    __tablename__ = 'category_limit'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    amount_limit = db.Column(db.Numeric(10, 2), nullable=False)
    period = db.Column(db.String(10), nullable=False)
    
    category = db.relationship('Category', back_populates='category_limits')
    
    def __repr__(self):
        return f'<CategoryLimit {self.amount_limit} for {self.category.name}>'

class UserBudget(db.Model):
    __tablename__ = 'user_budget'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount_limit = db.Column(db.Numeric(10, 2), nullable=False)
    period = db.Column(db.String(10), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    user = db.relationship('User', back_populates='user_budgets')
    
    def __repr__(self):
        return f'<UserBudget {self.amount_limit} for {self.user.username}>'

class DashboardStats(db.Model):
    __tablename__ = 'dashboard_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    period = db.Column(db.String(10), nullable=False, default='month')
    total_income = db.Column(db.Numeric(10, 2), default=0)
    total_expense = db.Column(db.Numeric(10, 2), default=0)
    category_breakdown = db.Column(JSON, default=dict)
    member_breakdown = db.Column(JSON, default=dict)
    monthly_timeline = db.Column(JSON, default=dict)
    daily_balance = db.Column(JSON, default=dict)
    last_calculated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', back_populates='dashboard_stats')
    
    def __repr__(self):
        return f'<DashboardStats for user {self.user_id} - {self.period}>'