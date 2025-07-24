#!/usr/bin/env python3
"""
Prometheus Metrics Integration - Audit 3 Phase 2
===============================================

This system provides Prometheus-compatible metrics collection:
- Server performance metrics
- Plugin execution metrics
- Resource usage monitoring
- Custom metrics registration
- HTTP metrics endpoint

Essential for production monitoring and observability
"""

import os
import time
import logging
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict, deque
import json
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricType:
    """Metric type constants"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

@dataclass
class Metric:
    """Metric data structure"""
    name: str
    type: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    help: str = ""
    timestamp: float = field(default_factory=time.time)
    
    def to_prometheus_format(self) -> str:
        """Convert to Prometheus exposition format"""
        lines = []
        
        # Add HELP line
        if self.help:
            lines.append(f"# HELP {self.name} {self.help}")
        
        # Add TYPE line
        lines.append(f"# TYPE {self.name} {self.type}")
        
        # Add metric line
        if self.labels:
            label_str = ",".join([f'{k}="{v}"' for k, v in self.labels.items()])
            lines.append(f"{self.name}{{{label_str}}} {self.value}")
        else:
            lines.append(f"{self.name} {self.value}")
        
        return "\n".join(lines)

class MetricsCollector:
    """
    Prometheus-compatible metrics collector
    """
    
    def __init__(self):
        self.metrics: Dict[str, Metric] = {}
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.summaries: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.lock = threading.Lock()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize default metrics
        self._init_default_metrics()
    
    def _init_default_metrics(self):
        """Initialize default system metrics"""
        # Server metrics
        self.register_counter("heimnetz_server_requests_total", "Total number of server requests")
        self.register_histogram("heimnetz_server_request_duration_seconds", "Server request duration in seconds")
        self.register_gauge("heimnetz_server_active_connections", "Number of active connections")
        self.register_gauge("heimnetz_server_memory_usage_bytes", "Server memory usage in bytes")
        self.register_gauge("heimnetz_server_cpu_usage_percent", "Server CPU usage percentage")
        
        # Plugin metrics
        self.register_counter("heimnetz_plugin_executions_total", "Total number of plugin executions")
        self.register_histogram("heimnetz_plugin_execution_duration_seconds", "Plugin execution duration in seconds")
        self.register_gauge("heimnetz_plugin_memory_usage_bytes", "Plugin memory usage in bytes")
        self.register_counter("heimnetz_plugin_errors_total", "Total number of plugin errors")
        self.register_gauge("heimnetz_plugin_active_count", "Number of active plugins")
        
        # System metrics
        self.register_gauge("heimnetz_system_load_average", "System load average")
        self.register_gauge("heimnetz_system_disk_usage_percent", "System disk usage percentage")
        self.register_gauge("heimnetz_system_network_bytes_sent", "Network bytes sent")
        self.register_gauge("heimnetz_system_network_bytes_received", "Network bytes received")
    
    def register_counter(self, name: str, help: str = "") -> None:
        """Register a counter metric"""
        with self.lock:
            self.metrics[name] = Metric(name, MetricType.COUNTER, 0.0, help=help)
            self.counters[name] = 0.0
    
    def register_gauge(self, name: str, help: str = "") -> None:
        """Register a gauge metric"""
        with self.lock:
            self.metrics[name] = Metric(name, MetricType.GAUGE, 0.0, help=help)
            self.gauges[name] = 0.0
    
    def register_histogram(self, name: str, help: str = "") -> None:
        """Register a histogram metric"""
        with self.lock:
            self.metrics[name] = Metric(name, MetricType.HISTOGRAM, 0.0, help=help)
            self.histograms[name] = []
    
    def register_summary(self, name: str, help: str = "") -> None:
        """Register a summary metric"""
        with self.lock:
            self.metrics[name] = Metric(name, MetricType.SUMMARY, 0.0, help=help)
            self.summaries[name] = deque(maxlen=1000)
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None) -> None:
        """Increment a counter metric"""
        with self.lock:
            if name in self.counters:
                self.counters[name] += value
                self.metrics[name].value = self.counters[name]
                self.metrics[name].labels = labels or {}
                self.metrics[name].timestamp = time.time()
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Set a gauge metric value"""
        with self.lock:
            if name in self.gauges:
                self.gauges[name] = value
                self.metrics[name].value = value
                self.metrics[name].labels = labels or {}
                self.metrics[name].timestamp = time.time()
    
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Observe a value in a histogram metric"""
        with self.lock:
            if name in self.histograms:
                self.histograms[name].append(value)
                # Update metric with count and sum
                values = self.histograms[name]
                self.metrics[name].value = len(values)
                self.metrics[name].labels = labels or {}
                self.metrics[name].timestamp = time.time()
    
    def observe_summary(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Observe a value in a summary metric"""
        with self.lock:
            if name in self.summaries:
                self.summaries[name].append(value)
                # Update metric with count and sum
                values = list(self.summaries[name])
                self.metrics[name].value = sum(values) / len(values) if values else 0
                self.metrics[name].labels = labels or {}
                self.metrics[name].timestamp = time.time()
    
    def get_metric(self, name: str) -> Optional[Metric]:
        """Get a specific metric"""
        with self.lock:
            return self.metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, Metric]:
        """Get all metrics"""
        with self.lock:
            return dict(self.metrics)
    
    def get_prometheus_format(self) -> str:
        """Get all metrics in Prometheus exposition format"""
        with self.lock:
            lines = []
            for metric in self.metrics.values():
                lines.append(metric.to_prometheus_format())
                lines.append("")  # Empty line between metrics
            return "\n".join(lines)
    
    def collect_system_metrics(self) -> None:
        """Collect system performance metrics"""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=None)
            self.set_gauge("heimnetz_server_cpu_usage_percent", cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.set_gauge("heimnetz_server_memory_usage_bytes", memory.used)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.set_gauge("heimnetz_system_disk_usage_percent", disk_percent)
            
            # Network I/O
            net_io = psutil.net_io_counters()
            self.set_gauge("heimnetz_system_network_bytes_sent", net_io.bytes_sent)
            self.set_gauge("heimnetz_system_network_bytes_received", net_io.bytes_recv)
            
            # Load average (Unix-like systems)
            try:
                load_avg = psutil.getloadavg()
                self.set_gauge("heimnetz_system_load_average", load_avg[0])
            except (AttributeError, OSError):
                # Windows doesn't have load average
                pass
                
        except ImportError:
            self.logger.warning("psutil not available for system metrics collection")
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
    
    def start_background_collection(self, interval: int = 30) -> None:
        """Start background metrics collection"""
        def collect_loop():
            while True:
                try:
                    self.collect_system_metrics()
                    time.sleep(interval)
                except Exception as e:
                    self.logger.error(f"Background metrics collection error: {e}")
                    time.sleep(interval)
        
        thread = threading.Thread(target=collect_loop, daemon=True)
        thread.start()
        self.logger.info(f"Started background metrics collection (interval: {interval}s)")

class PerformanceMonitor:
    """
    Performance monitoring system
    """
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Performance thresholds
        self.thresholds = {
            "max_response_time": 0.1,  # 100ms
            "max_memory_usage": 50 * 1024 * 1024,  # 50MB
            "max_cpu_usage": 80.0,  # 80%
            "max_error_rate": 0.05  # 5%
        }
        
        # Performance history
        self.response_times = deque(maxlen=1000)
        self.memory_usage = deque(maxlen=1000)
        self.cpu_usage = deque(maxlen=1000)
        self.error_counts = deque(maxlen=1000)
        
        # Alerts
        self.alert_callbacks: List[Callable] = []
    
    def track_request(self, duration: float, success: bool = True) -> None:
        """Track a request performance"""
        # Record metrics
        self.metrics.increment_counter("heimnetz_server_requests_total")
        self.metrics.observe_histogram("heimnetz_server_request_duration_seconds", duration)
        
        # Update history
        self.response_times.append(duration)
        
        # Check thresholds
        if duration > self.thresholds["max_response_time"]:
            self._trigger_alert("SLOW_REQUEST", {
                "duration": duration,
                "threshold": self.thresholds["max_response_time"]
            })
        
        if not success:
            self.metrics.increment_counter("heimnetz_plugin_errors_total")
            self.error_counts.append(1)
        else:
            self.error_counts.append(0)
    
    def track_plugin_execution(self, plugin_name: str, duration: float, 
                             memory_used: int, success: bool = True) -> None:
        """Track plugin execution performance"""
        labels = {"plugin": plugin_name}
        
        # Record metrics
        self.metrics.increment_counter("heimnetz_plugin_executions_total", labels=labels)
        self.metrics.observe_histogram("heimnetz_plugin_execution_duration_seconds", duration, labels=labels)
        self.metrics.set_gauge("heimnetz_plugin_memory_usage_bytes", memory_used, labels=labels)
        
        if not success:
            self.metrics.increment_counter("heimnetz_plugin_errors_total", labels=labels)
        
        # Check thresholds
        if duration > self.thresholds["max_response_time"]:
            self._trigger_alert("SLOW_PLUGIN", {
                "plugin": plugin_name,
                "duration": duration,
                "threshold": self.thresholds["max_response_time"]
            })
        
        if memory_used > self.thresholds["max_memory_usage"]:
            self._trigger_alert("HIGH_MEMORY", {
                "plugin": plugin_name,
                "memory_used": memory_used,
                "threshold": self.thresholds["max_memory_usage"]
            })
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics"""
        summary = {}
        
        # Response times
        if self.response_times:
            times = list(self.response_times)
            summary["response_times"] = {
                "avg": sum(times) / len(times),
                "min": min(times),
                "max": max(times),
                "p95": sorted(times)[int(len(times) * 0.95)] if len(times) > 0 else 0,
                "p99": sorted(times)[int(len(times) * 0.99)] if len(times) > 0 else 0
            }
        
        # Error rate
        if self.error_counts:
            errors = list(self.error_counts)
            summary["error_rate"] = sum(errors) / len(errors) if errors else 0
        
        # Memory usage
        if self.memory_usage:
            memory = list(self.memory_usage)
            summary["memory_usage"] = {
                "avg": sum(memory) / len(memory),
                "min": min(memory),
                "max": max(memory)
            }
        
        # CPU usage
        if self.cpu_usage:
            cpu = list(self.cpu_usage)
            summary["cpu_usage"] = {
                "avg": sum(cpu) / len(cpu),
                "min": min(cpu),
                "max": max(cpu)
            }
        
        return summary
    
    def add_alert_callback(self, callback: Callable) -> None:
        """Add an alert callback function"""
        self.alert_callbacks.append(callback)
    
    def _trigger_alert(self, alert_type: str, data: Dict[str, Any]) -> None:
        """Trigger performance alert"""
        alert = {
            "type": alert_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        self.logger.warning(f"Performance alert: {alert_type} - {data}")
        
        # Call registered callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")

class StressTestSuite:
    """
    Stress testing suite for performance validation
    """
    
    def __init__(self, metrics_collector: MetricsCollector, performance_monitor: PerformanceMonitor):
        self.metrics = metrics_collector
        self.performance = performance_monitor
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Test results
        self.test_results = {}
    
    def run_load_test(self, target_function: Callable, concurrent_requests: int = 100, 
                     duration: int = 60) -> Dict[str, Any]:
        """Run load test on target function"""
        import concurrent.futures
        import time
        
        self.logger.info(f"Starting load test: {concurrent_requests} concurrent requests for {duration}s")
        
        start_time = time.time()
        end_time = start_time + duration
        
        results = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "errors": []
        }
        
        def execute_request():
            request_start = time.time()
            try:
                target_function()
                request_end = time.time()
                duration = request_end - request_start
                results["response_times"].append(duration)
                results["successful_requests"] += 1
                return True
            except Exception as e:
                results["errors"].append(str(e))
                results["failed_requests"] += 1
                return False
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = []
            
            while time.time() < end_time:
                if len(futures) < concurrent_requests:
                    future = executor.submit(execute_request)
                    futures.append(future)
                    results["total_requests"] += 1
                
                # Clean up completed futures
                futures = [f for f in futures if not f.done()]
                
                time.sleep(0.01)  # Small delay to prevent overwhelming
            
            # Wait for remaining requests
            concurrent.futures.wait(futures)
        
        # Calculate statistics
        if results["response_times"]:
            times = results["response_times"]
            results["avg_response_time"] = sum(times) / len(times)
            results["min_response_time"] = min(times)
            results["max_response_time"] = max(times)
            results["p95_response_time"] = sorted(times)[int(len(times) * 0.95)]
            results["p99_response_time"] = sorted(times)[int(len(times) * 0.99)]
        
        results["success_rate"] = results["successful_requests"] / results["total_requests"] if results["total_requests"] > 0 else 0
        results["requests_per_second"] = results["total_requests"] / duration
        
        self.test_results["load_test"] = results
        self.logger.info(f"Load test completed: {results['success_rate']:.2%} success rate, {results['requests_per_second']:.2f} RPS")
        
        return results
    
    def run_memory_stress_test(self, target_function: Callable, 
                              max_memory_mb: int = 100) -> Dict[str, Any]:
        """Run memory stress test"""
        import psutil
        import gc
        
        self.logger.info(f"Starting memory stress test (max: {max_memory_mb}MB)")
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        results = {
            "initial_memory": initial_memory,
            "peak_memory": initial_memory,
            "final_memory": initial_memory,
            "memory_leak_detected": False,
            "executions": 0
        }
        
        # Run multiple executions
        for i in range(1000):
            try:
                target_function()
                results["executions"] += 1
                
                # Check memory usage
                current_memory = process.memory_info().rss
                if current_memory > results["peak_memory"]:
                    results["peak_memory"] = current_memory
                
                # Check if memory limit exceeded
                if current_memory > max_memory_mb * 1024 * 1024:
                    self.logger.warning(f"Memory limit exceeded: {current_memory / 1024 / 1024:.2f}MB")
                    break
                
                # Force garbage collection every 100 executions
                if i % 100 == 0:
                    gc.collect()
                    
            except Exception as e:
                self.logger.error(f"Memory stress test error: {e}")
                break
        
        # Final memory check
        gc.collect()
        time.sleep(1)  # Allow cleanup
        results["final_memory"] = process.memory_info().rss
        
        # Check for memory leaks
        memory_increase = results["final_memory"] - results["initial_memory"]
        if memory_increase > 10 * 1024 * 1024:  # 10MB threshold
            results["memory_leak_detected"] = True
            self.logger.warning(f"Potential memory leak detected: {memory_increase / 1024 / 1024:.2f}MB increase")
        
        self.test_results["memory_stress"] = results
        self.logger.info(f"Memory stress test completed: {results['executions']} executions, peak: {results['peak_memory'] / 1024 / 1024:.2f}MB")
        
        return results
    
    def run_cpu_stress_test(self, target_function: Callable, 
                           duration: int = 30) -> Dict[str, Any]:
        """Run CPU stress test"""
        import psutil
        
        self.logger.info(f"Starting CPU stress test for {duration}s")
        
        process = psutil.Process()
        start_time = time.time()
        end_time = start_time + duration
        
        results = {
            "duration": duration,
            "executions": 0,
            "cpu_usage_samples": [],
            "avg_cpu_usage": 0.0,
            "peak_cpu_usage": 0.0
        }
        
        # Background CPU monitoring
        def monitor_cpu():
            while time.time() < end_time:
                try:
                    cpu_percent = process.cpu_percent()
                    results["cpu_usage_samples"].append(cpu_percent)
                    if cpu_percent > results["peak_cpu_usage"]:
                        results["peak_cpu_usage"] = cpu_percent
                    time.sleep(0.1)
                except Exception:
                    pass
        
        cpu_thread = threading.Thread(target=monitor_cpu, daemon=True)
        cpu_thread.start()
        
        # Execute target function repeatedly
        while time.time() < end_time:
            try:
                target_function()
                results["executions"] += 1
            except Exception as e:
                self.logger.error(f"CPU stress test error: {e}")
                break
        
        # Calculate average CPU usage
        if results["cpu_usage_samples"]:
            results["avg_cpu_usage"] = sum(results["cpu_usage_samples"]) / len(results["cpu_usage_samples"])
        
        self.test_results["cpu_stress"] = results
        self.logger.info(f"CPU stress test completed: {results['executions']} executions, avg CPU: {results['avg_cpu_usage']:.2f}%")
        
        return results
    
    def generate_stress_test_report(self) -> str:
        """Generate comprehensive stress test report"""
        report = []
        report.append("# STRESS TEST REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")
        
        for test_name, results in self.test_results.items():
            report.append(f"## {test_name.upper()}")
            report.append("-" * 30)
            
            for key, value in results.items():
                if isinstance(value, float):
                    report.append(f"{key}: {value:.4f}")
                elif isinstance(value, list):
                    report.append(f"{key}: {len(value)} items")
                else:
                    report.append(f"{key}: {value}")
            
            report.append("")
        
        return "\n".join(report)

def main():
    """Main function for testing the monitoring system"""
    try:
        # Initialize metrics collector
        metrics = MetricsCollector()
        
        # Initialize performance monitor
        performance = PerformanceMonitor(metrics)
        
        # Initialize stress test suite
        stress_tester = StressTestSuite(metrics, performance)
        
        # Start background metrics collection
        metrics.start_background_collection()
        
        # Simulate some operations
        print("Testing metrics collection...")
        
        # Simulate server requests
        for i in range(10):
            start_time = time.time()
            time.sleep(0.05)  # Simulate request processing
            duration = time.time() - start_time
            performance.track_request(duration, success=True)
        
        # Simulate plugin executions
        for i in range(5):
            start_time = time.time()
            time.sleep(0.02)  # Simulate plugin execution
            duration = time.time() - start_time
            performance.track_plugin_execution("test_plugin", duration, 1024 * 1024)
        
        # Get performance summary
        summary = performance.get_performance_summary()
        print("Performance Summary:")
        print(json.dumps(summary, indent=2))
        
        # Get Prometheus metrics
        prometheus_output = metrics.get_prometheus_format()
        print("\nPrometheus Metrics:")
        print(prometheus_output[:500] + "..." if len(prometheus_output) > 500 else prometheus_output)
        
        # Run a simple stress test
        def dummy_function():
            time.sleep(0.001)
            return "test"
        
        print("\nRunning stress test...")
        load_results = stress_tester.run_load_test(dummy_function, concurrent_requests=10, duration=5)
        print(f"Load test results: {load_results['success_rate']:.2%} success rate")
        
        # Generate report
        report = stress_tester.generate_stress_test_report()
        print("\nStress Test Report:")
        print(report)
        
    except Exception as e:
        print(f"Error testing monitoring system: {e}")
        logger.error(f"Monitoring system test error: {e}")

if __name__ == "__main__":
    main()
