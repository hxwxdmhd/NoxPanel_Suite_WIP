#!/usr/bin/env python3
"""
Example Service Plugin
=====================
Demonstrates enhanced service plugin features for Audit 2 compliance
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unified_plugin_system_clean import ServicePlugin, PluginInfo
from typing import Dict, Any, List
import time
import threading

class ExampleServicePlugin(ServicePlugin):
    """Example service plugin demonstrating enhanced features"""
    
    def __init__(self):
        super().__init__()
        self.service_name = "ExampleService"
        self.service_thread = None
        self.service_running = False
        self.dependencies = []  # No dependencies for this example
        self.permissions = ["network.http", "filesystem.read"]
        
    def get_info(self) -> PluginInfo:
        """Get plugin information"""
        return PluginInfo(
            name="ExampleServicePlugin",
            version="1.0.0",
            description="Example service plugin with enhanced features",
            author="Enhanced Plugin System",
            category="service",
            dependencies=self.dependencies,
            permissions=self.permissions
        )
    
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """Initialize the service plugin"""
        try:
            self.config = config or {}
            self.initialized = True
            self.status = "initialized"
            self.logger.info("Service plugin initialized successfully")
            return True
        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"Service plugin initialization failed: {e}")
            return False
    
    def start(self) -> bool:
        """Start the service plugin"""
        try:
            if not self.initialized:
                if not self.initialize():
                    return False
            
            # Start the service
            if self.start_service():
                self.running = True
                self.status = "running"
                self.logger.info("Service plugin started successfully")
                return True
            else:
                return False
                
        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"Service plugin start failed: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the service plugin"""
        try:
            # Stop the service
            if self.stop_service():
                self.running = False
                self.status = "stopped"
                self.logger.info("Service plugin stopped")
                return True
            else:
                return False
        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"Service plugin stop failed: {e}")
            return False
    
    def cleanup(self) -> bool:
        """Clean up service plugin resources"""
        try:
            self.stop()
            self.initialized = False
            self.status = "inactive"
            self.logger.info("Service plugin cleaned up")
            return True
        except Exception as e:
            self.last_error = str(e)
            self.logger.error(f"Service plugin cleanup failed: {e}")
            return False
    
    def get_status(self) -> str:
        """Get plugin status"""
        return self.status
    
    def start_service(self) -> bool:
        """Start the service"""
        try:
            if self.service_running:
                self.logger.warning("Service already running")
                return True
            
            # Start service thread
            self.service_thread = threading.Thread(target=self._service_worker)
            self.service_thread.daemon = True
            self.service_running = True
            self.service_thread.start()
            
            self.logger.info(f"Service {self.service_name} started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start service: {e}")
            return False
    
    def stop_service(self) -> bool:
        """Stop the service"""
        try:
            if not self.service_running:
                self.logger.warning("Service not running")
                return True
            
            self.service_running = False
            
            # Wait for service thread to finish
            if self.service_thread and self.service_thread.is_alive():
                self.service_thread.join(timeout=5)
            
            self.logger.info(f"Service {self.service_name} stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop service: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'service_name': self.service_name,
            'running': self.service_running,
            'thread_alive': self.service_thread.is_alive() if self.service_thread else False,
            'uptime': time.time() - getattr(self, 'start_time', time.time()),
            'requests_handled': getattr(self, 'requests_handled', 0),
            'last_activity': getattr(self, 'last_activity', time.time())
        }
    
    def _service_worker(self):
        """Service worker thread"""
        self.start_time = time.time()
        self.requests_handled = 0
        
        while self.service_running:
            try:
                # Simulate service work
                time.sleep(1)
                self.requests_handled += 1
                self.last_activity = time.time()
                
                # Update metrics
                self.metrics['requests_handled'] = self.requests_handled
                self.metrics['uptime'] = time.time() - self.start_time
                
            except Exception as e:
                self.logger.error(f"Service worker error: {e}")
                break
    
    def get_health(self) -> Dict[str, Any]:
        """Get plugin health status"""
        return {
            'status': 'healthy' if self.running and self.service_running else 'inactive',
            'timestamp': '2025-07-18T18:40:00Z',
            'metrics': {
                'uptime': getattr(self, 'uptime', 0),
                'requests_handled': getattr(self, 'requests_handled', 0),
                'service_running': self.service_running,
                'last_activity': getattr(self, 'last_activity', time.time())
            },
            'last_error': self.last_error,
            'initialized': self.initialized,
            'running': self.running,
            'service_status': self.get_service_status()
        }

# Plugin entry point
if __name__ == "__main__":
    plugin = ExampleServicePlugin()
    print(f"Plugin: {plugin.get_info().name}")
    print(f"Version: {plugin.get_info().version}")
    print(f"Category: {plugin.get_info().category}")
    print("Plugin ready for testing!")
