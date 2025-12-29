"""
BiteMeBuddy - Food Delivery Platform
Main Application File
"""
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_pyfile('config.py')

# Database setup
db = SQLAlchemy(app)

# Import models
from models import User, Service, ServiceItem, Menu, Cart, Order, OrderItem, Message

# ==================== ROUTES ====================

@app.route('/')
def home():
    """Home page redirects to login"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        mobile = request.form.get('mobile')
        password = request.form.get('password')
        
        if not mobile or not password:
            flash('Please enter mobile number and password', 'error')
            return render_template('login.html')
        
        # Check if user exists
        user = User.query.filter_by(mobile=mobile).first()
        
        if user:
            # Verify password
            if check_password_hash(user.password, password):
                session['user_id'] = user.user_id
                session['user_name'] = user.name
                session['profile_pic'] = user.profile_pic or '/static/images/default_dp.png'
                session['mobile'] = user.mobile
                
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                # Wrong password - redirect to register
                flash('Invalid credentials. Please register first.', 'error')
                return redirect(url_for('register'))
        else:
            # User not found - redirect to register
            flash('Account not found. Please register.', 'error')
            return redirect(url_for('register'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        mobile = request.form.get('mobile')
        email = request.form.get('email')
        location = request.form.get('location')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        profile_pic = request.form.get('profile_pic', '')
        
        # Validation
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
        
        # Check if mobile already exists
        existing_user = User.query.filter_by(mobile=mobile).first()
        if existing_user:
            errors.append('Mobile number already registered')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html')
        
        # Create new user
        hashed_password = generate_password_hash(password)
        
        new_user = User(
            name=name,
            mobile=mobile,
            email=email,
            location=location,
            password=hashed_password,
            profile_pic=profile_pic or '/static/images/default_dp.png',
            registered_at=datetime.utcnow()
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Create welcome message
            welcome_msg = Message(
                user_id=new_user.user_id,
                content='Welcome to BiteMeBuddy! 🎉 Start ordering delicious food.',
                sent_at=datetime.utcnow()
            )
            db.session.add(welcome_msg)
            db.session.commit()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    """Main dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get services (only available)
    services = Service.query.filter(
        Service.available_until > datetime.utcnow()
    ).order_by(Service.added_at.desc()).all()
    
    # Get menu items
    menus = Menu.query.order_by(Menu.serial_number).all()
    
    # Get cart count
    cart_count = Cart.query.filter_by(user_id=user_id).count()
    
    # Get unread messages
    unread_count = Message.query.filter_by(
        user_id=user_id,
        is_read=False
    ).count()
    
    return render_template('dashboard.html',
                         services=services,
                         menus=menus,
                         cart_count=cart_count,
                         unread_count=unread_count)

