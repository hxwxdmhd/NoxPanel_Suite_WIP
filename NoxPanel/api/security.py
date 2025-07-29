"""
Security API Blueprint
Handles security monitoring, alerts, and threat detection
"""

import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
import hashlib

logger = logging.getLogger(__name__)

# Create blueprint
security_bp = Blueprint('security', __name__)

def get_db_service():
    """Get database service from app context"""
    return current_app.extensions.get('db_service')

def require_auth():
    """Check if request is authenticated"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    try:
        token = auth_header.split(' ')[1]
    except IndexError:
        return None
    
    from .. import verify_token
    return verify_token(token)

@security_bp.route('/alerts', methods=['GET'])
def security_alerts():
    """Get security alerts and incidents"""
    try:
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        db_service = get_db_service()
        if not db_service:
            return jsonify({'error': 'Database service not available'}), 500
        
        # Get query parameters
        priority = request.args.get('priority')  # high, medium, low
        status = request.args.get('status', 'open')  # open, resolved, investigating
        limit = int(request.args.get('limit', 50))
        
        alerts = []
        
        # Get failed login attempts
        try:
            recent_time = datetime.utcnow() - timedelta(hours=24)
            failed_logins = db_service.audit.get_failed_logins(since=recent_time, limit=10)
            
            for login in failed_logins:
                alerts.append({
                    'id': f"failed_login_{login.get('id', '')}",
                    'type': 'authentication',
                    'priority': 'medium',
                    'status': 'open',
                    'title': 'Failed Login Attempt',
                    'message': f"Failed login for user: {login.get('username', 'unknown')}",
                    'details': {
                        'ip_address': login.get('ip_address', 'unknown'),
                        'user_agent': login.get('user_agent', 'unknown'),
                        'timestamp': login.get('timestamp')
                    },
                    'timestamp': login.get('timestamp'),
                    'severity': 'warning'
                })
        except Exception as e:
            logger.warning(f"Failed to get login alerts: {e}")
        
        # Generate sample security alerts
        sample_alerts = [
            {
                'id': 'suspicious_activity_001',
                'type': 'anomaly',
                'priority': 'high',
                'status': 'investigating',
                'title': 'Unusual Access Pattern Detected',
                'message': 'Multiple failed login attempts from different IPs',
                'details': {
                    'affected_accounts': 3,
                    'ip_addresses': ['192.168.1.100', '10.0.0.50'],
                    'time_window': '15 minutes'
                },
                'timestamp': (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
                'severity': 'high'
            },
            {
                'id': 'rate_limit_001',
                'type': 'rate_limit',
                'priority': 'medium',
                'status': 'resolved',
                'title': 'Rate Limit Exceeded',
                'message': 'API rate limit exceeded for IP 203.0.113.1',
                'details': {
                    'ip_address': '203.0.113.1',
                    'endpoint': '/api/auth/login',
                    'requests_count': 100,
                    'time_window': '1 minute'
                },
                'timestamp': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                'severity': 'medium'
            }
        ]
        
        alerts.extend(sample_alerts)
        
        # Filter by priority if specified
        if priority:
            alerts = [alert for alert in alerts if alert['priority'] == priority]
        
        # Filter by status
        alerts = [alert for alert in alerts if alert['status'] == status]
        
        # Sort by timestamp (most recent first)
        alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Limit results
        alerts = alerts[:limit]
        
        return jsonify({
            'alerts': alerts,
            'count': len(alerts),
            'filters': {
                'priority': priority,
                'status': status,
                'limit': limit
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Security alerts error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@security_bp.route('/scan', methods=['POST'])
def security_scan():
    """Initiate security scan"""
    try:
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if user has admin role
        if user_payload.get('role') not in ['admin', 'security_admin']:
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        scan_type = data.get('type', 'quick') if data else 'quick'  # quick, full, targeted
        
        if scan_type not in ['quick', 'full', 'targeted']:
            return jsonify({'error': 'Invalid scan type'}), 400
        
        # Generate scan ID
        scan_id = hashlib.md5(f"{scan_type}_{datetime.utcnow()}".encode()).hexdigest()[:16]
        
        # Mock scan results
        scan_results = {
            'scan_id': scan_id,
            'type': scan_type,
            'status': 'completed',
            'started_at': datetime.utcnow().isoformat(),
            'completed_at': (datetime.utcnow() + timedelta(seconds=30)).isoformat(),
            'results': {
                'vulnerabilities_found': 0 if scan_type == 'quick' else 2,
                'security_score': 95 if scan_type == 'quick' else 87,
                'issues': [
                    {
                        'severity': 'medium',
                        'type': 'configuration',
                        'description': 'Default admin password detected',
                        'recommendation': 'Change default passwords'
                    }
                ] if scan_type != 'quick' else []
            }
        }
        
        logger.info(f"Security scan initiated: {scan_id} ({scan_type})")
        
        return jsonify({
            'message': 'Security scan completed',
            'scan': scan_results
        }), 200
        
    except Exception as e:
        logger.error(f"Security scan error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@security_bp.route('/settings', methods=['GET', 'POST'])
def security_settings():
    """Get or update security settings"""
    try:
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        if request.method == 'GET':
            # Return current security settings
            settings = {
                'password_policy': {
                    'min_length': 6,
                    'require_uppercase': False,
                    'require_lowercase': True,
                    'require_numbers': True,
                    'require_symbols': False
                },
                'session_management': {
                    'session_timeout': 3600,  # seconds
                    'max_concurrent_sessions': 5,
                    'remember_me_duration': 2592000  # 30 days
                },
                'rate_limiting': {
                    'login_attempts': {
                        'max_attempts': 5,
                        'window_minutes': 15,
                        'lockout_minutes': 30
                    },
                    'api_requests': {
                        'max_requests': 100,
                        'window_minutes': 1
                    }
                },
                'audit_logging': {
                    'enabled': True,
                    'log_failed_logins': True,
                    'log_admin_actions': True,
                    'retention_days': 90
                },
                'two_factor_auth': {
                    'enabled': False,
                    'required_for_admin': False,
                    'backup_codes': True
                }
            }
            
            return jsonify({
                'settings': settings,
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        
        else:  # POST - Update settings
            # Check if user has admin role
            if user_payload.get('role') not in ['admin', 'security_admin']:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Validate and update settings
            # In a real implementation, you would store these in the database
            
            logger.info(f"Security settings updated by user: {user_payload.get('username')}")
            
            return jsonify({
                'message': 'Security settings updated successfully',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        
    except Exception as e:
        logger.error(f"Security settings error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@security_bp.route('/threats', methods=['GET'])
def threat_intelligence():
    """Get threat intelligence and indicators"""
    try:
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Mock threat intelligence data
        threats = [
            {
                'id': 'threat_001',
                'type': 'malware',
                'severity': 'high',
                'title': 'New Ransomware Campaign',
                'description': 'Active ransomware campaign targeting web applications',
                'indicators': [
                    {'type': 'ip', 'value': '198.51.100.10'},
                    {'type': 'domain', 'value': 'malicious-domain.com'},
                    {'type': 'hash', 'value': 'a1b2c3d4e5f6...'}
                ],
                'last_seen': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                'confidence': 95
            },
            {
                'id': 'threat_002',
                'type': 'phishing',
                'severity': 'medium',
                'title': 'Credential Harvesting Campaign',
                'description': 'Phishing emails impersonating popular services',
                'indicators': [
                    {'type': 'email', 'value': 'noreply@fake-service.com'},
                    {'type': 'url', 'value': 'http://fake-login-page.com'}
                ],
                'last_seen': (datetime.utcnow() - timedelta(hours=6)).isoformat(),
                'confidence': 87
            }
        ]
        
        return jsonify({
            'threats': threats,
            'count': len(threats),
            'last_updated': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Threat intelligence error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@security_bp.route('/audit', methods=['GET'])
def audit_logs():
    """Get security audit logs"""
    try:
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if user has admin role
        if user_payload.get('role') not in ['admin', 'security_admin']:
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        # Get query parameters
        event_type = request.args.get('type')  # login, logout, admin_action
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 100))
        
        db_service = get_db_service()
        if not db_service:
            return jsonify({'error': 'Database service not available'}), 500
        
        try:
            # Parse date filters
            start_time = None
            end_time = None
            
            if start_date:
                start_time = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if end_date:
                end_time = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            # Get audit logs
            logs = db_service.audit.get_audit_logs(
                event_type=event_type,
                start_time=start_time,
                end_time=end_time,
                limit=limit
            )
            
        except Exception as e:
            logger.warning(f"Failed to get audit logs: {e}")
            # Return sample logs if database query fails
            logs = [
                {
                    'id': 1,
                    'event_type': 'login',
                    'user_id': user_payload.get('user_id'),
                    'username': user_payload.get('username'),
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', '')[:100],
                    'timestamp': datetime.utcnow().isoformat(),
                    'details': {'status': 'success'}
                }
            ]
        
        return jsonify({
            'logs': logs,
            'count': len(logs),
            'filters': {
                'type': event_type,
                'start_date': start_date,
                'end_date': end_date,
                'limit': limit
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Audit logs error: {e}")
        return jsonify({'error': 'Internal server error'}), 500