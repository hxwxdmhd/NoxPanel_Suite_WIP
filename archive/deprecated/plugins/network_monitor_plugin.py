#!/usr/bin/env python3
"""
Example Plugin - Network Monitor
================================

This is a demonstration plugin showing enhanced features.
"""

import time
import random
from typing import Dict, Any, List
from unified_plugin_system_clean import ServicePlugin, PluginInfo

class NetworkMonitorPlugin(ServicePlugin):
    """Example network monitoring service plugin"""
    
    def __init__(self):
        super().__init__()
        self.monitoring_active = False
        self.network_stats = {
            'bytes_sent': 0,
            'bytes_received': 0,
            'connections': 0,
            'latency_ms': 0
        }
        self.dependencies = []
    
    def get_info(self) -> PluginInfo:
        """Get plugin information"""
        return PluginInfo(
            name="NetworkMonitorPlugin",
            version="1.2.0",
            description="Network monitoring service with real-time metrics",
            author="Enhanced Plugin System",
            category="monitoring",
            dependencies=[],
            permissions=["network.monitor", "system.read"]
        )
    
    def start_service(self) -> bool:
        """Start the network monitoring service"""
        try:
            self.monitoring_active = True
            self.logger.info("Network monitoring service started")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start network monitoring: {e}")
            return False
    
    def stop_service(self) -> bool:
        """Stop the network monitoring service"""
        try:
            self.monitoring_active = False
            self.logger.info("Network monitoring service stopped")
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop network monitoring: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            'active': self.monitoring_active,
            'stats': self.network_stats,
            'uptime': time.time() - getattr(self, '_start_time', time.time())
        }
    
    def get_network_metrics(self) -> Dict[str, Any]:
        """Get current network metrics (simulated)"""
        if self.monitoring_active:
            # Simulate network metrics
            self.network_stats.update({
                'bytes_sent': random.randint(1000, 10000),
                'bytes_received': random.randint(5000, 50000),
                'connections': random.randint(10, 100),
                'latency_ms': random.randint(10, 200)
            })
        
        return self.network_stats
    
    def get_health(self) -> Dict[str, Any]:
        """Get plugin health status"""
        health = super().get_health()
        
        # Add network-specific health metrics
        health['metrics'].update({
            'monitoring_active': self.monitoring_active,
            'network_stats': self.network_stats,
            'service_type': 'network_monitor'
        })
        
        return health

# Make plugin discoverable
__plugin_class__ = NetworkMonitorPlugin
