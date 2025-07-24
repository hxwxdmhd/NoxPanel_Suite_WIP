#!/usr/bin/env python3
"""
ULTIMATE SUITE v11.0 - ADVANCED SERVER
Week 2 Implementation: Security, Performance, and Production Features

Author: Ultimate Suite Development Team
Date: July 18, 2025
Version: v2.0 (Advanced)
"""

import os
import sys
import json
import time
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from functools import wraps
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Core Flask and Extensions
from flask import Flask, request, jsonify, render_template_string, session, g
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_caching import Cache

# Database and ORM
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
import sqlite3

# Security and Validation
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
import bleach
import re

# Monitoring and Metrics
import psutil
import redis
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.environ.get('DATABASE_URL', f'sqlite:///{BASE_DIR}/heimnetz_advanced.db')
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_urlsafe(32))
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', secrets.token_urlsafe(32))

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('advanced_server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Prometheus Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('websocket_connections_active', 'Active WebSocket connections')
SYSTEM_CPU = Gauge('system_cpu_percent', 'System CPU usage percentage')
SYSTEM_MEMORY = Gauge('system_memory_percent', 'System memory usage percentage')

# Database Models
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(20), default='user')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    __table_args__ = (
        Index('idx_username', 'username'),
        Index('idx_email', 'email'),
    )

class SystemMetrics(Base):
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    cpu_percent = Column(Float)
    memory_percent = Column(Float)
    disk_percent = Column(Float)
    network_bytes_sent = Column(Integer)
    network_bytes_recv = Column(Integer)
    active_connections = Column(Integer)
    request_count = Column(Integer)
    avg_response_time = Column(Float)
    
    __table_args__ = (
        Index('idx_timestamp', 'timestamp'),
    )

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer)
    action = Column(String(100))
    resource = Column(String(100))
    details = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    __table_args__ = (
        Index('idx_timestamp_user', 'timestamp', 'user_id'),
    )

@dataclass
class SecurityConfig:
    """Security configuration settings"""
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digit: bool = True
    password_require_special: bool = True
    session_timeout: int = 3600  # 1 hour
    max_login_attempts: int = 5
    lockout_duration: int = 900  # 15 minutes
    jwt_expiration: int = 86400  # 24 hours

class SecurityManager:
    """Advanced security management system"""
    
    def __init__(self):
        self.config = SecurityConfig()
        self.failed_attempts = {}
        self.lockout_times = {}
        
    def validate_password(self, password: str) -> Dict[str, Any]:
        """Validate password strength"""
        errors = []
        
        if len(password) < self.config.password_min_length:
            errors.append(f"Password must be at least {self.config.password_min_length} characters")
        
        if self.config.password_require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.config.password_require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.config.password_require_digit and not re.search(r'[0-9]', password):
            errors.append("Password must contain at least one digit")
        
        if self.config.password_require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'strength': self._calculate_strength(password)
        }
    
    def _calculate_strength(self, password: str) -> int:
        """Calculate password strength score (0-100)"""
        score = 0
        
        # Length bonus
        score += min(len(password) * 2, 20)
        
        # Character variety bonus
        if re.search(r'[a-z]', password):
            score += 10
        if re.search(r'[A-Z]', password):
            score += 10
        if re.search(r'[0-9]', password):
            score += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 15
        
        # Complexity bonus
        if len(set(password)) / len(password) > 0.7:
            score += 15
        
        # Pattern penalty
        if re.search(r'(.)\1{2,}', password):
            score -= 10
        if re.search(r'(012|123|234|345|456|567|678|789|890)', password):
            score -= 5
        
        return max(0, min(100, score))
    
    def is_account_locked(self, identifier: str) -> bool:
        """Check if account is locked due to failed attempts"""
        if identifier not in self.lockout_times:
            return False
        
        if datetime.utcnow() > self.lockout_times[identifier]:
            del self.lockout_times[identifier]
            if identifier in self.failed_attempts:
                del self.failed_attempts[identifier]
            return False
        
        return True
    
    def record_failed_attempt(self, identifier: str):
        """Record failed login attempt"""
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = 0
        
        self.failed_attempts[identifier] += 1
        
        if self.failed_attempts[identifier] >= self.config.max_login_attempts:
            self.lockout_times[identifier] = datetime.utcnow() + timedelta(seconds=self.config.lockout_duration)
    
    def reset_failed_attempts(self, identifier: str):
        """Reset failed attempts counter"""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]
        if identifier in self.lockout_times:
            del self.lockout_times[identifier]
    
    def sanitize_input(self, text: str) -> str:
        """Sanitize user input"""
        return bleach.clean(text, tags=[], attributes={}, strip=True)
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

