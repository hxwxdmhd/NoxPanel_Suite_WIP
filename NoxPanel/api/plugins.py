"""
Plugins API Blueprint
Handles plugin management, installation, and configuration
"""

import logging
import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
import hashlib

logger = logging.getLogger(__name__)

# Create blueprint
plugins_bp = Blueprint('plugins', __name__)

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

@plugins_bp.route('/list', methods=['GET'])
def list_plugins():
    """Get list of all plugins"""
    try:
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get query parameters
        status = request.args.get('status')  # active, inactive, all
        category = request.args.get('category')  # security, monitoring, backup, etc.
        
        # Mock plugin data (in real implementation, this would come from database/filesystem)
        plugins = [
            {
                'id': 'fritzwatcher',
                'name': 'FritzWatcher',
                'description': 'Advanced network monitoring and device tracking for Fritz!Box routers',
                'version': '2.1.0',
                'category': 'monitoring',
                'status': 'active',
                'author': 'NoxPanel Team',
                'dependencies': ['network-utils', 'web-scraper'],
                'config': {
                    'fritz_ip': '192.168.178.1',
                    'update_interval': 300,
                    'monitor_devices': True
                },
                'permissions': ['network_access', 'device_monitoring'],
                'installed_at': '2024-01-15T10:30:00Z',
                'last_updated': '2024-07-20T14:22:00Z',
                'size': '2.3 MB',
                'downloads': 1523
            },
            {
                'id': 'security-scanner',
                'name': 'Security Scanner',
                'description': 'Comprehensive security vulnerability scanner',
                'version': '1.5.2',
                'category': 'security',
                'status': 'active',
                'author': 'Security Team',
                'dependencies': ['python-nmap', 'requests'],
                'config': {
                    'scan_interval': 3600,
                    'deep_scan': False,
                    'alert_threshold': 'medium'
                },
                'permissions': ['network_scan', 'file_access'],
                'installed_at': '2024-02-01T09:15:00Z',
                'last_updated': '2024-07-18T11:45:00Z',
                'size': '4.1 MB',
                'downloads': 892
            },
            {
                'id': 'backup-manager',
                'name': 'Backup Manager',
                'description': 'Automated backup and recovery system',
                'version': '1.2.0',
                'category': 'backup',
                'status': 'inactive',
                'author': 'Data Team',
                'dependencies': ['rsync', 'compression-lib'],
                'config': {
                    'backup_path': '/var/backups/noxpanel',
                    'schedule': 'daily',
                    'retention_days': 30
                },
                'permissions': ['file_system', 'cron_access'],
                'installed_at': '2024-03-10T16:20:00Z',
                'last_updated': '2024-06-05T13:30:00Z',
                'size': '1.8 MB',
                'downloads': 445
            },
            {
                'id': 'keepass-helper',
                'name': 'KeePass Helper',
                'description': 'Integration with KeePass password manager',
                'version': '1.0.5',
                'category': 'security',
                'status': 'active',
                'author': 'Security Team',
                'dependencies': ['pykeepass'],
                'config': {
                    'database_path': '',
                    'auto_lock': True,
                    'timeout': 300
                },
                'permissions': ['file_access', 'encryption'],
                'installed_at': '2024-04-12T12:10:00Z',
                'last_updated': '2024-07-15T09:25:00Z',
                'size': '850 KB',
                'downloads': 234
            }
        ]
        
        # Filter by status
        if status and status != 'all':
            plugins = [p for p in plugins if p['status'] == status]
        
        # Filter by category
        if category:
            plugins = [p for p in plugins if p['category'] == category]
        
        # Get plugin statistics
        total_plugins = len(plugins)
        active_plugins = len([p for p in plugins if p['status'] == 'active'])
        categories = list(set(p['category'] for p in plugins))
        
        return jsonify({
            'plugins': plugins,
            'statistics': {
                'total': total_plugins,
                'active': active_plugins,
                'inactive': total_plugins - active_plugins,
                'categories': categories
            },
            'filters': {
                'status': status,
                'category': category
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"List plugins error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@plugins_bp.route('/<plugin_id>', methods=['GET'])
def get_plugin_details(plugin_id):
    """Get detailed information about a specific plugin"""
    try:
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Mock detailed plugin information
        plugin_details = {
            'fritzwatcher': {
                'id': 'fritzwatcher',
                'name': 'FritzWatcher',
                'description': 'Advanced network monitoring and device tracking for Fritz!Box routers',
                'long_description': '''
                FritzWatcher provides comprehensive monitoring capabilities for Fritz!Box routers,
                including device tracking, bandwidth monitoring, and network security analysis.
                Features include real-time device detection, historical data tracking, and
                automated alerts for network changes.
                ''',
                'version': '2.1.0',
                'category': 'monitoring',
                'status': 'active',
                'author': 'NoxPanel Team',
                'homepage': 'https://github.com/noxpanel/fritzwatcher',
                'documentation': 'https://docs.noxpanel.com/plugins/fritzwatcher',
                'license': 'MIT',
                'dependencies': [
                    {'name': 'network-utils', 'version': '>=1.2.0', 'status': 'satisfied'},
                    {'name': 'web-scraper', 'version': '>=2.0.0', 'status': 'satisfied'}
                ],
                'config_schema': {
                    'fritz_ip': {
                        'type': 'string',
                        'default': '192.168.178.1',
                        'description': 'IP address of the Fritz!Box router'
                    },
                    'update_interval': {
                        'type': 'integer',
                        'default': 300,
                        'description': 'Update interval in seconds'
                    },
                    'monitor_devices': {
                        'type': 'boolean',
                        'default': True,
                        'description': 'Enable device monitoring'
                    }
                },
                'current_config': {
                    'fritz_ip': '192.168.178.1',
                    'update_interval': 300,
                    'monitor_devices': True
                },
                'permissions': ['network_access', 'device_monitoring'],
                'metrics': {
                    'devices_monitored': 23,
                    'data_points_collected': 15420,
                    'last_scan': '2024-07-29T06:45:00Z',
                    'uptime': '99.8%'
                },
                'logs': [
                    {
                        'timestamp': '2024-07-29T07:30:00Z',
                        'level': 'info',
                        'message': 'Device scan completed successfully'
                    },
                    {
                        'timestamp': '2024-07-29T07:00:00Z',
                        'level': 'info',
                        'message': 'New device detected: iPhone-12'
                    }
                ]
            }
        }
        
        if plugin_id not in plugin_details:
            return jsonify({'error': 'Plugin not found'}), 404
        
        return jsonify({
            'plugin': plugin_details[plugin_id],
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Get plugin details error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@plugins_bp.route('/<plugin_id>/config', methods=['GET', 'POST'])
def plugin_config(plugin_id):
    """Get or update plugin configuration"""
    try:
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        if request.method == 'GET':
            # Return current plugin configuration
            # In real implementation, this would come from database
            config = {
                'fritz_ip': '192.168.178.1',
                'update_interval': 300,
                'monitor_devices': True,
                'alert_new_devices': False,
                'log_level': 'info'
            }
            
            return jsonify({
                'plugin_id': plugin_id,
                'config': config,
                'last_updated': '2024-07-20T14:22:00Z',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        
        else:  # POST - Update configuration
            # Check if user has admin role
            if user_payload.get('role') not in ['admin', 'plugin_admin']:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No configuration data provided'}), 400
            
            config_updates = data.get('config', {})
            
            # Validate configuration (in real implementation)
            # Save configuration to database
            
            logger.info(f"Plugin {plugin_id} configuration updated by {user_payload.get('username')}")
            
            return jsonify({
                'message': 'Plugin configuration updated successfully',
                'plugin_id': plugin_id,
                'updated_fields': list(config_updates.keys()),
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        
    except Exception as e:
        logger.error(f"Plugin config error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@plugins_bp.route('/<plugin_id>/control', methods=['POST'])
def plugin_control(plugin_id):
    """Control plugin operations (start, stop, restart, etc.)"""
    try:
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if user has admin role
        if user_payload.get('role') not in ['admin', 'plugin_admin']:
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No action specified'}), 400
        
        action = data.get('action')  # start, stop, restart, reload
        
        if action not in ['start', 'stop', 'restart', 'reload']:
            return jsonify({'error': 'Invalid action'}), 400
        
        # Mock plugin control (in real implementation, this would interface with plugin manager)
        success = True
        message = f"Plugin {plugin_id} {action} successful"
        
        if success:
            logger.info(f"Plugin {plugin_id} {action} by {user_payload.get('username')}")
            return jsonify({
                'message': message,
                'plugin_id': plugin_id,
                'action': action,
                'status': 'active' if action in ['start', 'restart'] else 'inactive',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        else:
            return jsonify({'error': f'Failed to {action} plugin'}), 500
        
    except Exception as e:
        logger.error(f"Plugin control error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@plugins_bp.route('/install', methods=['POST'])
def install_plugin():
    """Install a new plugin"""
    try:
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if user has admin role
        if user_payload.get('role') not in ['admin', 'plugin_admin']:
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No installation data provided'}), 400
        
        plugin_source = data.get('source')  # url, file, repository
        plugin_url = data.get('url')
        plugin_name = data.get('name')
        
        if not plugin_source or not plugin_name:
            return jsonify({'error': 'Plugin source and name are required'}), 400
        
        # Mock installation process
        installation_id = hashlib.md5(f"{plugin_name}_{datetime.utcnow()}".encode()).hexdigest()[:16]
        
        # Simulate installation steps
        steps = [
            'Downloading plugin package',
            'Verifying dependencies',
            'Installing dependencies',
            'Configuring plugin',
            'Registering plugin',
            'Starting plugin'
        ]
        
        logger.info(f"Plugin installation started: {plugin_name} by {user_payload.get('username')}")
        
        return jsonify({
            'message': 'Plugin installation completed successfully',
            'installation_id': installation_id,
            'plugin_name': plugin_name,
            'steps_completed': steps,
            'status': 'installed',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Plugin installation error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@plugins_bp.route('/<plugin_id>/uninstall', methods=['POST'])
def uninstall_plugin(plugin_id):
    """Uninstall a plugin"""
    try:
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Check if user has admin role
        if user_payload.get('role') not in ['admin', 'plugin_admin']:
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        remove_data = data.get('remove_data', False) if data else False
        
        # Mock uninstallation process
        logger.info(f"Plugin uninstallation started: {plugin_id} by {user_payload.get('username')}")
        
        return jsonify({
            'message': 'Plugin uninstalled successfully',
            'plugin_id': plugin_id,
            'data_removed': remove_data,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Plugin uninstall error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@plugins_bp.route('/marketplace', methods=['GET'])
def plugin_marketplace():
    """Get available plugins from marketplace"""
    try:
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Mock marketplace data
        marketplace_plugins = [
            {
                'id': 'advanced-firewall',
                'name': 'Advanced Firewall',
                'description': 'Enhanced firewall management and monitoring',
                'version': '1.3.0',
                'category': 'security',
                'author': 'Security Corp',
                'rating': 4.8,
                'downloads': 15420,
                'price': 'free',
                'compatibility': ['noxpanel >= 1.0.0'],
                'last_updated': '2024-07-25T10:00:00Z'
            },
            {
                'id': 'log-analyzer',
                'name': 'Log Analyzer Pro',
                'description': 'Advanced log analysis and visualization',
                'version': '2.1.5',
                'category': 'monitoring',
                'author': 'DataViz Inc',
                'rating': 4.6,
                'downloads': 8932,
                'price': '$29.99',
                'compatibility': ['noxpanel >= 1.0.0'],
                'last_updated': '2024-07-20T15:30:00Z'
            }
        ]
        
        # Get query parameters
        category = request.args.get('category')
        search = request.args.get('search')
        
        # Filter by category
        if category:
            marketplace_plugins = [p for p in marketplace_plugins if p['category'] == category]
        
        # Filter by search
        if search:
            search_lower = search.lower()
            marketplace_plugins = [
                p for p in marketplace_plugins 
                if search_lower in p['name'].lower() or search_lower in p['description'].lower()
            ]
        
        return jsonify({
            'plugins': marketplace_plugins,
            'count': len(marketplace_plugins),
            'filters': {
                'category': category,
                'search': search
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Plugin marketplace error: {e}")
        return jsonify({'error': 'Internal server error'}), 500