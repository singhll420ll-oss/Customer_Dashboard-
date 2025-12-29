-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table 1: users
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    mobile VARCHAR(15) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    profile_pic_url TEXT DEFAULT 'default.jpg',
    location_lat DECIMAL(10, 8),
    location_lng DECIMAL(11, 8),
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: services (Global catalog)
CREATE TABLE IF NOT EXISTS services (
    service_id SERIAL PRIMARY KEY,
    service_name VARCHAR(200) NOT NULL,
    category VARCHAR(50),
    base_price DECIMAL(10,2) NOT NULL,
    discount DECIMAL(10,2) DEFAULT 0,
    image_url TEXT,
    description TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    available_until TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Table 3: service_items
CREATE TABLE IF NOT EXISTS service_items (
    item_id SERIAL PRIMARY KEY,
    service_id INT REFERENCES services(service_id) ON DELETE CASCADE,
    item_name VARCHAR(200) NOT NULL,
    item_price DECIMAL(10,2),
    item_image_url TEXT,
    item_description TEXT,
    serial_no INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for service items
CREATE INDEX IF NOT EXISTS idx_service ON service_items(service_id);

-- Table 4: menu_items (Global menu)
CREATE TABLE IF NOT EXISTS menu_items (
    menu_id SERIAL PRIMARY KEY,
    item_name VARCHAR(200) NOT NULL,
    base_price DECIMAL(10,2) NOT NULL,
    discount DECIMAL(10,2) DEFAULT 0,
    image_url TEXT,
    description TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    serial_no INT,
    is_available BOOLEAN DEFAULT TRUE
);

-- Table 5: cart
CREATE TABLE IF NOT EXISTS cart (
    cart_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    service_id INT REFERENCES services(service_id) ON DELETE CASCADE,
    menu_id INT REFERENCES menu_items(menu_id) ON DELETE CASCADE,
    item_type VARCHAR(10) CHECK (item_type IN ('service','menu')),
    quantity INT DEFAULT 1,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, service_id, menu_id, item_type)
);

-- Table 6: orders
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'pending',
    delivery_lat DECIMAL(10, 8),
    delivery_lng DECIMAL(11, 8),
    payment_method VARCHAR(30),
    payment_status VARCHAR(20) DEFAULT 'pending'
);

-- Create index for orders
CREATE INDEX IF NOT EXISTS idx_user_status ON orders(user_id, status);

-- Table 7: order_items
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(order_id) ON DELETE CASCADE,
    service_id INT REFERENCES services(service_id) ON DELETE SET NULL,
    menu_id INT REFERENCES menu_items(menu_id) ON DELETE SET NULL,
    item_type VARCHAR(10),
    quantity INT,
    price_at_time DECIMAL(10,2)
);

-- Create index for order items
CREATE INDEX IF NOT EXISTS idx_order ON order_items(order_id);

-- Table 8: messages (Global notifications)
CREATE TABLE IF NOT EXISTS messages (
    message_id SERIAL PRIMARY KEY,
    sender_name VARCHAR(100),
    message_text TEXT NOT NULL,
    message_image TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Insert sample data (remove in production or keep for demo)
INSERT INTO services (service_name, category, base_price, discount, description, image_url, is_active) VALUES
('Family Feast Combo', 'Combo', 1299.00, 200.00, 'Perfect for 4-5 people with variety of dishes', 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400', TRUE),
('Weekend Special Pizza', 'Pizza', 499.00, 50.00, 'Large pizza with 4 toppings of your choice', 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w-400', TRUE),
('Healthy Salad Bowl', 'Salad', 299.00, 20.00, 'Fresh vegetables with protein of choice', 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400', TRUE),
('Burger Meal Deal', 'Fast Food', 349.00, 40.00, 'Burger with fries and drink', 'https://images.unsplash.com/photo-1571091718767-18b5b14568ad?w=400', TRUE);

INSERT INTO menu_items (item_name, base_price, discount, description, image_url, serial_no, is_available) VALUES
('Margherita Pizza', 299.00, 30.00, 'Classic cheese pizza with tomato sauce', 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400', 1, TRUE),
('Chicken Burger', 199.00, 20.00, 'Grilled chicken burger with veggies', 'https://images.unsplash.com/photo-1571091718767-18b5b14568ad?w=400', 2, TRUE),
('Caesar Salad', 249.00, 25.00, 'Fresh salad with caesar dressing', 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400', 3, TRUE),
('French Fries', 99.00, 0.00, 'Crispy golden fries', 'https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=400', 4, TRUE);

INSERT INTO messages (sender_name, message_text, message_image, is_active) VALUES
('BiteMeBuddy', 'Welcome to BiteMeBuddy! Enjoy 20% off on your first order.', NULL, TRUE),
('BiteMeBuddy', 'New menu items added! Check out our specials.', NULL, TRUE),
('BiteMeBuddy', 'Weekend special: Free delivery on orders above ₹499', NULL, TRUE);
