#!/usr/bin/env python3
"""
Multi-Tenant Web Interface - Audit 5 Enterprise Scaling
=======================================================

This system provides a comprehensive multi-tenant web interface with:
- Complete tenant isolation and custom branding
- Dynamic tenant-specific dashboards
- Real-time resource monitoring and management
- User management and role-based access control
- Billing and subscription management
- API key management and monitoring
- Compliance and audit logging

Essential for enterprise multi-tenant web portal
"""

import os
import sys
import json
import time
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, g
from flask_cors import CORS
from functools import wraps
import uuid

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from tenant_manager import TenantManager, Tenant, TenantStatus, SubscriptionPlan, ResourceType
    from tenant_auth import TenantAuthManager, User, UserRole, Permission
    from resource_manager import ResourceMonitor, QuotaManager, ResourceStatus, AlertType
except ImportError:
    TenantManager = None
    Tenant = None
    TenantStatus = None
    SubscriptionPlan = None
    ResourceType = None
    TenantAuthManager = None
    User = None
    UserRole = None
    Permission = None
    ResourceMonitor = None
    QuotaManager = None
    ResourceStatus = None
    AlertType = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Enable CORS
CORS(app)

# Global managers
tenant_manager = None
auth_manager = None
resource_monitor = None
quota_manager = None

def init_managers():
    """Initialize all managers"""
    global tenant_manager, auth_manager, resource_monitor, quota_manager
    
    try:
        # Initialize database manager
        from tenant_manager import DatabaseManager
        db_manager = DatabaseManager()
        
        # Initialize managers
        tenant_manager = TenantManager(db_manager)
        auth_manager = TenantAuthManager(tenant_manager)
        resource_monitor = ResourceMonitor()
        quota_manager = QuotaManager(resource_monitor, tenant_manager)
        
        # Start resource monitoring
        resource_monitor.start_monitoring(interval=60)
        
        logger.info("All managers initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing managers: {e}")
        # Create mock managers for testing
        tenant_manager = None
        auth_manager = None
        resource_monitor = None
        quota_manager = None

def get_tenant_from_request():
    """Get tenant from current request"""
    try:
        # Try to get tenant from subdomain
        host = request.headers.get('Host', '')
        if host and '.' in host:
            subdomain = host.split('.')[0]
            if subdomain != 'www' and tenant_manager:
                tenant = tenant_manager.get_tenant_by_domain(host)
                if tenant:
                    return tenant
        
        # Try to get tenant from session
        tenant_id = session.get('tenant_id')
        if tenant_id and tenant_manager:
            return tenant_manager.get_tenant(tenant_id)
        
        # Try to get tenant from header
        tenant_id = request.headers.get('X-Tenant-ID')
        if tenant_id and tenant_manager:
            return tenant_manager.get_tenant(tenant_id)
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting tenant from request: {e}")
        return None

def get_current_user():
    """Get current user from session"""
    try:
        user_id = session.get('user_id')
        tenant_id = session.get('tenant_id')
        
        if user_id and tenant_id and auth_manager:
            return auth_manager.get_user(tenant_id, user_id)
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return None

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))
        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function

