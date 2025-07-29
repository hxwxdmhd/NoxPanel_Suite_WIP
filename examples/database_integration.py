from NoxPanel.noxcore.utils.logging_config import get_logger

# Security: Audit logging for security events
def log_security_event(event_type: str, details: dict, request_ip: str = None):
    """Log security-related events for audit trails."""
    security_event = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'details': details,
        'request_ip': request_ip,
        'severity': 'security'
    }
    logger.warning(f"SECURITY_EVENT: {json.dumps(security_event)}")

def log_access_attempt(endpoint: str, user_id: str = None, success: bool = True):
    """Log access attempts for security monitoring."""
    log_security_event('access_attempt', {
        'endpoint': endpoint,
        'user_id': user_id,
        'success': success
    })

logger = get_logger(__name__)

"""
Example usage and integration code for NoxGuard Database System
Demonstrates how to integrate the database with existing NoxPanel components
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from NoxPanel.noxcore.database_service import get_database_service, close_database_service
from NoxPanel.noxcore.database_admin import DatabaseAdmin

# Setup logging
logging.basicConfig(level=logging.INFO)

# Security: Audit logging for security events
def log_security_event(event_type: str, details: dict, request_ip: str = None):
    """Log security-related events for audit trails."""
    security_event = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'details': details,
        'request_ip': request_ip,
        'severity': 'security'
    }
    logger.warning(f"SECURITY_EVENT: {json.dumps(security_event)}")

def log_access_attempt(endpoint: str, user_id: str = None, success: bool = True):
    """Log access attempts for security monitoring."""
    log_security_event('access_attempt', {
        'endpoint': endpoint,
        'user_id': user_id,
        'success': success
    })

logger = logging.getLogger(__name__)

class NoxPanelIntegration:
    """Integration layer for NoxPanel with enhanced database"""
    
    def __init__(self, db_path: str = None):
        """Initialize with database service"""
        self.db = get_database_service(db_path)
        self.admin = DatabaseAdmin(db_path)
    
    def setup_system(self):
        """Setup initial system configuration"""
        logger.info("Setting up NoxPanel system...")
        
        # Check database health
        health = self.admin.health_check()
        if health['health_status'] != 'healthy':
            logger.warning(f"Database health issue: {health}")
            return False
        
        # Ensure required settings exist
        self._setup_default_settings()
        
        # Create sample data if empty
        self._create_sample_data()
        
        logger.info("System setup completed successfully")
        return True
    
    def _setup_default_settings(self):
        """Setup default system settings"""
        default_settings = {
            'system_name': 'NoxGuard Panel',
            'version': '1.0.0',
            'theme': 'dark',
            'auto_discovery': 'true',
            'scan_interval': '300',
            'max_devices': '1000',
            'security_level': 'high',
            'backup_enabled': 'true',
            'backup_interval': '24',
            'log_retention_days': '30',
            'knowledge_categories': json.dumps([
                'network', 'security', 'troubleshooting', 'documentation'
            ])
        }
        
        with self.db.db.get_connection() as conn:
            for key, value in default_settings.items():
                conn.execute("""
                    INSERT OR IGNORE INTO settings (key, value, category, description)
                    VALUES (?, ?, 'system', ?)
                """, (key, value, f"Default {key} setting"))
    
    def _create_sample_data(self):
        """Create sample data if database is empty"""
        # Check if we need sample data
        with self.db.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM knowledge_items")
            knowledge_count = cursor.fetchone()[0]
            
            if knowledge_count == 0:
                self._create_sample_knowledge()
            
            cursor.execute("SELECT COUNT(*) FROM tags")
            tag_count = cursor.fetchone()[0]
            
            if tag_count == 0:
                self._create_sample_tags()
    
    def _create_sample_knowledge(self):
        """Create sample knowledge items"""
        admin_user = self.db.users.get_user(username='admin')
        if not admin_user:
            return
        
        sample_knowledge = [
            {
                'title': 'Network Discovery Best Practices',
                'content': '''# Network Discovery Best Practices

## Overview
Network discovery is the process of automatically identifying devices on your network.

## Best Practices
1. Use multiple discovery methods (ping, ARP, SNMP)
2. Schedule regular scans during off-peak hours
3. Maintain an allow/deny list for sensitive devices
4. Document discovered devices properly

## Common Tools
- Nmap for port scanning
- ARP tables for local discovery
- SNMP for managed devices
- Custom scripts for specific protocols
''',
                'category': 'network',
                'content_type': 'markdown',
                'search_keywords': 'network discovery nmap arp snmp scanning'
            },
            {
                'title': 'Security Monitoring Guidelines',
                'content': '''# Security Monitoring Guidelines

## Key Areas to Monitor
- Failed login attempts
- Unusual network traffic patterns
- New device connections
- Port scanning activities
- Privilege escalation attempts

## Response Procedures
1. Document the incident
2. Assess the threat level
3. Contain if necessary
4. Investigate and remediate
5. Update monitoring rules

## Tools Integration
- Log analysis systems
- SIEM solutions
- Network monitoring tools
- Vulnerability scanners
''',
                'category': 'security',
                'content_type': 'markdown',
                'search_keywords': 'security monitoring siem logs alerts'
            },
            {
                'title': 'Troubleshooting Network Connectivity',
                'content': '''# Troubleshooting Network Connectivity

## Step-by-Step Process
1. Check physical connections
2. Verify IP configuration
3. Test local connectivity (ping gateway)
4. Test remote connectivity (ping external)
5. Check DNS resolution
6. Verify routing tables
7. Check firewall rules

## Common Issues
- IP conflicts
- DNS misconfigurations
- Routing problems
- Firewall blocking
- Hardware failures

## Useful Commands
```
ping 8.8.8.8
nslookup domain.com
traceroute destination
netstat -rn
```
''',
                'category': 'troubleshooting',
                'content_type': 'markdown',
                'search_keywords': 'troubleshooting connectivity ping dns routing'
            }
        ]
        
        for item in sample_knowledge:
            knowledge_id = self.db.knowledge.create_knowledge_item(
                title=item['title'],
                content=item['content'],
                category=item['category'],
                author_id=admin_user['id'],
                content_type=item['content_type'],
                search_keywords=item['search_keywords']
            )
            logger.info(f"Created knowledge item: {item['title']} (ID: {knowledge_id})")
    
    def _create_sample_tags(self):
        """Create sample tags"""
        admin_user = self.db.users.get_user(username='admin')
        if not admin_user:
            return
        
        sample_tags = [
            {'name': 'network', 'description': 'Network-related content', 'color': '#2196F3'},
            {'name': 'security', 'description': 'Security-related content', 'color': '#F44336'},
            {'name': 'troubleshooting', 'description': 'Troubleshooting guides', 'color': '#FF9800'},
            {'name': 'documentation', 'description': 'General documentation', 'color': '#4CAF50'},
            {'name': 'monitoring', 'description': 'Monitoring and alerting', 'color': '#9C27B0'},
            {'name': 'automation', 'description': 'Automation scripts and tools', 'color': '#00BCD4'},
            {'name': 'urgent', 'description': 'Urgent/critical information', 'color': '#FF5722'},
            {'name': 'tutorial', 'description': 'Step-by-step tutorials', 'color': '#607D8B'}
        ]
        
        for tag in sample_tags:
            tag_id = self.db.tags.create_tag(
                name=tag['name'],
                description=tag['description'],
                color=tag['color'],
                created_by=admin_user['id']
            )
            logger.info(f"Created tag: {tag['name']} (ID: {tag_id})")
    
    def close(self):
        """Close database connections"""
        close_database_service()

def example_usage():
    """Example usage of the integrated database system"""
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    try:
        db_path = os.path.join(temp_dir, 'noxpanel.db')
        
        # Initialize the integration
        integration = NoxPanelIntegration(db_path)
        
        # Setup the system
        integration.setup_system()
        
        # Get admin user
        admin_user = integration.db.users.get_user(username='admin')
        if admin_user:
            # Search knowledge
            results = integration.db.knowledge.search_knowledge_items('network')
            logger.info(f"Found {len(results)} knowledge items")
            
            # Create conversation
            conv_id = integration.db.conversations.create_conversation(
                user_id=admin_user['id'],
                title="Test Chat"
            )
            logger.info(f"Created conversation: {conv_id}")
            
            # Add messages
            integration.db.conversations.add_message(
                conversation_id=conv_id,
                role='user',
                content='How do I troubleshoot network connectivity?'
            )
            
            integration.db.conversations.add_message(
                conversation_id=conv_id,
                role='assistant', 
                content='Here is a step-by-step approach to troubleshoot network connectivity...'
            )
            
            logger.info("Added messages to conversation")
            
            # Generate report
            status = integration.admin.status()
            logger.info(f"Database has {status['table_counts']['knowledge_items']} knowledge items")
        
        logger.info("Example completed successfully!")
        
        integration.close()
        
    finally:
        shutil.rmtree(temp_dir)

if __name__ == '__main__':
    example_usage()