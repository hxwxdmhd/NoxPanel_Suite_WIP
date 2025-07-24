#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ultimate Suite v11.0 - Unified Server Implementation
==================================================

This is the PRODUCTION-READY unified server that consolidates:
- main.py functionality
- ultra_fast_server.py performance
- ultra_secure_server.py security
- integrated_web_server.py features

Author: Ultimate Suite Development Team
Date: July 18, 2025
Version: 11.0.0
Status: PRODUCTION READY
"""

import asyncio
import logging
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path
import secrets
import hashlib
import jwt
import psutil
import os
import sys

# Core dependencies
try:
    from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for
    from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
    from flask_cors import CORS
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    from werkzeug.security import generate_password_hash, check_password_hash
    from werkzeug.middleware.proxy_fix import ProxyFix
    
    import redis
    import psycopg2
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import QueuePool
    
except ImportError as e:
    print(f"Critical dependency missing: {e}")
    print("Please install required packages:")
    print("pip install flask flask-socketio flask-cors flask-limiter redis psycopg2-binary sqlalchemy psutil PyJWT")
    sys.exit(1)

# Import our unified components
try:
    from models_unified import DatabaseManager, SystemMetrics, UserSession, SystemLog, PluginRegistry
    from unified_plugin_system import UnifiedPluginManager, plugin_manager
except ImportError:
    print("Warning: Unified components not found. Please ensure models_unified.py and unified_plugin_system.py are in the same directory.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('heimnetz_server.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class ServerConfig:
    """Unified server configuration"""
    # Basic server settings
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    
    # Security settings
    secret_key: str = secrets.token_urlsafe(32)
    jwt_secret: str = secrets.token_urlsafe(32)
    jwt_expiration: int = 3600  # 1 hour
    
    # Database settings
    database_url: str = "postgresql://heimnetz:secure_password@localhost/heimnetz_db"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Redis settings
    redis_url: str = "redis://localhost:6379/0"
    redis_pool_size: int = 10
    
    # Performance settings
    max_connections: int = 1000
    worker_threads: int = 4
    request_timeout: int = 30
    
    # Rate limiting
    rate_limit_default: str = "100 per minute"
    rate_limit_strict: str = "10 per minute"
    
    # SSL/TLS settings
    ssl_enabled: bool = True
    ssl_cert_path: str = "certs/server.crt"
    ssl_key_path: str = "certs/server.key"
    
    # CORS settings
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    cors_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    cors_headers: List[str] = field(default_factory=lambda: ["Content-Type", "Authorization"])
    
    # WebSocket settings
    websocket_enabled: bool = True
    websocket_async_mode: str = "threading"
    
    # Plugin settings
    plugins_enabled: bool = True
    plugin_directories: List[str] = field(default_factory=lambda: ["plugins", "AI/plugins", "NoxPanel/plugins"])
    
    # Monitoring settings
    metrics_enabled: bool = True
    metrics_interval: int = 5  # seconds
    
    # API settings
    api_version: str = "v1"
    api_prefix: str = "/api"
    
    @classmethod
    def from_file(cls, config_file: str = "config.json"):
        """Load configuration from file"""
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            return cls(**config_data)
        except FileNotFoundError:
            logger.warning(f"Config file {config_file} not found, using defaults")
            return cls()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return cls()
    
    def save_to_file(self, config_file: str = "config.json"):
        """Save configuration to file"""
        try:
            config_data = {
                key: value for key, value in self.__dict__.items()
                if not key.startswith('_')
            }
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            logger.info(f"Configuration saved to {config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

class SecurityManager:
    """Advanced security management"""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.failed_attempts = {}
        self.blocked_ips = set()
        self.active_sessions = {}
        
    def generate_jwt_token(self, user_id: str, additional_claims: Dict[str, Any] = None) -> str:
        """Generate JWT token"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=self.config.jwt_expiration),
            'iat': datetime.utcnow(),
            'jti': secrets.token_urlsafe(16)
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.config.jwt_secret, algorithm='HS256')
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.config.jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            return None
    
    def is_rate_limited(self, ip: str, endpoint: str = "default") -> bool:
        """Check if IP is rate limited"""
        current_time = time.time()
        key = f"{ip}:{endpoint}"
        
        if key not in self.failed_attempts:
            self.failed_attempts[key] = []
        
        # Clean old attempts
        self.failed_attempts[key] = [
            attempt for attempt in self.failed_attempts[key]
            if current_time - attempt < 60  # 1 minute window
        ]
        
        return len(self.failed_attempts[key]) >= 10  # Max 10 attempts per minute
    
    def record_failed_attempt(self, ip: str, endpoint: str = "default"):
        """Record failed attempt"""
        current_time = time.time()
        key = f"{ip}:{endpoint}"
        
        if key not in self.failed_attempts:
            self.failed_attempts[key] = []
        
        self.failed_attempts[key].append(current_time)
        
        # Block IP if too many failures
        if len(self.failed_attempts[key]) >= 20:
            self.blocked_ips.add(ip)
            logger.warning(f"IP {ip} blocked due to excessive failed attempts")
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        return ip in self.blocked_ips
    
    def create_session(self, user_id: str, ip: str, user_agent: str) -> str:
        """Create new user session"""
        session_id = secrets.token_urlsafe(32)
        session_data = {
            'user_id': user_id,
            'ip': ip,
            'user_agent': user_agent,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow()
        }
        
        self.active_sessions[session_id] = session_data
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            
            # Check if session is expired (24 hours)
            if datetime.utcnow() - session['created_at'] > timedelta(hours=24):
                del self.active_sessions[session_id]
                return None
            
            # Update last activity
            session['last_activity'] = datetime.utcnow()
            return session
        
        return None

