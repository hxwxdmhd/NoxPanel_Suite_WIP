"""
Dashboard API Blueprint
Provides real-time dashboard data and metrics for the NoxPanel system
"""

import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__)

def get_db_service():
    """Get database service from app context"""
    return current_app.extensions.get('db_service')

def require_auth():
    """Check if request is authenticated"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    try:
        token = auth_header.split(' ')[1]  # Bearer <token>
    except IndexError:
        return None
    
    # Import token verification
    import app
    
    payload = app.verify_token(token)
    return payload

@dashboard_bp.route('/overview', methods=['GET'])
def dashboard_overview():
    """Get dashboard overview data"""
    try:
        # Check authentication
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get database service
        db_service = get_db_service()
        if not db_service:
            return jsonify({'error': 'Database service not available'}), 500
        
        # Calculate time ranges
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        # Get system metrics
        metrics = {}
        
        # User statistics
        try:
            total_users = db_service.users.count_users()
            active_users_24h = db_service.users.count_active_users(since=last_24h)
            metrics['users'] = {
                'total': total_users,
                'active_24h': active_users_24h,
                'growth_7d': db_service.users.count_new_users(since=last_7d)
            }
        except Exception as e:
            logger.warning(f"Failed to get user metrics: {e}")
            metrics['users'] = {'total': 0, 'active_24h': 0, 'growth_7d': 0}
        
        # Session statistics
        try:
            total_sessions = db_service.sessions.count_sessions()
            active_sessions = db_service.sessions.count_active_sessions()
            metrics['sessions'] = {
                'total': total_sessions,
                'active': active_sessions,
                'avg_duration': db_service.sessions.get_avg_session_duration()
            }
        except Exception as e:
            logger.warning(f"Failed to get session metrics: {e}")
            metrics['sessions'] = {'total': 0, 'active': 0, 'avg_duration': 0}
        
        # Knowledge base statistics
        try:
            total_entries = db_service.knowledge.count_entries()
            recent_entries = db_service.knowledge.count_entries(since=last_7d)
            metrics['knowledge'] = {
                'total_entries': total_entries,
                'recent_entries': recent_entries,
                'categories': db_service.knowledge.count_categories()
            }
        except Exception as e:
            logger.warning(f"Failed to get knowledge metrics: {e}")
            metrics['knowledge'] = {'total_entries': 0, 'recent_entries': 0, 'categories': 0}
        
        # System health
        try:
            with db_service.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                
            metrics['system'] = {
                'database_tables': table_count,
                'uptime': '24h',  # This would be calculated from app start time
                'status': 'healthy'
            }
        except Exception as e:
            logger.warning(f"Failed to get system metrics: {e}")
            metrics['system'] = {'database_tables': 0, 'uptime': '0', 'status': 'error'}
        
        return jsonify({
            'overview': metrics,
            'timestamp': now.isoformat(),
            'period': '24h'
        }), 200
        
    except Exception as e:
        logger.error(f"Dashboard overview error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@dashboard_bp.route('/metrics/time-series', methods=['GET'])
def time_series_metrics():
    """Get time-series metrics for charts"""
    try:
        # Check authentication
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get query parameters
        period = request.args.get('period', '24h')  # 24h, 7d, 30d
        metric = request.args.get('metric', 'all')  # users, sessions, knowledge, all
        
        # Get database service
        db_service = get_db_service()
        if not db_service:
            return jsonify({'error': 'Database service not available'}), 500
        
        # Calculate time range based on period
        now = datetime.utcnow()
        if period == '24h':
            start_time = now - timedelta(hours=24)
            interval = timedelta(hours=1)
        elif period == '7d':
            start_time = now - timedelta(days=7)
            interval = timedelta(hours=6)
        elif period == '30d':
            start_time = now - timedelta(days=30)
            interval = timedelta(days=1)
        else:
            return jsonify({'error': 'Invalid period'}), 400
        
        # Generate time series data
        time_series = {}
        current_time = start_time
        
        # Create time points
        time_points = []
        while current_time <= now:
            time_points.append(current_time)
            current_time += interval
        
        # Get metrics for each time point
        if metric == 'all' or metric == 'users':
            user_data = []
            for time_point in time_points:
                try:
                    count = db_service.users.count_active_users(since=time_point - interval, until=time_point)
                    user_data.append({
                        'timestamp': time_point.isoformat(),
                        'value': count
                    })
                except:
                    user_data.append({
                        'timestamp': time_point.isoformat(),
                        'value': 0
                    })
            time_series['users'] = user_data
        
        if metric == 'all' or metric == 'sessions':
            session_data = []
            for time_point in time_points:
                try:
                    count = db_service.sessions.count_sessions(since=time_point - interval, until=time_point)
                    session_data.append({
                        'timestamp': time_point.isoformat(),
                        'value': count
                    })
                except:
                    session_data.append({
                        'timestamp': time_point.isoformat(),
                        'value': 0
                    })
            time_series['sessions'] = session_data
        
        if metric == 'all' or metric == 'knowledge':
            knowledge_data = []
            for time_point in time_points:
                try:
                    count = db_service.knowledge.count_entries(since=time_point - interval, until=time_point)
                    knowledge_data.append({
                        'timestamp': time_point.isoformat(),
                        'value': count
                    })
                except:
                    knowledge_data.append({
                        'timestamp': time_point.isoformat(),
                        'value': 0
                    })
            time_series['knowledge'] = knowledge_data
        
        return jsonify({
            'time_series': time_series,
            'period': period,
            'start_time': start_time.isoformat(),
            'end_time': now.isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Time series metrics error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@dashboard_bp.route('/alerts', methods=['GET'])
def dashboard_alerts():
    """Get current system alerts and notifications"""
    try:
        # Check authentication
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get database service
        db_service = get_db_service()
        if not db_service:
            return jsonify({'error': 'Database service not available'}), 500
        
        alerts = []
        
        # Check for system issues
        try:
            # Database size check
            with db_service.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0]
                
            if db_size > 100 * 1024 * 1024:  # 100MB
                alerts.append({
                    'id': 'db_size_warning',
                    'type': 'warning',
                    'priority': 'medium',
                    'title': 'Database Size Warning',
                    'message': f'Database size is {db_size / (1024*1024):.1f}MB',
                    'timestamp': datetime.utcnow().isoformat()
                })
        except Exception as e:
            alerts.append({
                'id': 'db_check_error',
                'type': 'error',
                'priority': 'high',
                'title': 'Database Check Failed',
                'message': f'Unable to check database status: {str(e)}',
                'timestamp': datetime.utcnow().isoformat()
            })
        
        # Check for failed login attempts
        try:
            recent_failures = db_service.audit.count_failed_logins(since=datetime.utcnow() - timedelta(hours=1))
            if recent_failures > 10:
                alerts.append({
                    'id': 'login_failures',
                    'type': 'security',
                    'priority': 'high',
                    'title': 'High Login Failure Rate',
                    'message': f'{recent_failures} failed login attempts in the last hour',
                    'timestamp': datetime.utcnow().isoformat()
                })
        except Exception as e:
            logger.warning(f"Failed to check login failures: {e}")
        
        # Mock some additional alerts for demonstration
        if len(alerts) == 0:
            alerts.append({
                'id': 'system_healthy',
                'type': 'success',
                'priority': 'low',
                'title': 'System Healthy',
                'message': 'All systems operating normally',
                'timestamp': datetime.utcnow().isoformat()
            })
        
        return jsonify({
            'alerts': alerts,
            'count': len(alerts),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Dashboard alerts error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@dashboard_bp.route('/stats/summary', methods=['GET'])
def stats_summary():
    """Get summary statistics for dashboard widgets"""
    try:
        # Check authentication
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get database service
        db_service = get_db_service()
        if not db_service:
            return jsonify({'error': 'Database service not available'}), 500
        
        # Calculate summary stats
        summary = {}
        
        # Recent activity
        try:
            now = datetime.utcnow()
            last_hour = now - timedelta(hours=1)
            last_day = now - timedelta(days=1)
            
            summary['activity'] = {
                'logins_last_hour': db_service.users.count_logins(since=last_hour),
                'logins_last_day': db_service.users.count_logins(since=last_day),
                'new_entries_today': db_service.knowledge.count_entries(since=last_day),
                'active_sessions': db_service.sessions.count_active_sessions()
            }
        except Exception as e:
            logger.warning(f"Failed to get activity stats: {e}")
            summary['activity'] = {
                'logins_last_hour': 0,
                'logins_last_day': 0,
                'new_entries_today': 0,
                'active_sessions': 0
            }
        
        # Top categories
        try:
            top_categories = db_service.knowledge.get_top_categories(limit=5)
            summary['top_categories'] = top_categories
        except Exception as e:
            logger.warning(f"Failed to get top categories: {e}")
            summary['top_categories'] = []
        
        # System performance
        summary['performance'] = {
            'response_time': '50ms',  # This would be measured
            'cpu_usage': '25%',       # This would be from system monitoring
            'memory_usage': '60%',    # This would be from system monitoring
            'disk_usage': '45%'       # This would be from system monitoring
        }
        
        return jsonify({
            'summary': summary,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Stats summary error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@dashboard_bp.route('/export', methods=['POST'])
def export_dashboard_data():
    """Export dashboard data in various formats"""
    try:
        # Check authentication
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        export_format = data.get('format', 'json')  # json, csv
        data_type = data.get('type', 'overview')    # overview, metrics, alerts
        
        if export_format not in ['json', 'csv']:
            return jsonify({'error': 'Invalid export format'}), 400
        
        # Get database service
        db_service = get_db_service()
        if not db_service:
            return jsonify({'error': 'Database service not available'}), 500
        
        # Generate export data based on type
        if data_type == 'overview':
            # Re-use overview endpoint logic
            pass
        
        # For now, return a simple response
        export_data = {
            'exported_at': datetime.utcnow().isoformat(),
            'format': export_format,
            'type': data_type,
            'data': 'Export functionality coming soon'
        }
        
        return jsonify(export_data), 200
        
    except Exception as e:
        logger.error(f"Dashboard export error: {e}")
        return jsonify({'error': 'Internal server error'}), 500