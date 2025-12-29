"""
Database Models
"""
from datetime import datetime
from app import db

class User(db.Model):
    """User table"""
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200))
    profile_pic = db.Column(db.String(500))
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    cart_items = db.relationship('Cart', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)
    messages = db.relationship('Message', backref='user', lazy=True)

class Service(db.Model):
    """Services table"""
    __tablename__ = 'services'
    
    service_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100))
    price = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0)
    final_price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(500))
    description = db.Column(db.Text)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    available_until = db.Column(db.DateTime)
    
    items = db.relationship('ServiceItem', backref='service', lazy=True)

class ServiceItem(db.Model):
    """Service items"""
    __tablename__ = 'service_items'
    
    item_id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.service_id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(500))
    price = db.Column(db.Float)
    description = db.Column(db.Text)
    serial_number = db.Column(db.Integer)

class Menu(db.Model):
    """Menu items"""
    __tablename__ = 'menus'
    
    menu_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(500))
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0)
    final_price = db.Column(db.Float, nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    serial_number = db.Column(db.Integer)

class Cart(db.Model):
    """Shopping cart"""
    __tablename__ = 'cart'
    
    cart_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    item_type = db.Column(db.String(20), nullable=False)  # 'service' or 'menu'
    item_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    """Orders"""
    __tablename__ = 'orders'
    
    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Pending')
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_address = db.Column(db.String(500))
    payment_method = db.Column(db.String(50))
    
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    """Order items"""
    __tablename__ = 'order_items'
    
    order_item_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    item_type = db.Column(db.String(20), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=False)

class Message(db.Model):
    """Messages"""
    __tablename__ = 'messages'
    
    message_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500))
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