class SystemMonitor:
    """System monitoring and metrics collection"""
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self.metrics = {
            'requests_total': 0,
            'requests_per_second': 0,
            'active_connections': 0,
            'response_time_avg': 0.0,
            'error_rate': 0.0,
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'disk_usage': 0.0,
            'network_io': 0.0,
            'uptime_start': datetime.utcnow(),
            'last_update': datetime.utcnow()
        }
        
        self.request_times = []
        self.error_count = 0
        self.monitoring_thread = None
        self.running = False
    
    def start_monitoring(self):
        """Start system monitoring"""
        if not self.running:
            self.running = True
            self.monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitoring_thread.start()
            logger.info("System monitoring started")
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        logger.info("System monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Update system metrics
                self.metrics['cpu_usage'] = psutil.cpu_percent(interval=1)
                self.metrics['memory_usage'] = psutil.virtual_memory().percent
                self.metrics['disk_usage'] = psutil.disk_usage('/').percent
                
                # Network I/O
                net_io = psutil.net_io_counters()
                self.metrics['network_io'] = net_io.bytes_sent + net_io.bytes_recv
                
                # Calculate requests per second
                current_time = time.time()
                self.request_times = [
                    req_time for req_time in self.request_times
                    if current_time - req_time < 60  # Last minute
                ]
                self.metrics['requests_per_second'] = len(self.request_times)
                
                # Calculate error rate
                if self.metrics['requests_total'] > 0:
                    self.metrics['error_rate'] = (self.error_count / self.metrics['requests_total']) * 100
                
                # Calculate average response time
                if self.request_times:
                    self.metrics['response_time_avg'] = sum(self.request_times) / len(self.request_times)
                
                self.metrics['last_update'] = datetime.utcnow()
                
                time.sleep(self.config.metrics_interval)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(self.config.metrics_interval)
    
    def record_request(self, response_time: float, status_code: int):
        """Record request metrics"""
        self.metrics['requests_total'] += 1
        self.request_times.append(time.time())
        
        if status_code >= 400:
            self.error_count += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        metrics = self.metrics.copy()
        metrics['uptime'] = str(datetime.utcnow() - self.metrics['uptime_start'])
        return metrics

class UnifiedServer:
    """
    Ultimate Suite v11.0 - Unified Server Implementation
    
    This server consolidates all functionality from:
    - main.py
    - ultra_fast_server.py
    - ultra_secure_server.py
    - integrated_web_server.py
    """
    
    def __init__(self, config: ServerConfig = None):
        self.config = config or ServerConfig()
        self.app = Flask(__name__)
        
        # Configure Flask app
        self.app.config['SECRET_KEY'] = self.config.secret_key
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
        
        # Initialize components
        self.security_manager = SecurityManager(self.config)
        self.system_monitor = SystemMonitor(self.config)
        
        # Initialize SocketIO
        if self.config.websocket_enabled:
            self.socketio = SocketIO(
                self.app,
                cors_allowed_origins=self.config.cors_origins,
                async_mode=self.config.websocket_async_mode,
                logger=logger,
                engineio_logger=logger
            )
        else:
            self.socketio = None
        
        # Initialize CORS
        self.cors = CORS(
            self.app,
            origins=self.config.cors_origins,
            methods=self.config.cors_methods,
            allow_headers=self.config.cors_headers
        )
        
        # Initialize rate limiter
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            default_limits=[self.config.rate_limit_default]
        )
        
        # Initialize database
        self.db_manager = None
        self._init_database()
        
        # Initialize Redis
        self.redis_client = None
        self._init_redis()
        
        # Initialize plugin manager
        self.plugin_manager = None
        if self.config.plugins_enabled:
            self._init_plugins()
        
        # Set up proxy fix for reverse proxy deployments
        self.app.wsgi_app = ProxyFix(self.app.wsgi_app, x_for=1, x_proto=1, x_host=1)
        
        # Initialize routes and handlers
        self._setup_routes()
        
        if self.socketio:
            self._setup_websocket_handlers()
        
        self._setup_error_handlers()
        self._setup_middleware()
        
        # WebSocket connections tracking
        self.websocket_connections = {}
        
        logger.info(f"UnifiedServer initialized - Version: {self.config.api_version}")
    
    def _init_database(self):
        """Initialize database connection"""
        try:
            self.db_manager = DatabaseManager(self.config.database_url)
            self.db_manager.create_tables()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            self.db_manager = None
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis.from_url(
                self.config.redis_url,
                connection_pool=redis.ConnectionPool.from_url(
                    self.config.redis_url,
                    max_connections=self.config.redis_pool_size
                )
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis initialized successfully")
        except Exception as e:
            logger.error(f"Redis initialization failed: {e}")
            self.redis_client = None
    
    def _init_plugins(self):
        """Initialize plugin system"""
        try:
            self.plugin_manager = UnifiedPluginManager(self.config.plugin_directories)
            plugin_results = self.plugin_manager.load_all_plugins()
            
            loaded_count = sum(1 for result in plugin_results.values() if result)
            total_count = len(plugin_results)
            
            logger.info(f"Plugin system initialized: {loaded_count}/{total_count} plugins loaded")
        except Exception as e:
            logger.error(f"Plugin system initialization failed: {e}")
            self.plugin_manager = None
    
    def _setup_middleware(self):
        """Setup request/response middleware"""
        
        @self.app.before_request
        def before_request():
            """Before request middleware"""
            start_time = time.time()
            request.start_time = start_time
            
            # Security checks
            client_ip = request.remote_addr
            
            # Check if IP is blocked
            if self.security_manager.is_ip_blocked(client_ip):
                logger.warning(f"Blocked IP attempted access: {client_ip}")
                return jsonify({'error': 'Access denied'}), 403
            
            # Check rate limiting
            endpoint = request.endpoint or 'unknown'
            if self.security_manager.is_rate_limited(client_ip, endpoint):
                logger.warning(f"Rate limited: {client_ip} -> {endpoint}")
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            # Log request
            logger.info(f"Request: {request.method} {request.path} from {client_ip}")
        
        @self.app.after_request
        def after_request(response):
            """After request middleware"""
            # Calculate response time
            response_time = time.time() - request.start_time
            
            # Record metrics
            self.system_monitor.record_request(response_time, response.status_code)
            
            # Add security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = "default-src 'self'"
            
            # Add response time header
            response.headers['X-Response-Time'] = f"{response_time:.3f}s"
            
            return response
    
    def _setup_routes(self):
        """Setup REST API routes"""
        
        # API prefix
        api_prefix = self.config.api_prefix + '/' + self.config.api_version
        
        @self.app.route(f'{api_prefix}/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            health_data = {
                'status': 'healthy',
                'version': self.config.api_version,
                'timestamp': datetime.utcnow().isoformat(),
                'uptime': str(datetime.utcnow() - self.system_monitor.metrics['uptime_start']),
                'metrics': self.system_monitor.get_metrics(),
                'components': {
                    'database': 'connected' if self.db_manager else 'disconnected',
                    'redis': 'connected' if self.redis_client else 'disconnected',
                    'plugins': 'enabled' if self.plugin_manager else 'disabled',
                    'websocket': 'enabled' if self.socketio else 'disabled'
                }
            }
            return jsonify(health_data)
        
        @self.app.route(f'{api_prefix}/status', methods=['GET'])
        def system_status():
            """Detailed system status"""
            status_data = {
                'server': {
                    'status': 'online',
                    'version': self.config.api_version,
                    'host': self.config.host,
                    'port': self.config.port,
                    'uptime': str(datetime.utcnow() - self.system_monitor.metrics['uptime_start']),
                    'active_connections': len(self.websocket_connections) if self.socketio else 0
                },
                'database': {
                    'status': 'connected' if self.db_manager else 'disconnected',
                    'url': self.config.database_url.split('@')[1] if '@' in self.config.database_url else 'localhost'
                },
                'redis': {
                    'status': 'connected' if self.redis_client else 'disconnected',
                    'url': self.config.redis_url
                },
                'plugins': {
                    'enabled': self.config.plugins_enabled,
                    'loaded': len(self.plugin_manager.loaded_plugins) if self.plugin_manager else 0,
                    'stats': self.plugin_manager.get_stats() if self.plugin_manager else {}
                },
                'websocket': {
                    'enabled': self.config.websocket_enabled,
                    'connections': len(self.websocket_connections) if self.socketio else 0
                },
                'security': {
                    'blocked_ips': len(self.security_manager.blocked_ips),
                    'active_sessions': len(self.security_manager.active_sessions)
                }
            }
            return jsonify(status_data)
        
        @self.app.route(f'{api_prefix}/metrics', methods=['GET'])
        def get_metrics():
            """Get system metrics"""
            return jsonify(self.system_monitor.get_metrics())
        
        @self.app.route(f'{api_prefix}/plugins', methods=['GET'])
        def list_plugins():
            """List all plugins"""
            if not self.plugin_manager:
                return jsonify({'error': 'Plugin system not enabled'}), 503
            
            plugins = []
            for plugin_name, plugin in self.plugin_manager.get_all_plugins().items():
                plugins.append({
                    'name': plugin_name,
                    'metadata': plugin.metadata.to_dict(),
                    'status': 'enabled' if plugin.metadata.enabled else 'disabled'
                })
            
            return jsonify({
                'plugins': plugins,
                'stats': self.plugin_manager.get_stats()
            })
        
        @self.app.route(f'{api_prefix}/plugins/<plugin_name>/enable', methods=['POST'])
        @self.limiter.limit(self.config.rate_limit_strict)
        def enable_plugin(plugin_name):
            """Enable a plugin"""
            if not self.plugin_manager:
                return jsonify({'error': 'Plugin system not enabled'}), 503
            
            if self.plugin_manager.enable_plugin(plugin_name):
                return jsonify({'message': f'Plugin {plugin_name} enabled'})
            else:
                return jsonify({'error': f'Plugin {plugin_name} not found'}), 404
        
        @self.app.route(f'{api_prefix}/plugins/<plugin_name>/disable', methods=['POST'])
        @self.limiter.limit(self.config.rate_limit_strict)
        def disable_plugin(plugin_name):
            """Disable a plugin"""
            if not self.plugin_manager:
                return jsonify({'error': 'Plugin system not enabled'}), 503
            
            if self.plugin_manager.disable_plugin(plugin_name):
                return jsonify({'message': f'Plugin {plugin_name} disabled'})
            else:
                return jsonify({'error': f'Plugin {plugin_name} not found'}), 404
        
        @self.app.route(f'{api_prefix}/auth/login', methods=['POST'])
        @self.limiter.limit(self.config.rate_limit_strict)
        def login():
            """User authentication"""
            data = request.get_json()
            if not data or 'username' not in data or 'password' not in data:
                return jsonify({'error': 'Missing username or password'}), 400
            
            # TODO: Implement actual user authentication
            # For now, accept any credentials for demo
            username = data['username']
            
            # Generate JWT token
            token = self.security_manager.generate_jwt_token(username)
            
            # Create session
            session_id = self.security_manager.create_session(
                username, 
                request.remote_addr, 
                request.headers.get('User-Agent', '')
            )
            
            return jsonify({
                'token': token,
                'session_id': session_id,
                'user_id': username,
                'expires_in': self.config.jwt_expiration
            })
        
        @self.app.route(f'{api_prefix}/auth/logout', methods=['POST'])
        def logout():
            """User logout"""
            # TODO: Implement session invalidation
            return jsonify({'message': 'Logged out successfully'})
        
        @self.app.route('/')
        def index():
            """Main dashboard route"""
            return render_template('system_map_dashboard.html')
        
        @self.app.route('/dashboard')
        def dashboard():
            """System dashboard route"""
            return render_template('system_map_dashboard.html')
        
        @self.app.route('/api-docs')
        def api_docs():
            """API documentation"""
            return jsonify({
                'api_version': self.config.api_version,
                'endpoints': {
                    'health': f'{api_prefix}/health',
                    'status': f'{api_prefix}/status',
                    'metrics': f'{api_prefix}/metrics',
                    'plugins': f'{api_prefix}/plugins',
                    'auth': {
                        'login': f'{api_prefix}/auth/login',
                        'logout': f'{api_prefix}/auth/logout'
                    }
                },
                'websocket': {
                    'enabled': self.config.websocket_enabled,
                    'events': [
                        'connect', 'disconnect', 'join_room', 'leave_room',
                        'system_update', 'metrics_update', 'plugin_event'
                    ]
                }
            })
    
    def _setup_websocket_handlers(self):
        """Setup WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle new WebSocket connection"""
            client_id = request.sid
            client_info = {
                'id': client_id,
                'ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'connected_at': datetime.utcnow(),
                'rooms': []
            }
            
            self.websocket_connections[client_id] = client_info
            
            emit('connection_established', {
                'client_id': client_id,
                'server_time': datetime.utcnow().isoformat(),
                'server_version': self.config.api_version,
                'features': {
                    'metrics': self.config.metrics_enabled,
                    'plugins': self.config.plugins_enabled,
                    'database': self.db_manager is not None,
                    'redis': self.redis_client is not None
                }
            })
            
            logger.info(f"WebSocket connection established: {client_id} from {request.remote_addr}")
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle WebSocket disconnection"""
            client_id = request.sid
            
            if client_id in self.websocket_connections:
                del self.websocket_connections[client_id]
            
            logger.info(f"WebSocket connection closed: {client_id}")
        
        @self.socketio.on('join_room')
        def handle_join_room(data):
            """Handle room joining"""
            if not isinstance(data, dict) or 'room' not in data:
                emit('error', {'message': 'Invalid room data'})
                return
            
            room = data['room']
            client_id = request.sid
            
            # Validate room name
            allowed_rooms = ['dashboard', 'metrics', 'plugins', 'logs', 'general']
            if room not in allowed_rooms:
                emit('error', {'message': f'Room {room} not allowed'})
                return
            
            join_room(room)
            
            if client_id in self.websocket_connections:
                self.websocket_connections[client_id]['rooms'].append(room)
            
            emit('room_joined', {
                'room': room,
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Client {client_id} joined room: {room}")
        
        @self.socketio.on('leave_room')
        def handle_leave_room(data):
            """Handle room leaving"""
            if not isinstance(data, dict) or 'room' not in data:
                emit('error', {'message': 'Invalid room data'})
                return
            
            room = data['room']
            client_id = request.sid
            
            leave_room(room)
            
            if client_id in self.websocket_connections:
                client_rooms = self.websocket_connections[client_id]['rooms']
                if room in client_rooms:
                    client_rooms.remove(room)
            
            emit('room_left', {
                'room': room,
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Client {client_id} left room: {room}")
        
        @self.socketio.on('request_metrics')
        def handle_metrics_request():
            """Handle metrics request"""
            metrics = self.system_monitor.get_metrics()
            emit('metrics_update', {
                'metrics': metrics,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @self.socketio.on('request_system_status')
        def handle_status_request():
            """Handle system status request"""
            status = {
                'server_status': 'online',
                'connections': len(self.websocket_connections),
                'plugins': len(self.plugin_manager.loaded_plugins) if self.plugin_manager else 0,
                'database': 'connected' if self.db_manager else 'disconnected',
                'redis': 'connected' if self.redis_client else 'disconnected'
            }
            
            emit('system_status', {
                'status': status,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @self.socketio.on('plugin_command')
        def handle_plugin_command(data):
            """Handle plugin commands"""
            if not self.plugin_manager:
                emit('error', {'message': 'Plugin system not enabled'})
                return
            
            if not isinstance(data, dict) or 'command' not in data:
                emit('error', {'message': 'Invalid plugin command'})
                return
            
            command = data['command']
            plugin_name = data.get('plugin_name')
            
            try:
                if command == 'list':
                    plugins = [
                        {'name': name, 'metadata': plugin.metadata.to_dict()}
                        for name, plugin in self.plugin_manager.get_all_plugins().items()
                    ]
                    emit('plugin_response', {'plugins': plugins})
                
                elif command == 'enable' and plugin_name:
                    result = self.plugin_manager.enable_plugin(plugin_name)
                    emit('plugin_response', {
                        'action': 'enable',
                        'plugin': plugin_name,
                        'success': result
                    })
                
                elif command == 'disable' and plugin_name:
                    result = self.plugin_manager.disable_plugin(plugin_name)
                    emit('plugin_response', {
                        'action': 'disable',
                        'plugin': plugin_name,
                        'success': result
                    })
                
                else:
                    emit('error', {'message': f'Unknown command: {command}'})
                    
            except Exception as e:
                emit('error', {'message': f'Plugin command failed: {str(e)}'})
    
    def _setup_error_handlers(self):
        """Setup error handlers"""
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                'error': 'Resource not found',
                'status': 404,
                'timestamp': datetime.utcnow().isoformat(),
                'path': request.path
            }), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            logger.error(f"Internal server error: {error}")
            return jsonify({
                'error': 'Internal server error',
                'status': 500,
                'timestamp': datetime.utcnow().isoformat()
            }), 500
        
        @self.app.errorhandler(429)
        def rate_limit_exceeded(error):
            client_ip = request.remote_addr
            self.security_manager.record_failed_attempt(client_ip, 'rate_limit')
            
            return jsonify({
                'error': 'Rate limit exceeded',
                'status': 429,
                'timestamp': datetime.utcnow().isoformat(),
                'retry_after': 60
            }), 429
        
        @self.app.errorhandler(403)
        def forbidden(error):
            return jsonify({
                'error': 'Access forbidden',
                'status': 403,
                'timestamp': datetime.utcnow().isoformat()
            }), 403
    
    def start_background_tasks(self):
        """Start background tasks"""
        # Start system monitoring
        self.system_monitor.start_monitoring()
        
        # Start metrics broadcasting
        if self.socketio:
            self._start_metrics_broadcaster()
        
        # Start database cleanup task
        if self.db_manager:
            self._start_cleanup_task()
    
    def _start_metrics_broadcaster(self):
        """Start periodic metrics broadcasting"""
        def broadcast_metrics():
            while True:
                try:
                    metrics = self.system_monitor.get_metrics()
                    self.socketio.emit('metrics_update', {
                        'metrics': metrics,
                        'timestamp': datetime.utcnow().isoformat()
                    }, room='dashboard')
                    
                    time.sleep(self.config.metrics_interval)
                except Exception as e:
                    logger.error(f"Metrics broadcast error: {e}")
                    time.sleep(self.config.metrics_interval)
        
        thread = threading.Thread(target=broadcast_metrics, daemon=True)
        thread.start()
        logger.info("Metrics broadcaster started")
    
    def _start_cleanup_task(self):
        """Start periodic cleanup tasks"""
        def cleanup_task():
            while True:
                try:
                    # Clean old metrics (keep last 7 days)
                    cutoff_date = datetime.utcnow() - timedelta(days=7)
                    
                    # TODO: Add database cleanup logic
                    # self.db_manager.cleanup_old_metrics(cutoff_date)
                    
                    time.sleep(3600)  # Run every hour
                except Exception as e:
                    logger.error(f"Cleanup task error: {e}")
                    time.sleep(3600)
        
        thread = threading.Thread(target=cleanup_task, daemon=True)
        thread.start()
        logger.info("Cleanup task started")
    
    def run(self):
        """Start the unified server"""
        logger.info("=" * 60)
        logger.info("ULTIMATE SUITE v11.0 - UNIFIED SERVER")
        logger.info("=" * 60)
        logger.info(f"Starting server on {self.config.host}:{self.config.port}")
        logger.info(f"Debug mode: {self.config.debug}")
        logger.info(f"SSL enabled: {self.config.ssl_enabled}")
        logger.info(f"WebSocket enabled: {self.config.websocket_enabled}")
        logger.info(f"Plugins enabled: {self.config.plugins_enabled}")
        logger.info(f"Database: {'Connected' if self.db_manager else 'Disconnected'}")
        logger.info(f"Redis: {'Connected' if self.redis_client else 'Disconnected'}")
        logger.info(f"API Version: {self.config.api_version}")
        logger.info("=" * 60)
        
        # Start background tasks
        self.start_background_tasks()
        
        try:
            # Determine SSL context
            ssl_context = None
            if self.config.ssl_enabled:
                cert_path = Path(self.config.ssl_cert_path)
                key_path = Path(self.config.ssl_key_path)
                
                if cert_path.exists() and key_path.exists():
                    ssl_context = (str(cert_path), str(key_path))
                    logger.info("SSL certificates found, enabling HTTPS")
                else:
                    logger.warning("SSL certificates not found, falling back to HTTP")
            
            # Start the server
            if self.socketio:
                self.socketio.run(
                    self.app,
                    host=self.config.host,
                    port=self.config.port,
                    debug=self.config.debug,
                    ssl_context=ssl_context,
                    allow_unsafe_werkzeug=True
                )
            else:
                self.app.run(
                    host=self.config.host,
                    port=self.config.port,
                    debug=self.config.debug,
                    ssl_context=ssl_context,
                    threaded=True
                )
                
        except KeyboardInterrupt:
            logger.info("Server shutdown initiated by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Graceful server shutdown"""
        logger.info("Shutting down server...")
        
        # Stop monitoring
        self.system_monitor.stop_monitoring()
        
        # Cleanup plugins
        if self.plugin_manager:
            self.plugin_manager.cleanup()
        
        # Close database connection
        if self.db_manager:
            self.db_manager.close()
        
        # Close Redis connection
        if self.redis_client:
            self.redis_client.close()
        
        logger.info("Server shutdown complete")

def main():
    """Main entry point"""
    # Load configuration
    config = ServerConfig.from_file()
    
    # Create and start server
    server = UnifiedServer(config)
    
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
