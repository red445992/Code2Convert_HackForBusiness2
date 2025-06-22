from flask import Blueprint, request, jsonify
from services.auth_service import AuthService, token_required

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Initialize auth service
auth_service = AuthService()

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new shop"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        # Register shop
        result = auth_service.register_shop(data)
        
        if result['success']:
            return jsonify({
                'message': result['message'],
                'shop_id': result['shop_id'],
                'token': result['token'],
                'shop': result['shop_data']
            }), 201
        else:
            return jsonify({'message': result['message']}), 400
            
    except Exception as e:
        return jsonify({'message': f'Registration error: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Shop login"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        email = data.get('email')
        password = data.get('password')
        
        # Authenticate shop
        result = auth_service.login_shop(email, password)
        
        if result['success']:
            return jsonify({
                'message': result['message'],
                'token': result['token'],
                'shop': result['shop_data']
            }), 200
        else:
            return jsonify({'message': result['message']}), 401
            
    except Exception as e:
        return jsonify({'message': f'Login error: {str(e)}'}), 500

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    """Get current shop profile"""
    try:
        shop = request.current_shop
        
        return jsonify({
            'shop': {
                'id': shop['id'],
                'shop_name': shop['shop_name'],
                'owner_name': shop['owner_name'],
                'email': shop['email'],
                'phone': shop['phone'],
                'address': shop['address'],
                'city': shop['city'],
                'district': shop['district'],
                'created_at': shop['created_at'],
                'last_login_at': shop['last_login_at']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Profile error: {str(e)}'}), 500

@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile():
    """Update shop profile"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        shop_id = request.current_shop['id']
        
        # Update profile
        result = auth_service.update_shop_profile(shop_id, data)
        
        if result['success']:
            return jsonify({'message': result['message']}), 200
        else:
            return jsonify({'message': result['message']}), 400
            
    except Exception as e:
        return jsonify({'message': f'Update error: {str(e)}'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """Change shop password"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'message': 'No data provided'}), 400
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'message': 'Current and new passwords are required'}), 400
        
        shop_id = request.current_shop['id']
        
        # Change password
        result = auth_service.change_password(shop_id, current_password, new_password)
        
        if result['success']:
            return jsonify({'message': result['message']}), 200
        else:
            return jsonify({'message': result['message']}), 400
            
    except Exception as e:
        return jsonify({'message': f'Password change error: {str(e)}'}), 500

@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    """Verify JWT token"""
    try:
        data = request.get_json()
        
        if not data or 'token' not in data:
            return jsonify({'message': 'Token is required'}), 400
        
        token = data['token']
        
        # Verify token
        result = auth_service.verify_token(token)
        
        if result['success']:
            # Get shop details
            shop = auth_service.get_shop_by_id(result['payload']['shop_id'])
            
            if shop:
                return jsonify({
                    'valid': True,
                    'shop': {
                        'id': shop['id'],
                        'shop_name': shop['shop_name'],
                        'owner_name': shop['owner_name'],
                        'email': shop['email']
                    }
                }), 200
            else:
                return jsonify({'valid': False, 'message': 'Shop not found'}), 404
        else:
            return jsonify({'valid': False, 'message': result['message']}), 401
            
    except Exception as e:
        return jsonify({'message': f'Token verification error: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """Logout (client-side token removal)"""
    try:
        # In JWT, logout is typically handled client-side by removing the token
        # For additional security, you could maintain a blacklist of tokens
        
        return jsonify({
            'message': 'Logged out successfully. Please remove the token from client storage.'
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Logout error: {str(e)}'}), 500

@auth_bp.route('/refresh-token', methods=['POST'])
@token_required
def refresh_token():
    """Refresh JWT token"""
    try:
        shop = request.current_shop
        
        # Generate new token
        new_token = auth_service.generate_token(shop['id'], shop['email'])
        
        return jsonify({
            'message': 'Token refreshed successfully',
            'token': new_token
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Token refresh error: {str(e)}'}), 500

# Health check for auth service
@auth_bp.route('/health', methods=['GET'])
def auth_health():
    """Auth service health check"""
    return jsonify({
        'service': 'Authentication Service',
        'status': 'healthy',
        'endpoints': [
            'POST /auth/register',
            'POST /auth/login',
            'GET /auth/profile',
            'PUT /auth/profile',
            'POST /auth/change-password',
            'POST /auth/verify-token',
            'POST /auth/logout',
            'POST /auth/refresh-token'
        ]
    }), 200