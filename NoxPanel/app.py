"""
Main Flask Application for NoxPanel System
Enhanced with WebSocket support, JWT authentication, and comprehensive API endpoints
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import jwt
from functools import wraps

# Import existing services
from noxcore.database_service import DatabaseService
from noxcore.utils.config import NoxConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NoxPanelApp:
    """Main NoxPanel Application"""
    
    def __init__(self, config_path=None):
        """Initialize the application"""
        self.app = Flask(__name__)
        self.config = NoxConfig(config_path or 'config')
        self._configure_app()
        self._setup_cors()
        self._setup_socketio()
        self._initialize_database()
        self._register_blueprints()
        self._setup_error_handlers()
        
    def _configure_app(self):
        """Configure Flask application"""
        self.app.config.update({
            'SECRET_KEY': os.getenv('FLASK_SECRET_KEY', 'nox-panel-secret-key-change-me'),
            'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-me'),
            'JWT_ACCESS_TOKEN_EXPIRES': timedelta(minutes=15),
            'JWT_REFRESH_TOKEN_EXPIRES': timedelta(days=7),
            'DATABASE_URL': os.getenv('DATABASE_URL', 'data/db/noxpanel.db'),
            'DEBUG': os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        })
        
    def _setup_cors(self):
        """Setup CORS for frontend communication"""
        CORS(self.app, 
             origins=['http://localhost:3000', 'http://localhost:5000'],
             supports_credentials=True,
             allow_headers=['Content-Type', 'Authorization'])
        
    def _setup_socketio(self):
        """Setup Socket.IO for real-time communication"""
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins=['http://localhost:3000', 'http://localhost:5000'],
            ping_timeout=60,
            ping_interval=25
        )
        
    def _initialize_database(self):
        """Initialize database service"""
        db_path = self.app.config['DATABASE_URL']
        self.db_service = DatabaseService(db_path=db_path, auto_migrate=True)
        logger.info(f"Database initialized at: {db_path}")
        
    def _register_blueprints(self):
        """Register API blueprints"""
        try:
            from api.auth import auth_bp
            from api.dashboard import dashboard_bp
            from api.security import security_bp
            from api.plugins import plugins_bp
            from api.crawler import crawler_bp
            
            # Initialize blueprints with database service
            self.app.extensions['db_service'] = self.db_service
            
            # Register blueprints with API prefix
            self.app.register_blueprint(auth_bp, url_prefix='/api/auth')
            self.app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
            self.app.register_blueprint(security_bp, url_prefix='/api/security')
            self.app.register_blueprint(plugins_bp, url_prefix='/api/plugins')
            self.app.register_blueprint(crawler_bp, url_prefix='/api/crawler')
            
            # Register WebSocket handlers
            from api.websocket import register_websocket_handlers
            register_websocket_handlers(self.socketio, self.db_service)
            
            logger.info("API blueprints registered successfully")
            
        except Exception as e:
            logger.error(f"Failed to register blueprints: {e}")
            # Continue without API blueprints for basic functionality
        
    def _setup_error_handlers(self):
        """Setup global error handlers"""
        
        @self.app.errorhandler(400)
        def bad_request(error):
            return jsonify({'error': 'Bad request', 'message': str(error)}), 400
            
        @self.app.errorhandler(401)
        def unauthorized(error):
            return jsonify({'error': 'Unauthorized', 'message': 'Invalid credentials'}), 401
            
        @self.app.errorhandler(403)
        def forbidden(error):
            return jsonify({'error': 'Forbidden', 'message': 'Insufficient permissions'}), 403
            
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': 'Not found', 'message': 'Resource not found'}), 404
            
        @self.app.errorhandler(500)
        def internal_error(error):
            logger.error(f"Internal server error: {error}")
            return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500
    
    def setup_routes(self):
        """Setup basic application routes"""
        
        @self.app.route('/')
        def index():
            """Health check endpoint"""
            return jsonify({
                'status': 'ok',
                'service': 'NoxPanel',
                'version': '1.0.0',
                'timestamp': datetime.utcnow().isoformat()
            })
            
        @self.app.route('/health')
        def health():
            """Detailed health check"""
            try:
                # Test database connection
                with self.db_service.db.get_connection() as conn:
                    conn.execute('SELECT 1')
                    db_status = 'healthy'
            except Exception as e:
                db_status = f'error: {str(e)}'
                
            return jsonify({
                'status': 'healthy' if db_status == 'healthy' else 'degraded',
                'checks': {
                    'database': db_status,
                    'socketio': 'healthy'
                },
                'timestamp': datetime.utcnow().isoformat()
            })
            
        @self.app.route('/api/status')
        def api_status():
            """API status endpoint"""
            return jsonify({
                'api_version': 'v1',
                'endpoints': {
                    'auth': '/api/auth',
                    'dashboard': '/api/dashboard',
                    'security': '/api/security',
                    'plugins': '/api/plugins',
                    'crawler': '/api/crawler'
                },
                'websocket': '/socket.io',
                'documentation': '/api/docs'
            })
    
    def run(self, host='0.0.0.0', port=5001, debug=None):
        """Run the application"""
        if debug is None:
            debug = self.app.config['DEBUG']
            
        logger.info(f"Starting NoxPanel on {host}:{port}")
        self.socketio.run(
            self.app,
            host=host,
            port=port,
            debug=debug,
            allow_unsafe_werkzeug=True
        )

# JWT utility functions
def create_access_token(user_id, username, role='user'):
    """Create JWT access token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(minutes=15),
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    return jwt.encode(payload, os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-me'), algorithm='HS256')

def create_refresh_token(user_id, username):
    """Create JWT refresh token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow(),
        'type': 'refresh'
    }
    return jwt.encode(payload, os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-me'), algorithm='HS256')

def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-me'), algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator for routes that require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        payload = verify_token(token)
        if payload is None:
            return jsonify({'error': 'Token is invalid or expired'}), 401
        
        # Add user info to request context
        request.current_user = {
            'user_id': payload.get('user_id'),
            'username': payload.get('username'),
            'role': payload.get('role', 'user')
        }
        
        return f(*args, **kwargs)
    return decorated

def role_required(required_role):
    """Decorator for routes that require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, 'current_user'):
                return jsonify({'error': 'Authentication required'}), 401
            
            user_role = request.current_user.get('role', 'user')
            if user_role != required_role and user_role != 'admin':
                return jsonify({'error': f'Role {required_role} required'}), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator

# Application factory
def create_app(config_path=None):
    """Create and configure the Flask application"""
    nox_app = NoxPanelApp(config_path)
    nox_app.setup_routes()
    return nox_app.app, nox_app.socketio

if __name__ == '__main__':
    # Create application instance
    nox_app = NoxPanelApp()
    nox_app.setup_routes()
    
    # Run the application
    nox_app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5001)),
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )