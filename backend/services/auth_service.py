# backend/services/auth_service.py
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
import sqlite3
import re

class AuthService:
    def __init__(self, db_path='shoptracker.db'):
        self.db_path = db_path
        self.secret_key = current_app.config.get('SECRET_KEY', 'your-secret-key-change-in-production')
        
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def hash_password(self, password):
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', 
                                          password.encode('utf-8'), 
                                          salt.encode('utf-8'), 
                                          100000)
        return f"{salt}:{password_hash.hex()}"
    
    def verify_password(self, password, hashed):
        """Verify password against hash"""
        try:
            salt, stored_hash = hashed.split(':')
            password_hash = hashlib.pbkdf2_hmac('sha256',
                                              password.encode('utf-8'),
                                              salt.encode('utf-8'),
                                              100000)
            return password_hash.hex() == stored_hash
        except:
            return False
    
    def validate_email(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_phone(self, phone):
        """Validate Nepali phone number"""
        # Nepal phone numbers: +977-XXXXXXXXX or 98XXXXXXXX
        pattern = r'^(\+977-?)?[98]\d{8}$'
        return re.match(pattern, phone) is not None
    
    def register_shop(self, shop_data):
        """Register a new shop"""
        try:
            # Validate required fields
            required_fields = ['shop_name', 'owner_name', 'email', 'phone', 'password', 'address']
            for field in required_fields:
                if not shop_data.get(field):
                    return {'success': False, 'message': f'{field} is required'}
            
            # Validate email format
            if not self.validate_email(shop_data['email']):
                return {'success': False, 'message': 'Invalid email format'}
            
            # Validate phone format
            if not self.validate_phone(shop_data['phone']):
                return {'success': False, 'message': 'Invalid phone number format'}
            
            # Check password strength
            if len(shop_data['password']) < 6:
                return {'success': False, 'message': 'Password must be at least 6 characters'}
            
            conn = self.get_db_connection()
            
            # Check if email or phone already exists
            existing = conn.execute(
                'SELECT id FROM shops WHERE email = ? OR phone = ?',
                (shop_data['email'], shop_data['phone'])
            ).fetchone()
            
            if existing:
                conn.close()
                return {'success': False, 'message': 'Email or phone already registered'}
            
            # Hash password
            password_hash = self.hash_password(shop_data['password'])
            
            # Insert new shop
            cursor = conn.execute('''
                INSERT INTO shops (shop_name, owner_name, email, phone, password_hash, 
                                 address, city, district, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                shop_data['shop_name'],
                shop_data['owner_name'],
                shop_data['email'],
                shop_data['phone'],
                password_hash,
                shop_data['address'],
                shop_data.get('city', ''),
                shop_data.get('district', ''),
                datetime.now().isoformat(),
                True
            ))
            
            shop_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Generate JWT token
            token = self.generate_token(shop_id, shop_data['email'])
            
            return {
                'success': True,
                'message': 'Shop registered successfully',
                'shop_id': shop_id,
                'token': token,
                'shop_data': {
                    'id': shop_id,
                    'shop_name': shop_data['shop_name'],
                    'owner_name': shop_data['owner_name'],
                    'email': shop_data['email'],
                    'phone': shop_data['phone']
                }
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Registration failed: {str(e)}'}
    
    def login_shop(self, email, password):
        """Authenticate shop login"""
        try:
            if not email or not password:
                return {'success': False, 'message': 'Email and password are required'}
            
            conn = self.get_db_connection()
            shop = conn.execute('''
                SELECT id, shop_name, owner_name, email, phone, password_hash, 
                       is_active, last_login_at
                FROM shops WHERE email = ?
            ''', (email,)).fetchone()
            
            if not shop:
                conn.close()
                return {'success': False, 'message': 'Invalid email or password'}
            
            if not shop['is_active']:
                conn.close()
                return {'success': False, 'message': 'Account is deactivated'}
            
            # Verify password
            if not self.verify_password(password, shop['password_hash']):
                conn.close()
                return {'success': False, 'message': 'Invalid email or password'}
            
            # Update last login
            conn.execute('''
                UPDATE shops SET last_login_at = ? WHERE id = ?
            ''', (datetime.now().isoformat(), shop['id']))
            conn.commit()
            conn.close()
            
            # Generate JWT token
            token = self.generate_token(shop['id'], shop['email'])
            
            return {
                'success': True,
                'message': 'Login successful',
                'token': token,
                'shop_data': {
                    'id': shop['id'],
                    'shop_name': shop['shop_name'],
                    'owner_name': shop['owner_name'],
                    'email': shop['email'],
                    'phone': shop['phone'],
                    'last_login': shop['last_login_at']
                }
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Login failed: {str(e)}'}
    
    def generate_token(self, shop_id, email):
        """Generate JWT token"""
        payload = {
            'shop_id': shop_id,
            'email': email,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(days=30)  # Token expires in 30 days
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        return token
    
    def verify_token(self, token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return {'success': True, 'payload': payload}
        except jwt.ExpiredSignatureError:
            return {'success': False, 'message': 'Token has expired'}
        except jwt.InvalidTokenError:
            return {'success': False, 'message': 'Invalid token'}
    
    def get_shop_by_id(self, shop_id):
        """Get shop details by ID"""
        try:
            conn = self.get_db_connection()
            shop = conn.execute('''
                SELECT id, shop_name, owner_name, email, phone, address, 
                       city, district, created_at, last_login_at, is_active
                FROM shops WHERE id = ? AND is_active = 1
            ''', (shop_id,)).fetchone()
            conn.close()
            
            if shop:
                return dict(shop)
            return None
            
        except Exception as e:
            print(f"Error getting shop: {e}")
            return None
    
    def update_shop_profile(self, shop_id, update_data):
        """Update shop profile"""
        try:
            allowed_fields = ['shop_name', 'owner_name', 'phone', 'address', 'city', 'district']
            
            # Filter allowed fields
            updates = {k: v for k, v in update_data.items() if k in allowed_fields and v}
            
            if not updates:
                return {'success': False, 'message': 'No valid fields to update'}
            
            # Validate phone if provided
            if 'phone' in updates and not self.validate_phone(updates['phone']):
                return {'success': False, 'message': 'Invalid phone number format'}
            
            conn = self.get_db_connection()
            
            # Check if new phone already exists (if phone is being updated)
            if 'phone' in updates:
                existing = conn.execute(
                    'SELECT id FROM shops WHERE phone = ? AND id != ?',
                    (updates['phone'], shop_id)
                ).fetchone()
                
                if existing:
                    conn.close()
                    return {'success': False, 'message': 'Phone number already in use'}
            
            # Build update query
            set_clause = ', '.join([f'{field} = ?' for field in updates.keys()])
            values = list(updates.values()) + [shop_id]
            
            conn.execute(f'''
                UPDATE shops SET {set_clause}, updated_at = ?
                WHERE id = ?
            ''', values + [datetime.now().isoformat()])
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': 'Profile updated successfully'}
            
        except Exception as e:
            return {'success': False, 'message': f'Update failed: {str(e)}'}
    
    def change_password(self, shop_id, current_password, new_password):
        """Change shop password"""
        try:
            if len(new_password) < 6:
                return {'success': False, 'message': 'New password must be at least 6 characters'}
            
            conn = self.get_db_connection()
            shop = conn.execute(
                'SELECT password_hash FROM shops WHERE id = ?',
                (shop_id,)
            ).fetchone()
            
            if not shop:
                conn.close()
                return {'success': False, 'message': 'Shop not found'}
            
            # Verify current password
            if not self.verify_password(current_password, shop['password_hash']):
                conn.close()
                return {'success': False, 'message': 'Current password is incorrect'}
            
            # Hash new password
            new_password_hash = self.hash_password(new_password)
            
            # Update password
            conn.execute('''
                UPDATE shops SET password_hash = ?, updated_at = ?
                WHERE id = ?
            ''', (new_password_hash, datetime.now().isoformat(), shop_id))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': 'Password changed successfully'}
            
        except Exception as e:
            return {'success': False, 'message': f'Password change failed: {str(e)}'}

# Authentication decorator
def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'message': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            auth_service = AuthService()
            result = auth_service.verify_token(token)
            
            if not result['success']:
                return jsonify({'message': result['message']}), 401
            
            # Add shop info to request context
            current_shop = auth_service.get_shop_by_id(result['payload']['shop_id'])
            if not current_shop:
                return jsonify({'message': 'Shop not found'}), 401
            
            request.current_shop = current_shop
            
        except Exception as e:
            return jsonify({'message': 'Token verification failed'}), 401
        
        return f(*args, **kwargs)
    
    return decorated