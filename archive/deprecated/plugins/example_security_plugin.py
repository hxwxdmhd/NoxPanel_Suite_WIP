#!/usr/bin/env python3
"""
Example Security Plugin
=====================
Demonstrates enhanced plugin features for Audit 2 compliance
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unified_plugin_system_clean import SecurityPlugin, PluginInfo
from typing import Dict, Any, List

class ExampleSecurityPlugin(SecurityPlugin):
    """Example security plugin demonstrating enhanced features"""
    
    def __init__(self):
        super().__init__()
        self.security_level = "HIGH"
        self.dependencies = []  # No dependencies for this example
        self.permissions = ["system.monitor", "api.call"]
        
    def get_info(self) -> PluginInfo:
        """Get plugin information"""
        return PluginInfo(
            name="ExampleSecurityPlugin",
            version="1.0.0",
            description="Example security plugin with enhanced features",
            author="Enhanced Plugin System",
            category="security",
            dependencies=self.dependencies,
            permissions=self.permissions
        )
    
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """Initialize the security plugin"""
        try:
            self.config = config or {}
            self.initialized = True
            self.status = "initialized"
            self.logger.info("Security plugin initialized successfully")
            return True
        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"Security plugin initialization failed: {e}")
            return False
    
    def start(self) -> bool:
        """Start the security plugin"""
        try:
            if not self.initialized:
                if not self.initialize():
                    return False
            
            self.running = True
            self.status = "running"
            self.logger.info("Security plugin started successfully")
            return True
        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"Security plugin start failed: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the security plugin"""
        try:
            self.running = False
            self.status = "stopped"
            self.logger.info("Security plugin stopped")
            return True
        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"Security plugin stop failed: {e}")
            return False
    
    def cleanup(self) -> bool:
        """Clean up security plugin resources"""
        try:
            self.stop()
            self.initialized = False
            self.status = "inactive"
            self.logger.info("Security plugin cleaned up")
            return True
        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"Security plugin cleanup failed: {e}")
            return False
    
    def get_status(self) -> str:
        """Get plugin status"""
        return self.status
    
    def validate_security(self, context: Dict[str, Any]) -> bool:
        """Validate security context"""
        try:
            # Example security validation logic
            if not context:
                return False
            
            # Check for required security fields
            required_fields = ['user_id', 'permissions', 'timestamp']
            for field in required_fields:
                if field not in context:
                    self.logger.warning(f"Missing security field: {field}")
                    return False
            
            # Validate permissions
            user_permissions = context.get('permissions', [])
            if not isinstance(user_permissions, list):
                return False
            
            # Example: Check if user has required permissions
            if 'admin' not in user_permissions and 'security' not in user_permissions:
                self.logger.warning("Insufficient permissions for security operation")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Security validation failed: {e}")
            return False
    
    def get_security_level(self) -> str:
        """Get security level provided"""
        return self.security_level
    
    def get_health(self) -> Dict[str, Any]:
        """Get plugin health status"""
        return {
            'status': 'healthy' if self.running else 'inactive',
            'timestamp': '2025-07-18T18:40:00Z',
            'metrics': {
                'security_checks': 0,
                'validation_success_rate': 100.0,
                'last_check': '2025-07-18T18:40:00Z'
            },
            'last_error': self.last_error,
            'initialized': self.initialized,
            'running': self.running,
            'security_level': self.security_level
        }

# Plugin entry point
if __name__ == "__main__":
    plugin = ExampleSecurityPlugin()
    print(f"Plugin: {plugin.get_info().name}")
    print(f"Version: {plugin.get_info().version}")
    print(f"Security Level: {plugin.get_security_level()}")
    print("Plugin ready for testing!")
