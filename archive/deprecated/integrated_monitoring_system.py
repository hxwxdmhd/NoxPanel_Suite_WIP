#!/usr/bin/env python3
"""
Integrated Monitoring System - Audit 3 Phase 2 Complete
======================================================

This system integrates all monitoring components:
- Prometheus metrics collection
- Performance monitoring
- Memory leak detection
- Stress testing
- Real-time dashboard
- Automated alerting

Production-ready monitoring for the Heimnetz plugin ecosystem
"""

import os
import sys
import time
import logging
import threading
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import traceback

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import monitoring components
try:
    from prometheus_metrics_system import MetricsCollector, PerformanceMonitor, StressTestSuite
    from memory_leak_detector import MemoryLeakDetector, MemoryLeak
except ImportError as e:
    logging.error(f"Failed to import monitoring components: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MonitoringConfig:
    """Configuration for the monitoring system"""
    metrics_enabled: bool = True
    performance_monitoring: bool = True
    memory_leak_detection: bool = True
    stress_testing: bool = False
    
    # Metrics collection
    metrics_interval: int = 30
    metrics_retention: int = 3600  # 1 hour
    
    # Performance monitoring
    performance_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "max_response_time": 0.1,  # 100ms
        "max_memory_usage": 50 * 1024 * 1024,  # 50MB
        "max_cpu_usage": 80.0,  # 80%
        "max_error_rate": 0.05  # 5%
    })
    
    # Memory leak detection
    memory_check_interval: int = 60
    memory_history_size: int = 100
    
    # Alerting
    alert_webhooks: List[str] = field(default_factory=list)
    alert_email: Optional[str] = None
    
    # Dashboard
    dashboard_enabled: bool = True
    dashboard_port: int = 8080