class PerformanceMonitor:
    """Advanced performance monitoring system"""
    
    def __init__(self):
        self.metrics_history = []
        self.alert_thresholds = {
            'cpu': 80.0,
            'memory': 85.0,
            'disk': 90.0,
            'response_time': 1.0
        }
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system metrics"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            
            metrics = {
                'timestamp': datetime.utcnow().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available,
                'memory_used': memory.used,
                'disk_percent': disk.percent,
                'disk_free': disk.free,
                'disk_used': disk.used,
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_recv': network.bytes_recv,
                'process_memory_rss': process_memory.rss,
                'process_memory_vms': process_memory.vms,
                'active_connections': len(getattr(g, 'websocket_connections', [])),
                'uptime': (datetime.utcnow() - getattr(g, 'server_start_time', datetime.utcnow())).total_seconds()
            }
            
            # Update Prometheus metrics
            SYSTEM_CPU.set(cpu_percent)
            SYSTEM_MEMORY.set(memory.percent)
            
            # Store in history
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > 1000:
                self.metrics_history.pop(0)
            
            # Check for alerts
            self._check_alerts(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return {}
    
    def _check_alerts(self, metrics: Dict[str, Any]):
        """Check for performance alerts"""
        alerts = []
        
        if metrics['cpu_percent'] > self.alert_thresholds['cpu']:
            alerts.append({
                'type': 'cpu_high',
                'message': f"High CPU usage: {metrics['cpu_percent']:.1f}%",
                'severity': 'warning'
            })
        
        if metrics['memory_percent'] > self.alert_thresholds['memory']:
            alerts.append({
                'type': 'memory_high',
                'message': f"High memory usage: {metrics['memory_percent']:.1f}%",
                'severity': 'warning'
            })
        
        if metrics['disk_percent'] > self.alert_thresholds['disk']:
            alerts.append({
                'type': 'disk_high',
                'message': f"High disk usage: {metrics['disk_percent']:.1f}%",
                'severity': 'critical'
            })
        
        if alerts:
            logger.warning(f"Performance alerts: {alerts}")
            # Emit alerts via WebSocket
            if hasattr(g, 'socketio'):
                g.socketio.emit('performance_alert', {'alerts': alerts})

class CacheManager:
    """Advanced caching system with Redis support"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or REDIS_URL
        self.redis_client = None
        self.memory_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
        
        try:
            self.redis_client = redis.from_url(self.redis_url, socket_connect_timeout=5)
            self.redis_client.ping()
            logger.info("Redis cache connected successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using memory cache.")
            self.redis_client = None
    
    def get(self, key: str) -> Any:
        """Get value from cache"""
        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    self.cache_stats['hits'] += 1
                    return json.loads(value)
            else:
                if key in self.memory_cache:
                    entry = self.memory_cache[key]
                    if entry['expires'] > datetime.utcnow():
                        self.cache_stats['hits'] += 1
                        return entry['value']
                    else:
                        del self.memory_cache[key]
            
            self.cache_stats['misses'] += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.cache_stats['misses'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache"""
        try:
            if self.redis_client:
                self.redis_client.setex(key, ttl, json.dumps(value))
            else:
                self.memory_cache[key] = {
                    'value': value,
                    'expires': datetime.utcnow() + timedelta(seconds=ttl)
                }
            
            self.cache_stats['sets'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if self.redis_client:
                self.redis_client.delete(key)
            else:
                if key in self.memory_cache:
                    del self.memory_cache[key]
            
            self.cache_stats['deletes'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache entries"""
        try:
            if self.redis_client:
                self.redis_client.flushdb()
            else:
                self.memory_cache.clear()
            
            return True
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'sets': self.cache_stats['sets'],
            'deletes': self.cache_stats['deletes'],
            'hit_rate': hit_rate,
            'total_requests': total_requests,
            'backend': 'redis' if self.redis_client else 'memory'
        }

class AdvancedServer:
    """Ultimate Suite v11.0 - Advanced Server Implementation"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_configuration()
        self.setup_database()
        self.setup_security()
        self.setup_caching()
        self.setup_monitoring()
        self.setup_websocket()
        self.setup_routes()
        self.setup_error_handlers()
        
        # Initialize managers
        self.security_manager = SecurityManager()
        self.performance_monitor = PerformanceMonitor()
        self.cache_manager = CacheManager()
        
        # Server state
        self.server_start_time = datetime.utcnow()
        self.websocket_connections = set()
        
        logger.info("AdvancedServer initialized successfully")
    
    def setup_configuration(self):
        """Configure Flask application"""
        self.app.config.update({
            'SECRET_KEY': SECRET_KEY,
            'JWT_SECRET_KEY': JWT_SECRET_KEY,
            'JWT_ACCESS_TOKEN_EXPIRES': timedelta(hours=24),
            'SQLALCHEMY_DATABASE_URI': DATABASE_URL,
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'CACHE_TYPE': 'redis',
            'CACHE_REDIS_URL': REDIS_URL,
            'RATELIMIT_STORAGE_URL': REDIS_URL,
            'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max file size
        })
        
        # Trust proxy headers
        self.app.wsgi_app = ProxyFix(self.app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    
    def setup_database(self):
        """Initialize database connection and tables"""
        try:
            self.engine = create_engine(DATABASE_URL, poolclass=StaticPool, connect_args={'check_same_thread': False})
            self.db_session = scoped_session(sessionmaker(bind=self.engine))
            
            # Create tables
            Base.metadata.create_all(self.engine)
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def setup_security(self):
        """Setup security components"""
        # CORS
        CORS(self.app, origins=['*'], supports_credentials=True)
        
        # JWT
        self.jwt = JWTManager(self.app)
        
        # Rate limiting with fallback to memory storage
        try:
            self.limiter = Limiter(
                app=self.app,
                key_func=get_remote_address,
                default_limits=["200 per day", "50 per hour"],
                storage_uri=REDIS_URL
            )
        except Exception as e:
            logger.warning(f"Redis rate limiting failed: {e}. Using memory storage.")
            self.limiter = Limiter(
                app=self.app,
                key_func=get_remote_address,
                default_limits=["200 per day", "50 per hour"],
                storage_uri="memory://"
            )
        
        # Security headers
        @self.app.after_request
        def set_security_headers(response):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
            return response
        
        logger.info("Security components initialized")
    
    def setup_caching(self):
        """Setup caching system"""
        try:
            # Try to configure cache with Redis
            self.cache = Cache(self.app, config={'CACHE_TYPE': 'redis', 'CACHE_REDIS_URL': REDIS_URL})
            # Test Redis connection
            self.cache.get('test_key')
            logger.info("Redis caching system initialized")
        except Exception as e:
            logger.warning(f"Redis cache initialization failed: {e}. Using simple cache.")
            # Fallback to simple cache
            self.app.config['CACHE_TYPE'] = 'simple'
            self.cache = Cache(self.app)
            logger.info("Simple caching system initialized")
    
    def setup_monitoring(self):
        """Setup monitoring and metrics"""
        @self.app.before_request
        def before_request():
            g.start_time = time.time()
            g.server_start_time = self.server_start_time
            g.websocket_connections = self.websocket_connections
            
            # Record request metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown',
                status='started'
            ).inc()
        
        @self.app.after_request
        def after_request(response):
            # Record request duration
            if hasattr(g, 'start_time'):
                duration = time.time() - g.start_time
                REQUEST_DURATION.observe(duration)
                
                # Update request metrics
                REQUEST_COUNT.labels(
                    method=request.method,
                    endpoint=request.endpoint or 'unknown',
                    status=response.status_code
                ).inc()
            
            return response
        
        logger.info("Monitoring system initialized")
    
    def setup_websocket(self):
        """Setup WebSocket with Socket.IO"""
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins="*",
            async_mode='threading',
            ping_timeout=60,
            ping_interval=25
        )
        
        @self.socketio.on('connect')
        def handle_connect():
            self.websocket_connections.add(request.sid)
            ACTIVE_CONNECTIONS.set(len(self.websocket_connections))
            logger.info(f"WebSocket connected: {request.sid}")
            emit('connected', {'status': 'success', 'sid': request.sid})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            if request.sid in self.websocket_connections:
                self.websocket_connections.remove(request.sid)
            ACTIVE_CONNECTIONS.set(len(self.websocket_connections))
            logger.info(f"WebSocket disconnected: {request.sid}")
        
        @self.socketio.on('subscribe_metrics')
        def handle_subscribe_metrics():
            join_room('metrics')
            emit('subscribed', {'room': 'metrics'})
        
        @self.socketio.on('unsubscribe_metrics')
        def handle_unsubscribe_metrics():
            leave_room('metrics')
            emit('unsubscribed', {'room': 'metrics'})
        
        logger.info("WebSocket system initialized")
    
    def setup_routes(self):
        """Setup API routes"""
        
        @self.app.route('/')
        def index():
            return render_template_string(DASHBOARD_TEMPLATE)
        
        @self.app.route('/api/v1/health')
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'version': 'v2.0',
                'uptime': (datetime.utcnow() - self.server_start_time).total_seconds()
            })
        
        @self.app.route('/api/v1/metrics')
        def get_metrics():
            """Get system metrics"""
            metrics = self.performance_monitor.collect_metrics()
            return jsonify(metrics)
        
        @self.app.route('/api/v1/prometheus')
        def prometheus_metrics():
            """Prometheus metrics endpoint"""
            return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}
        
        @self.app.route('/api/v1/cache/stats')
        def cache_stats():
            """Get cache statistics"""
            return jsonify(self.cache_manager.get_stats())
        
        @self.app.route('/api/v1/auth/register', methods=['POST'])
        @self.limiter.limit("5 per minute")
        def register():
            """User registration endpoint"""
            data = request.get_json()
            
            if not data or not data.get('username') or not data.get('email') or not data.get('password'):
                return jsonify({'error': 'Missing required fields'}), 400
            
            # Validate input
            username = self.security_manager.sanitize_input(data['username'])
            email = self.security_manager.sanitize_input(data['email'])
            password = data['password']
            
            if not self.security_manager.validate_email(email):
                return jsonify({'error': 'Invalid email format'}), 400
            
            password_check = self.security_manager.validate_password(password)
            if not password_check['valid']:
                return jsonify({'error': 'Password validation failed', 'details': password_check['errors']}), 400
            
            # Check if user exists
            existing_user = self.db_session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                return jsonify({'error': 'User already exists'}), 409
            
            # Create new user
            password_hash = generate_password_hash(password)
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                role=data.get('role', 'user')
            )
            
            self.db_session.add(user)
            self.db_session.commit()
            
            # Log audit event
            self.log_audit_event(user.id, 'user_register', 'user', f"User {username} registered")
            
            return jsonify({
                'message': 'User registered successfully',
                'user_id': user.id,
                'username': user.username
            }), 201
        
        @self.app.route('/api/v1/auth/login', methods=['POST'])
        @self.limiter.limit("10 per minute")
        def login():
            """User login endpoint"""
            data = request.get_json()
            
            if not data or not data.get('username') or not data.get('password'):
                return jsonify({'error': 'Missing credentials'}), 400
            
            username = self.security_manager.sanitize_input(data['username'])
            password = data['password']
            
            # Check account lockout
            if self.security_manager.is_account_locked(username):
                return jsonify({'error': 'Account temporarily locked due to failed login attempts'}), 423
            
            # Find user
            user = self.db_session.query(User).filter(User.username == username).first()
            
            if not user or not check_password_hash(user.password_hash, password):
                self.security_manager.record_failed_attempt(username)
                return jsonify({'error': 'Invalid credentials'}), 401
            
            if not user.is_active:
                return jsonify({'error': 'Account is disabled'}), 403
            
            # Reset failed attempts
            self.security_manager.reset_failed_attempts(username)
            
            # Update last login
            user.last_login = datetime.utcnow()
            self.db_session.commit()
            
            # Create JWT token
            access_token = create_access_token(identity=user.id)
            
            # Log audit event
            self.log_audit_event(user.id, 'user_login', 'user', f"User {username} logged in")
            
            return jsonify({
                'access_token': access_token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role
                }
            })
        
        @self.app.route('/api/v1/auth/profile')
        @jwt_required()
        def get_profile():
            """Get user profile"""
            user_id = get_jwt_identity()
            user = self.db_session.query(User).get(user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            return jsonify({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None
            })
        
        logger.info("API routes initialized")
    
    def setup_error_handlers(self):
        """Setup error handlers"""
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': 'Not found'}), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            self.db_session.rollback()
            return jsonify({'error': 'Internal server error'}), 500
        
        @self.app.errorhandler(429)
        def rate_limit_exceeded(error):
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        logger.info("Error handlers initialized")
    
    def log_audit_event(self, user_id: int, action: str, resource: str, details: str):
        """Log audit event"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource=resource,
                details=details,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')
            )
            
            self.db_session.add(audit_log)
            self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Audit logging error: {e}")
    
    def start_background_tasks(self):
        """Start background monitoring tasks"""
        def metrics_collector():
            while True:
                try:
                    metrics = self.performance_monitor.collect_metrics()
                    
                    # Store metrics in database
                    db_metrics = SystemMetrics(
                        cpu_percent=metrics.get('cpu_percent'),
                        memory_percent=metrics.get('memory_percent'),
                        disk_percent=metrics.get('disk_percent'),
                        network_bytes_sent=metrics.get('network_bytes_sent'),
                        network_bytes_recv=metrics.get('network_bytes_recv'),
                        active_connections=metrics.get('active_connections'),
                        avg_response_time=metrics.get('avg_response_time', 0)
                    )
                    
                    self.db_session.add(db_metrics)
                    self.db_session.commit()
                    
                    # Emit to WebSocket subscribers
                    self.socketio.emit('metrics_update', metrics, room='metrics')
                    
                except Exception as e:
                    logger.error(f"Background metrics collection error: {e}")
                
                time.sleep(5)  # Collect metrics every 5 seconds
        
        # Start metrics collection in background thread
        metrics_thread = threading.Thread(target=metrics_collector, daemon=True)
        metrics_thread.start()
        
        logger.info("Background tasks started")
    
    def run(self, host='127.0.0.1', port=5000, debug=False):
        """Run the advanced server"""
        logger.info("="*60)
        logger.info("ULTIMATE SUITE v11.0 - ADVANCED SERVER")
        logger.info("="*60)
        logger.info(f"Starting server on {host}:{port}")
        logger.info(f"Debug mode: {debug}")
        logger.info(f"Database: {DATABASE_URL}")
        logger.info(f"Cache: Redis enabled: {self.cache_manager.redis_client is not None}")
        logger.info("="*60)
        
        # Start background tasks
        self.start_background_tasks()
        
        # Run the server
        self.socketio.run(
            self.app,
            host=host,
            port=port,
            debug=debug,
            use_reloader=False,
            log_output=True
        )

# Advanced Dashboard Template with Modern UI
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ultimate Suite v11.0 - Advanced Dashboard</title>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .header p {
            font-size: 1.2rem;
            color: #666;
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .status-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            transition: transform 0.3s ease;
        }
        
        .status-card:hover {
            transform: translateY(-5px);
        }
        
        .status-card h3 {
            font-size: 1.3rem;
            margin-bottom: 15px;
            color: #444;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-value {
            font-weight: bold;
            color: #667eea;
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .chart-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }
        
        .chart-card h3 {
            margin-bottom: 20px;
            color: #444;
        }
        
        .logs-section {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }
        
        .logs-section h3 {
            margin-bottom: 20px;
            color: #444;
        }
        
        .log-entries {
            max-height: 300px;
            overflow-y: auto;
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
        }
        
        .log-entry {
            padding: 5px 0;
            border-bottom: 1px solid #eee;
        }
        
        .log-entry:last-child {
            border-bottom: none;
        }
        
        .log-timestamp {
            color: #666;
            font-weight: bold;
        }
        
        .log-level {
            font-weight: bold;
            margin: 0 10px;
        }
        
        .log-info { color: #17a2b8; }
        .log-warning { color: #ffc107; }
        .log-error { color: #dc3545; }
        .log-success { color: #28a745; }
        
        .status-online {
            color: #28a745;
            font-weight: bold;
        }
        
        .status-offline {
            color: #dc3545;
            font-weight: bold;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #eee;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .status-grid {
                grid-template-columns: 1fr;
            }
            
            .charts-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Ultimate Suite v11.0</h1>
            <p>Advanced Dashboard - Week 2 Implementation</p>
            <div id="connection-status" class="status-online">● Connected</div>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <h3>📊 System Status</h3>
                <div class="metric">
                    <span>Server Status</span>
                    <span class="metric-value status-online">Online</span>
                </div>
                <div class="metric">
                    <span>Database</span>
                    <span class="metric-value status-online">Connected</span>
                </div>
                <div class="metric">
                    <span>WebSocket</span>
                    <span class="metric-value status-online">Active</span>
                </div>
                <div class="metric">
                    <span>Cache</span>
                    <span class="metric-value" id="cache-status">Checking...</span>
                </div>
            </div>
            
            <div class="status-card">
                <h3>⚡ Performance</h3>
                <div class="metric">
                    <span>CPU Usage</span>
                    <span class="metric-value" id="cpu-usage">0%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="cpu-progress" style="width: 0%"></div>
                </div>
                <div class="metric">
                    <span>Memory Usage</span>
                    <span class="metric-value" id="memory-usage">0%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="memory-progress" style="width: 0%"></div>
                </div>
                <div class="metric">
                    <span>Disk Usage</span>
                    <span class="metric-value" id="disk-usage">0%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="disk-progress" style="width: 0%"></div>
                </div>
            </div>
            
            <div class="status-card">
                <h3>🌐 Network</h3>
                <div class="metric">
                    <span>Active Connections</span>
                    <span class="metric-value" id="active-connections">0</span>
                </div>
                <div class="metric">
                    <span>Bytes Sent</span>
                    <span class="metric-value" id="bytes-sent">0</span>
                </div>
                <div class="metric">
                    <span>Bytes Received</span>
                    <span class="metric-value" id="bytes-recv">0</span>
                </div>
                <div class="metric">
                    <span>Uptime</span>
                    <span class="metric-value" id="uptime">0s</span>
                </div>
            </div>
            
            <div class="status-card">
                <h3>🔒 Security</h3>
                <div class="metric">
                    <span>Authentication</span>
                    <span class="metric-value status-online">JWT Active</span>
                </div>
                <div class="metric">
                    <span>Rate Limiting</span>
                    <span class="metric-value status-online">Enabled</span>
                </div>
                <div class="metric">
                    <span>CORS</span>
                    <span class="metric-value status-online">Configured</span>
                </div>
                <div class="metric">
                    <span>SSL/TLS</span>
                    <span class="metric-value">Development</span>
                </div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h3>📈 CPU Usage Over Time</h3>
                <canvas id="cpuChart" width="400" height="200"></canvas>
            </div>
            
            <div class="chart-card">
                <h3>💾 Memory Usage Over Time</h3>
                <canvas id="memoryChart" width="400" height="200"></canvas>
            </div>
        </div>
        
        <div class="logs-section">
            <h3>📋 System Logs</h3>
            <div class="log-entries" id="log-entries">
                <div class="log-entry">
                    <span class="log-timestamp">2025-07-18 15:00:00</span>
                    <span class="log-level log-success">INFO</span>
                    <span>Advanced server initialized successfully</span>
                </div>
                <div class="log-entry">
                    <span class="log-timestamp">2025-07-18 15:00:01</span>
                    <span class="log-level log-info">INFO</span>
                    <span>Database connected and tables created</span>
                </div>
                <div class="log-entry">
                    <span class="log-timestamp">2025-07-18 15:00:02</span>
                    <span class="log-level log-info">INFO</span>
                    <span>WebSocket system initialized</span>
                </div>
                <div class="log-entry">
                    <span class="log-timestamp">2025-07-18 15:00:03</span>
                    <span class="log-level log-success">INFO</span>
                    <span>Security systems activated</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Initialize Socket.IO connection
        const socket = io();
        
        // Connection status
        const connectionStatus = document.getElementById('connection-status');
        
        socket.on('connect', () => {
            connectionStatus.textContent = '● Connected';
            connectionStatus.className = 'status-online';
            socket.emit('subscribe_metrics');
        });
        
        socket.on('disconnect', () => {
            connectionStatus.textContent = '● Disconnected';
            connectionStatus.className = 'status-offline';
        });
        
        // Initialize charts
        const cpuChart = new Chart(document.getElementById('cpuChart'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'CPU Usage (%)',
                    data: [],
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    fill: true
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
        
        const memoryChart = new Chart(document.getElementById('memoryChart'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Memory Usage (%)',
                    data: [],
                    borderColor: '#764ba2',
                    backgroundColor: 'rgba(118, 75, 162, 0.1)',
                    fill: true
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
        
        // Update metrics
        function updateMetrics(metrics) {
            // Update performance metrics
            document.getElementById('cpu-usage').textContent = metrics.cpu_percent?.toFixed(1) + '%' || '0%';
            document.getElementById('memory-usage').textContent = metrics.memory_percent?.toFixed(1) + '%' || '0%';
            document.getElementById('disk-usage').textContent = metrics.disk_percent?.toFixed(1) + '%' || '0%';
            
            // Update progress bars
            document.getElementById('cpu-progress').style.width = (metrics.cpu_percent || 0) + '%';
            document.getElementById('memory-progress').style.width = (metrics.memory_percent || 0) + '%';
            document.getElementById('disk-progress').style.width = (metrics.disk_percent || 0) + '%';
            
            // Update network metrics
            document.getElementById('active-connections').textContent = metrics.active_connections || 0;
            document.getElementById('bytes-sent').textContent = formatBytes(metrics.network_bytes_sent || 0);
            document.getElementById('bytes-recv').textContent = formatBytes(metrics.network_bytes_recv || 0);
            document.getElementById('uptime').textContent = formatUptime(metrics.uptime || 0);
            
            // Update charts
            const now = new Date().toLocaleTimeString();
            
            if (cpuChart.data.labels.length > 10) {
                cpuChart.data.labels.shift();
                cpuChart.data.datasets[0].data.shift();
            }
            
            cpuChart.data.labels.push(now);
            cpuChart.data.datasets[0].data.push(metrics.cpu_percent || 0);
            cpuChart.update();
            
            if (memoryChart.data.labels.length > 10) {
                memoryChart.data.labels.shift();
                memoryChart.data.datasets[0].data.shift();
            }
            
            memoryChart.data.labels.push(now);
            memoryChart.data.datasets[0].data.push(metrics.memory_percent || 0);
            memoryChart.update();
        }
        
        // Listen for metrics updates
        socket.on('metrics_update', updateMetrics);
        
        // Format bytes
        function formatBytes(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        // Format uptime
        function formatUptime(seconds) {
            const days = Math.floor(seconds / 86400);
            const hours = Math.floor((seconds % 86400) / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = Math.floor(seconds % 60);
            
            if (days > 0) {
                return `${days}d ${hours}h ${minutes}m`;
            } else if (hours > 0) {
                return `${hours}h ${minutes}m ${secs}s`;
            } else if (minutes > 0) {
                return `${minutes}m ${secs}s`;
            } else {
                return `${secs}s`;
            }
        }
        
        // Fetch initial metrics
        fetch('/api/v1/metrics')
            .then(response => response.json())
            .then(updateMetrics)
            .catch(console.error);
        
        // Fetch cache status
        fetch('/api/v1/cache/stats')
            .then(response => response.json())
            .then(stats => {
                document.getElementById('cache-status').textContent = stats.backend === 'redis' ? 'Redis' : 'Memory';
                document.getElementById('cache-status').className = 'metric-value status-online';
            })
            .catch(() => {
                document.getElementById('cache-status').textContent = 'Offline';
                document.getElementById('cache-status').className = 'metric-value status-offline';
            });
        
        // Add log entry
        function addLogEntry(timestamp, level, message) {
            const logEntries = document.getElementById('log-entries');
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.innerHTML = `
                <span class="log-timestamp">${timestamp}</span>
                <span class="log-level log-${level.toLowerCase()}">${level}</span>
                <span>${message}</span>
            `;
            logEntries.appendChild(entry);
            
            // Keep only last 50 entries
            while (logEntries.children.length > 50) {
                logEntries.removeChild(logEntries.firstChild);
            }
            
            // Scroll to bottom
            logEntries.scrollTop = logEntries.scrollHeight;
        }
        
        // Listen for performance alerts
        socket.on('performance_alert', (data) => {
            data.alerts.forEach(alert => {
                addLogEntry(
                    new Date().toLocaleString(),
                    alert.severity.toUpperCase(),
                    alert.message
                );
            });
        });
        
        // Periodic metrics update
        setInterval(() => {
            fetch('/api/v1/metrics')
                .then(response => response.json())
                .then(updateMetrics)
                .catch(console.error);
        }, 5000);
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    server = AdvancedServer()
    server.run(host='127.0.0.1', port=5001, debug=True)
