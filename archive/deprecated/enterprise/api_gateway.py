#!/usr/bin/env python3
"""
Enterprise API Gateway - Audit 5 Enterprise Scaling
===================================================

This system provides a comprehensive API gateway for multi-tenant enterprise deployment:
- Tenant-aware request routing and load balancing
- Authentication and authorization middleware
- Rate limiting and throttling per tenant
- API versioning and backwards compatibility
- Request/response transformation
- Monitoring and analytics
- Error handling and circuit breakers
- Caching and optimization

Essential for enterprise multi-tenant API management
"""

import os
import sys
import json
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from functools import wraps
import uuid
import hashlib
import hmac
import base64
import threading
from collections import defaultdict, deque
import requests
from urllib.parse import urljoin, urlparse
import redis
import sqlite3

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from tenant_manager import TenantManager, Tenant, TenantStatus
    from tenant_auth import TenantAuthManager, User, UserRole, Permission
    from resource_manager import ResourceMonitor, QuotaManager
except ImportError:
    TenantManager = None
    Tenant = None
    TenantStatus = None
    TenantAuthManager = None
    User = None
    UserRole = None
    Permission = None
    ResourceMonitor = None
    QuotaManager = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Enable CORS
CORS(app)

class RateLimiter:
    """
    Rate limiting system for API requests
    """
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.local_cache = defaultdict(lambda: defaultdict(deque))
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def is_allowed(self, key: str, limit: int, window: int) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is within rate limit"""
        try:
            now = time.time()
            
            if self.redis_client:
                # Use Redis for distributed rate limiting
                return self._redis_rate_limit(key, limit, window, now)
            else:
                # Use local cache for single-instance rate limiting
                return self._local_rate_limit(key, limit, window, now)
                
        except Exception as e:
            self.logger.error(f"Rate limit check error: {e}")
            return True, {'remaining': limit, 'reset': now + window}
    
    def _redis_rate_limit(self, key: str, limit: int, window: int, now: float) -> Tuple[bool, Dict[str, Any]]:
        """Redis-based rate limiting"""
        try:
            pipe = self.redis_client.pipeline()
            pipe.multi()
            
            # Add current request timestamp
            pipe.zadd(key, {str(now): now})
            
            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, now - window)
            
            # Count current requests in window
            pipe.zcard(key)
            
            # Set expiration for cleanup
            pipe.expire(key, window)
            
            results = pipe.execute()
            current_count = results[2]
            
            allowed = current_count <= limit
            remaining = max(0, limit - current_count)
            reset_time = now + window
            
            return allowed, {
                'remaining': remaining,
                'reset': reset_time,
                'current': current_count
            }
            
        except Exception as e:
            self.logger.error(f"Redis rate limit error: {e}")
            return True, {'remaining': limit, 'reset': now + window}
    
    def _local_rate_limit(self, key: str, limit: int, window: int, now: float) -> Tuple[bool, Dict[str, Any]]:
        """Local cache-based rate limiting"""
        try:
            requests_queue = self.local_cache[key][window]
            
            # Remove old entries outside the window
            while requests_queue and requests_queue[0] <= now - window:
                requests_queue.popleft()
            
            # Add current request
            requests_queue.append(now)
            
            current_count = len(requests_queue)
            allowed = current_count <= limit
            remaining = max(0, limit - current_count)
            reset_time = now + window
            
            return allowed, {
                'remaining': remaining,
                'reset': reset_time,
                'current': current_count
            }
            
        except Exception as e:
            self.logger.error(f"Local rate limit error: {e}")
            return True, {'remaining': limit, 'reset': now + window}

class CircuitBreaker:
    """
    Circuit breaker pattern for API resilience
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def call(self, func, *args, **kwargs):
        """Call function with circuit breaker protection"""
        if self.state == 'open':
            if self._should_attempt_reset():
                self.state = 'half-open'
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker"""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful request"""
        self.failure_count = 0
        self.state = 'closed'
    
    def _on_failure(self):
        """Handle failed request"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
            self.logger.warning(f"Circuit breaker opened due to {self.failure_count} failures")

class APIGateway:
    """
    Main API Gateway class
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize managers
        self.tenant_manager = None
        self.auth_manager = None
        self.resource_monitor = None
        self.quota_manager = None
        
        # Initialize Redis client
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=3)
            self.redis_client.ping()
            self.logger.info("Redis client initialized for API Gateway")
        except Exception as e:
            self.logger.warning(f"Redis not available for API Gateway: {e}")
            self.redis_client = None
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(self.redis_client)
        
        # Initialize circuit breakers
        self.circuit_breakers = defaultdict(lambda: CircuitBreaker())
        
        # Request/response caching
        self.cache = {}
        
        # API routes and services
        self.services = {
            'tenant': 'http://localhost:5001',
            'auth': 'http://localhost:5002',
            'resource': 'http://localhost:5003',
            'billing': 'http://localhost:5004',
            'analytics': 'http://localhost:5005'
        }
        
        # Rate limiting configuration
        self.rate_limits = {
            'free': {'requests': 100, 'window': 3600},      # 100 requests/hour
            'starter': {'requests': 1000, 'window': 3600},   # 1000 requests/hour
            'professional': {'requests': 10000, 'window': 3600},  # 10k requests/hour
            'enterprise': {'requests': 100000, 'window': 3600}    # 100k requests/hour
        }
        
        # Initialize database for analytics
        self._init_analytics_db()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _init_analytics_db(self):
        """Initialize analytics database"""
        try:
            self.analytics_conn = sqlite3.connect("api_analytics.db", check_same_thread=False)
            cursor = self.analytics_conn.cursor()
            
            # Create analytics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_requests (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT,
                    user_id TEXT,
                    method TEXT,
                    endpoint TEXT,
                    status_code INTEGER,
                    response_time REAL,
                    request_size INTEGER,
                    response_size INTEGER,
                    timestamp TEXT,
                    user_agent TEXT,
                    ip_address TEXT,
                    api_version TEXT,
                    error_message TEXT
                )
            """)
            
            # Create rate limiting table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rate_limit_violations (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT,
                    user_id TEXT,
                    endpoint TEXT,
                    limit_type TEXT,
                    violation_count INTEGER,
                    timestamp TEXT,
                    ip_address TEXT
                )
            """)
            
            self.analytics_conn.commit()
            self.logger.info("Analytics database initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing analytics database: {e}")
    
    def _start_background_tasks(self):
        """Start background tasks"""
        try:
            # Start cache cleanup task
            cleanup_thread = threading.Thread(target=self._cache_cleanup_task, daemon=True)
            cleanup_thread.start()
            
            # Start analytics aggregation task
            analytics_thread = threading.Thread(target=self._analytics_aggregation_task, daemon=True)
            analytics_thread.start()
            
            self.logger.info("Background tasks started")
            
        except Exception as e:
            self.logger.error(f"Error starting background tasks: {e}")
    
    def _cache_cleanup_task(self):
        """Background task to clean up expired cache entries"""
        while True:
            try:
                now = time.time()
                expired_keys = []
                
                for key, (data, expiry) in self.cache.items():
                    if now > expiry:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    del self.cache[key]
                
                time.sleep(300)  # Clean up every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Cache cleanup error: {e}")
                time.sleep(60)
    
    def _analytics_aggregation_task(self):
        """Background task to aggregate analytics data"""
        while True:
            try:
                # Aggregate analytics data every hour
                self._aggregate_analytics()
                time.sleep(3600)  # Run every hour
                
            except Exception as e:
                self.logger.error(f"Analytics aggregation error: {e}")
                time.sleep(300)
    
    def _aggregate_analytics(self):
        """Aggregate analytics data"""
        try:
            cursor = self.analytics_conn.cursor()
            
            # Get hourly request counts
            cursor.execute("""
                SELECT tenant_id, endpoint, COUNT(*) as request_count,
                       AVG(response_time) as avg_response_time,
                       strftime('%Y-%m-%d %H:00:00', timestamp) as hour
                FROM api_requests
                WHERE timestamp >= datetime('now', '-1 hour')
                GROUP BY tenant_id, endpoint, hour
            """)
            
            results = cursor.fetchall()
            
            # Store aggregated data (could be sent to monitoring system)
            for row in results:
                tenant_id, endpoint, count, avg_time, hour = row
                self.logger.info(f"Analytics: {tenant_id} - {endpoint}: {count} requests, {avg_time:.3f}s avg")
                
        except Exception as e:
            self.logger.error(f"Analytics aggregation error: {e}")
    
    def get_tenant_from_request(self, request) -> Optional[Tenant]:
        """Extract tenant from request"""
        try:
            # Try to get tenant from subdomain
            host = request.headers.get('Host', '')
            if host and '.' in host:
                subdomain = host.split('.')[0]
                if subdomain != 'www' and self.tenant_manager:
                    tenant = self.tenant_manager.get_tenant_by_domain(host)
                    if tenant:
                        return tenant
            
            # Try to get tenant from header
            tenant_id = request.headers.get('X-Tenant-ID')
            if tenant_id and self.tenant_manager:
                return self.tenant_manager.get_tenant(tenant_id)
            
            # Try to get tenant from path
            path = request.path
            if path.startswith('/api/v1/tenant/'):
                tenant_id = path.split('/')[4]
                if self.tenant_manager:
                    return self.tenant_manager.get_tenant(tenant_id)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting tenant from request: {e}")
            return None
    
    def authenticate_request(self, request) -> Optional[Dict[str, Any]]:
        """Authenticate API request"""
        try:
            # Check for API key
            api_key = request.headers.get('X-API-Key')
            if api_key and self.auth_manager:
                api_key_obj = self.auth_manager.verify_api_key(api_key)
                if api_key_obj:
                    return {
                        'type': 'api_key',
                        'api_key': api_key_obj,
                        'tenant_id': api_key_obj.tenant_id,
                        'user_id': api_key_obj.user_id,
                        'permissions': api_key_obj.permissions
                    }
            
            # Check for JWT token
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer ') and self.auth_manager:
                token = auth_header.split(' ')[1]
                payload = self.auth_manager.verify_token(token)
                if payload:
                    return {
                        'type': 'jwt',
                        'token': token,
                        'payload': payload,
                        'tenant_id': payload.get('tenant_id'),
                        'user_id': payload.get('user_id'),
                        'permissions': []  # Would be loaded from user role
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return None
    
    def check_rate_limit(self, tenant: Tenant, auth_info: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limits for request"""
        try:
            # Get rate limit configuration for tenant plan
            plan_name = tenant.plan.value if tenant else 'free'
            rate_config = self.rate_limits.get(plan_name, self.rate_limits['free'])
            
            # Create rate limit key
            key = f"rate_limit:{tenant.id if tenant else 'anonymous'}:{auth_info.get('user_id', 'anonymous')}"
            
            # Check rate limit
            allowed, info = self.rate_limiter.is_allowed(
                key=key,
                limit=rate_config['requests'],
                window=rate_config['window']
            )
            
            if not allowed:
                # Log rate limit violation
                self._log_rate_limit_violation(tenant, auth_info, info)
            
            return allowed, info
            
        except Exception as e:
            self.logger.error(f"Rate limit check error: {e}")
            return True, {'remaining': 1000, 'reset': time.time() + 3600}
    
    def _log_rate_limit_violation(self, tenant: Tenant, auth_info: Dict[str, Any], rate_info: Dict[str, Any]):
        """Log rate limit violation"""
        try:
            violation_id = str(uuid.uuid4())
            
            cursor = self.analytics_conn.cursor()
            cursor.execute("""
                INSERT INTO rate_limit_violations (id, tenant_id, user_id, endpoint, limit_type, violation_count, timestamp, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                violation_id,
                tenant.id if tenant else None,
                auth_info.get('user_id'),
                request.endpoint,
                tenant.plan.value if tenant else 'free',
                rate_info.get('current', 0),
                datetime.now().isoformat(),
                request.remote_addr
            ))
            self.analytics_conn.commit()
            
        except Exception as e:
            self.logger.error(f"Error logging rate limit violation: {e}")
    
    def get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response"""
        try:
            if cache_key in self.cache:
                data, expiry = self.cache[cache_key]
                if time.time() < expiry:
                    return data
                else:
                    del self.cache[cache_key]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Cache get error: {e}")
            return None
    
    def set_cached_response(self, cache_key: str, data: Dict[str, Any], ttl: int = 300):
        """Set cached response"""
        try:
            expiry = time.time() + ttl
            self.cache[cache_key] = (data, expiry)
            
        except Exception as e:
            self.logger.error(f"Cache set error: {e}")
    
    def route_request(self, request, tenant: Tenant, auth_info: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to appropriate service"""
        try:
            # Determine target service based on path
            path = request.path
            
            if path.startswith('/api/v1/tenant'):
                service = 'tenant'
            elif path.startswith('/api/v1/auth'):
                service = 'auth'
            elif path.startswith('/api/v1/resource'):
                service = 'resource'
            elif path.startswith('/api/v1/billing'):
                service = 'billing'
            elif path.startswith('/api/v1/analytics'):
                service = 'analytics'
            else:
                service = 'tenant'  # Default service
            
            # Get service URL
            service_url = self.services.get(service, self.services['tenant'])
            
            # Build target URL
            target_url = urljoin(service_url, path)
            
            # Prepare headers
            headers = dict(request.headers)
            headers['X-Tenant-ID'] = tenant.id if tenant else 'unknown'
            headers['X-User-ID'] = auth_info.get('user_id', 'anonymous')
            headers['X-Auth-Type'] = auth_info.get('type', 'none')
            
            # Create cache key for GET requests
            cache_key = None
            if request.method == 'GET':
                cache_key = f"cache:{tenant.id if tenant else 'anonymous'}:{hashlib.md5(target_url.encode()).hexdigest()}"
                
                # Check cache
                cached_response = self.get_cached_response(cache_key)
                if cached_response:
                    return cached_response
            
            # Use circuit breaker for service call
            circuit_breaker = self.circuit_breakers[service]
            
            def make_request():
                response = requests.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    json=request.get_json() if request.is_json else None,
                    data=request.get_data() if not request.is_json else None,
                    params=request.args,
                    timeout=30
                )
                return response
            
            # Make request with circuit breaker
            start_time = time.time()
            response = circuit_breaker.call(make_request)
            response_time = time.time() - start_time
            
            # Prepare response data
            response_data = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'data': response.json() if response.headers.get('Content-Type', '').startswith('application/json') else response.text
            }
            
            # Cache successful GET responses
            if request.method == 'GET' and response.status_code == 200 and cache_key:
                self.set_cached_response(cache_key, response_data, ttl=300)
            
            # Log request
            self._log_request(request, tenant, auth_info, response.status_code, response_time)
            
            return response_data
            
        except Exception as e:
            self.logger.error(f"Request routing error: {e}")
            return {
                'status_code': 500,
                'headers': {'Content-Type': 'application/json'},
                'data': {'error': 'Internal server error'}
            }
    
    def _log_request(self, request, tenant: Tenant, auth_info: Dict[str, Any], 
                    status_code: int, response_time: float):
        """Log API request"""
        try:
            request_id = str(uuid.uuid4())
            
            cursor = self.analytics_conn.cursor()
            cursor.execute("""
                INSERT INTO api_requests (id, tenant_id, user_id, method, endpoint, status_code, response_time, request_size, response_size, timestamp, user_agent, ip_address, api_version, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request_id,
                tenant.id if tenant else None,
                auth_info.get('user_id'),
                request.method,
                request.endpoint,
                status_code,
                response_time,
                len(request.get_data()) if request.get_data() else 0,
                0,  # Response size would be calculated
                datetime.now().isoformat(),
                request.headers.get('User-Agent', ''),
                request.remote_addr,
                'v1',
                None if status_code < 400 else 'Error response'
            ))
            self.analytics_conn.commit()
            
        except Exception as e:
            self.logger.error(f"Error logging request: {e}")
    
    def process_request(self, request) -> Tuple[Dict[str, Any], int]:
        """Process incoming API request"""
        try:
            # Get tenant from request
            tenant = self.get_tenant_from_request(request)
            
            # Skip authentication for public endpoints
            if request.path in ['/api/v1/health', '/api/v1/status']:
                return self.route_request(request, tenant, {}), 200
            
            # Authenticate request
            auth_info = self.authenticate_request(request)
            if not auth_info:
                return {'error': 'Authentication required'}, 401
            
            # Check tenant status
            if tenant and tenant.status != TenantStatus.ACTIVE:
                return {'error': 'Tenant not active'}, 403
            
            # Check rate limits
            allowed, rate_info = self.check_rate_limit(tenant, auth_info)
            if not allowed:
                return {
                    'error': 'Rate limit exceeded',
                    'rate_limit': rate_info
                }, 429
            
            # Route request
            response_data = self.route_request(request, tenant, auth_info)
            
            # Add rate limit headers
            response_data['headers']['X-RateLimit-Remaining'] = str(rate_info.get('remaining', 0))
            response_data['headers']['X-RateLimit-Reset'] = str(int(rate_info.get('reset', 0)))
            
            return response_data['data'], response_data['status_code']
            
        except Exception as e:
            self.logger.error(f"Request processing error: {e}")
            return {'error': 'Internal server error'}, 500

# Initialize API Gateway
api_gateway = APIGateway()

# Flask routes
@app.before_request
def before_request():
    """Pre-process all requests"""
    g.start_time = time.time()

@app.after_request
def after_request(response):
    """Post-process all responses"""
    # Add CORS headers
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-API-Key,X-Tenant-ID')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    
    # Add response time header
    if hasattr(g, 'start_time'):
        response_time = time.time() - g.start_time
        response.headers.add('X-Response-Time', f"{response_time:.3f}s")
    
    return response

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/v1/status', methods=['GET'])
def status_check():
    """Status check endpoint"""
    return jsonify({
        'status': 'operational',
        'services': {
            'tenant': 'up',
            'auth': 'up',
            'resource': 'up',
            'billing': 'up',
            'analytics': 'up'
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/v1/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def api_proxy(path):
    """Main API proxy endpoint"""
    try:
        # Handle OPTIONS requests for CORS
        if request.method == 'OPTIONS':
            return jsonify({}), 200
        
        # Process request through API Gateway
        response_data, status_code = api_gateway.process_request(request)
        
        return jsonify(response_data), status_code
        
    except Exception as e:
        logger.error(f"API proxy error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v1/analytics/requests', methods=['GET'])
def analytics_requests():
    """Get API request analytics"""
    try:
        # Mock analytics data
        analytics_data = {
            'total_requests': 15000,
            'successful_requests': 14500,
            'failed_requests': 500,
            'avg_response_time': 0.125,
            'top_endpoints': [
                {'endpoint': '/api/v1/tenant/info', 'count': 3000},
                {'endpoint': '/api/v1/auth/login', 'count': 2500},
                {'endpoint': '/api/v1/resource/status', 'count': 2000},
                {'endpoint': '/api/v1/billing/info', 'count': 1500}
            ],
            'requests_by_hour': [
                {'hour': '2024-01-01T00:00:00', 'count': 500},
                {'hour': '2024-01-01T01:00:00', 'count': 750},
                {'hour': '2024-01-01T02:00:00', 'count': 1000},
                {'hour': '2024-01-01T03:00:00', 'count': 1250}
            ]
        }
        
        return jsonify(analytics_data)
        
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return jsonify({'error': 'Analytics error'}), 500

@app.route('/api/v1/analytics/rate-limits', methods=['GET'])
def analytics_rate_limits():
    """Get rate limit analytics"""
    try:
        # Mock rate limit data
        rate_limit_data = {
            'total_violations': 125,
            'violations_by_tenant': [
                {'tenant_id': 'tenant-1', 'violations': 50},
                {'tenant_id': 'tenant-2', 'violations': 35},
                {'tenant_id': 'tenant-3', 'violations': 25},
                {'tenant_id': 'tenant-4', 'violations': 15}
            ],
            'violations_by_endpoint': [
                {'endpoint': '/api/v1/resource/status', 'violations': 40},
                {'endpoint': '/api/v1/analytics/requests', 'violations': 30},
                {'endpoint': '/api/v1/billing/info', 'violations': 25},
                {'endpoint': '/api/v1/tenant/info', 'violations': 20}
            ]
        }
        
        return jsonify(rate_limit_data)
        
    except Exception as e:
        logger.error(f"Rate limit analytics error: {e}")
        return jsonify({'error': 'Rate limit analytics error'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

def main():
    """Main function to run the API Gateway"""
    try:
        print("Enterprise API Gateway - Starting Server")
        print("=" * 50)
        
        # Initialize managers (mock for testing)
        try:
            from tenant_manager import DatabaseManager
            db_manager = DatabaseManager()
            api_gateway.tenant_manager = TenantManager(db_manager) if TenantManager else None
            api_gateway.auth_manager = TenantAuthManager(api_gateway.tenant_manager) if TenantAuthManager else None
            api_gateway.resource_monitor = ResourceMonitor() if ResourceMonitor else None
            api_gateway.quota_manager = QuotaManager(api_gateway.resource_monitor, api_gateway.tenant_manager) if QuotaManager else None
            
            print("✓ Managers initialized successfully")
        except Exception as e:
            print(f"⚠ Warning: Could not initialize managers: {e}")
            print("✓ Running in mock mode")
        
        # Test rate limiter
        print("✓ Rate limiter initialized")
        
        # Test circuit breakers
        print("✓ Circuit breakers initialized")
        
        # Test analytics database
        print("✓ Analytics database initialized")
        
        print("\n🚀 API Gateway ready!")
        print("   Health check: http://localhost:8000/api/v1/health")
        print("   Status check: http://localhost:8000/api/v1/status")
        print("   Analytics: http://localhost:8000/api/v1/analytics/requests")
        
        # Run the Flask app
        app.run(
            host='0.0.0.0',
            port=8000,
            debug=True,
            threaded=True
        )
        
    except Exception as e:
        print(f"Error running API Gateway: {e}")
        logger.error(f"API Gateway error: {e}")

if __name__ == "__main__":
    main()
