# from flask import Flask, render_template

# app = Flask(__name__)

# @app.route('/')
# def index():
#     return render_template('dashboard/owner_dashboard.html')

# @app.route('/login')
# def login():
#     return render_template('auth/login.html')

# @app.route('/register')
# def register():
#     return render_template('auth/register.html')

# @app.route('/dashboard/admin')
# def admin_dashboard():
#     return render_template('dashboard/admin_dashboard.html')

# @app.route('/dashboard/owner')
# def owner_dashboard():
#     return render_template('dashboard/owner_dashboard.html')

# @app.route('/dashboard/member')
# def member_dashboard():
#     return render_template('dashboard/member_dashboard.html')

# @app.route('/profile')
# def profile():
#     return render_template('profile.html')

# @app.route('/members')                    # ← изменено
# def members():
#     return render_template('members.html')

# @app.route('/transactions')
# def transactions():
#     return render_template('transactions.html')

# @app.route('/categories')
# def categories():
#     return render_template('categories.html')

# if __name__ == '__main__':
#     app.run(debug=True)