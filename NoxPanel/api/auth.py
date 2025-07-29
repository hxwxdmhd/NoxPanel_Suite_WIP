"""
Authentication API Blueprint
Handles user registration, login, logout, and JWT token management
"""

import logging
import hashlib
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from functools import wraps

logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__)

def get_db_service():
    """Get database service from app context"""
    return current_app.extensions.get('db_service')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        
        # Validate required fields
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        if len(username) < 3 or len(password) < 6:
            return jsonify({'error': 'Username must be at least 3 characters, password at least 6'}), 400
        
        # Get database service
        db_service = get_db_service()
        if not db_service:
            return jsonify({'error': 'Database service not available'}), 500
        
        # Check if user already exists
        existing_user = db_service.users.get_user_by_username(username)
        if existing_user:
            return jsonify({'error': 'Username already exists'}), 409
        
        # Create new user
        user_id = db_service.users.create_user(
            username=username,
            password=password,
            email=email,
            role='user'
        )
        
        if user_id:
            logger.info(f"New user registered: {username}")
            return jsonify({
                'message': 'User registered successfully',
                'user_id': user_id,
                'username': username
            }), 201
        else:
            return jsonify({'error': 'Failed to create user'}), 500
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT tokens"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Get database service
        db_service = get_db_service()
        if not db_service:
            return jsonify({'error': 'Database service not available'}), 500
        
        # Authenticate user
        user = db_service.users.authenticate_user(username, password)
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Import token functions from app module
        import app
        
        # Create tokens
        access_token = app.create_access_token(user['id'], user['username'], user.get('role', 'user'))
        refresh_token = app.create_refresh_token(user['id'], user['username'])
        
        # Update last login
        db_service.users.update_last_login(user['id'])
        
        logger.info(f"User logged in: {username}")
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'role': user.get('role', 'user'),
                'email': user.get('email')
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Refresh access token using refresh token"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        refresh_token = data.get('refresh_token')
        if not refresh_token:
            return jsonify({'error': 'Refresh token is required'}), 400
        
        # Import token functions from app module
        import app
        
        # Verify refresh token
        payload = app.verify_token(refresh_token)
        if not payload or payload.get('type') != 'refresh':
            return jsonify({'error': 'Invalid refresh token'}), 401
        
        # Get database service
        db_service = get_db_service()
        if not db_service:
            return jsonify({'error': 'Database service not available'}), 500
        
        # Verify user still exists and is active
        user = db_service.users.get_user_by_id(payload.get('user_id'))
        if not user or not user.get('active', True):
            return jsonify({'error': 'User not found or inactive'}), 401
        
        # Create new access token
        access_token = app.create_access_token(
            user['id'], 
            user['username'], 
            user.get('role', 'user')
        )
        
        return jsonify({
            'access_token': access_token
        }), 200
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user (client-side token removal)"""
    try:
        # For JWT, logout is mainly client-side token removal
        # In a production system, you might want to maintain a blacklist
        
        return jsonify({
            'message': 'Logout successful'
        }), 200
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/profile', methods=['GET'])
def profile():
    """Get current user profile"""
    try:
        # This endpoint requires authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header required'}), 401
        
        try:
            token = auth_header.split(' ')[1]  # Bearer <token>
        except IndexError:
            return jsonify({'error': 'Invalid token format'}), 401
        
        # Import token verification
        from .. import verify_token
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Get database service
        db_service = get_db_service()
        if not db_service:
            return jsonify({'error': 'Database service not available'}), 500
        
        # Get user details
        user = db_service.users.get_user_by_id(payload.get('user_id'))
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user.get('email'),
                'role': user.get('role', 'user'),
                'created_at': user.get('created_at'),
                'last_login': user.get('last_login')
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Profile fetch error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """Change user password"""
    try:
        # This endpoint requires authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header required'}), 401
        
        try:
            token = auth_header.split(' ')[1]  # Bearer <token>
        except IndexError:
            return jsonify({'error': 'Invalid token format'}), 401
        
        # Import token verification
        from .. import verify_token
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': 'New password must be at least 6 characters'}), 400
        
        # Get database service
        db_service = get_db_service()
        if not db_service:
            return jsonify({'error': 'Database service not available'}), 500
        
        # Verify current password
        user = db_service.users.get_user_by_id(payload.get('user_id'))
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Authenticate with current password
        if not db_service.users.authenticate_user(user['username'], current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        # Update password
        success = db_service.users.update_password(user['id'], new_password)
        if success:
            logger.info(f"Password changed for user: {user['username']}")
            return jsonify({'message': 'Password changed successfully'}), 200
        else:
            return jsonify({'error': 'Failed to update password'}), 500
        
    except Exception as e:
        logger.error(f"Password change error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Initialize the blueprint with the database service
def init_auth_bp(app, db_service):
    """Initialize the auth blueprint with database service"""
    app.extensions['db_service'] = db_service