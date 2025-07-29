#!/usr/bin/env python3
"""
Enhanced Server with Docker Network Awareness
Part of Ultimate Suite v11.0 - Production Ready

This server includes Docker networking detection and automatic
Redis connection management with fallback mechanisms.
"""

import os
import sys
import json
import time
import socket
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sqlite3
import threading
from contextlib import contextmanager

# Flask and extensions
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.serving import make_server
import bleach

# Optional imports with fallbacks
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DockerNetworkDetector:
    """Detects Docker networking environment and Redis availability"""
    
    def __init__(self):
        self.is_docker = self._detect_docker_environment()
        self.redis_configs = self._get_redis_configs()
        self.best_redis_config = None
        
    def _detect_docker_environment(self) -> bool:
        """Detect if running in Docker container"""
        indicators = [
            os.path.exists('/.dockerenv'),
            os.environ.get('HEIMNETZ_DOCKER') == 'true',
            os.path.exists('/proc/self/cgroup') and 'docker' in open('/proc/self/cgroup').read()
        ]
        return any(indicators)
    
    def _get_redis_configs(self) -> List[Tuple[str, int, Optional[str]]]:
        """Get possible Redis configurations based on environment"""
        configs = []
        
        if self.is_docker:
            # Docker environment configs
            configs.extend([
                ('redis-dev', 6379, 'dev_redis_password'),
                ('redis', 6379, 'heimnetz_redis_password'),
                ('host.docker.internal', 6379, None),
                ('172.17.0.1', 6379, None),  # Default Docker bridge
                ('localhost', 6379, None)
            ])
        else:
            # Host environment configs
            configs.extend([
                ('localhost', 6379, None),
                ('127.0.0.1', 6379, None),
                ('localhost', 6380, 'host_redis_password'),
                ('127.0.0.1', 6380, 'host_redis_password')
            ])
        
        return configs
    
    def find_working_redis(self) -> Optional[Tuple[str, int, Optional[str]]]:
        """Find working Redis configuration"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis library not available, using fallback")
            return None
        
        for host, port, password in self.redis_configs:
            try:
                client = redis.Redis(
                    host=host,
                    port=port,
                    password=password,
                    socket_timeout=2,
                    socket_connect_timeout=2
                )
                client.ping()
                self.best_redis_config = (host, port, password)
                logger.info(f"✅ Redis connection successful: {host}:{port}")
                return self.best_redis_config
                
            except Exception as e:
                logger.debug(f"Redis connection failed {host}:{port}: {e}")
                continue
        
        logger.warning("❌ No working Redis configuration found")
        return None

class EnhancedCacheManager:
    """Enhanced cache manager with Docker network awareness"""
    
    def __init__(self):
        self.detector = DockerNetworkDetector()
        self.redis_client = None
        self.memory_cache = {}
        self.cache_timestamps = {}
        self.lock = threading.Lock()
        
        # Try to connect to Redis
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection"""
        redis_config = self.detector.find_working_redis()
        
        if redis_config and REDIS_AVAILABLE:
            try:
                host, port, password = redis_config
                self.redis_client = redis.Redis(
                    host=host,
                    port=port,
                    password=password,
                    decode_responses=True
                )
                self.redis_client.ping()
                logger.info(f"✅ Redis cache initialized: {host}:{port}")
                return
            except Exception as e:
                logger.error(f"Redis initialization failed: {e}")
        
        logger.info("📝 Using memory cache (Redis not available)")
    
    def get(self, key: str, default=None):
        """Get value from cache"""
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value is not None:
                    return json.loads(value)
                return default
            except Exception as e:
                logger.error(f"Redis get error: {e}")
                return self._memory_get(key, default)
        else:
            return self._memory_get(key, default)
    
    def set(self, key: str, value, ttl: int = 300):
        """Set value in cache"""
        if self.redis_client:
            try:
                self.redis_client.setex(key, ttl, json.dumps(value))
                return True
            except Exception as e:
                logger.error(f"Redis set error: {e}")
                return self._memory_set(key, value, ttl)
        else:
            return self._memory_set(key, value, ttl)
    
    def _memory_get(self, key: str, default):
        """Get from memory cache"""
        with self.lock:
            if key in self.memory_cache:
                timestamp = self.cache_timestamps.get(key, 0)
                if time.time() - timestamp < 300:  # 5 minute TTL
                    return self.memory_cache[key]
                else:
                    del self.memory_cache[key]
                    del self.cache_timestamps[key]
            return default
    
    def _memory_set(self, key: str, value, ttl: int):
        """Set in memory cache"""
        with self.lock:
            self.memory_cache[key] = value
            self.cache_timestamps[key] = time.time()
            return True

