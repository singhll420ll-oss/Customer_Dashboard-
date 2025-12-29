"""
BiteMeBuddy - Food Delivery Platform
Main Application File (UPDATED & SAFE)
"""

import os
from datetime import datetime

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash, jsonify
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# ==================== APP SETUP ====================

app = Flask(__name__)

# Safe config load
app.config.from_pyfile('config.py', silent=True)

# Force SECRET_KEY fallback (CRITICAL FIX)
app.secret_key = app.config.get(
    "SECRET_KEY",
    os.environ.get("SECRET_KEY", "dev-secret-key-change-this")
)

# Ensure SQLAlchemy config
app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)

# Database
db = SQLAlchemy(app)

# ==================== MODELS ====================

from models import (
    User, Service, ServiceItem, Menu,
    Cart, Order, OrderItem, Message
)

# ==================== ROUTES ====================

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        mobile = request.form.get('mobile')
        password = request.form.get('password')

        if not mobile or not password:
            flash('Please enter mobile number and password', 'error')
            return render_template('login.html')

        user = User.query.filter_by(mobile=mobile).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.user_id
            session['user_name'] = user.name
            session['mobile'] = user.mobile
            session['profile_pic'] = user.profile_pic or '/static/images/default_dp.png'

            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))

        flash('Invalid credentials. Please register first.', 'error')
        return redirect(url_for('register'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name')
        mobile = request.form.get('mobile')
        email = request.form.get('email')
        location = request.form.get('location')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        profile_pic = request.form.get('profile_pic', '')

        errors = []

        if not name or len(name) < 2:
            errors.append('Name must be at least 2 characters')

        if not mobile or len(mobile) != 10 or not mobile.isdigit():
            errors.append('Enter valid 10-digit mobile number')

        if not email or '@' not in email:
            errors.append('Enter valid email address')

        if not location:
            errors.append('Location is required')

        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters')

        if password != confirm_password:
            errors.append('Passwords do not match')

        if User.query.filter_by(mobile=mobile).first():
            errors.append('Mobile number already registered')

        if errors:
            for err in errors:
                flash(err, 'error')
            return render_template('register.html')

        new_user = User(
            name=name,
            mobile=mobile,
            email=email,
            location=location,
            password=generate_password_hash(password),
            profile_pic=profile_pic or '/static/images/default_dp.png',
            registered_at=datetime.utcnow()
        )

        try:
            db.session.add(new_user)
            db.session.commit()

            db.session.add(Message(
                user_id=new_user.user_id,
                content='Welcome to BiteMeBuddy! 🎉',
                sent_at=datetime.utcnow()
            ))
            db.session.commit()

            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))

        except Exception:
            db.session.rollback()
            flash('Registration failed. Try again.', 'error')

    return render_template('register.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    services = Service.query.filter(
        Service.available_until > datetime.utcnow()
    ).order_by(Service.added_at.desc()).all()

    menus = Menu.query.order_by(Menu.serial_number).all()
    cart_count = Cart.query.filter_by(user_id=user_id).count()
    unread_count = Message.query.filter_by(user_id=user_id, is_read=False).count()

    return render_template(
        'dashboard.html',
        services=services,
        menus=menus,
        cart_count=cart_count,
        unread_count=unread_count
    )


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500


# ==================== INIT ====================

def create_tables():
    with app.app_context():
        db.create_all()
        print("Database tables created")


if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0', port=5000, debug=True)