class MonitoringDashboard:
    """
    Real-time monitoring dashboard
    """
    
    def __init__(self, monitoring_system: 'IntegratedMonitoringSystem'):
        self.monitoring_system = monitoring_system
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.dashboard_data = {}
        self.update_interval = 5  # 5 seconds
        self.dashboard_thread = None
        self.running = False
    
    def start(self) -> None:
        """Start the dashboard update loop"""
        if self.running:
            return
        
        self.running = True
        self.dashboard_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.dashboard_thread.start()
        self.logger.info("Monitoring dashboard started")
    
    def stop(self) -> None:
        """Stop the dashboard"""
        self.running = False
        if self.dashboard_thread:
            self.dashboard_thread.join(timeout=5)
        self.logger.info("Monitoring dashboard stopped")
    
    def _update_loop(self) -> None:
        """Main dashboard update loop"""
        while self.running:
            try:
                self._update_dashboard_data()
                time.sleep(self.update_interval)
            except Exception as e:
                self.logger.error(f"Dashboard update error: {e}")
                time.sleep(self.update_interval)
    
    def _update_dashboard_data(self) -> None:
        """Update dashboard data"""
        try:
            self.dashboard_data = {
                "timestamp": datetime.now().isoformat(),
                "system_status": self._get_system_status(),
                "metrics": self._get_metrics_summary(),
                "performance": self._get_performance_summary(),
                "memory": self._get_memory_summary(),
                "alerts": self._get_recent_alerts(),
                "plugins": self._get_plugin_status()
            }
        except Exception as e:
            self.logger.error(f"Failed to update dashboard data: {e}")
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        try:
            # Get component statuses
            metrics_status = "HEALTHY" if self.monitoring_system.metrics_collector else "DISABLED"
            performance_status = "HEALTHY" if self.monitoring_system.performance_monitor else "DISABLED"
            memory_status = "HEALTHY" if self.monitoring_system.memory_detector else "DISABLED"
            
            # Check for critical issues
            recent_alerts = self.monitoring_system.get_recent_alerts(minutes=5)
            critical_alerts = [a for a in recent_alerts if a.get("severity") == "CRITICAL"]
            
            overall_status = "CRITICAL" if critical_alerts else "HEALTHY"
            
            return {
                "overall": overall_status,
                "components": {
                    "metrics": metrics_status,
                    "performance": performance_status,
                    "memory": memory_status
                },
                "critical_alerts": len(critical_alerts),
                "uptime": self.monitoring_system.get_uptime()
            }
        except Exception as e:
            self.logger.error(f"Failed to get system status: {e}")
            return {"overall": "ERROR", "error": str(e)}
    
    def _get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        try:
            if not self.monitoring_system.metrics_collector:
                return {"status": "DISABLED"}
            
            metrics = self.monitoring_system.metrics_collector.get_all_metrics()
            return {
                "total_metrics": len(metrics),
                "server_requests": metrics.get("heimnetz_server_requests_total", {}).get("value", 0),
                "plugin_executions": metrics.get("heimnetz_plugin_executions_total", {}).get("value", 0),
                "active_connections": metrics.get("heimnetz_server_active_connections", {}).get("value", 0),
                "memory_usage": metrics.get("heimnetz_server_memory_usage_bytes", {}).get("value", 0)
            }
        except Exception as e:
            self.logger.error(f"Failed to get metrics summary: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        try:
            if not self.monitoring_system.performance_monitor:
                return {"status": "DISABLED"}
            
            return self.monitoring_system.performance_monitor.get_performance_summary()
        except Exception as e:
            self.logger.error(f"Failed to get performance summary: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    def _get_memory_summary(self) -> Dict[str, Any]:
        """Get memory summary"""
        try:
            if not self.monitoring_system.memory_detector:
                return {"status": "DISABLED"}
            
            return self.monitoring_system.memory_detector.get_memory_statistics()
        except Exception as e:
            self.logger.error(f"Failed to get memory summary: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    def _get_recent_alerts(self) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        try:
            return self.monitoring_system.get_recent_alerts(minutes=60)
        except Exception as e:
            self.logger.error(f"Failed to get recent alerts: {e}")
            return []
    
    def _get_plugin_status(self) -> Dict[str, Any]:
        """Get plugin status summary"""
        try:
            # This would integrate with the plugin system
            return {
                "active_plugins": 0,
                "healthy_plugins": 0,
                "error_plugins": 0
            }
        except Exception as e:
            self.logger.error(f"Failed to get plugin status: {e}")
            return {"status": "ERROR", "error": str(e)}
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data"""
        return self.dashboard_data.copy()

class AlertManager:
    """
    Alert management system
    """
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.alert_history = []
        self.alert_callbacks = []
        self.alert_counts = defaultdict(int)
        self.last_alert_time = {}
        
        # Alert thresholds
        self.alert_cooldown = 300  # 5 minutes
    
    def add_alert_callback(self, callback: Callable) -> None:
        """Add alert callback"""
        self.alert_callbacks.append(callback)
    
    def send_alert(self, alert_type: str, severity: str, message: str, 
                   data: Dict[str, Any] = None) -> None:
        """Send an alert"""
        alert = {
            "type": alert_type,
            "severity": severity,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
            "count": self.alert_counts[alert_type] + 1
        }
        
        # Check cooldown
        last_alert = self.last_alert_time.get(alert_type, 0)
        if time.time() - last_alert < self.alert_cooldown:
            self.logger.debug(f"Alert {alert_type} in cooldown period")
            return
        
        # Update counters
        self.alert_counts[alert_type] += 1
        self.last_alert_time[alert_type] = time.time()
        
        # Store alert
        self.alert_history.append(alert)
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
        
        # Log alert
        self.logger.warning(f"ALERT [{severity}] {alert_type}: {message}")
        
        # Send to callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")
        
        # Send to external systems
        self._send_external_alert(alert)
    
    def _send_external_alert(self, alert: Dict[str, Any]) -> None:
        """Send alert to external systems"""
        try:
            # Webhook notifications
            for webhook_url in self.config.alert_webhooks:
                self._send_webhook_alert(webhook_url, alert)
            
            # Email notifications
            if self.config.alert_email:
                self._send_email_alert(self.config.alert_email, alert)
                
        except Exception as e:
            self.logger.error(f"Failed to send external alert: {e}")
    
    def _send_webhook_alert(self, webhook_url: str, alert: Dict[str, Any]) -> None:
        """Send webhook alert"""
        try:
            import requests
            response = requests.post(webhook_url, json=alert, timeout=10)
            response.raise_for_status()
            self.logger.info(f"Webhook alert sent to {webhook_url}")
        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}")
    
    def _send_email_alert(self, email: str, alert: Dict[str, Any]) -> None:
        """Send email alert"""
        try:
            # Email implementation would go here
            self.logger.info(f"Email alert would be sent to {email}")
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
    
    def get_recent_alerts(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert["timestamp"]) > cutoff_time
        ]

class IntegratedMonitoringSystem:
    """
    Main integrated monitoring system
    """
    
    def __init__(self, config: MonitoringConfig = None):
        self.config = config or MonitoringConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.start_time = datetime.now()
        
        # Initialize components
        self.metrics_collector = None
        self.performance_monitor = None
        self.memory_detector = None
        self.stress_tester = None
        self.dashboard = None
        self.alert_manager = AlertManager(self.config)
        
        # System state
        self.running = False
        self.monitoring_threads = []
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """Initialize monitoring components"""
        try:
            # Initialize metrics collector
            if self.config.metrics_enabled:
                self.metrics_collector = MetricsCollector()
                self.logger.info("Metrics collector initialized")
            
            # Initialize performance monitor
            if self.config.performance_monitoring:
                self.performance_monitor = PerformanceMonitor(
                    self.metrics_collector if self.metrics_collector else None
                )
                self.logger.info("Performance monitor initialized")
            
            # Initialize memory leak detector
            if self.config.memory_leak_detection:
                self.memory_detector = MemoryLeakDetector(
                    check_interval=self.config.memory_check_interval,
                    history_size=self.config.memory_history_size
                )
                # Add leak callback
                self.memory_detector.add_leak_callback(self._handle_memory_leak)
                self.logger.info("Memory leak detector initialized")
            
            # Initialize stress tester
            if self.config.stress_testing:
                self.stress_tester = StressTestSuite(
                    self.metrics_collector,
                    self.performance_monitor
                )
                self.logger.info("Stress tester initialized")
            
            # Initialize dashboard
            if self.config.dashboard_enabled:
                self.dashboard = MonitoringDashboard(self)
                self.logger.info("Monitoring dashboard initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize monitoring components: {e}")
            raise
    
    def start(self) -> None:
        """Start the monitoring system"""
        if self.running:
            self.logger.warning("Monitoring system already running")
            return
        
        self.running = True
        
        try:
            # Start metrics collection
            if self.metrics_collector:
                self.metrics_collector.start_background_collection(
                    interval=self.config.metrics_interval
                )
            
            # Start memory leak detection
            if self.memory_detector:
                self.memory_detector.start_monitoring()
            
            # Start dashboard
            if self.dashboard:
                self.dashboard.start()
            
            # Add performance monitor callbacks
            if self.performance_monitor:
                self.performance_monitor.add_alert_callback(self._handle_performance_alert)
            
            self.logger.info("Integrated monitoring system started")
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring system: {e}")
            self.running = False
            raise
    
    def stop(self) -> None:
        """Stop the monitoring system"""
        if not self.running:
            return
        
        self.running = False
        
        try:
            # Stop memory leak detection
            if self.memory_detector:
                self.memory_detector.stop_monitoring()
            
            # Stop dashboard
            if self.dashboard:
                self.dashboard.stop()
            
            # Wait for threads to finish
            for thread in self.monitoring_threads:
                thread.join(timeout=5)
            
            self.logger.info("Integrated monitoring system stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping monitoring system: {e}")
    
    def _handle_memory_leak(self, leak: MemoryLeak) -> None:
        """Handle memory leak detection"""
        self.alert_manager.send_alert(
            alert_type="MEMORY_LEAK",
            severity=leak.severity,
            message=f"Memory leak detected in {leak.plugin_name}: {leak.leak_type}",
            data=leak.to_dict()
        )
    
    def _handle_performance_alert(self, alert: Dict[str, Any]) -> None:
        """Handle performance alert"""
        self.alert_manager.send_alert(
            alert_type="PERFORMANCE",
            severity="HIGH",
            message=f"Performance issue: {alert['type']}",
            data=alert
        )
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            "running": self.running,
            "uptime": self.get_uptime(),
            "components": {
                "metrics_collector": self.metrics_collector is not None,
                "performance_monitor": self.performance_monitor is not None,
                "memory_detector": self.memory_detector is not None,
                "stress_tester": self.stress_tester is not None,
                "dashboard": self.dashboard is not None
            },
            "alerts": {
                "recent_count": len(self.alert_manager.get_recent_alerts(minutes=60)),
                "critical_count": len([
                    a for a in self.alert_manager.get_recent_alerts(minutes=60)
                    if a.get("severity") == "CRITICAL"
                ])
            }
        }
        
        # Add component-specific status
        if self.metrics_collector:
            status["metrics"] = len(self.metrics_collector.get_all_metrics())
        
        if self.performance_monitor:
            status["performance"] = self.performance_monitor.get_performance_summary()
        
        if self.memory_detector:
            status["memory"] = self.memory_detector.get_memory_statistics()
        
        return status
    
    def get_uptime(self) -> float:
        """Get system uptime in seconds"""
        return (datetime.now() - self.start_time).total_seconds()
    
    def get_recent_alerts(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        return self.alert_manager.get_recent_alerts(minutes)
    
    def force_health_check(self) -> Dict[str, Any]:
        """Force a comprehensive health check"""
        health_check = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "HEALTHY",
            "components": {},
            "issues": []
        }
        
        try:
            # Check metrics collector
            if self.metrics_collector:
                metrics = self.metrics_collector.get_all_metrics()
                health_check["components"]["metrics"] = {
                    "status": "HEALTHY",
                    "metric_count": len(metrics)
                }
            
            # Check performance monitor
            if self.performance_monitor:
                performance = self.performance_monitor.get_performance_summary()
                health_check["components"]["performance"] = {
                    "status": "HEALTHY",
                    "summary": performance
                }
            
            # Check memory detector
            if self.memory_detector:
                memory_stats = self.memory_detector.get_memory_statistics()
                health_check["components"]["memory"] = {
                    "status": "HEALTHY",
                    "statistics": memory_stats
                }
                
                # Check for memory leaks
                if memory_stats.get("detected_leaks", 0) > 0:
                    health_check["issues"].append("Memory leaks detected")
                    if memory_stats.get("leak_by_severity", {}).get("CRITICAL", 0) > 0:
                        health_check["overall_status"] = "CRITICAL"
            
            # Check for critical alerts
            recent_alerts = self.get_recent_alerts(minutes=5)
            critical_alerts = [a for a in recent_alerts if a.get("severity") == "CRITICAL"]
            if critical_alerts:
                health_check["issues"].append(f"{len(critical_alerts)} critical alerts")
                health_check["overall_status"] = "CRITICAL"
            
        except Exception as e:
            health_check["overall_status"] = "ERROR"
            health_check["issues"].append(f"Health check error: {str(e)}")
            self.logger.error(f"Health check error: {e}")
        
        return health_check
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus-formatted metrics"""
        if not self.metrics_collector:
            return "# Metrics collector not available\n"
        
        return self.metrics_collector.get_prometheus_format()

def main():
    """Main function for testing the integrated monitoring system"""
    try:
        # Create configuration
        config = MonitoringConfig(
            metrics_enabled=True,
            performance_monitoring=True,
            memory_leak_detection=True,
            stress_testing=True,
            dashboard_enabled=True
        )
        
        # Initialize monitoring system
        monitoring = IntegratedMonitoringSystem(config)
        
        # Add alert callback
        def alert_callback(alert):
            print(f"ALERT: {alert['type']} - {alert['severity']} - {alert['message']}")
        
        monitoring.alert_manager.add_alert_callback(alert_callback)
        
        # Start monitoring
        monitoring.start()
        
        print("Integrated monitoring system started. Running tests...")
        
        # Simulate some activity
        for i in range(5):
            # Simulate request
            monitoring.performance_monitor.track_request(0.05, success=True)
            
            # Simulate plugin execution
            monitoring.performance_monitor.track_plugin_execution(
                "test_plugin", 0.02, 1024 * 1024, success=True
            )
            
            time.sleep(2)
        
        # Get system status
        status = monitoring.get_system_status()
        print("\nSystem Status:")
        print(json.dumps(status, indent=2))
        
        # Force health check
        health = monitoring.force_health_check()
        print("\nHealth Check:")
        print(json.dumps(health, indent=2))
        
        # Get Prometheus metrics
        metrics = monitoring.get_prometheus_metrics()
        print("\nPrometheus Metrics (sample):")
        print(metrics[:500] + "..." if len(metrics) > 500 else metrics)
        
        # Wait a bit for background monitoring
        time.sleep(10)
        
        # Stop monitoring
        monitoring.stop()
        
        print("\nIntegrated monitoring system test completed successfully!")
        
    except Exception as e:
        print(f"Error testing integrated monitoring system: {e}")
        logger.error(f"Integrated monitoring system test error: {e}")

if __name__ == "__main__":
    main()