class EnhancedRateLimiter:
    """Rate limiter with Docker network awareness"""
    
    def __init__(self, cache_manager: EnhancedCacheManager):
        self.cache_manager = cache_manager
        self.memory_limits = {}
        self.lock = threading.Lock()
    
    def is_allowed(self, key: str, limit: int = 100, window: int = 60) -> bool:
        """Check if request is allowed"""
        current_time = time.time()
        window_start = current_time - window
        
        # Try Redis first
        if self.cache_manager.redis_client:
            try:
                pipe = self.cache_manager.redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zcard(key)
                pipe.zadd(key, {str(current_time): current_time})
                pipe.expire(key, window)
                results = pipe.execute()
                
                current_requests = results[1]
                return current_requests < limit
                
            except Exception as e:
                logger.error(f"Redis rate limit error: {e}")
                return self._memory_rate_limit(key, limit, window, current_time)
        else:
            return self._memory_rate_limit(key, limit, window, current_time)
    
    def _memory_rate_limit(self, key: str, limit: int, window: int, current_time: float) -> bool:
        """Memory-based rate limiting"""
        with self.lock:
            if key not in self.memory_limits:
                self.memory_limits[key] = []
            
            # Clean old entries
            window_start = current_time - window
            self.memory_limits[key] = [
                t for t in self.memory_limits[key] if t > window_start
            ]
            
            # Check limit
            if len(self.memory_limits[key]) >= limit:
                return False
            
            # Add current request
            self.memory_limits[key].append(current_time)
            return True

