"""
Crawler API Blueprint
Handles web crawler operations, data visualization, and network analysis
"""

import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
import hashlib
import json

logger = logging.getLogger(__name__)

# Create blueprint
crawler_bp = Blueprint('crawler', __name__)

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

@crawler_bp.route('/jobs', methods=['GET'])
def list_crawler_jobs():
    """Get list of crawler jobs"""
    try:
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get query parameters
        status = request.args.get('status')  # active, completed, failed, pending
        limit = int(request.args.get('limit', 50))
        
        # Mock crawler jobs data
        jobs = [
            {
                'id': 'job_001',
                'name': 'Network Device Discovery',
                'description': 'Scan local network for devices and services',
                'status': 'active',
                'type': 'network_scan',
                'progress': 65,
                'started_at': '2024-07-29T07:00:00Z',
                'estimated_completion': '2024-07-29T08:30:00Z',
                'target': '192.168.1.0/24',
                'results_count': 23,
                'config': {
                    'scan_type': 'comprehensive',
                    'port_range': '1-1000',
                    'timeout': 30
                }
            },
            {
                'id': 'job_002',
                'name': 'Website Structure Analysis',
                'description': 'Analyze website structure and dependencies',
                'status': 'completed',
                'type': 'web_crawl',
                'progress': 100,
                'started_at': '2024-07-29T05:30:00Z',
                'completed_at': '2024-07-29T06:45:00Z',
                'target': 'https://example.com',
                'results_count': 156,
                'config': {
                    'max_depth': 3,
                    'follow_external': False,
                    'extract_assets': True
                }
            },
            {
                'id': 'job_003',
                'name': 'Security Vulnerability Scan',
                'description': 'Scan for common security vulnerabilities',
                'status': 'failed',
                'type': 'security_scan',
                'progress': 30,
                'started_at': '2024-07-29T04:00:00Z',
                'failed_at': '2024-07-29T04:15:00Z',
                'target': '10.0.0.0/16',
                'error': 'Network timeout - target unreachable',
                'config': {
                    'scan_intensity': 'aggressive',
                    'vuln_types': ['sql_injection', 'xss', 'csrf']
                }
            }
        ]
        
        # Filter by status
        if status:
            jobs = [job for job in jobs if job['status'] == status]
        
        # Limit results
        jobs = jobs[:limit]
        
        # Calculate statistics
        total_jobs = len(jobs)
        status_counts = {}
        for job in jobs:
            job_status = job['status']
            status_counts[job_status] = status_counts.get(job_status, 0) + 1
        
        return jsonify({
            'jobs': jobs,
            'statistics': {
                'total': total_jobs,
                'by_status': status_counts
            },
            'filters': {
                'status': status,
                'limit': limit
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"List crawler jobs error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@crawler_bp.route('/jobs', methods=['POST'])
def create_crawler_job():
    """Create a new crawler job"""
    try:
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No job data provided'}), 400
        
        job_name = data.get('name')
        job_type = data.get('type')  # network_scan, web_crawl, security_scan
        target = data.get('target')
        config = data.get('config', {})
        
        if not job_name or not job_type or not target:
            return jsonify({'error': 'Name, type, and target are required'}), 400
        
        if job_type not in ['network_scan', 'web_crawl', 'security_scan']:
            return jsonify({'error': 'Invalid job type'}), 400
        
        # Generate job ID
        job_id = hashlib.md5(f"{job_name}_{datetime.utcnow()}".encode()).hexdigest()[:16]
        
        # Create job
        job = {
            'id': job_id,
            'name': job_name,
            'description': data.get('description', ''),
            'type': job_type,
            'target': target,
            'status': 'pending',
            'progress': 0,
            'created_at': datetime.utcnow().isoformat(),
            'created_by': user_payload.get('username'),
            'config': config
        }
        
        logger.info(f"Crawler job created: {job_id} by {user_payload.get('username')}")
        
        return jsonify({
            'message': 'Crawler job created successfully',
            'job': job
        }), 201
        
    except Exception as e:
        logger.error(f"Create crawler job error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@crawler_bp.route('/jobs/<job_id>', methods=['GET'])
def get_crawler_job(job_id):
    """Get detailed information about a crawler job"""
    try:
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Mock detailed job information
        job_details = {
            'id': job_id,
            'name': 'Network Device Discovery',
            'description': 'Comprehensive scan of local network infrastructure',
            'type': 'network_scan',
            'status': 'active',
            'progress': 75,
            'target': '192.168.1.0/24',
            'started_at': '2024-07-29T07:00:00Z',
            'estimated_completion': '2024-07-29T08:30:00Z',
            'created_by': 'admin',
            'config': {
                'scan_type': 'comprehensive',
                'port_range': '1-1000',
                'timeout': 30,
                'concurrent_scans': 50,
                'service_detection': True
            },
            'results': {
                'devices_found': 23,
                'services_identified': 87,
                'open_ports': 156,
                'vulnerabilities': 3
            },
            'logs': [
                {
                    'timestamp': '2024-07-29T07:30:00Z',
                    'level': 'info',
                    'message': 'Discovered device: Router (192.168.1.1)'
                },
                {
                    'timestamp': '2024-07-29T07:25:00Z',
                    'level': 'info',
                    'message': 'Scanning subnet 192.168.1.0/24'
                },
                {
                    'timestamp': '2024-07-29T07:00:00Z',
                    'level': 'info',
                    'message': 'Job started'
                }
            ],
            'performance': {
                'scan_rate': '2.5 hosts/sec',
                'data_collected': '4.2 MB',
                'cpu_usage': '15%',
                'memory_usage': '128 MB'
            }
        }
        
        return jsonify({
            'job': job_details,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Get crawler job error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@crawler_bp.route('/jobs/<job_id>/control', methods=['POST'])
def control_crawler_job(job_id):
    """Control crawler job (start, stop, pause, resume)"""
    try:
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No action specified'}), 400
        
        action = data.get('action')  # start, stop, pause, resume
        
        if action not in ['start', 'stop', 'pause', 'resume']:
            return jsonify({'error': 'Invalid action'}), 400
        
        # Mock job control
        success = True
        new_status = {
            'start': 'active',
            'stop': 'stopped',
            'pause': 'paused',
            'resume': 'active'
        }.get(action)
        
        if success:
            logger.info(f"Crawler job {job_id} {action} by {user_payload.get('username')}")
            return jsonify({
                'message': f'Job {action} successful',
                'job_id': job_id,
                'action': action,
                'new_status': new_status,
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        else:
            return jsonify({'error': f'Failed to {action} job'}), 500
        
    except Exception as e:
        logger.error(f"Control crawler job error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@crawler_bp.route('/jobs/<job_id>/results', methods=['GET'])
def get_crawler_results(job_id):
    """Get results from a crawler job"""
    try:
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get query parameters
        result_type = request.args.get('type')  # devices, services, vulnerabilities, all
        format_type = request.args.get('format', 'json')  # json, csv, xml
        limit = int(request.args.get('limit', 100))
        
        # Mock crawler results
        results = {
            'job_id': job_id,
            'status': 'completed',
            'total_results': 156,
            'collected_at': '2024-07-29T06:45:00Z',
            'data': {
                'devices': [
                    {
                        'ip': '192.168.1.1',
                        'hostname': 'router.local',
                        'mac': '00:1A:2B:3C:4D:5E',
                        'vendor': 'AVM GmbH',
                        'type': 'router',
                        'os': 'Fritz!OS',
                        'ports': [80, 443, 22],
                        'services': ['http', 'https', 'ssh']
                    },
                    {
                        'ip': '192.168.1.100',
                        'hostname': 'desktop-pc',
                        'mac': 'AA:BB:CC:DD:EE:FF',
                        'vendor': 'Intel Corp',
                        'type': 'computer',
                        'os': 'Windows 10',
                        'ports': [135, 445, 3389],
                        'services': ['rpc', 'smb', 'rdp']
                    }
                ],
                'network_topology': {
                    'nodes': [
                        {'id': '192.168.1.1', 'type': 'router', 'label': 'Router'},
                        {'id': '192.168.1.100', 'type': 'computer', 'label': 'Desktop PC'},
                        {'id': '192.168.1.101', 'type': 'smartphone', 'label': 'iPhone'},
                        {'id': '192.168.1.102', 'type': 'tablet', 'label': 'iPad'}
                    ],
                    'edges': [
                        {'from': '192.168.1.1', 'to': '192.168.1.100', 'type': 'ethernet'},
                        {'from': '192.168.1.1', 'to': '192.168.1.101', 'type': 'wifi'},
                        {'from': '192.168.1.1', 'to': '192.168.1.102', 'type': 'wifi'}
                    ]
                },
                'vulnerabilities': [
                    {
                        'target': '192.168.1.100',
                        'type': 'open_port',
                        'severity': 'medium',
                        'description': 'SMB service exposed',
                        'recommendation': 'Disable SMB if not needed'
                    }
                ],
                'statistics': {
                    'total_devices': 23,
                    'device_types': {'router': 1, 'computer': 8, 'smartphone': 7, 'tablet': 4, 'other': 3},
                    'total_ports': 156,
                    'unique_services': 24,
                    'security_issues': 3
                }
            }
        }
        
        # Filter by result type
        if result_type and result_type != 'all':
            if result_type in results['data']:
                filtered_data = {result_type: results['data'][result_type]}
                results['data'] = filtered_data
            else:
                return jsonify({'error': 'Invalid result type'}), 400
        
        return jsonify({
            'results': results,
            'format': format_type,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Get crawler results error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@crawler_bp.route('/visualization/network', methods=['GET'])
def network_visualization():
    """Get network topology data for visualization"""
    try:
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get query parameters
        job_id = request.args.get('job_id')
        layout = request.args.get('layout', 'force')  # force, hierarchical, circular
        
        # Mock network visualization data
        visualization_data = {
            'nodes': [
                {
                    'id': 'router',
                    'label': 'Fritz!Box Router',
                    'type': 'router',
                    'ip': '192.168.1.1',
                    'position': {'x': 0, 'y': 0},
                    'size': 30,
                    'color': '#ff6b6b',
                    'properties': {
                        'vendor': 'AVM',
                        'model': 'Fritz!Box 7590',
                        'uptime': '15 days',
                        'connections': 12
                    }
                },
                {
                    'id': 'desktop1',
                    'label': 'Desktop PC',
                    'type': 'computer',
                    'ip': '192.168.1.100',
                    'position': {'x': -100, 'y': 80},
                    'size': 20,
                    'color': '#4ecdc4',
                    'properties': {
                        'os': 'Windows 10',
                        'last_seen': '2024-07-29T07:30:00Z',
                        'services': ['SSH', 'HTTP', 'SMB']
                    }
                },
                {
                    'id': 'phone1',
                    'label': 'iPhone 12',
                    'type': 'smartphone',
                    'ip': '192.168.1.101',
                    'position': {'x': 100, 'y': 80},
                    'size': 15,
                    'color': '#45b7d1',
                    'properties': {
                        'vendor': 'Apple',
                        'connection': 'WiFi',
                        'signal_strength': '-45 dBm'
                    }
                }
            ],
            'edges': [
                {
                    'id': 'router-desktop1',
                    'from': 'router',
                    'to': 'desktop1',
                    'type': 'ethernet',
                    'label': '1 Gbps',
                    'color': '#95a5a6',
                    'width': 3,
                    'properties': {
                        'bandwidth': '1000 Mbps',
                        'latency': '< 1ms',
                        'status': 'active'
                    }
                },
                {
                    'id': 'router-phone1',
                    'from': 'router',
                    'to': 'phone1',
                    'type': 'wifi',
                    'label': 'WiFi 6',
                    'color': '#9b59b6',
                    'width': 2,
                    'properties': {
                        'bandwidth': '200 Mbps',
                        'latency': '< 5ms',
                        'status': 'active'
                    }
                }
            ],
            'metadata': {
                'total_nodes': 23,
                'total_edges': 22,
                'layout': layout,
                'last_updated': '2024-07-29T07:45:00Z',
                'scan_duration': '45 minutes',
                'coverage': '100%'
            }
        }
        
        return jsonify({
            'visualization': visualization_data,
            'job_id': job_id,
            'layout': layout,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Network visualization error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@crawler_bp.route('/templates', methods=['GET'])
def crawler_templates():
    """Get predefined crawler job templates"""
    try:
        user_payload = require_auth()
        if not user_payload:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Mock crawler templates
        templates = [
            {
                'id': 'network_discovery',
                'name': 'Network Discovery',
                'description': 'Discover all devices on the local network',
                'type': 'network_scan',
                'category': 'discovery',
                'config': {
                    'scan_type': 'comprehensive',
                    'port_range': '1-1000',
                    'timeout': 30,
                    'service_detection': True,
                    'os_detection': True
                },
                'estimated_duration': '30-60 minutes',
                'requirements': ['network_access'],
                'outputs': ['device_list', 'network_topology', 'service_inventory']
            },
            {
                'id': 'security_audit',
                'name': 'Security Audit',
                'description': 'Comprehensive security vulnerability assessment',
                'type': 'security_scan',
                'category': 'security',
                'config': {
                    'scan_intensity': 'moderate',
                    'vuln_types': ['sql_injection', 'xss', 'csrf', 'open_ports'],
                    'compliance_checks': True,
                    'generate_report': True
                },
                'estimated_duration': '1-3 hours',
                'requirements': ['admin_access'],
                'outputs': ['vulnerability_report', 'compliance_status', 'remediation_guide']
            },
            {
                'id': 'web_analysis',
                'name': 'Website Analysis',
                'description': 'Analyze website structure, performance, and SEO',
                'type': 'web_crawl',
                'category': 'analysis',
                'config': {
                    'max_depth': 5,
                    'follow_external': False,
                    'extract_assets': True,
                    'performance_metrics': True,
                    'seo_analysis': True
                },
                'estimated_duration': '15-45 minutes',
                'requirements': ['internet_access'],
                'outputs': ['site_map', 'performance_report', 'seo_report']
            }
        ]
        
        return jsonify({
            'templates': templates,
            'count': len(templates),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Crawler templates error: {e}")
        return jsonify({'error': 'Internal server error'}), 500