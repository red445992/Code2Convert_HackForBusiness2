# backend/config/database_setup.py
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
import re

def create_tables():
    """Create all database tables"""
    conn = sqlite3.connect('shoptracker.db')
    cursor = conn.cursor()
    
    # Create shops table with authentication fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_name VARCHAR(255) NOT NULL,
            owner_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            phone VARCHAR(20) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            address TEXT NOT NULL,
            city VARCHAR(100),
            district VARCHAR(100),
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            shop_type VARCHAR(50) DEFAULT 'general',
            is_active BOOLEAN DEFAULT 1,
            email_verified BOOLEAN DEFAULT 0,
            phone_verified BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            last_login_at TIMESTAMP
        )
    ''')
    
    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            category VARCHAR(100),
            brand VARCHAR(100),
            barcode VARCHAR(50),
            unit VARCHAR(20) DEFAULT 'pcs',
            description TEXT,
            image_url TEXT,
            is_common BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
    ''')
    
    # Create inventory table (shop-specific stock)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            current_stock INTEGER DEFAULT 0,
            buying_price DECIMAL(10, 2),
            selling_price DECIMAL(10, 2),
            reorder_level INTEGER DEFAULT 5,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (shop_id) REFERENCES shops (id),
            FOREIGN KEY (product_id) REFERENCES products (id),
            UNIQUE(shop_id, product_id)
        )
    ''')
    
    # Create transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            transaction_type VARCHAR(20) NOT NULL, -- 'sale', 'restock', 'adjustment'
            quantity INTEGER NOT NULL,
            unit_price DECIMAL(10, 2),
            total_amount DECIMAL(10, 2),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (shop_id) REFERENCES shops (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # Create user sessions table (for session management)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL,
            device_info TEXT,
            ip_address VARCHAR(45),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (shop_id) REFERENCES shops (id)
        )
    ''')
    
    # Create password reset tokens table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_id INTEGER NOT NULL,
            token VARCHAR(255) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (shop_id) REFERENCES shops (id)
        )
    ''')
    
    # Create email verification tokens table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_verification_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_id INTEGER NOT NULL,
            token VARCHAR(255) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (shop_id) REFERENCES shops (id)
        )
    ''')
    
    # Create login attempts table (for security)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(255),
            ip_address VARCHAR(45),
            success BOOLEAN DEFAULT 0,
            attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_agent TEXT
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_shops_email ON shops(email)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_shops_phone ON shops(phone)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_inventory_shop ON inventory(shop_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_shop ON transactions(shop_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(created_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_shop ON user_sessions(shop_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(token_hash)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_login_attempts_email ON login_attempts(email)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip_address)')
    
    conn.commit()
    conn.close()
    print("Database tables created successfully!")

def insert_sample_products():
    """Insert common products for Nepali shops"""
    conn = sqlite3.connect('shoptracker.db')
    cursor = conn.cursor()
    
    common_products = [
        # Beverages
        ('Coca Cola 250ml', 'Beverages', 'Coca Cola', '1234567890123', 'bottle', 'Soft drink', None, 1),
        ('Pepsi 250ml', 'Beverages', 'Pepsi', '1234567890124', 'bottle', 'Soft drink', None, 1),
        ('Sprite 250ml', 'Beverages', 'Sprite', '1234567890125', 'bottle', 'Soft drink', None, 1),
        ('Fanta 250ml', 'Beverages', 'Fanta', '1234567890126', 'bottle', 'Soft drink', None, 1),
        ('Real Juice 200ml', 'Beverages', 'Real', '1234567890127', 'tetra pack', 'Fruit juice', None, 1),
        
        # Noodles & Snacks
        ('Wai Wai Noodles', 'Noodles', 'CG Foods', '1234567890128', 'packet', 'Instant noodles', None, 1),
        ('Rara Noodles', 'Noodles', 'Chaudhary Group', '1234567890129', 'packet', 'Instant noodles', None, 1),
        ('Mayos Noodles', 'Noodles', 'Himalayan Snax', '1234567890130', 'packet', 'Instant noodles', None, 1),
        ('Kurkure', 'Snacks', 'PepsiCo', '1234567890131', 'packet', 'Corn snacks', None, 1),
        ('Lays Chips', 'Snacks', 'PepsiCo', '1234567890132', 'packet', 'Potato chips', None, 1),
        
        # Dairy Products
        ('DDC Milk 500ml', 'Dairy', 'DDC', '1234567890133', 'packet', 'Fresh milk', None, 1),
        ('Dairy Development Corporation Curd', 'Dairy', 'DDC', '1234567890134', 'cup', 'Yogurt', None, 1),
        
        # Biscuits
        ('Parle-G Biscuits', 'Biscuits', 'Parle', '1234567890135', 'packet', 'Glucose biscuits', None, 1),
        ('Tiger Biscuits', 'Biscuits', 'Britannia', '1234567890136', 'packet', 'Cream biscuits', None, 1),
        ('Monaco Biscuits', 'Biscuits', 'Parle', '1234567890137', 'packet', 'Salty biscuits', None, 1),
        
        # Personal Care
        ('Lux Soap', 'Personal Care', 'Unilever', '1234567890138', 'bar', 'Beauty soap', None, 1),
        ('Lifebuoy Soap', 'Personal Care', 'Unilever', '1234567890139', 'bar', 'Health soap', None, 1),
        ('Fair & Lovely 50g', 'Personal Care', 'Unilever', '1234567890140', 'tube', 'Fairness cream', None, 1),
        
        # Household Items
        ('Vim Bar', 'Household', 'Hindustan Unilever', '1234567890141', 'bar', 'Dishwash bar', None, 1),
        ('Surf Excel 1kg', 'Household', 'Unilever', '1234567890142', 'packet', 'Detergent powder', None, 1),
        
        # Cigarettes & Tobacco
        ('Surya Cigarettes', 'Tobacco', 'Surya Tobacco', '1234567890143', 'packet', 'Cigarettes', None, 1),
        ('Khukuri Rum 180ml', 'Alcohol', 'Khukuri', '1234567890144', 'bottle', 'Local rum', None, 1),
        
        # Stationery
        ('Pilot Pen', 'Stationery', 'Pilot', '1234567890145', 'piece', 'Ball pen', None, 1),
        ('Copy Book', 'Stationery', 'Local', '1234567890146', 'piece', 'Exercise book', None, 1),
        
        # Mobile & Electronics
        ('Mobile Recharge Card', 'Services', 'Telecom', '1234567890147', 'card', 'Phone recharge', None, 1),
        
        # Additional Nepali Products
        ('Khukuri Beer 650ml', 'Alcohol', 'Gorkha Brewery', '1234567890148', 'bottle', 'Local beer', None, 1),
        ('Gorkha Beer 650ml', 'Alcohol', 'Gorkha Brewery', '1234567890149', 'bottle', 'Local beer', None, 1),
        ('Tuborg Beer 650ml', 'Alcohol', 'Carlsberg', '1234567890150', 'bottle', 'International beer', None, 1),
        ('Goldstar Beer 650ml', 'Alcohol', 'Carlsberg', '1234567890151', 'bottle', 'Local beer', None, 1),
        
        # Rice & Grains
        ('Basmati Rice 1kg', 'Grains', 'Various', '1234567890152', 'kg', 'Premium rice', None, 1),
        ('Normal Rice 1kg', 'Grains', 'Local', '1234567890153', 'kg', 'Regular rice', None, 1),
        ('Lentils (Masuro) 1kg', 'Grains', 'Local', '1234567890154', 'kg', 'Red lentils', None, 1),
        
        # Spices & Cooking
        ('Turmeric Powder 100g', 'Spices', 'Local', '1234567890155', 'packet', 'Spice powder', None, 1),
        ('Red Chili Powder 100g', 'Spices', 'Local', '1234567890156', 'packet', 'Spice powder', None, 1),
        ('Garam Masala 50g', 'Spices', 'Everest', '1234567890157', 'packet', 'Spice mix', None, 1),
        ('Cooking Oil 1L', 'Cooking', 'Various', '1234567890158', 'bottle', 'Refined oil', None, 1),
        
        # Tea & Coffee
        ('Red Label Tea 250g', 'Beverages', 'Brooke Bond', '1234567890159', 'packet', 'Black tea', None, 1),
        ('Nescafe Coffee 50g', 'Beverages', 'Nestle', '1234567890160', 'jar', 'Instant coffee', None, 1),
    ]
    
    for product in common_products:
        cursor.execute('''
            INSERT OR IGNORE INTO products 
            (name, category, brand, barcode, unit, description, image_url, is_common)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', product)
    
    conn.commit()
    conn.close()
    print(f"Inserted {len(common_products)} sample products!")

# Authentication Helper Functions
def hash_password(password):
    """Hash password using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"

def verify_password(password, stored_hash):
    """Verify password against stored hash"""
    try:
        salt, hash_value = stored_hash.split(':')
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return password_hash == hash_value
    except ValueError:
        return False

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate Nepali phone number format"""
    # Nepal phone numbers: +977-98xxxxxxxx or 98xxxxxxxx
    pattern = r'^(\+977[-\s]?)?[98]\d{8}$'
    return re.match(pattern, phone) is not None

def generate_token():
    """Generate secure random token"""
    return secrets.token_urlsafe(32)

def create_shop_account(shop_name, owner_name, email, phone, password, address, city, district, latitude=None, longitude=None, shop_type='general'):
    """Create a new shop account with validation"""
    
    # Validate inputs
    if not validate_email(email):
        return {"success": False, "error": "Invalid email format"}
    
    if not validate_phone(phone):
        return {"success": False, "error": "Invalid phone number format"}
    
    if len(password) < 6:
        return {"success": False, "error": "Password must be at least 6 characters long"}
    
    conn = sqlite3.connect('shoptracker.db')
    cursor = conn.cursor()
    
    try:
        # Check if email or phone already exists
        cursor.execute('SELECT id FROM shops WHERE email = ? OR phone = ?', (email, phone))
        if cursor.fetchone():
            return {"success": False, "error": "Email or phone number already registered"}
        
        # Hash password
        password_hash = hash_password(password)
        
        # Insert new shop
        cursor.execute('''
            INSERT INTO shops 
            (shop_name, owner_name, email, phone, password_hash, address, city, district, latitude, longitude, shop_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (shop_name, owner_name, email, phone, password_hash, address, city, district, latitude, longitude, shop_type))
        
        shop_id = cursor.lastrowid
        conn.commit()
        
        return {"success": True, "shop_id": shop_id, "message": "Account created successfully"}
        
    except sqlite3.IntegrityError as e:
        return {"success": False, "error": "Database constraint violation"}
    except Exception as e:
        return {"success": False, "error": f"An error occurred: {str(e)}"}
    finally:
        conn.close()

def authenticate_shop(email, password, ip_address=None, user_agent=None):
    """Authenticate shop login"""
    conn = sqlite3.connect('shoptracker.db')
    cursor = conn.cursor()
    
    try:
        # Log login attempt
        cursor.execute('''
            INSERT INTO login_attempts (email, ip_address, success, user_agent)
            VALUES (?, ?, ?, ?)
        ''', (email, ip_address, False, user_agent))
        
        # Get shop details
        cursor.execute('''
            SELECT id, password_hash, is_active FROM shops WHERE email = ?
        ''', (email,))
        
        shop = cursor.fetchone()
        
        if not shop:
            conn.commit()
            return {"success": False, "error": "Invalid email or password"}
        
        shop_id, stored_hash, is_active = shop
        
        if not is_active:
            conn.commit()
            return {"success": False, "error": "Account is deactivated"}
        
        # Verify password
        if not verify_password(password, stored_hash):
            conn.commit()
            return {"success": False, "error": "Invalid email or password"}
        
        # Update login attempt as successful
        cursor.execute('''
            UPDATE login_attempts 
            SET success = 1 
            WHERE email = ? AND ip_address = ? AND attempted_at = (
                SELECT MAX(attempted_at) FROM login_attempts WHERE email = ?
            )
        ''', (email, ip_address, email))
        
        # Update last login
        cursor.execute('''
            UPDATE shops SET last_login_at = CURRENT_TIMESTAMP WHERE id = ?
        ''', (shop_id,))
        
        # Generate session token
        session_token = generate_token()
        token_hash = hashlib.sha256(session_token.encode()).hexdigest()
        expires_at = datetime.now() + timedelta(days=30)  # 30 days session
        
        # Create session
        cursor.execute('''
            INSERT INTO user_sessions (shop_id, token_hash, ip_address, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (shop_id, token_hash, ip_address, expires_at))
        
        conn.commit()
        
        return {
            "success": True, 
            "shop_id": shop_id, 
            "session_token": session_token,
            "expires_at": expires_at.isoformat()
        }
        
    except Exception as e:
        return {"success": False, "error": f"Authentication error: {str(e)}"}
    finally:
        conn.close()

def verify_session(session_token):
    """Verify session token"""
    if not session_token:
        return {"success": False, "error": "No session token provided"}
    
    token_hash = hashlib.sha256(session_token.encode()).hexdigest()
    
    conn = sqlite3.connect('shoptracker.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT s.shop_id, sh.shop_name, sh.owner_name, sh.email 
            FROM user_sessions s
            JOIN shops sh ON s.shop_id = sh.id
            WHERE s.token_hash = ? AND s.is_active = 1 AND s.expires_at > CURRENT_TIMESTAMP
        ''', (token_hash,))
        
        session = cursor.fetchone()
        
        if not session:
            return {"success": False, "error": "Invalid or expired session"}
        
        shop_id, shop_name, owner_name, email = session
        
        return {
            "success": True,
            "shop_id": shop_id,
            "shop_name": shop_name,
            "owner_name": owner_name,
            "email": email
        }
        
    except Exception as e:
        return {"success": False, "error": f"Session verification error: {str(e)}"}
    finally:
        conn.close()

def logout_session(session_token):
    """Logout and deactivate session"""
    if not session_token:
        return {"success": False, "error": "No session token provided"}
    
    token_hash = hashlib.sha256(session_token.encode()).hexdigest()
    
    conn = sqlite3.connect('shoptracker.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE user_sessions SET is_active = 0 WHERE token_hash = ?
        ''', (token_hash,))
        
        conn.commit()
        
        return {"success": True, "message": "Logged out successfully"}
        
    except Exception as e:
        return {"success": False, "error": f"Logout error: {str(e)}"}
    finally:
        conn.close()

def cleanup_expired_sessions():
    """Clean up expired sessions and tokens"""
    conn = sqlite3.connect('shoptracker.db')
    cursor = conn.cursor()
    
    try:
        # Remove expired sessions
        cursor.execute('DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP')
        
        # Remove expired password reset tokens
        cursor.execute('DELETE FROM password_reset_tokens WHERE expires_at < CURRENT_TIMESTAMP')
        
        # Remove expired email verification tokens
        cursor.execute('DELETE FROM email_verification_tokens WHERE expires_at < CURRENT_TIMESTAMP')
        
        # Remove old login attempts (keep only last 30 days)
        cursor.execute('''
            DELETE FROM login_attempts 
            WHERE attempted_at < datetime('now', '-30 days')
        ''')
        
        conn.commit()
        print("Expired sessions and tokens cleaned up successfully!")
        
    except Exception as e:
        print(f"Cleanup error: {str(e)}")
    finally:
        conn.close()

def initialize_database():
    """Initialize database with tables and sample data"""
    print("Initializing ShopTracker database...")
    create_tables()
    insert_sample_products()
    cleanup_expired_sessions()
    print("Database initialization completed!")

if __name__ == "__main__":
    initialize_database()
    
    # Example usage of authentication functions
    print("\n--- Testing Authentication ---")
    
    # Create a test shop account
    result = create_shop_account(
        shop_name="Test Shop",
        owner_name="John Doe",
        email="test@example.com",
        phone="9812345678",
        password="test123",
        address="Kathmandu",
        city="Kathmandu",
        district="Kathmandu"
    )
    print("Account creation:", result)
    
    # Test login
    if result.get("success"):
        login_result = authenticate_shop("test@example.com", "test123", "127.0.0.1")
        print("Login result:", login_result)
        
        # Test session verification
        if login_result.get("success"):
            session_token = login_result.get("session_token")
            verify_result = verify_session(session_token)
            print("Session verification:", verify_result)
            
            # Test logout
            logout_result = logout_session(session_token)
            print("Logout result:", logout_result)