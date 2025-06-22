# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import uuid
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Database configuration
DATABASE = 'shoptracker.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database with required tables"""
    conn = get_db_connection()
    
    # Create tables
    conn.execute('''
        CREATE TABLE IF NOT EXISTS shops (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            owner_name TEXT,
            phone TEXT,
            address TEXT,
            city TEXT,
            district TEXT,
            registration_date TEXT,
            is_active BOOLEAN DEFAULT 1,
            subscription_tier TEXT DEFAULT 'free'
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            brand TEXT,
            unit TEXT DEFAULT 'piece',
            barcode TEXT,
            default_price REAL DEFAULT 0.0,
            image_url TEXT,
            is_common BOOLEAN DEFAULT 0,
            created_date TEXT
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id TEXT PRIMARY KEY,
            shop_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            current_stock INTEGER DEFAULT 0,
            selling_price REAL DEFAULT 0.0,
            cost_price REAL DEFAULT 0.0,
            reorder_level INTEGER DEFAULT 5,
            last_updated TEXT,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (shop_id) REFERENCES shops (id),
            FOREIGN KEY (product_id) REFERENCES products (id),
            UNIQUE(shop_id, product_id)
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            shop_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price_per_unit REAL DEFAULT 0.0,
            total_amount REAL DEFAULT 0.0,
            notes TEXT,
            transaction_date TEXT,
            created_by TEXT DEFAULT 'system',
            FOREIGN KEY (shop_id) REFERENCES shops (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def seed_common_products():
    """Add common Nepali products to database"""
    common_products = [
        ('Wai Wai Chicken', 'Noodles', 'Wai Wai', 'packet', 20.0),
        ('Coca Cola 250ml', 'Beverages', 'Coca Cola', 'bottle', 25.0),
        ('Khukuri Rum 750ml', 'Alcohol', 'Khukuri', 'bottle', 800.0),
        ('Everest Masala Tea', 'Tea', 'Everest', 'packet', 15.0),
        ('Dairy Milk Chocolate', 'Chocolates', 'Cadbury', 'piece', 45.0),
        ('Kurkure Masala Munch', 'Snacks', 'Kurkure', 'packet', 10.0),
        ('Goldstar Shoes Polish', 'Personal Care', 'Goldstar', 'piece', 35.0),
        ('Ariel Washing Powder 1kg', 'Household', 'Ariel', 'packet', 180.0),
        ('Pepsi 250ml', 'Beverages', 'Pepsi', 'bottle', 23.0),
        ('Maggi Noodles', 'Noodles', 'Maggi', 'packet', 25.0),
        ('Real Juice 200ml', 'Beverages', 'Real', 'tetrapack', 30.0),
        ('Lays Classic', 'Snacks', 'Lays', 'packet', 20.0)
    ]
    
    conn = get_db_connection()
    
    # Check if products already exist
    existing = conn.execute('SELECT COUNT(*) as count FROM products WHERE is_common = 1').fetchone()
    
    if existing['count'] == 0:
        for name, category, brand, unit, price in common_products:
            product_id = str(uuid.uuid4())
            conn.execute('''
                INSERT INTO products (id, name, category, brand, unit, default_price, is_common, created_date)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            ''', (product_id, name, category, brand, unit, price, datetime.now().isoformat()))
        
        conn.commit()
        print(f"Added {len(common_products)} common products to database")
    
    conn.close()

def create_demo_shop():
    """Create a demo shop for testing"""
    conn = get_db_connection()
    
    # Check if demo shop exists
    existing = conn.execute('SELECT id FROM shops WHERE name = ?', ('Demo Shop',)).fetchone()
    
    if not existing:
        shop_id = str(uuid.uuid4())
        conn.execute('''
            INSERT INTO shops (id, name, owner_name, phone, address, city, district, registration_date, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (shop_id, 'Demo Shop', 'Demo Owner', '9841234567', 'Dhulikhel', 'Dhulikhel', 'Kavrepalanchok', 
              datetime.now().isoformat(), True))
        
        conn.commit()
        print(f"Created demo shop with ID: {shop_id}")
        
        return shop_id
    else:
        return existing['id']
    
    conn.close()

# API Routes

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products (common + custom products)"""
    try:
        conn = get_db_connection()
        
        # Get filter parameters
        category = request.args.get('category')
        is_common = request.args.get('common')
        search = request.args.get('search')
        
        query = 'SELECT * FROM products WHERE 1=1'
        params = []
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        if is_common:
            query += ' AND is_common = ?'
            params.append(1 if is_common.lower() == 'true' else 0)
        
        if search:
            query += ' AND (name LIKE ? OR brand LIKE ?)'
            search_term = f'%{search}%'
            params.extend([search_term, search_term])
        
        query += ' ORDER BY is_common DESC, name ASC'
        
        products = conn.execute(query, params).fetchall()
        conn.close()
        
        products_list = []
        for product in products:
            products_list.append({
                'id': product['id'],
                'name': product['name'],
                'category': product['category'],
                'brand': product['brand'],
                'unit': product['unit'],
                'default_price': product['default_price'],
                'is_common': bool(product['is_common']),
                'image_url': product['image_url']
            })
        
        return jsonify({
            'success': True,
            'products': products_list,
            'count': len(products_list)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/inventory/<shop_id>', methods=['GET'])
def get_inventory(shop_id):
    """Get current inventory for a shop"""
    try:
        conn = get_db_connection()
        
        # Get inventory with product details
        inventory_items = conn.execute('''
            SELECT 
                i.id,
                i.current_stock,
                i.selling_price,
                i.cost_price,
                i.reorder_level,
                i.last_updated,
                p.id as product_id,
                p.name as product_name,
                p.category,
                p.brand,
                p.unit,
                p.image_url,
                CASE WHEN i.current_stock <= i.reorder_level THEN 1 ELSE 0 END as low_stock
            FROM inventory i
            JOIN products p ON i.product_id = p.id
            WHERE i.shop_id = ? AND i.is_active = 1
            ORDER BY p.name
        ''', (shop_id,)).fetchall()
        
        conn.close()
        
        inventory_list = []
        for item in inventory_items:
            inventory_list.append({
                'id': item['id'],
                'product_id': item['product_id'],
                'product_name': item['product_name'],
                'category': item['category'],
                'brand': item['brand'],
                'unit': item['unit'],
                'current_stock': item['current_stock'],
                'selling_price': item['selling_price'],
                'cost_price': item['cost_price'],
                'reorder_level': item['reorder_level'],
                'low_stock': bool(item['low_stock']),
                'last_updated': item['last_updated'],
                'image_url': item['image_url']
            })
        
        return jsonify({
            'success': True,
            'inventory': inventory_list,
            'count': len(inventory_list)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/inventory/sale', methods=['POST'])
def record_sale():
    """Record a quick sale - reduces inventory"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['shop_id', 'product_id', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400
        
        shop_id = data['shop_id']
        product_id = data['product_id']
        quantity = int(data['quantity'])
        selling_price = data.get('selling_price', 0.0)
        
        if quantity <= 0:
            return jsonify({'success': False, 'error': 'Quantity must be positive'}), 400
        
        conn = get_db_connection()
        
        # Check if inventory exists
        inventory = conn.execute('''
            SELECT id, current_stock, selling_price 
            FROM inventory 
            WHERE shop_id = ? AND product_id = ?
        ''', (shop_id, product_id)).fetchone()
        
        if not inventory:
            # Create new inventory entry if doesn't exist
            inventory_id = str(uuid.uuid4())
            conn.execute('''
                INSERT INTO inventory (id, shop_id, product_id, current_stock, selling_price, last_updated)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (inventory_id, shop_id, product_id, 0, selling_price, datetime.now().isoformat()))
            current_stock = 0
            used_price = selling_price
        else:
            inventory_id = inventory['id']
            current_stock = inventory['current_stock']
            used_price = selling_price if selling_price > 0 else inventory['selling_price']
        
        # Check if enough stock available
        if current_stock < quantity:
            conn.close()
            return jsonify({
                'success': False, 
                'error': f'Insufficient stock. Available: {current_stock}, Requested: {quantity}'
            }), 400
        
        # Update inventory
        new_stock = current_stock - quantity
        conn.execute('''
            UPDATE inventory 
            SET current_stock = ?, selling_price = ?, last_updated = ?
            WHERE id = ?
        ''', (new_stock, used_price, datetime.now().isoformat(), inventory_id))
        
        # Record transaction
        transaction_id = str(uuid.uuid4())
        total_amount = quantity * used_price
        conn.execute('''
            INSERT INTO transactions (id, shop_id, product_id, transaction_type, quantity, 
                                    price_per_unit, total_amount, transaction_date)
            VALUES (?, ?, ?, 'sale', ?, ?, ?, ?)
        ''', (transaction_id, shop_id, product_id, quantity, used_price, total_amount, 
              datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Sale recorded successfully',
            'transaction_id': transaction_id,
            'new_stock': new_stock,
            'total_amount': total_amount
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/inventory/restock', methods=['POST'])
def record_restock():
    """Record restocking - increases inventory"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['shop_id', 'product_id', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400
        
        shop_id = data['shop_id']
        product_id = data['product_id']
        quantity = int(data['quantity'])
        cost_price = data.get('cost_price', 0.0)
        selling_price = data.get('selling_price', 0.0)
        
        if quantity <= 0:
            return jsonify({'success': False, 'error': 'Quantity must be positive'}), 400
        
        conn = get_db_connection()
        
        # Check if inventory exists
        inventory = conn.execute('''
            SELECT id, current_stock 
            FROM inventory 
            WHERE shop_id = ? AND product_id = ?
        ''', (shop_id, product_id)).fetchone()
        
        if not inventory:
            # Create new inventory entry
            inventory_id = str(uuid.uuid4())
            new_stock = quantity
            conn.execute('''
                INSERT INTO inventory (id, shop_id, product_id, current_stock, cost_price, 
                                     selling_price, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (inventory_id, shop_id, product_id, quantity, cost_price, selling_price,
                  datetime.now().isoformat()))
        else:
            # Update existing inventory
            inventory_id = inventory['id']
            new_stock = inventory['current_stock'] + quantity
            
            update_fields = ['current_stock = ?', 'last_updated = ?']
            update_values = [new_stock, datetime.now().isoformat()]
            
            if cost_price > 0:
                update_fields.append('cost_price = ?')
                update_values.append(cost_price)
            if selling_price > 0:
                update_fields.append('selling_price = ?')
                update_values.append(selling_price)
            
            update_values.append(inventory_id)
            
            conn.execute(f'''
                UPDATE inventory 
                SET {', '.join(update_fields)}
                WHERE id = ?
            ''', update_values)
        
        # Record transaction
        transaction_id = str(uuid.uuid4())
        total_cost = quantity * cost_price
        conn.execute('''
            INSERT INTO transactions (id, shop_id, product_id, transaction_type, quantity, 
                                    price_per_unit, total_amount, transaction_date)
            VALUES (?, ?, ?, 'restock', ?, ?, ?, ?)
        ''', (transaction_id, shop_id, product_id, quantity, cost_price, total_cost,
              datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Restock recorded successfully',
            'transaction_id': transaction_id,
            'new_stock': new_stock,
            'total_cost': total_cost
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/shops/<shop_id>/stats', methods=['GET'])
def get_shop_stats(shop_id):
    """Get basic statistics for a shop"""
    try:
        conn = get_db_connection()
        
        # Get total products in inventory
        total_products = conn.execute('''
            SELECT COUNT(*) as count FROM inventory WHERE shop_id = ? AND is_active = 1
        ''', (shop_id,)).fetchone()['count']
        
        # Get low stock items
        low_stock_items = conn.execute('''
            SELECT COUNT(*) as count FROM inventory 
            WHERE shop_id = ? AND current_stock <= reorder_level AND is_active = 1
        ''', (shop_id,)).fetchone()['count']
        
        # Get today's sales
        today = datetime.now().date().isoformat()
        today_sales = conn.execute('''
            SELECT COALESCE(SUM(total_amount), 0) as total,
                   COALESCE(COUNT(*), 0) as transactions
            FROM transactions 
            WHERE shop_id = ? AND transaction_type = 'sale' 
            AND DATE(transaction_date) = ?
        ''', (shop_id, today)).fetchone()
        
        # Get total inventory value
        inventory_value = conn.execute('''
            SELECT COALESCE(SUM(current_stock * selling_price), 0) as total
            FROM inventory 
            WHERE shop_id = ? AND is_active = 1
        ''', (shop_id,)).fetchone()['total']
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_products': total_products,
                'low_stock_items': low_stock_items,
                'today_sales_amount': float(today_sales['total']),
                'today_sales_count': today_sales['transactions'],
                'inventory_value': float(inventory_value)
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Utility Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'ShopTracker API is running'})

if __name__ == '__main__':
    # Initialize database on startup
    init_database()
    seed_common_products()
    demo_shop_id = create_demo_shop()
    
    print(f"ShopTracker API Starting...")
    print(f"Demo Shop ID: {demo_shop_id}")
    print(f"API Endpoints:")
    print(f"  GET  /api/products")
    print(f"  GET  /api/inventory/<shop_id>")
    print(f"  POST /api/inventory/sale")
    print(f"  POST /api/inventory/restock")
    print(f"  GET  /api/shops/<shop_id>/stats")
    
    app.run(debug=True, host='0.0.0.0', port=5000)