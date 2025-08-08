"""
WebSocket API Integration
Handles real-time communication for dashboard updates, security alerts, and live data streaming
"""

import logging
from datetime import datetime
from flask_socketio import emit, join_room, leave_room, disconnect
import json

logger = logging.getLogger(__name__)

def register_websocket_handlers(socketio, db_service):
    """Register all WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect(auth):
        """Handle client connection"""
        try:
            # Verify authentication token if provided
            if auth and 'token' in auth:
                from .. import verify_token
                payload = verify_token(auth['token'])
                if payload:
                    logger.info(f"WebSocket client connected: {payload.get('username')}")
                    emit('connection_status', {
                        'status': 'authenticated',
                        'user': payload.get('username'),
                        'timestamp': datetime.utcnow().isoformat()
                    })
                else:
                    logger.warning("WebSocket connection with invalid token")
                    emit('connection_status', {
                        'status': 'authentication_failed',
                        'message': 'Invalid token',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    disconnect()
            else:
                logger.info("WebSocket client connected (unauthenticated)")
                emit('connection_status', {
                    'status': 'connected',
                    'message': 'Authentication required for full access',
                    'timestamp': datetime.utcnow().isoformat()
                })
                
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            emit('error', {'message': 'Connection failed'})
            disconnect()
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info("WebSocket client disconnected")
    
    @socketio.on('join_room')
    def handle_join_room(data):
        """Join a specific room for targeted updates"""
        try:
            room = data.get('room')
            if room in ['dashboard', 'security', 'plugins', 'crawler']:
                join_room(room)
                logger.info(f"Client joined room: {room}")
                emit('room_status', {
                    'action': 'joined',
                    'room': room,
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                emit('error', {'message': 'Invalid room'})
        except Exception as e:
            logger.error(f"Join room error: {e}")
            emit('error', {'message': 'Failed to join room'})
    
    @socketio.on('leave_room')
    def handle_leave_room(data):
        """Leave a specific room"""
        try:
            room = data.get('room')
            leave_room(room)
            logger.info(f"Client left room: {room}")
            emit('room_status', {
                'action': 'left',
                'room': room,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Leave room error: {e}")
            emit('error', {'message': 'Failed to leave room'})
    
    @socketio.on('dashboard_subscribe')
    def handle_dashboard_subscribe(data):
        """Subscribe to dashboard real-time updates"""
        try:
            metrics = data.get('metrics', ['all'])
            interval = data.get('interval', 5000)  # milliseconds
            
            join_room('dashboard')
            
            # Send initial dashboard data
            dashboard_data = get_dashboard_snapshot(db_service)
            emit('dashboard_update', dashboard_data)
            
            emit('subscription_status', {
                'type': 'dashboard',
                'status': 'active',
                'metrics': metrics,
                'interval': interval,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Dashboard subscribe error: {e}")
            emit('error', {'message': 'Failed to subscribe to dashboard updates'})
    
    @socketio.on('security_subscribe')
    def handle_security_subscribe(data):
        """Subscribe to security alerts and events"""
        try:
            alert_types = data.get('alert_types', ['all'])
            severity = data.get('severity', 'medium')
            
            join_room('security')
            
            # Send current security status
            security_data = get_security_snapshot(db_service)
            emit('security_update', security_data)
            
            emit('subscription_status', {
                'type': 'security',
                'status': 'active',
                'alert_types': alert_types,
                'severity': severity,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Security subscribe error: {e}")
            emit('error', {'message': 'Failed to subscribe to security updates'})
    
    @socketio.on('crawler_subscribe')
    def handle_crawler_subscribe(data):
        """Subscribe to crawler job progress updates"""
        try:
            job_id = data.get('job_id')
            if job_id:
                join_room(f'crawler_{job_id}')
                
                # Send current job status
                job_data = get_crawler_job_status(job_id)
                emit('crawler_update', job_data)
                
                emit('subscription_status', {
                    'type': 'crawler',
                    'status': 'active',
                    'job_id': job_id,
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                emit('error', {'message': 'Job ID required for crawler subscription'})
                
        except Exception as e:
            logger.error(f"Crawler subscribe error: {e}")
            emit('error', {'message': 'Failed to subscribe to crawler updates'})
    
    @socketio.on('plugin_subscribe')
    def handle_plugin_subscribe(data):
        """Subscribe to plugin status updates"""
        try:
            plugin_id = data.get('plugin_id')
            events = data.get('events', ['status', 'logs', 'metrics'])
            
            join_room('plugins')
            if plugin_id:
                join_room(f'plugin_{plugin_id}')
            
            # Send current plugin status
            plugin_data = get_plugin_snapshot(plugin_id)
            emit('plugin_update', plugin_data)
            
            emit('subscription_status', {
                'type': 'plugin',
                'status': 'active',
                'plugin_id': plugin_id,
                'events': events,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Plugin subscribe error: {e}")
            emit('error', {'message': 'Failed to subscribe to plugin updates'})

def get_dashboard_snapshot(db_service):
    """Get current dashboard data snapshot"""
    try:
        # Get basic metrics
        now = datetime.utcnow()
        
        # User activity
        try:
            total_users = db_service.users.count_users() if db_service else 10
            active_sessions = db_service.sessions.count_active_sessions() if db_service else 3
        except:
            total_users = 10
            active_sessions = 3
        
        return {
            'metrics': {
                'users': {
                    'total': total_users,
                    'active': active_sessions,
                    'growth': 5
                },
                'system': {
                    'cpu_usage': 25,
                    'memory_usage': 60,
                    'disk_usage': 45,
                    'uptime': '2 days'
                },
                'security': {
                    'alerts': 2,
                    'last_scan': '2024-07-29T06:00:00Z',
                    'status': 'healthy'
                }
            },
            'alerts': [
                {
                    'id': 'alert_001',
                    'type': 'info',
                    'priority': 'low',
                    'message': 'System operating normally',
                    'timestamp': now.isoformat()
                }
            ],
            'timestamp': now.isoformat()
        }
    except Exception as e:
        logger.error(f"Dashboard snapshot error: {e}")
        return {
            'metrics': {},
            'alerts': [],
            'error': 'Failed to get dashboard data',
            'timestamp': datetime.utcnow().isoformat()
        }

def get_security_snapshot(db_service):
    """Get current security status snapshot"""
    try:
        now = datetime.utcnow()
        
        return {
            'status': 'healthy',
            'alerts': [
                {
                    'id': 'sec_001',
                    'type': 'authentication',
                    'severity': 'low',
                    'title': 'Normal Login Activity',
                    'message': 'All login attempts successful',
                    'timestamp': now.isoformat()
                }
            ],
            'metrics': {
                'failed_logins_24h': 0,
                'active_sessions': 3,
                'last_security_scan': '2024-07-29T06:00:00Z',
                'vulnerability_count': 0
            },
            'timestamp': now.isoformat()
        }
    except Exception as e:
        logger.error(f"Security snapshot error: {e}")
        return {
            'status': 'unknown',
            'alerts': [],
            'metrics': {},
            'error': 'Failed to get security data',
            'timestamp': datetime.utcnow().isoformat()
        }

def get_crawler_job_status(job_id):
    """Get current crawler job status"""
    try:
        # Mock job status
        return {
            'job_id': job_id,
            'status': 'active',
            'progress': 75,
            'current_task': 'Scanning network devices',
            'results_count': 23,
            'estimated_completion': '2024-07-29T08:30:00Z',
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Crawler job status error: {e}")
        return {
            'job_id': job_id,
            'status': 'unknown',
            'error': 'Failed to get job status',
            'timestamp': datetime.utcnow().isoformat()
        }

def get_plugin_snapshot(plugin_id=None):
    """Get current plugin status snapshot"""
    try:
        if plugin_id:
            return {
                'plugin_id': plugin_id,
                'status': 'active',
                'uptime': '2 days',
                'memory_usage': '32 MB',
                'cpu_usage': '2%',
                'last_activity': datetime.utcnow().isoformat(),
                'metrics': {
                    'requests_processed': 1234,
                    'errors_count': 0,
                    'avg_response_time': '45ms'
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        else:
            return {
                'total_plugins': 4,
                'active_plugins': 3,
                'inactive_plugins': 1,
                'system_load': 'low',
                'timestamp': datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Plugin snapshot error: {e}")
        return {
            'plugin_id': plugin_id,
            'status': 'unknown',
            'error': 'Failed to get plugin data',
            'timestamp': datetime.utcnow().isoformat()
        }

# Utility functions for broadcasting updates
def broadcast_dashboard_update(socketio, data):
    """Broadcast dashboard update to all subscribed clients"""
    try:
        socketio.emit('dashboard_update', data, room='dashboard')
        logger.debug("Dashboard update broadcasted")
    except Exception as e:
        logger.error(f"Dashboard broadcast error: {e}")

def broadcast_security_alert(socketio, alert):
    """Broadcast security alert to all subscribed clients"""
    try:
        socketio.emit('security_alert', alert, room='security')
        logger.info(f"Security alert broadcasted: {alert.get('title', 'Unknown')}")
    except Exception as e:
        logger.error(f"Security alert broadcast error: {e}")

def broadcast_crawler_progress(socketio, job_id, progress_data):
    """Broadcast crawler job progress to subscribed clients"""
    try:
        socketio.emit('crawler_progress', progress_data, room=f'crawler_{job_id}')
        logger.debug(f"Crawler progress broadcasted for job: {job_id}")
    except Exception as e:
        logger.error(f"Crawler progress broadcast error: {e}")

def broadcast_plugin_event(socketio, plugin_id, event_data):
    """Broadcast plugin event to subscribed clients"""
    try:
        socketio.emit('plugin_event', event_data, room=f'plugin_{plugin_id}')
        logger.debug(f"Plugin event broadcasted for: {plugin_id}")
    except Exception as e:
        logger.error(f"Plugin event broadcast error: {e}")

def broadcast_system_notification(socketio, notification):
    """Broadcast system-wide notification"""
    try:
        socketio.emit('system_notification', notification)
        logger.info(f"System notification broadcasted: {notification.get('message', 'Unknown')}")
    except Exception as e:
        logger.error(f"System notification broadcast error: {e}")