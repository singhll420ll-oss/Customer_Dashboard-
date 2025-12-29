import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_session import Session
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import bcrypt
from werkzeug.utils import secure_filename
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-123')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['UPLOAD_FOLDER'] = 'static/images/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

Session(app)

# Database connection
def get_db_connection():
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    conn.autocommit = False
    return conn

# Database initialization
def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            with open('database/schema.sql', 'r') as f:
                cur.execute(f.read())
            conn.commit()

# Auth middleware
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        mobile = request.form.get('mobile')
        password = request.form.get('password')
        
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Check if user exists
                    cur.execute("SELECT * FROM users WHERE mobile = %s", (mobile,))
                    user = cur.fetchone()
                    
                    if not user:
                        # Redirect to registration for new users
                        return redirect(url_for('register'))
                    
                    # Verify password
                    if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                        session['user_id'] = user['user_id']
                        session['full_name'] = user['full_name']
                        session['mobile'] = user['mobile']
                        return redirect(url_for('dashboard'))
                    else:
                        flash('Invalid password', 'error')
        except Exception as e:
            flash('Login failed. Please try again.', 'error')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        mobile = request.form.get('mobile')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        lat = request.form.get('lat')
        lng = request.form.get('lng')
        
        # Validation
        if not all([mobile, password, full_name]):
            flash('Please fill all required fields', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
        
        # Handle profile picture upload
        profile_pic_url = 'default.jpg'
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename:
                filename = secure_filename(f"{mobile}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                profile_pic_url = f"uploads/{filename}"
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO users (mobile, password_hash, full_name, email, 
                                         profile_pic_url, location_lat, location_lng)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING user_id
                    """, (mobile, hashed_password, full_name, email, 
                          profile_pic_url, lat, lng))
                    user_id = cur.fetchone()[0]
                    conn.commit()
                    
                    # Auto login
                    session['user_id'] = user_id
                    session['full_name'] = full_name
                    session['mobile'] = mobile
                    
                    return redirect(url_for('dashboard'))
        except psycopg2.IntegrityError:
            flash('Mobile number or email already registered', 'error')
        except Exception as e:
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('auth/register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard/index.html')

@app.route('/services')
@login_required
def services():
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM services 
                    WHERE is_active = TRUE 
                    ORDER BY added_at DESC
                """)
                services_list = cur.fetchall()
                
                # Calculate final prices
                for service in services_list:
                    service['final_price'] = float(service['base_price']) - float(service['discount'])
                
    except Exception as e:
        services_list = []
    
    return render_template('dashboard/services.html', services=services_list)

@app.route('/service/<int:service_id>')
@login_required
def service_details(service_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get service details
                cur.execute("SELECT * FROM services WHERE service_id = %s", (service_id,))
                service = cur.fetchone()
                
                if service:
                    service['final_price'] = float(service['base_price']) - float(service['discount'])
                    
                    # Get service items
                    cur.execute("""
                        SELECT * FROM service_items 
                        WHERE service_id = %s 
                        ORDER BY serial_no
                    """, (service_id,))
                    items = cur.fetchall()
                    service['items'] = items
                
                return jsonify({'service': service})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/menu')
@login_required
def menu():
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM menu_items 
                    WHERE is_available = TRUE 
                    ORDER BY serial_no
                """)
                menu_items = cur.fetchall()
                
                # Calculate final prices
                for item in menu_items:
                    item['final_price'] = float(item['base_price']) - float(item['discount'])
                
    except Exception as e:
        menu_items = []
    
    return render_template('dashboard/menu.html', menu_items=menu_items)

@app.route('/cart')
@login_required
def cart():
    user_id = session['user_id']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get cart items with details
                cur.execute("""
                    SELECT c.*, 
                           s.service_name, s.image_url as service_image, s.base_price as service_price, s.discount as service_discount,
                           m.item_name as menu_item_name, m.image_url as menu_image, m.base_price as menu_price, m.discount as menu_discount
                    FROM cart c
                    LEFT JOIN services s ON c.service_id = s.service_id AND c.item_type = 'service'
                    LEFT JOIN menu_items m ON c.menu_id = m.menu_id AND c.item_type = 'menu'
                    WHERE c.user_id = %s
                    ORDER BY c.added_at DESC
                """, (user_id,))
                cart_items = cur.fetchall()
                
                # Calculate totals
                subtotal = 0
                for item in cart_items:
                    if item['item_type'] == 'service':
                        price = float(item['service_price']) - float(item['service_discount'])
                    else:
                        price = float(item['menu_price']) - float(item['menu_discount'])
                    subtotal += price * item['quantity']
                
    except Exception as e:
        cart_items = []
        subtotal = 0
    
    return render_template('dashboard/cart.html', cart_items=cart_items, subtotal=subtotal)

@app.route('/add-to-cart', methods=['POST'])
@login_required
def add_to_cart():
    user_id = session['user_id']
    item_type = request.json.get('type')
    item_id = request.json.get('id')
    quantity = request.json.get('quantity', 1)
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if item_type == 'service':
                    # Check if already in cart
                    cur.execute("""
                        SELECT * FROM cart 
                        WHERE user_id = %s AND service_id = %s AND item_type = 'service'
                    """, (user_id, item_id))
                    existing = cur.fetchone()
                    
                    if existing:
                        # Update quantity
                        cur.execute("""
                            UPDATE cart SET quantity = quantity + %s 
                            WHERE cart_id = %s
                        """, (quantity, existing[0]))
                    else:
                        # Add new item
                        cur.execute("""
                            INSERT INTO cart (user_id, service_id, item_type, quantity)
                            VALUES (%s, %s, %s, %s)
                        """, (user_id, item_id, 'service', quantity))
                
                elif item_type == 'menu':
                    # Check if already in cart
                    cur.execute("""
                        SELECT * FROM cart 
                        WHERE user_id = %s AND menu_id = %s AND item_type = 'menu'
                    """, (user_id, item_id))
                    existing = cur.fetchone()
                    
                    if existing:
                        # Update quantity
                        cur.execute("""
                            UPDATE cart SET quantity = quantity + %s 
                            WHERE cart_id = %s
                        """, (quantity, existing[0]))
                    else:
                        # Add new item
                        cur.execute("""
                            INSERT INTO cart (user_id, menu_id, item_type, quantity)
                            VALUES (%s, %s, %s, %s)
                        """, (user_id, item_id, 'menu', quantity))
                
                conn.commit()
                return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update-cart/<int:cart_id>', methods=['POST'])
@login_required
def update_cart(cart_id):
    action = request.json.get('action')  # 'increase', 'decrease', 'remove'
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if action == 'remove':
                    cur.execute("DELETE FROM cart WHERE cart_id = %s", (cart_id,))
                else:
                    cur.execute("SELECT quantity FROM cart WHERE cart_id = %s", (cart_id,))
                    current_qty = cur.fetchone()[0]
                    
                    if action == 'increase':
                        new_qty = current_qty + 1
                    elif action == 'decrease' and current_qty > 1:
                        new_qty = current_qty - 1
                    else:
                        new_qty = current_qty
                    
                    cur.execute("UPDATE cart SET quantity = %s WHERE cart_id = %s", (new_qty, cart_id))
                
                conn.commit()
                return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    user_id = session['user_id']
    payment_method = request.json.get('payment_method')
    lat = request.json.get('lat')
    lng = request.json.get('lng')
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get cart items and calculate total
                cur.execute("""
                    SELECT c.*, 
                           s.service_id, s.base_price as service_price, s.discount as service_discount,
                           m.menu_id, m.base_price as menu_price, m.discount as menu_discount
                    FROM cart c
                    LEFT JOIN services s ON c.service_id = s.service_id AND c.item_type = 'service'
                    LEFT JOIN menu_items m ON c.menu_id = m.menu_id AND c.item_type = 'menu'
                    WHERE c.user_id = %s
                """, (user_id,))
                cart_items = cur.fetchall()
                
                if not cart_items:
                    return jsonify({'error': 'Cart is empty'}), 400
                
                # Calculate total
                total = 0
                for item in cart_items:
                    if item['item_type'] == 'service':
                        price = float(item['service_price']) - float(item['service_discount'])
                    else:
                        price = float(item['menu_price']) - float(item['menu_discount'])
                    total += price * item['quantity']
                
                # Create order
                cur.execute("""
                    INSERT INTO orders (user_id, total_amount, delivery_lat, delivery_lng, 
                                      payment_method, payment_status)
                    VALUES (%s, %s, %s, %s, %s, 'pending')
                    RETURNING order_id
                """, (user_id, total, lat, lng, payment_method))
                order_id = cur.fetchone()['order_id']
                
                # Create order items
                for item in cart_items:
                    if item['item_type'] == 'service':
                        price = float(item['service_price']) - float(item['service_discount'])
                        cur.execute("""
                            INSERT INTO order_items (order_id, service_id, item_type, quantity, price_at_time)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (order_id, item['service_id'], 'service', item['quantity'], price))
                    else:
                        price = float(item['menu_price']) - float(item['menu_discount'])
                        cur.execute("""
                            INSERT INTO order_items (order_id, menu_id, item_type, quantity, price_at_time)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (order_id, item['menu_id'], 'menu', item['quantity'], price))
                
                # Clear cart
                cur.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
                
                conn.commit()
                return jsonify({'success': True, 'order_id': order_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/orders')
@login_required
def orders():
    user_id = session['user_id']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get current orders
                cur.execute("""
                    SELECT * FROM orders 
                    WHERE user_id = %s AND status IN ('pending', 'preparing', 'delivery')
                    ORDER BY order_date DESC
                """, (user_id,))
                current_orders = cur.fetchall()
                
                # Get past orders
                cur.execute("""
                    SELECT * FROM orders 
                    WHERE user_id = %s AND status IN ('delivered', 'cancelled')
                    ORDER BY order_date DESC
                """, (user_id,))
                past_orders = cur.fetchall()
                
                # Get order items for all orders
                all_orders = current_orders + past_orders
                order_ids = [order['order_id'] for order in all_orders]
                
                if order_ids:
                    cur.execute("""
                        SELECT oi.*, 
                               s.service_name, s.image_url as service_image,
                               m.item_name as menu_item_name, m.image_url as menu_image
                        FROM order_items oi
                        LEFT JOIN services s ON oi.service_id = s.service_id AND oi.item_type = 'service'
                        LEFT JOIN menu_items m ON oi.menu_id = m.menu_id AND oi.item_type = 'menu'
                        WHERE oi.order_id = ANY(%s)
                    """, (order_ids,))
                    order_items = cur.fetchall()
                    
                    # Group items by order_id
                    items_by_order = {}
                    for item in order_items:
                        order_id = item['order_id']
                        if order_id not in items_by_order:
                            items_by_order[order_id] = []
                        items_by_order[order_id].append(item)
                else:
                    items_by_order = {}
                
    except Exception as e:
        current_orders = []
        past_orders = []
        items_by_order = {}
    
    return render_template('dashboard/orders.html', 
                         current_orders=current_orders, 
                         past_orders=past_orders,
                         items_by_order=items_by_order)

@app.route('/profile')
@login_required
def profile():
    user_id = session['user_id']
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                user = cur.fetchone()
    except Exception as e:
        user = None
    
    return render_template('dashboard/profile.html', user=user)

@app.route('/messages')
@login_required
def get_messages():
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM messages 
                    WHERE is_active = TRUE 
                    ORDER BY sent_at DESC 
                    LIMIT 5
                """)
                messages = cur.fetchall()
                return jsonify(messages)
    except Exception as e:
        return jsonify([])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Check if database needs initialization
    if not os.path.exists('database/schema.sql'):
        print("Creating database schema...")
        init_db()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') != 'production')