@app.route('/service/<int:service_id>')
def service_details(service_id):
    """Service details page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    service = Service.query.get(service_id)
    if not service:
        flash('Service not found', 'error')
        return redirect(url_for('dashboard'))
    
    items = ServiceItem.query.filter_by(
        service_id=service_id
    ).order_by(ServiceItem.serial_number).all()
    
    return render_template('service_details.html',
                         service=service,
                         items=items)

@app.route('/api/add_to_cart', methods=['POST'])
def add_to_cart():
    """Add item to cart API"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login'})
    
    try:
        data = request.get_json()
        item_type = data.get('type')
        item_id = data.get('id')
        user_id = session['user_id']
        
        # Check if already in cart
        existing = Cart.query.filter_by(
            user_id=user_id,
            item_type=item_type,
            item_id=item_id
        ).first()
        
        if existing:
            existing.quantity += 1
        else:
            cart_item = Cart(
                user_id=user_id,
                item_type=item_type,
                item_id=item_id,
                quantity=1,
                added_at=datetime.utcnow()
            )
            db.session.add(cart_item)
        
        db.session.commit()
        
        # Get updated count
        cart_count = Cart.query.filter_by(user_id=user_id).count()
        
        return jsonify({
            'success': True,
            'message': 'Added to cart',
            'cart_count': cart_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/cart')
def view_cart():
    """View cart page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    
    items_data = []
    total = 0
    
    for item in cart_items:
        if item.item_type == 'service':
            product = Service.query.get(item.item_id)
            type_name = 'Service'
        else:
            product = Menu.query.get(item.item_id)
            type_name = 'Menu Item'
        
        if product:
            item_total = product.final_price * item.quantity
            total += item_total
            
            items_data.append({
                'cart_id': item.cart_id,
                'product_id': item.item_id,
                'type': item.item_type,
                'type_name': type_name,
                'name': product.name,
                'price': product.final_price,
                'quantity': item.quantity,
                'image': product.image_url or '/static/images/default_food.jpg',
                'item_total': item_total
            })
    
    return render_template('cart.html',
                         items=items_data,
                         total=total)

@app.route('/api/update_cart', methods=['POST'])
def update_cart():
    """Update cart quantity"""
    if 'user_id' not in session:
        return jsonify({'success': False})
    
    data = request.get_json()
    cart_id = data.get('cart_id')
    action = data.get('action')
    
    cart_item = Cart.query.get(cart_id)
    if not cart_item or cart_item.user_id != session['user_id']:
        return jsonify({'success': False})
    
    if action == 'increase':
        cart_item.quantity += 1
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            db.session.delete(cart_item)
    elif action == 'remove':
        db.session.delete(cart_item)
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Checkout page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Get cart items
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    if not cart_items:
        flash('Cart is empty', 'error')
        return redirect(url_for('dashboard'))
    
    # Calculate total
    total = 0
    for item in cart_items:
        if item.item_type == 'service':
            product = Service.query.get(item.item_id)
        else:
            product = Menu.query.get(item.item_id)
        
        if product:
            total += product.final_price * item.quantity
    
    if request.method == 'POST':
        # Get form data
        address = request.form.get('address', user.location)
        payment_method = request.form.get('payment_method', 'cash')
        
        if not address:
            flash('Delivery address required', 'error')
            return render_template('checkout.html',
                                 user=user,
                                 total=total,
                                 cart_count=len(cart_items))
        
        try:
            # Create order
            order = Order(
                user_id=user_id,
                total_amount=total,
                status='Pending',
                order_date=datetime.utcnow(),
                delivery_address=address,
                payment_method=payment_method
            )
            db.session.add(order)
            db.session.flush()
            
            # Add order items
            for item in cart_items:
                if item.item_type == 'service':
                    product = Service.query.get(item.item_id)
                else:
                    product = Menu.query.get(item.item_id)
                
                if product:
                    order_item = OrderItem(
                        order_id=order.order_id,
                        item_type=item.item_type,
                        item_id=item.item_id,
                        quantity=item.quantity,
                        price=product.final_price
                    )
                    db.session.add(order_item)
            
            # Clear cart
            Cart.query.filter_by(user_id=user_id).delete()
            
            # Send confirmation
            msg = Message(
                user_id=user_id,
                content=f'Order #{order.order_id} confirmed! Total: ₹{total:.2f}',
                sent_at=datetime.utcnow()
            )
            db.session.add(msg)
            
            db.session.commit()
            
            flash(f'Order #{order.order_id} placed successfully!', 'success')
            return redirect(url_for('order_history'))
            
        except Exception as e:
            db.session.rollback()
            flash('Order failed. Try again.', 'error')
    
    return render_template('checkout.html',
                         user=user,
                         total=total,
                         cart_count=len(cart_items))

@app.route('/orders')
def order_history():
    """Order history page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    orders = Order.query.filter_by(user_id=user_id).order_by(
        Order.order_date.desc()
    ).all()
    
    return render_template('order_history.html', orders=orders)

@app.route('/profile')
def profile():
    """User profile"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Get stats
    total_orders = Order.query.filter_by(user_id=user_id).count()
    
    total_spent_result = db.session.query(
        db.func.sum(Order.total_amount)
    ).filter_by(user_id=user_id).first()
    total_spent = total_spent_result[0] or 0
    
    return render_template('profile.html',
                         user=user,
                         total_orders=total_orders,
                         total_spent=total_spent)

@app.route('/messages')
def messages():
    """User messages"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user_messages = Message.query.filter_by(user_id=user_id).order_by(
        Message.sent_at.desc()
    ).all()
    
    # Mark as read
    for msg in user_messages:
        if not msg.is_read:
            msg.is_read = True
    
    db.session.commit()
    
    return render_template('messages.html', messages=user_messages)

@app.route('/api/get_location')
def get_location():
    """Get user location API"""
    # Simplified - in production use proper geolocation
    return jsonify({
        'success': True,
        'location': 'Current Location (Approximate)'
    })

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500

# ==================== INITIALIZE ====================

def create_tables():
    """Create database tables"""
    with app.app_context():
        db.create_all()
        print("Database tables created")

if __name__ == '__main__':
    create_tables()
    app.run(debug=True, host='0.0.0.0', port=5000)