def require_tenant(f):
    """Decorator to require tenant context"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tenant = get_tenant_from_request()
        if not tenant:
            return jsonify({'error': 'Tenant not found'}), 404
        g.current_tenant = tenant
        return f(*args, **kwargs)
    return decorated_function

def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({'error': 'Authentication required'}), 401
            
            if auth_manager and not auth_manager.check_permission(user, permission):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'GET':
        return render_template('login.html')
    
    try:
        data = request.get_json() or request.form
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        # Get tenant from request
        tenant = get_tenant_from_request()
        if not tenant:
            return jsonify({'error': 'Tenant not found'}), 404
        
        # Authenticate user
        if auth_manager:
            user = auth_manager.authenticate_user(
                tenant_id=tenant.id,
                email=email,
                password=password,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')
            )
            
            if user:
                # Set session
                session['user_id'] = user.id
                session['tenant_id'] = tenant.id
                session['user_role'] = user.role.value
                session.permanent = True
                
                # Generate tokens
                tokens = auth_manager.generate_tokens(user)
                
                return jsonify({
                    'success': True,
                    'user': user.to_dict(),
                    'tokens': tokens,
                    'redirect_url': url_for('dashboard')
                })
        
        return jsonify({'error': 'Invalid credentials'}), 401
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'GET':
        return render_template('register.html')
    
    try:
        data = request.get_json() or request.form
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        
        if not all([name, email, password]):
            return jsonify({'error': 'All fields required'}), 400
        
        # Get tenant from request
        tenant = get_tenant_from_request()
        if not tenant:
            return jsonify({'error': 'Tenant not found'}), 404
        
        # Create user
        if auth_manager:
            user = auth_manager.create_user(
                tenant_id=tenant.id,
                email=email,
                name=name,
                password=password,
                role=UserRole.USER
            )
            
            if user:
                return jsonify({
                    'success': True,
                    'message': 'User created successfully',
                    'redirect_url': url_for('login')
                })
        
        return jsonify({'error': 'Registration failed'}), 500
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

# Dashboard Routes
@app.route('/')
@app.route('/dashboard')
@require_auth
@require_tenant
def dashboard():
    """Main dashboard"""
    try:
        tenant = g.current_tenant
        user = g.current_user
        
        # Get tenant statistics
        stats = {
            'total_users': 0,
            'active_users': 0,
            'resource_usage': {},
            'alerts': [],
            'billing_info': {}
        }
        
        if tenant_manager:
            # Get tenant users (mock data)
            stats['total_users'] = 15
            stats['active_users'] = 12
        
        if quota_manager:
            # Get resource usage
            for resource_type in ResourceType:
                # Mock current usage
                current_usage = 50 if resource_type == ResourceType.USERS else 1024
                status, alert = quota_manager.check_quota_status(
                    tenant.id, resource_type, current_usage
                )
                
                stats['resource_usage'][resource_type.value] = {
                    'current': current_usage,
                    'limit': 100 if resource_type == ResourceType.USERS else 10240,
                    'status': status.value if status else 'normal'
                }
                
                if alert:
                    stats['alerts'].append({
                        'type': alert.alert_type.value,
                        'message': alert.message,
                        'resource': alert.resource_type.value
                    })
        
        if resource_monitor:
            # Get system metrics
            system_metrics = resource_monitor.get_latest_system_metrics()
            if system_metrics:
                stats['system_metrics'] = {
                    'cpu_usage': system_metrics.cpu_usage,
                    'memory_usage': system_metrics.memory_usage,
                    'disk_usage': system_metrics.disk_usage,
                    'active_connections': system_metrics.active_connections
                }
        
        return render_template('dashboard.html', 
                             tenant=tenant, 
                             user=user, 
                             stats=stats)
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return render_template('error.html', error="Dashboard error"), 500

@app.route('/users')
@require_auth
@require_tenant
@require_permission(Permission.USER_READ)
def users():
    """User management"""
    try:
        tenant = g.current_tenant
        user = g.current_user
        
        # Get tenant users (mock data)
        users_list = [
            {
                'id': str(uuid.uuid4()),
                'name': 'John Doe',
                'email': 'john@example.com',
                'role': 'admin',
                'is_active': True,
                'created_at': datetime.now().isoformat()
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Jane Smith',
                'email': 'jane@example.com',
                'role': 'user',
                'is_active': True,
                'created_at': datetime.now().isoformat()
            }
        ]
        
        return render_template('users.html', 
                             tenant=tenant, 
                             user=user, 
                             users=users_list)
        
    except Exception as e:
        logger.error(f"Users error: {e}")
        return render_template('error.html', error="Users error"), 500

@app.route('/resources')
@require_auth
@require_tenant
@require_permission(Permission.DATA_READ)
def resources():
    """Resource management"""
    try:
        tenant = g.current_tenant
        user = g.current_user
        
        # Get resource usage data
        resource_data = {}
        
        if quota_manager:
            for resource_type in ResourceType:
                # Mock current usage
                current_usage = 50 if resource_type == ResourceType.USERS else 1024
                limit = 100 if resource_type == ResourceType.USERS else 10240
                
                status, alert = quota_manager.check_quota_status(
                    tenant.id, resource_type, current_usage
                )
                
                resource_data[resource_type.value] = {
                    'current': current_usage,
                    'limit': limit,
                    'percentage': (current_usage / limit) * 100,
                    'status': status.value if status else 'normal'
                }
        
        # Get recent alerts
        alerts = []
        if quota_manager:
            alerts = quota_manager.get_tenant_alerts(tenant.id, resolved=False)
        
        return render_template('resources.html', 
                             tenant=tenant, 
                             user=user, 
                             resource_data=resource_data,
                             alerts=alerts)
        
    except Exception as e:
        logger.error(f"Resources error: {e}")
        return render_template('error.html', error="Resources error"), 500

@app.route('/billing')
@require_auth
@require_tenant
@require_permission(Permission.BILLING_READ)
def billing():
    """Billing management"""
    try:
        tenant = g.current_tenant
        user = g.current_user
        
        # Get billing information (mock data)
        billing_info = {
            'current_plan': tenant.plan.value,
            'billing_cycle': 'monthly',
            'next_billing_date': (datetime.now() + timedelta(days=15)).isoformat(),
            'current_usage': {
                'users': 50,
                'storage': 1024,
                'api_calls': 5000
            },
            'monthly_cost': 99.99,
            'usage_history': [
                {
                    'date': (datetime.now() - timedelta(days=30)).isoformat(),
                    'cost': 89.99,
                    'usage': {'users': 45, 'storage': 980, 'api_calls': 4500}
                },
                {
                    'date': (datetime.now() - timedelta(days=60)).isoformat(),
                    'cost': 79.99,
                    'usage': {'users': 40, 'storage': 850, 'api_calls': 4000}
                }
            ]
        }
        
        return render_template('billing.html', 
                             tenant=tenant, 
                             user=user, 
                             billing_info=billing_info)
        
    except Exception as e:
        logger.error(f"Billing error: {e}")
        return render_template('error.html', error="Billing error"), 500

@app.route('/api-keys')
@require_auth
@require_tenant
@require_permission(Permission.API_READ)
def api_keys():
    """API key management"""
    try:
        tenant = g.current_tenant
        user = g.current_user
        
        # Get API keys (mock data)
        api_keys_list = [
            {
                'id': str(uuid.uuid4()),
                'name': 'Production API Key',
                'key': 'hk_' + ''.join(['x' for _ in range(40)]),
                'permissions': ['api:read', 'api:write'],
                'created_at': datetime.now().isoformat(),
                'last_used': datetime.now().isoformat(),
                'usage_count': 1250
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Development API Key',
                'key': 'hk_' + ''.join(['y' for _ in range(40)]),
                'permissions': ['api:read'],
                'created_at': (datetime.now() - timedelta(days=30)).isoformat(),
                'last_used': (datetime.now() - timedelta(days=1)).isoformat(),
                'usage_count': 750
            }
        ]
        
        return render_template('api_keys.html', 
                             tenant=tenant, 
                             user=user, 
                             api_keys=api_keys_list)
        
    except Exception as e:
        logger.error(f"API keys error: {e}")
        return render_template('error.html', error="API keys error"), 500

@app.route('/settings')
@require_auth
@require_tenant
@require_permission(Permission.TENANT_READ)
def settings():
    """Tenant settings"""
    try:
        tenant = g.current_tenant
        user = g.current_user
        
        return render_template('settings.html', 
                             tenant=tenant, 
                             user=user)
        
    except Exception as e:
        logger.error(f"Settings error: {e}")
        return render_template('error.html', error="Settings error"), 500

# API Routes
@app.route('/api/tenant/info')
@require_auth
@require_tenant
def api_tenant_info():
    """Get tenant information"""
    try:
        tenant = g.current_tenant
        
        return jsonify({
            'id': tenant.id,
            'name': tenant.name,
            'domain': tenant.domain,
            'plan': tenant.plan.value,
            'status': tenant.status.value,
            'created_at': tenant.created_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"API tenant info error: {e}")
        return jsonify({'error': 'Failed to get tenant info'}), 500

@app.route('/api/user/profile')
@require_auth
def api_user_profile():
    """Get user profile"""
    try:
        user = g.current_user
        
        return jsonify({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role.value,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None
        })
        
    except Exception as e:
        logger.error(f"API user profile error: {e}")
        return jsonify({'error': 'Failed to get user profile'}), 500

@app.route('/api/resources/status')
@require_auth
@require_tenant
@require_permission(Permission.DATA_READ)
def api_resources_status():
    """Get resource status"""
    try:
        tenant = g.current_tenant
        
        resource_status = {}
        
        if quota_manager:
            for resource_type in ResourceType:
                # Mock current usage
                current_usage = 50 if resource_type == ResourceType.USERS else 1024
                limit = 100 if resource_type == ResourceType.USERS else 10240
                
                status, alert = quota_manager.check_quota_status(
                    tenant.id, resource_type, current_usage
                )
                
                resource_status[resource_type.value] = {
                    'current': current_usage,
                    'limit': limit,
                    'percentage': (current_usage / limit) * 100,
                    'status': status.value if status else 'normal'
                }
        
        return jsonify(resource_status)
        
    except Exception as e:
        logger.error(f"API resources status error: {e}")
        return jsonify({'error': 'Failed to get resource status'}), 500

@app.route('/api/system/metrics')
@require_auth
@require_tenant
@require_permission(Permission.SYSTEM_MONITOR)
def api_system_metrics():
    """Get system metrics"""
    try:
        if resource_monitor:
            system_metrics = resource_monitor.get_latest_system_metrics()
            if system_metrics:
                return jsonify({
                    'cpu_usage': system_metrics.cpu_usage,
                    'memory_usage': system_metrics.memory_usage,
                    'disk_usage': system_metrics.disk_usage,
                    'network_io': system_metrics.network_io,
                    'active_connections': system_metrics.active_connections,
                    'response_time': system_metrics.response_time,
                    'timestamp': system_metrics.timestamp.isoformat()
                })
        
        return jsonify({'error': 'System metrics not available'}), 503
        
    except Exception as e:
        logger.error(f"API system metrics error: {e}")
        return jsonify({'error': 'Failed to get system metrics'}), 500

@app.route('/api/alerts')
@require_auth
@require_tenant
@require_permission(Permission.DATA_READ)
def api_alerts():
    """Get tenant alerts"""
    try:
        tenant = g.current_tenant
        
        alerts = []
        if quota_manager:
            tenant_alerts = quota_manager.get_tenant_alerts(tenant.id, resolved=False)
            
            for alert in tenant_alerts:
                alerts.append({
                    'id': alert.id,
                    'type': alert.alert_type.value,
                    'resource': alert.resource_type.value,
                    'message': alert.message,
                    'current_usage': alert.current_usage,
                    'limit': alert.limit,
                    'threshold': alert.threshold,
                    'created_at': alert.created_at.isoformat()
                })
        
        return jsonify(alerts)
        
    except Exception as e:
        logger.error(f"API alerts error: {e}")
        return jsonify({'error': 'Failed to get alerts'}), 500

@app.route('/api/users', methods=['POST'])
@require_auth
@require_tenant
@require_permission(Permission.USER_CREATE)
def api_create_user():
    """Create new user"""
    try:
        tenant = g.current_tenant
        data = request.get_json()
        
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')
        
        if not all([name, email, password]):
            return jsonify({'error': 'All fields required'}), 400
        
        if auth_manager:
            user = auth_manager.create_user(
                tenant_id=tenant.id,
                email=email,
                name=name,
                password=password,
                role=UserRole(role)
            )
            
            if user:
                return jsonify({
                    'success': True,
                    'user': user.to_dict()
                })
        
        return jsonify({'error': 'Failed to create user'}), 500
        
    except Exception as e:
        logger.error(f"API create user error: {e}")
        return jsonify({'error': 'Failed to create user'}), 500

@app.route('/api/api-keys', methods=['POST'])
@require_auth
@require_tenant
@require_permission(Permission.API_ADMIN)
def api_create_api_key():
    """Create new API key"""
    try:
        tenant = g.current_tenant
        user = g.current_user
        data = request.get_json()
        
        name = data.get('name')
        permissions = data.get('permissions', ['api:read'])
        
        if not name:
            return jsonify({'error': 'API key name required'}), 400
        
        if auth_manager:
            # Convert permission strings to Permission enum
            perm_set = set()
            for perm in permissions:
                try:
                    perm_set.add(Permission(perm))
                except ValueError:
                    continue
            
            api_key = auth_manager.create_api_key(
                tenant_id=tenant.id,
                user_id=user.id,
                name=name,
                permissions=perm_set
            )
            
            if api_key:
                return jsonify({
                    'success': True,
                    'api_key': {
                        'id': api_key.id,
                        'name': api_key.name,
                        'key': api_key.key,
                        'permissions': [p.value for p in api_key.permissions],
                        'created_at': api_key.created_at.isoformat()
                    }
                })
        
        return jsonify({'error': 'Failed to create API key'}), 500
        
    except Exception as e:
        logger.error(f"API create API key error: {e}")
        return jsonify({'error': 'Failed to create API key'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Internal server error"), 500

# Template creation (basic HTML templates)
def create_templates():
    """Create basic HTML templates"""
    try:
        templates_dir = os.path.join(project_root, 'templates')
        os.makedirs(templates_dir, exist_ok=True)
        
        # Base template
        base_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Heimnetz Enterprise{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('dashboard') }}">
                <i class="fas fa-shield-alt"></i> Heimnetz Enterprise
            </a>
            {% if current_user %}
            <div class="navbar-nav ms-auto">
                <div class="dropdown">
                    <a class="nav-link dropdown-toggle text-white" href="#" data-bs-toggle="dropdown">
                        <i class="fas fa-user"></i> {{ current_user.name }}
                    </a>
                    <ul class="dropdown-menu">
                        <li><a class="dropdown-item" href="{{ url_for('settings') }}">Settings</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item" href="{{ url_for('logout') }}">Logout</a></li>
                    </ul>
                </div>
            </div>
            {% endif %}
        </div>
    </nav>

    {% if current_user %}
    <div class="container-fluid mt-3">
        <div class="row">
            <div class="col-md-2">
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-title">Navigation</h6>
                        <nav class="nav flex-column">
                            <a class="nav-link" href="{{ url_for('dashboard') }}">
                                <i class="fas fa-tachometer-alt"></i> Dashboard
                            </a>
                            <a class="nav-link" href="{{ url_for('users') }}">
                                <i class="fas fa-users"></i> Users
                            </a>
                            <a class="nav-link" href="{{ url_for('resources') }}">
                                <i class="fas fa-server"></i> Resources
                            </a>
                            <a class="nav-link" href="{{ url_for('billing') }}">
                                <i class="fas fa-credit-card"></i> Billing
                            </a>
                            <a class="nav-link" href="{{ url_for('api_keys') }}">
                                <i class="fas fa-key"></i> API Keys
                            </a>
                        </nav>
                    </div>
                </div>
            </div>
            <div class="col-md-10">
                {% block content %}{% endblock %}
            </div>
        </div>
    </div>
    {% else %}
    <div class="container mt-5">
        {% block content %}{% endblock %}
    </div>
    {% endif %}

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>"""
        
        with open(os.path.join(templates_dir, 'base.html'), 'w') as f:
            f.write(base_template)
        
        # Login template
        login_template = """{% extends "base.html" %}

{% block title %}Login - Heimnetz Enterprise{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h4 class="mb-0">Login</h4>
            </div>
            <div class="card-body">
                <form id="loginForm">
                    <div class="mb-3">
                        <label for="email" class="form-label">Email</label>
                        <input type="email" class="form-control" id="email" name="email" required>
                    </div>
                    <div class="mb-3">
                        <label for="password" class="form-label">Password</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Login</button>
                    <a href="{{ url_for('register') }}" class="btn btn-link">Register</a>
                </form>
            </div>
        </div>
    </div>
</div>

<script>
document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const data = {
        email: formData.get('email'),
        password: formData.get('password')
    };
    
    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            window.location.href = result.redirect_url;
        } else {
            alert(result.error || 'Login failed');
        }
    } catch (error) {
        alert('Login failed');
    }
});
</script>
{% endblock %}"""
        
        with open(os.path.join(templates_dir, 'login.html'), 'w') as f:
            f.write(login_template)
        
        # Dashboard template
        dashboard_template = """{% extends "base.html" %}

{% block title %}Dashboard - Heimnetz Enterprise{% endblock %}

{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>Dashboard</h2>
    <div class="text-muted">
        <i class="fas fa-building"></i> {{ tenant.name }}
    </div>
</div>

<div class="row">
    <div class="col-md-3">
        <div class="card text-white bg-primary">
            <div class="card-body">
                <div class="d-flex justify-content-between">
                    <div>
                        <h5 class="card-title">Total Users</h5>
                        <h3>{{ stats.total_users }}</h3>
                    </div>
                    <div class="align-self-center">
                        <i class="fas fa-users fa-2x"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card text-white bg-success">
            <div class="card-body">
                <div class="d-flex justify-content-between">
                    <div>
                        <h5 class="card-title">Active Users</h5>
                        <h3>{{ stats.active_users }}</h3>
                    </div>
                    <div class="align-self-center">
                        <i class="fas fa-user-check fa-2x"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card text-white bg-warning">
            <div class="card-body">
                <div class="d-flex justify-content-between">
                    <div>
                        <h5 class="card-title">Alerts</h5>
                        <h3>{{ stats.alerts|length }}</h3>
                    </div>
                    <div class="align-self-center">
                        <i class="fas fa-exclamation-triangle fa-2x"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card text-white bg-info">
            <div class="card-body">
                <div class="d-flex justify-content-between">
                    <div>
                        <h5 class="card-title">Plan</h5>
                        <h3>{{ tenant.plan.title() }}</h3>
                    </div>
                    <div class="align-self-center">
                        <i class="fas fa-star fa-2x"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row mt-4">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5>Resource Usage</h5>
            </div>
            <div class="card-body">
                {% for resource, data in stats.resource_usage.items() %}
                <div class="mb-3">
                    <label class="form-label">{{ resource.title() }}</label>
                    <div class="progress">
                        <div class="progress-bar 
                            {% if data.status == 'critical' %}bg-danger
                            {% elif data.status == 'warning' %}bg-warning
                            {% else %}bg-success{% endif %}"
                             style="width: {{ (data.current / data.limit * 100) | round(1) }}%">
                            {{ data.current }} / {{ data.limit }}
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5>Recent Alerts</h5>
            </div>
            <div class="card-body">
                {% if stats.alerts %}
                    {% for alert in stats.alerts %}
                    <div class="alert alert-warning alert-dismissible fade show" role="alert">
                        <i class="fas fa-exclamation-triangle"></i>
                        {{ alert.message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                    {% endfor %}
                {% else %}
                    <p class="text-muted">No active alerts</p>
                {% endif %}
            </div>
        </div>
    </div>
</div>

{% if stats.system_metrics %}
<div class="row mt-4">
    <div class="col-md-12">
        <div class="card">
            <div class="card-header">
                <h5>System Metrics</h5>
            </div>
            <div class="card-body">
                <canvas id="systemMetricsChart" width="400" height="200"></canvas>
            </div>
        </div>
    </div>
</div>
{% endif %}
{% endblock %}

{% block scripts %}
{% if stats.system_metrics %}
<script>
const ctx = document.getElementById('systemMetricsChart').getContext('2d');
const chart = new Chart(ctx, {
    type: 'doughnut',
    data: {
        labels: ['CPU Usage', 'Memory Usage', 'Disk Usage'],
        datasets: [{
            data: [
                {{ stats.system_metrics.cpu_usage }},
                {{ stats.system_metrics.memory_usage }},
                {{ stats.system_metrics.disk_usage }}
            ],
            backgroundColor: [
                '#FF6384',
                '#36A2EB',
                '#FFCE56'
            ]
        }]
    },
    options: {
        responsive: true,
        plugins: {
            title: {
                display: true,
                text: 'System Resource Usage (%)'
            }
        }
    }
});
</script>
{% endif %}
{% endblock %}"""
        
        with open(os.path.join(templates_dir, 'dashboard.html'), 'w') as f:
            f.write(dashboard_template)
        
        # Error template
        error_template = """{% extends "base.html" %}

{% block title %}Error - Heimnetz Enterprise{% endblock %}

{% block content %}
<div class="text-center">
    <h1 class="display-4">Oops!</h1>
    <p class="lead">{{ error }}</p>
    <a href="{{ url_for('dashboard') }}" class="btn btn-primary">Go to Dashboard</a>
</div>
{% endblock %}"""
        
        with open(os.path.join(templates_dir, 'error.html'), 'w') as f:
            f.write(error_template)
        
        logger.info("HTML templates created successfully")
        
    except Exception as e:
        logger.error(f"Error creating templates: {e}")

def main():
    """Main function to run the web interface"""
    try:
        print("Multi-Tenant Web Interface - Starting Server")
        print("=" * 50)
        
        # Initialize managers
        init_managers()
        
        # Create templates
        create_templates()
        
        # Run the Flask app
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True
        )
        
    except Exception as e:
        print(f"Error running web interface: {e}")
        logger.error(f"Web interface error: {e}")

if __name__ == "__main__":
    main()