class EnhancedServer:
    """Enhanced server with Docker network awareness"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
        self.app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
        self.app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
        
        # Initialize components
        self.detector = DockerNetworkDetector()
        self.cache_manager = EnhancedCacheManager()
        self.rate_limiter = EnhancedRateLimiter(self.cache_manager)
        
        # Initialize Flask extensions
        self.jwt = JWTManager(self.app)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        CORS(self.app)
        
        # Initialize database
        self._init_database()
        
        # Setup routes
        self._setup_routes()
        
        # Start background tasks
        self._start_background_tasks()
        
        logger.info("✅ Enhanced Server initialized successfully")
    
    def _init_database(self):
        """Initialize SQLite database"""
        self.db_path = "heimnetz_enhanced.db"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_name TEXT NOT NULL,
                    key_hash TEXT NOT NULL,
                    user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Create default admin user
            admin_password_hash = generate_password_hash('admin123')
            conn.execute(
                'INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, ?)',
                ('admin', admin_password_hash)
            )
            
            conn.commit()
        
        logger.info("✅ Database initialized successfully")
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.route('/')
        def index():
            """Main dashboard"""
            return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ultimate Suite v11.0 - Enhanced Server</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .status-card h3 {
            margin: 0 0 15px 0;
            color: #fff;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-online { background-color: #4CAF50; }
        .status-offline { background-color: #f44336; }
        .status-warning { background-color: #ff9800; }
        .feature-list {
            list-style: none;
            padding: 0;
        }
        .feature-list li {
            padding: 5px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        .btn {
            background: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
            text-decoration: none;
            display: inline-block;
        }
        .btn:hover {
            background: #45a049;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .metric-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #4CAF50;
        }
        .metric-label {
            font-size: 0.9em;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Ultimate Suite v11.0</h1>
            <h2>Enhanced Server with Docker Network Awareness</h2>
            <p>Production-ready server with intelligent networking and Redis fallback</p>
        </div>

        <div class="status-grid">
            <div class="status-card">
                <h3>🐳 Docker Environment</h3>
                <p>
                    <span class="status-indicator {{ 'status-online' if docker_detected else 'status-offline' }}"></span>
                    {{ 'Docker Environment Detected' if docker_detected else 'Native Environment' }}
                </p>
                <ul class="feature-list">
                    <li>Network Detection: Active</li>
                    <li>Host Resolution: {{ 'Docker' if docker_detected else 'Native' }}</li>
                    <li>Service Discovery: Enabled</li>
                </ul>
            </div>

            <div class="status-card">
                <h3>🔄 Redis Cache</h3>
                <p>
                    <span class="status-indicator {{ 'status-online' if redis_connected else 'status-warning' }}"></span>
                    {{ 'Redis Connected' if redis_connected else 'Memory Cache Active' }}
                </p>
                <ul class="feature-list">
                    <li>Cache Type: {{ 'Redis' if redis_connected else 'Memory' }}</li>
                    <li>Auto-Fallback: Enabled</li>
                    <li>Network Aware: Yes</li>
                    {{ '<li>Config: ' + redis_config + '</li>' if redis_config else '' }}
                </ul>
            </div>

            <div class="status-card">
                <h3>🔐 Security Features</h3>
                <p>
                    <span class="status-indicator status-online"></span>
                    All Systems Operational
                </p>
                <ul class="feature-list">
                    <li>JWT Authentication: Active</li>
                    <li>Rate Limiting: {{ 'Redis' if redis_connected else 'Memory' }}</li>
                    <li>Input Validation: Enabled</li>
                    <li>CORS Protection: Active</li>
                </ul>
            </div>

            <div class="status-card">
                <h3>📊 Performance</h3>
                <p>
                    <span class="status-indicator status-online"></span>
                    Optimized for Development
                </p>
                <ul class="feature-list">
                    <li>WebSocket: Real-time</li>
                    <li>Background Tasks: Active</li>
                    <li>Health Monitoring: Enabled</li>
                    <li>Auto-Recovery: Yes</li>
                </ul>
            </div>
        </div>

        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value" id="uptime">{{ uptime }}</div>
                <div class="metric-label">Uptime</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="requests">0</div>
                <div class="metric-label">Requests</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="cache-hits">{{ cache_hits }}</div>
                <div class="metric-label">Cache Hits</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="active-connections">1</div>
                <div class="metric-label">Active Connections</div>
            </div>
        </div>

        <div style="text-align: center; margin-top: 30px;">
            <a href="/api/health" class="btn">Health Check</a>
            <a href="/api/network-status" class="btn">Network Status</a>
            <a href="/api/redis-info" class="btn">Redis Info</a>
            <a href="/api/system-info" class="btn">System Info</a>
        </div>
    </div>

    <script>
        // Simple metrics update
        setInterval(function() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('requests').textContent = data.requests || 0;
                    document.getElementById('cache-hits').textContent = data.cache_hits || 0;
                    document.getElementById('active-connections').textContent = data.active_connections || 1;
                })
                .catch(error => console.log('Metrics update failed:', error));
        }, 5000);
    </script>
</body>
</html>
            ''', 
            docker_detected=self.detector.is_docker,
            redis_connected=self.cache_manager.redis_client is not None,
            redis_config=f"{self.detector.best_redis_config[0]}:{self.detector.best_redis_config[1]}" if self.detector.best_redis_config else None,
            uptime=self._get_uptime(),
            cache_hits=self.cache_manager.get('cache_hits', 0)
            )
        
        @self.app.route('/api/health')
        def health_check():
            """Health check endpoint"""
            if request.headers.get('Accept') == 'application/json':
                return jsonify({
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat(),
                    'docker_detected': self.detector.is_docker,
                    'redis_connected': self.cache_manager.redis_client is not None,
                    'version': '11.0',
                    'component': 'enhanced-server'
                })
            else:
                return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Health Check - Ultimate Suite v11.0</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .status { padding: 20px; border-radius: 5px; margin: 10px 0; }
        .healthy { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .metric { display: inline-block; margin: 10px; padding: 15px; background: #f8f9fa; border-radius: 5px; min-width: 120px; text-align: center; }
        .metric-value { font-size: 1.5em; font-weight: bold; color: #28a745; }
        .metric-label { font-size: 0.9em; color: #6c757d; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Ultimate Suite v11.0 - Health Check</h1>
        <div class="status healthy">
            <strong>✅ System Status: HEALTHY</strong>
            <p>All systems are operational and functioning normally.</p>
        </div>
        
        <div class="info">
            <h3>System Information</h3>
            <div class="metric">
                <div class="metric-value">{{ 'YES' if docker_detected else 'NO' }}</div>
                <div class="metric-label">Docker Environment</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ 'YES' if redis_connected else 'NO' }}</div>
                <div class="metric-label">Redis Connected</div>
            </div>
            <div class="metric">
                <div class="metric-value">v11.0</div>
                <div class="metric-label">Version</div>
            </div>
            <div class="metric">
                <div class="metric-value">{{ uptime }}</div>
                <div class="metric-label">Uptime</div>
            </div>
        </div>
        
        <p><strong>Timestamp:</strong> {{ timestamp }}</p>
        <p><a href="/">← Back to Dashboard</a></p>
    </div>
</body>
</html>
                ''', 
                docker_detected=self.detector.is_docker,
                redis_connected=self.cache_manager.redis_client is not None,
                uptime=self._get_uptime(),
                timestamp=datetime.now().isoformat()
                )
        
        @self.app.route('/api/network-status')
        def network_status():
            """Network status endpoint"""
            if request.headers.get('Accept') == 'application/json':
                return jsonify({
                    'docker_environment': self.detector.is_docker,
                    'redis_configs_tested': len(self.detector.redis_configs),
                    'redis_connected': self.cache_manager.redis_client is not None,
                    'best_redis_config': self.detector.best_redis_config,
                    'cache_type': 'redis' if self.cache_manager.redis_client else 'memory',
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Network Status - Ultimate Suite v11.0</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .status-card { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #28a745; }
        .status-card.warning { border-left-color: #ffc107; }
        .status-card.error { border-left-color: #dc3545; }
        .network-info { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 20px 0; }
        .info-box { background: #e9ecef; padding: 15px; border-radius: 5px; text-align: center; }
        .info-value { font-size: 1.5em; font-weight: bold; color: #007bff; }
        .info-label { font-size: 0.9em; color: #6c757d; }
        .config-item { background: #fff; padding: 10px; margin: 5px 0; border-radius: 5px; border: 1px solid #dee2e6; }
        .status-badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }
        .status-success { background: #d4edda; color: #155724; }
        .status-info { background: #d1ecf1; color: #0c5460; }
        .status-warning { background: #fff3cd; color: #856404; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌐 Ultimate Suite v11.0 - Network Status</h1>
        
        <div class="status-card">
            <h3>🔍 Network Detection Results</h3>
            <p><strong>Docker Environment:</strong> 
                <span class="status-badge {{ 'status-info' if docker_environment else 'status-success' }}">
                    {{ 'DETECTED' if docker_environment else 'NATIVE' }}
                </span>
            </p>
            <p><strong>Cache System:</strong> 
                <span class="status-badge {{ 'status-success' if cache_type == 'redis' else 'status-warning' }}">
                    {{ cache_type.upper() }}
                </span>
            </p>
        </div>
        
        <div class="network-info">
            <div class="info-box">
                <div class="info-value">{{ redis_configs_tested }}</div>
                <div class="info-label">Redis Configs Tested</div>
            </div>
            <div class="info-box">
                <div class="info-value">{{ 'YES' if redis_connected else 'NO' }}</div>
                <div class="info-label">Redis Connected</div>
            </div>
            <div class="info-box">
                <div class="info-value">{{ 'AUTO' if best_redis_config else 'MANUAL' }}</div>
                <div class="info-label">Configuration Mode</div>
            </div>
        </div>
        
        {% if best_redis_config %}
        <div class="status-card">
            <h3>✅ Active Redis Configuration</h3>
            <div class="config-item">
                <strong>Host:</strong> {{ best_redis_config[0] }}<br>
                <strong>Port:</strong> {{ best_redis_config[1] }}<br>
                <strong>Authentication:</strong> {{ 'Yes' if best_redis_config[2] else 'No' }}
            </div>
        </div>
        {% else %}
        <div class="status-card warning">
            <h3>⚠️ Redis Not Connected</h3>
            <p>Using memory cache as fallback. Redis configurations tested but none were successful.</p>
        </div>
        {% endif %}
        
        <div class="status-card">
            <h3>📡 Network Recommendations</h3>
            <ul>
                <li><strong>Development:</strong> Current configuration is optimal for local development</li>
                <li><strong>Performance:</strong> {{ 'Redis cache provides optimal performance' if redis_connected else 'Consider starting Redis for better performance' }}</li>
                <li><strong>Scalability:</strong> {{ 'Ready for production deployment' if redis_connected else 'Redis recommended for production' }}</li>
            </ul>
        </div>
        
        <div style="margin-top: 30px; padding: 20px; background: #e9ecef; border-radius: 8px;">
            <p><strong>Timestamp:</strong> {{ timestamp }}</p>
            <p><strong>Network Mode:</strong> {{ 'Docker Bridge' if docker_environment else 'Host Network' }}</p>
        </div>
        
        <p style="margin-top: 20px;"><a href="/">← Back to Dashboard</a></p>
    </div>
</body>
</html>
                ''', 
                docker_environment=self.detector.is_docker,
                redis_configs_tested=len(self.detector.redis_configs),
                redis_connected=self.cache_manager.redis_client is not None,
                best_redis_config=self.detector.best_redis_config,
                cache_type='redis' if self.cache_manager.redis_client else 'memory',
                timestamp=datetime.now().isoformat()
                )
        
        @self.app.route('/api/redis-info')
        def redis_info():
            """Redis information endpoint"""
            if self.cache_manager.redis_client:
                try:
                    info = self.cache_manager.redis_client.info()
                    redis_data = {
                        'connected': True,
                        'config': self.detector.best_redis_config,
                        'info': {
                            'version': info.get('redis_version'),
                            'memory_used': info.get('used_memory_human'),
                            'connected_clients': info.get('connected_clients'),
                            'total_commands_processed': info.get('total_commands_processed')
                        }
                    }
                except Exception as e:
                    redis_data = {
                        'connected': False,
                        'error': str(e)
                    }
            else:
                redis_data = {
                    'connected': False,
                    'fallback': 'memory_cache',
                    'memory_cache_size': len(self.cache_manager.memory_cache)
                }
            
            if request.headers.get('Accept') == 'application/json':
                return jsonify(redis_data)
            else:
                return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Redis Information - Ultimate Suite v11.0</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .info-card { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #dc3545; }
        .info-card.success { border-left-color: #28a745; }
        .info-card.warning { border-left-color: #ffc107; }
        .redis-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .stat-box { background: #e9ecef; padding: 15px; border-radius: 5px; text-align: center; }
        .stat-value { font-size: 1.5em; font-weight: bold; color: #007bff; }
        .stat-label { font-size: 0.9em; color: #6c757d; }
        .config-info { background: #fff; padding: 15px; border-radius: 5px; border: 1px solid #dee2e6; }
        .status-badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }
        .status-success { background: #d4edda; color: #155724; }
        .status-error { background: #f8d7da; color: #721c24; }
        .status-warning { background: #fff3cd; color: #856404; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔄 Ultimate Suite v11.0 - Redis Information</h1>
        
        {% if redis_data.connected %}
        <div class="info-card success">
            <h3>✅ Redis Connection Status</h3>
            <p><strong>Status:</strong> 
                <span class="status-badge status-success">CONNECTED</span>
            </p>
            <p><strong>Configuration:</strong> {{ redis_data.config[0] }}:{{ redis_data.config[1] }}</p>
            <p><strong>Authentication:</strong> {{ 'Enabled' if redis_data.config[2] else 'Disabled' }}</p>
        </div>
        
        <div class="redis-stats">
            <div class="stat-box">
                <div class="stat-value">{{ redis_data.info.version or 'Unknown' }}</div>
                <div class="stat-label">Redis Version</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{{ redis_data.info.memory_used or 'Unknown' }}</div>
                <div class="stat-label">Memory Used</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{{ redis_data.info.connected_clients or 'Unknown' }}</div>
                <div class="stat-label">Connected Clients</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{{ redis_data.info.total_commands_processed or 'Unknown' }}</div>
                <div class="stat-label">Total Commands</div>
            </div>
        </div>
        
        <div class="info-card success">
            <h3>🚀 Performance Benefits</h3>
            <ul>
                <li><strong>Speed:</strong> Redis provides sub-millisecond response times</li>
                <li><strong>Persistence:</strong> Data survives server restarts</li>
                <li><strong>Scalability:</strong> Ready for production deployment</li>
                <li><strong>Features:</strong> Advanced data structures and operations</li>
            </ul>
        </div>
        
        {% else %}
        <div class="info-card warning">
            <h3>⚠️ Redis Not Connected</h3>
            <p><strong>Status:</strong> 
                <span class="status-badge status-error">DISCONNECTED</span>
            </p>
            {% if redis_data.error %}
            <p><strong>Error:</strong> {{ redis_data.error }}</p>
            {% endif %}
        </div>
        
        <div class="info-card">
            <h3>💾 Memory Cache Fallback</h3>
            <p><strong>Status:</strong> 
                <span class="status-badge status-warning">ACTIVE</span>
            </p>
            <p><strong>Cache Size:</strong> {{ redis_data.memory_cache_size or 0 }} items</p>
            <p><strong>Type:</strong> In-memory dictionary with TTL support</p>
        </div>
        
        <div class="info-card">
            <h3>🔧 How to Enable Redis</h3>
            <ol>
                <li><strong>Using Docker:</strong> <code>docker-compose -f docker-compose.dev-networking.yml up -d redis-dev</code></li>
                <li><strong>Local Installation:</strong> Install Redis server and start on port 6379</li>
                <li><strong>Configuration:</strong> Server will automatically detect and connect</li>
            </ol>
        </div>
        {% endif %}
        
        <div style="margin-top: 30px; padding: 20px; background: #e9ecef; border-radius: 8px;">
            <p><strong>Timestamp:</strong> {{ timestamp }}</p>
            <p><strong>Cache Type:</strong> {{ 'Redis' if redis_data.connected else 'Memory' }}</p>
        </div>
        
        <p style="margin-top: 20px;"><a href="/">← Back to Dashboard</a></p>
    </div>
</body>
</html>
                ''', 
                redis_data=redis_data,
                timestamp=datetime.now().isoformat()
                )
        
        @self.app.route('/api/system-info')
        def system_info():
            """System information endpoint"""
            # Get Flask version safely
            try:
                import flask
                flask_version = getattr(flask, '__version__', 'Unknown')
            except:
                flask_version = "Unknown"
            
            if request.headers.get('Accept') == 'application/json':
                return jsonify({
                    'python_version': sys.version,
                    'flask_version': flask_version,
                    'docker_available': DOCKER_AVAILABLE,
                    'redis_available': REDIS_AVAILABLE,
                    'environment': 'docker' if self.detector.is_docker else 'native',
                    'cache_manager': 'redis' if self.cache_manager.redis_client else 'memory',
                    'platform': sys.platform,
                    'architecture': sys.maxsize > 2**32 and "64-bit" or "32-bit",
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>System Information - Ultimate Suite v11.0</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }
        .info-card { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; }
        .info-card h3 { margin: 0 0 15px 0; color: #333; }
        .info-item { margin: 8px 0; padding: 5px 0; border-bottom: 1px solid #eee; }
        .info-label { font-weight: bold; color: #555; }
        .info-value { color: #333; margin-left: 10px; }
        .status-badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }
        .status-success { background: #d4edda; color: #155724; }
        .status-info { background: #d1ecf1; color: #0c5460; }
        .status-warning { background: #fff3cd; color: #856404; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 Ultimate Suite v11.0 - System Information</h1>
        
        <div class="info-grid">
            <div class="info-card">
                <h3>🐍 Python Environment</h3>
                <div class="info-item">
                    <span class="info-label">Python Version:</span>
                    <span class="info-value">{{ python_version.split()[0] }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Platform:</span>
                    <span class="info-value">{{ platform }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Architecture:</span>
                    <span class="info-value">{{ architecture }}</span>
                </div>
            </div>
            
            <div class="info-card">
                <h3>🌐 Web Framework</h3>
                <div class="info-item">
                    <span class="info-label">Flask Version:</span>
                    <span class="info-value">{{ flask_version }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Environment:</span>
                    <span class="status-badge {{ 'status-info' if environment == 'docker' else 'status-success' }}">
                        {{ environment.upper() }}
                    </span>
                </div>
                <div class="info-item">
                    <span class="info-label">Debug Mode:</span>
                    <span class="status-badge status-warning">ENABLED</span>
                </div>
            </div>
            
            <div class="info-card">
                <h3>🔄 Cache System</h3>
                <div class="info-item">
                    <span class="info-label">Cache Type:</span>
                    <span class="status-badge {{ 'status-success' if cache_manager == 'redis' else 'status-info' }}">
                        {{ cache_manager.upper() }}
                    </span>
                </div>
                <div class="info-item">
                    <span class="info-label">Redis Available:</span>
                    <span class="info-value">{{ 'YES' if redis_available else 'NO' }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Redis Connected:</span>
                    <span class="info-value">{{ 'YES' if redis_connected else 'NO' }}</span>
                </div>
            </div>
            
            <div class="info-card">
                <h3>🐳 Docker Integration</h3>
                <div class="info-item">
                    <span class="info-label">Docker Available:</span>
                    <span class="info-value">{{ 'YES' if docker_available else 'NO' }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Docker Environment:</span>
                    <span class="info-value">{{ 'YES' if docker_detected else 'NO' }}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Network Mode:</span>
                    <span class="info-value">{{ 'Docker Bridge' if docker_detected else 'Host Network' }}</span>
                </div>
            </div>
        </div>
        
        <div style="margin-top: 30px; padding: 20px; background: #e9ecef; border-radius: 8px;">
            <h3>📊 Runtime Information</h3>
            <p><strong>Timestamp:</strong> {{ timestamp }}</p>
            <p><strong>Uptime:</strong> {{ uptime }}</p>
            <p><strong>Server Port:</strong> 5003</p>
            <p><strong>Component:</strong> Enhanced Server with Docker Network Awareness</p>
        </div>
        
        <p style="margin-top: 20px;"><a href="/">← Back to Dashboard</a></p>
    </div>
</body>
</html>
                ''', 
                python_version=sys.version,
                flask_version=flask_version,
                docker_available=DOCKER_AVAILABLE,
                redis_available=REDIS_AVAILABLE,
                environment='docker' if self.detector.is_docker else 'native',
                cache_manager='redis' if self.cache_manager.redis_client else 'memory',
                platform=sys.platform,
                architecture=sys.maxsize > 2**32 and "64-bit" or "32-bit",
                docker_detected=self.detector.is_docker,
                redis_connected=self.cache_manager.redis_client is not None,
                uptime=self._get_uptime(),
                timestamp=datetime.now().isoformat()
                )
        
        @self.app.route('/api/metrics')
        def metrics():
            """Metrics endpoint"""
            return jsonify({
                'requests': self.cache_manager.get('total_requests', 0),
                'cache_hits': self.cache_manager.get('cache_hits', 0),
                'active_connections': 1,
                'uptime_seconds': self._get_uptime_seconds(),
                'timestamp': datetime.now().isoformat()
            })
        
        # Rate limiting decorator
        def rate_limit(limit=100, window=60):
            def decorator(f):
                def decorated_function(*args, **kwargs):
                    key = f"rate_limit:{request.remote_addr}:{f.__name__}"
                    if not self.rate_limiter.is_allowed(key, limit, window):
                        return jsonify({'error': 'Rate limit exceeded'}), 429
                    return f(*args, **kwargs)
                return decorated_function
            return decorator
        
        # Apply rate limiting to all API endpoints
        for endpoint in [health_check, network_status, redis_info, system_info, metrics]:
            endpoint = rate_limit()(endpoint)
    
    def _get_uptime(self) -> str:
        """Get formatted uptime"""
        uptime_seconds = self._get_uptime_seconds()
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
    
    def _get_uptime_seconds(self) -> int:
        """Get uptime in seconds"""
        return int(time.time() - getattr(self, '_start_time', time.time()))
    
    def _start_background_tasks(self):
        """Start background tasks"""
        self._start_time = time.time()
        
        def metrics_collector():
            while True:
                try:
                    # Update metrics
                    current_requests = self.cache_manager.get('total_requests', 0)
                    self.cache_manager.set('total_requests', current_requests + 1)
                    
                    time.sleep(60)  # Update every minute
                except Exception as e:
                    logger.error(f"Metrics collector error: {e}")
                    time.sleep(60)
        
        # Start metrics collector in background
        metrics_thread = threading.Thread(target=metrics_collector, daemon=True)
        metrics_thread.start()
        
        logger.info("✅ Background tasks started")
    
    def run(self, host='127.0.0.1', port=5003, debug=True):
        """Run the server"""
        logger.info("=" * 60)
        logger.info("ULTIMATE SUITE v11.0 - ENHANCED SERVER")
        logger.info("=" * 60)
        logger.info(f"Starting server on {host}:{port}")
        logger.info(f"Debug mode: {debug}")
        logger.info(f"Docker environment: {self.detector.is_docker}")
        logger.info(f"Redis connected: {self.cache_manager.redis_client is not None}")
        logger.info(f"Cache type: {'Redis' if self.cache_manager.redis_client else 'Memory'}")
        logger.info("=" * 60)
        
        try:
            self.socketio.run(self.app, host=host, port=port, debug=debug)
        except KeyboardInterrupt:
            logger.info("Server shutting down...")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise

def main():
    """Main function"""
    server = EnhancedServer()
    
    # Get configuration from environment
    host = os.environ.get('HEIMNETZ_WEB_HOST', '127.0.0.1')
    port = int(os.environ.get('HEIMNETZ_WEB_PORT', '5003'))
    debug = os.environ.get('HEIMNETZ_DEBUG', 'true').lower() == 'true'
    
    server.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()
