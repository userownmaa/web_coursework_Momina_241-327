from flask import render_template, Blueprint, flash, redirect, url_for
from flask_login import login_required, current_user
from project import db
from project.models import User

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('У вас нет доступа к административной панели', 'danger')
        return redirect(url_for('main.index'))
    
    users = User.query.all()
    return render_template('dashboard/admin_dashboard.html', users=users)