# Enhanced Plugin Sandbox Isolation - Monitoring Guide

This document provides comprehensive guidance for monitoring, telemetry, and observability of the Enhanced Plugin Sandbox Isolation system.

## Table of Contents

- [Monitoring Overview](#monitoring-overview)
- [Telemetry Collection](#telemetry-collection)
- [Real-time Monitoring](#real-time-monitoring)
- [Performance Metrics](#performance-metrics)
- [Health Checks](#health-checks)
- [Alerting and Notifications](#alerting-and-notifications)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Monitoring Overview

### Monitoring Architecture

The Enhanced Plugin Sandbox Isolation system provides multi-layered monitoring:

```
┌─────────────────────────────────────────────────────────────┐
│                 Application Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   Dashboard     │  │   Alerting      │                  │
│  └─────────────────┘  └─────────────────┘                  │
├─────────────────────────────────────────────────────────────┤
│                 Aggregation Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   Metrics       │  │   Logs          │                  │
│  └─────────────────┘  └─────────────────┘                  │
├─────────────────────────────────────────────────────────────┤
│                 Collection Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   Telemetry     │  │   Monitoring    │                  │
│  │   Collector     │  │   Agent         │                  │
│  └─────────────────┘  └─────────────────┘                  │
├─────────────────────────────────────────────────────────────┤
│                 Sandbox Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   Resource      │  │   Security      │                  │
│  │   Monitor       │  │   Monitor       │                  │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### Key Monitoring Dimensions

1. **Resource Utilization**: CPU, Memory, Disk, Network
2. **Security Events**: Violations, Threats, Anomalies
3. **Performance Metrics**: Execution time, Throughput, Latency
4. **Health Status**: System health, Component status
5. **Business Metrics**: Plugin success rates, User activity

## Telemetry Collection

### Core Telemetry Data

```python
import asyncio
import time
import psutil
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional

@dataclass
class ResourceSample:
    """Single resource measurement sample"""
    timestamp: float
    memory_mb: float
    cpu_percent: float
    disk_io_bytes: int = 0
    network_io_bytes: int = 0
    thread_count: int = 0
    file_descriptors: int = 0

@dataclass
class SandboxTelemetry:
    """Comprehensive telemetry data for sandbox execution"""
    sandbox_id: str
    start_time: float
    end_time: float = 0.0
    peak_memory_mb: float = 0.0
    peak_cpu_percent: float = 0.0
    avg_memory_mb: float = 0.0
    avg_cpu_percent: float = 0.0
    
    # Resource samples over time
    resource_samples: List[ResourceSample] = field(default_factory=list)
    
    # Operation counts
    file_operations_count: int = 0
    network_operations_count: int = 0
    system_calls_count: int = 0
    
    # Security metrics
    violations_count: int = 0
    security_events: List[Dict[str, Any]] = field(default_factory=list)
    
    # Performance metrics
    plugin_execution_time: float = 0.0
    sandbox_overhead_time: float = 0.0
    
    # Status flags
    cleanup_successful: bool = False
    terminated_by_timeout: bool = False
    terminated_by_violation: bool = False
    
    # Metadata
    plugin_metadata: Optional[Dict[str, Any]] = None
    environment_info: Dict[str, Any] = field(default_factory=dict)

class TelemetryCollector:
    """Collects telemetry data from sandbox executions"""
    
    def __init__(self, collection_interval: float = 0.5):
        self.collection_interval = collection_interval
        self.active_collections = {}
        self.historical_data = []
        self.max_history_size = 1000
    
    async def start_collection(self, sandbox_id: str, process_id: int) -> SandboxTelemetry:
        """Start telemetry collection for a sandbox execution"""
        
        telemetry = SandboxTelemetry(
            sandbox_id=sandbox_id,
            start_time=time.time()
        )
        
        self.active_collections[sandbox_id] = {
            'telemetry': telemetry,
            'process_id': process_id,
            'collection_task': asyncio.create_task(
                self._collect_metrics(sandbox_id, process_id)
            )
        }
        
        return telemetry
    
    async def stop_collection(self, sandbox_id: str) -> SandboxTelemetry:
        """Stop telemetry collection and finalize data"""
        
        if sandbox_id not in self.active_collections:
            raise ValueError(f"No active collection for sandbox {sandbox_id}")
        
        collection_info = self.active_collections[sandbox_id]
        telemetry = collection_info['telemetry']
        
        # Stop collection task
        collection_info['collection_task'].cancel()
        try:
            await collection_info['collection_task']
        except asyncio.CancelledError:
            pass
        
        # Finalize telemetry
        telemetry.end_time = time.time()
        self._calculate_aggregated_metrics(telemetry)
        
        # Store historical data
        self.historical_data.append(telemetry)
        if len(self.historical_data) > self.max_history_size:
            self.historical_data.pop(0)
        
        # Cleanup
        del self.active_collections[sandbox_id]
        
        return telemetry
    
    async def _collect_metrics(self, sandbox_id: str, process_id: int):
        """Continuously collect metrics for a sandbox execution"""
        
        try:
            process = psutil.Process(process_id)
            telemetry = self.active_collections[sandbox_id]['telemetry']
            
            while True:
                try:
                    # Collect current resource usage
                    memory_info = process.memory_info()
                    cpu_percent = process.cpu_percent()
                    io_counters = process.io_counters()
                    
                    sample = ResourceSample(
                        timestamp=time.time(),
                        memory_mb=memory_info.rss / 1024 / 1024,
                        cpu_percent=cpu_percent,
                        disk_io_bytes=io_counters.read_bytes + io_counters.write_bytes,
                        thread_count=process.num_threads(),
                        file_descriptors=process.num_fds() if hasattr(process, 'num_fds') else 0
                    )
                    
                    telemetry.resource_samples.append(sample)
                    
                    # Update peak values
                    telemetry.peak_memory_mb = max(telemetry.peak_memory_mb, sample.memory_mb)
                    telemetry.peak_cpu_percent = max(telemetry.peak_cpu_percent, sample.cpu_percent)
                    
                    await asyncio.sleep(self.collection_interval)
                    
                except psutil.NoSuchProcess:
                    # Process ended
                    break
                except Exception as e:
                    print(f"Error collecting metrics: {e}")
                    await asyncio.sleep(self.collection_interval)
                    
        except asyncio.CancelledError:
            pass
    
    def _calculate_aggregated_metrics(self, telemetry: SandboxTelemetry):
        """Calculate aggregated metrics from samples"""
        
        if not telemetry.resource_samples:
            return
        
        # Calculate averages
        total_memory = sum(sample.memory_mb for sample in telemetry.resource_samples)
        total_cpu = sum(sample.cpu_percent for sample in telemetry.resource_samples)
        sample_count = len(telemetry.resource_samples)
        
        telemetry.avg_memory_mb = total_memory / sample_count
        telemetry.avg_cpu_percent = total_cpu / sample_count
        
        # Calculate execution times
        if telemetry.end_time > telemetry.start_time:
            total_time = telemetry.end_time - telemetry.start_time
            telemetry.sandbox_overhead_time = max(0, total_time - telemetry.plugin_execution_time)
    
    def get_historical_data(self, limit: int = 100) -> List[SandboxTelemetry]:
        """Get historical telemetry data"""
        return self.historical_data[-limit:]
```

### Custom Metrics Collection

```python
class CustomMetricsCollector:
    """Collect custom application-specific metrics"""
    
    def __init__(self):
        self.custom_metrics = {}
        self.metric_history = {}
    
    def record_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """Record a custom metric value"""
        
        timestamp = time.time()
        tags = tags or {}
        
        if metric_name not in self.custom_metrics:
            self.custom_metrics[metric_name] = {
                'current_value': value,
                'last_updated': timestamp,
                'tags': tags
            }
            self.metric_history[metric_name] = []
        
        self.custom_metrics[metric_name]['current_value'] = value
        self.custom_metrics[metric_name]['last_updated'] = timestamp
        
        # Store history
        self.metric_history[metric_name].append({
            'timestamp': timestamp,
            'value': value,
            'tags': tags
        })
        
        # Limit history size
        if len(self.metric_history[metric_name]) > 1000:
            self.metric_history[metric_name].pop(0)
    
    def increment_counter(self, counter_name: str, tags: Dict[str, str] = None):
        """Increment a counter metric"""
        
        current_value = self.custom_metrics.get(counter_name, {}).get('current_value', 0)
        self.record_metric(counter_name, current_value + 1, tags)
    
    def record_timing(self, timer_name: str, duration: float, tags: Dict[str, str] = None):
        """Record a timing metric"""
        
        self.record_metric(f"{timer_name}.duration", duration, tags)
    
    def get_metric_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        
        summary = {}
        for metric_name, metric_data in self.custom_metrics.items():
            history = self.metric_history.get(metric_name, [])
            
            if history:
                values = [entry['value'] for entry in history]
                summary[metric_name] = {
                    'current_value': metric_data['current_value'],
                    'last_updated': metric_data['last_updated'],
                    'min_value': min(values),
                    'max_value': max(values),
                    'avg_value': sum(values) / len(values),
                    'sample_count': len(values)
                }
            else:
                summary[metric_name] = metric_data
        
        return summary
```

## Real-time Monitoring

### Monitoring Dashboard

```python
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

class MonitoringDashboard:
    """Real-time monitoring dashboard for sandbox operations"""
    
    def __init__(self, telemetry_collector: TelemetryCollector):
        self.telemetry_collector = telemetry_collector
        self.custom_metrics = CustomMetricsCollector()
        self.active_sandboxes = {}
        self.alert_thresholds = self._get_default_thresholds()
        self.dashboard_data = {}
        self.update_interval = 2.0
        self.monitoring_task = None
    
    def _get_default_thresholds(self) -> Dict[str, Any]:
        """Get default alert thresholds"""
        return {
            'memory_mb': {
                'warning': 100,
                'critical': 200
            },
            'cpu_percent': {
                'warning': 70.0,
                'critical': 90.0
            },
            'execution_time_seconds': {
                'warning': 30,
                'critical': 60
            },
            'violation_count': {
                'warning': 3,
                'critical': 5
            }
        }
    
    async def start_monitoring(self):
        """Start real-time monitoring"""
        
        if self.monitoring_task and not self.monitoring_task.done():
            return
        
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop real-time monitoring"""
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        
        try:
            while True:
                await self._update_dashboard_data()
                await self._check_alerts()
                await asyncio.sleep(self.update_interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Monitoring loop error: {e}")
    
    async def _update_dashboard_data(self):
        """Update dashboard data"""
        
        current_time = time.time()
        
        # Collect current system metrics
        system_metrics = self._get_system_metrics()
        
        # Collect active sandbox metrics
        active_sandbox_metrics = self._get_active_sandbox_metrics()
        
        # Get historical performance data
        historical_data = self.telemetry_collector.get_historical_data(50)
        performance_trends = self._calculate_performance_trends(historical_data)
        
        # Update dashboard data
        self.dashboard_data.update({
            'timestamp': current_time,
            'system_metrics': system_metrics,
            'active_sandboxes': active_sandbox_metrics,
            'performance_trends': performance_trends,
            'custom_metrics': self.custom_metrics.get_metric_summary(),
            'alert_status': self._get_alert_status()
        })
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get overall system metrics"""
        
        return {
            'cpu_percent': psutil.cpu_percent(interval=None),
            'memory': psutil.virtual_memory()._asdict(),
            'disk': psutil.disk_usage('/')._asdict(),
            'network': psutil.net_io_counters()._asdict(),
            'active_sandbox_count': len(self.telemetry_collector.active_collections)
        }
    
    def _get_active_sandbox_metrics(self) -> Dict[str, Any]:
        """Get metrics for currently active sandboxes"""
        
        active_metrics = {}
        
        for sandbox_id, collection_info in self.telemetry_collector.active_collections.items():
            telemetry = collection_info['telemetry']
            
            if telemetry.resource_samples:
                latest_sample = telemetry.resource_samples[-1]
                
                active_metrics[sandbox_id] = {
                    'current_memory_mb': latest_sample.memory_mb,
                    'current_cpu_percent': latest_sample.cpu_percent,
                    'execution_time': time.time() - telemetry.start_time,
                    'peak_memory_mb': telemetry.peak_memory_mb,
                    'peak_cpu_percent': telemetry.peak_cpu_percent,
                    'sample_count': len(telemetry.resource_samples),
                    'violations_count': telemetry.violations_count
                }
        
        return active_metrics
    
    def _calculate_performance_trends(self, historical_data: List[SandboxTelemetry]) -> Dict[str, Any]:
        """Calculate performance trends from historical data"""
        
        if not historical_data:
            return {}
        
        # Calculate trends over time
        execution_times = [t.plugin_execution_time for t in historical_data if t.plugin_execution_time > 0]
        memory_peaks = [t.peak_memory_mb for t in historical_data]
        cpu_peaks = [t.peak_cpu_percent for t in historical_data]
        
        trends = {}
        
        if execution_times:
            trends['avg_execution_time'] = sum(execution_times) / len(execution_times)
            trends['max_execution_time'] = max(execution_times)
            trends['min_execution_time'] = min(execution_times)
        
        if memory_peaks:
            trends['avg_peak_memory'] = sum(memory_peaks) / len(memory_peaks)
            trends['max_peak_memory'] = max(memory_peaks)
        
        if cpu_peaks:
            trends['avg_peak_cpu'] = sum(cpu_peaks) / len(cpu_peaks)
            trends['max_peak_cpu'] = max(cpu_peaks)
        
        # Calculate success rate
        total_executions = len(historical_data)
        successful_executions = sum(1 for t in historical_data if not t.terminated_by_violation)
        trends['success_rate'] = successful_executions / total_executions if total_executions > 0 else 0
        
        return trends
    
    def _get_alert_status(self) -> Dict[str, Any]:
        """Get current alert status"""
        
        alerts = {
            'active_alerts': [],
            'warning_count': 0,
            'critical_count': 0
        }
        
        # Check system-level alerts
        system_metrics = self.dashboard_data.get('system_metrics', {})
        
        if system_metrics.get('cpu_percent', 0) > self.alert_thresholds['cpu_percent']['critical']:
            alerts['active_alerts'].append({
                'type': 'critical',
                'metric': 'system_cpu',
                'value': system_metrics['cpu_percent'],
                'threshold': self.alert_thresholds['cpu_percent']['critical'],
                'message': 'System CPU usage critical'
            })
            alerts['critical_count'] += 1
        
        # Check sandbox-level alerts
        for sandbox_id, metrics in self.dashboard_data.get('active_sandboxes', {}).items():
            if metrics['current_memory_mb'] > self.alert_thresholds['memory_mb']['warning']:
                alert_level = 'critical' if metrics['current_memory_mb'] > self.alert_thresholds['memory_mb']['critical'] else 'warning'
                alerts['active_alerts'].append({
                    'type': alert_level,
                    'metric': 'sandbox_memory',
                    'sandbox_id': sandbox_id,
                    'value': metrics['current_memory_mb'],
                    'threshold': self.alert_thresholds['memory_mb'][alert_level],
                    'message': f'Sandbox {sandbox_id} memory usage {alert_level}'
                })
                
                if alert_level == 'critical':
                    alerts['critical_count'] += 1
                else:
                    alerts['warning_count'] += 1
        
        return alerts
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data"""
        return self.dashboard_data.copy()
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format"""
        
        if format.lower() == 'json':
            return json.dumps(self.dashboard_data, indent=2, default=str)
        elif format.lower() == 'prometheus':
            return self._export_prometheus_format()
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_prometheus_format(self) -> str:
        """Export metrics in Prometheus format"""
        
        metrics = []
        timestamp = int(time.time() * 1000)  # Prometheus uses milliseconds
        
        # System metrics
        system_metrics = self.dashboard_data.get('system_metrics', {})
        metrics.append(f'sandbox_system_cpu_percent {system_metrics.get("cpu_percent", 0)} {timestamp}')
        
        if 'memory' in system_metrics:
            memory = system_metrics['memory']
            metrics.append(f'sandbox_system_memory_used_bytes {memory.get("used", 0)} {timestamp}')
            metrics.append(f'sandbox_system_memory_total_bytes {memory.get("total", 0)} {timestamp}')
        
        # Active sandbox metrics
        for sandbox_id, sandbox_metrics in self.dashboard_data.get('active_sandboxes', {}).items():
            labels = f'{{sandbox_id="{sandbox_id}"}}'
            metrics.append(f'sandbox_memory_mb{labels} {sandbox_metrics.get("current_memory_mb", 0)} {timestamp}')
            metrics.append(f'sandbox_cpu_percent{labels} {sandbox_metrics.get("current_cpu_percent", 0)} {timestamp}')
            metrics.append(f'sandbox_execution_time_seconds{labels} {sandbox_metrics.get("execution_time", 0)} {timestamp}')
        
        return '\n'.join(metrics)
```

## Performance Metrics

### Key Performance Indicators (KPIs)

```python
class PerformanceMetrics:
    """Track and analyze performance metrics"""
    
    def __init__(self):
        self.metrics_buffer = []
        self.performance_baselines = {}
        self.sla_thresholds = self._get_sla_thresholds()
    
    def _get_sla_thresholds(self) -> Dict[str, float]:
        """Define SLA thresholds"""
        return {
            'execution_time_p95': 30.0,  # 95th percentile execution time
            'memory_efficiency': 0.8,    # Memory utilization efficiency
            'cpu_efficiency': 0.7,       # CPU utilization efficiency
            'success_rate': 0.99,        # Plugin execution success rate
            'throughput_per_minute': 100  # Plugins per minute
        }
    
    def calculate_performance_metrics(self, telemetry_data: List[SandboxTelemetry]) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        
        if not telemetry_data:
            return {}
        
        metrics = {}
        
        # Execution time metrics
        execution_times = [t.plugin_execution_time for t in telemetry_data if t.plugin_execution_time > 0]
        if execution_times:
            metrics['execution_time'] = {
                'mean': statistics.mean(execution_times),
                'median': statistics.median(execution_times),
                'p95': self._percentile(execution_times, 95),
                'p99': self._percentile(execution_times, 99),
                'max': max(execution_times),
                'min': min(execution_times)
            }
        
        # Resource utilization metrics
        memory_peaks = [t.peak_memory_mb for t in telemetry_data]
        cpu_peaks = [t.peak_cpu_percent for t in telemetry_data]
        
        if memory_peaks:
            metrics['memory_utilization'] = {
                'mean_peak': statistics.mean(memory_peaks),
                'max_peak': max(memory_peaks),
                'p95_peak': self._percentile(memory_peaks, 95)
            }
        
        if cpu_peaks:
            metrics['cpu_utilization'] = {
                'mean_peak': statistics.mean(cpu_peaks),
                'max_peak': max(cpu_peaks),
                'p95_peak': self._percentile(cpu_peaks, 95)
            }
        
        # Success rate metrics
        total_executions = len(telemetry_data)
        successful_executions = sum(1 for t in telemetry_data if not t.terminated_by_violation and not t.terminated_by_timeout)
        
        metrics['reliability'] = {
            'success_rate': successful_executions / total_executions if total_executions > 0 else 0,
            'timeout_rate': sum(1 for t in telemetry_data if t.terminated_by_timeout) / total_executions if total_executions > 0 else 0,
            'violation_rate': sum(1 for t in telemetry_data if t.terminated_by_violation) / total_executions if total_executions > 0 else 0
        }
        
        # Throughput metrics
        if len(telemetry_data) >= 2:
            time_span = max(t.end_time for t in telemetry_data) - min(t.start_time for t in telemetry_data)
            throughput_per_second = len(telemetry_data) / time_span if time_span > 0 else 0
            
            metrics['throughput'] = {
                'executions_per_second': throughput_per_second,
                'executions_per_minute': throughput_per_second * 60
            }
        
        # SLA compliance
        metrics['sla_compliance'] = self._calculate_sla_compliance(metrics)
        
        return metrics
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = int(percentile / 100.0 * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _calculate_sla_compliance(self, metrics: Dict[str, Any]) -> Dict[str, bool]:
        """Calculate SLA compliance status"""
        
        compliance = {}
        
        # Execution time compliance
        if 'execution_time' in metrics:
            compliance['execution_time_p95'] = metrics['execution_time']['p95'] <= self.sla_thresholds['execution_time_p95']
        
        # Success rate compliance
        if 'reliability' in metrics:
            compliance['success_rate'] = metrics['reliability']['success_rate'] >= self.sla_thresholds['success_rate']
        
        # Throughput compliance
        if 'throughput' in metrics:
            compliance['throughput'] = metrics['throughput']['executions_per_minute'] >= self.sla_thresholds['throughput_per_minute']
        
        # Overall compliance
        compliance['overall'] = all(compliance.values()) if compliance else False
        
        return compliance
```

## Health Checks

### System Health Monitoring

```python
import aiohttp
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class HealthChecker:
    """Comprehensive health checking for sandbox system"""
    
    def __init__(self, telemetry_collector: TelemetryCollector):
        self.telemetry_collector = telemetry_collector
        self.health_checks = {}
        self.last_health_check = None
        self.health_history = []
    
    async def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks and return status"""
        
        health_results = {
            'timestamp': time.time(),
            'overall_status': HealthStatus.UNKNOWN,
            'checks': {},
            'summary': {}
        }
        
        # Run individual health checks
        checks = [
            ('system_resources', self._check_system_resources()),
            ('sandbox_capacity', self._check_sandbox_capacity()),
            ('telemetry_system', self._check_telemetry_system()),
            ('security_system', self._check_security_system()),
            ('performance', self._check_performance())
        ]
        
        check_results = await asyncio.gather(*[check[1] for check in checks])
        
        for (check_name, _), result in zip(checks, check_results):
            health_results['checks'][check_name] = result
        
        # Calculate overall status
        health_results['overall_status'] = self._calculate_overall_status(health_results['checks'])
        health_results['summary'] = self._create_health_summary(health_results['checks'])
        
        # Store results
        self.last_health_check = health_results
        self.health_history.append(health_results)
        
        # Limit history size
        if len(self.health_history) > 100:
            self.health_history.pop(0)
        
        return health_results
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource availability"""
        
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine status based on usage levels
            status = HealthStatus.HEALTHY
            issues = []
            
            if cpu_percent > 90:
                status = HealthStatus.UNHEALTHY
                issues.append(f"CPU usage critical: {cpu_percent:.1f}%")
            elif cpu_percent > 75:
                status = HealthStatus.DEGRADED
                issues.append(f"CPU usage high: {cpu_percent:.1f}%")
            
            if memory.percent > 90:
                status = HealthStatus.UNHEALTHY
                issues.append(f"Memory usage critical: {memory.percent:.1f}%")
            elif memory.percent > 75:
                status = HealthStatus.DEGRADED
                issues.append(f"Memory usage high: {memory.percent:.1f}%")
            
            if disk.percent > 95:
                status = HealthStatus.UNHEALTHY
                issues.append(f"Disk usage critical: {disk.percent:.1f}%")
            elif disk.percent > 85:
                status = HealthStatus.DEGRADED
                issues.append(f"Disk usage high: {disk.percent:.1f}%")
            
            return {
                'status': status.value,
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'issues': issues,
                'details': {
                    'cpu': cpu_percent,
                    'memory': memory._asdict(),
                    'disk': disk._asdict()
                }
            }
            
        except Exception as e:
            return {
                'status': HealthStatus.UNKNOWN.value,
                'error': str(e)
            }
    
    async def _check_sandbox_capacity(self) -> Dict[str, Any]:
        """Check sandbox execution capacity"""
        
        try:
            active_sandboxes = len(self.telemetry_collector.active_collections)
            max_concurrent_sandboxes = 20  # Configuration value
            
            capacity_usage = active_sandboxes / max_concurrent_sandboxes
            
            status = HealthStatus.HEALTHY
            issues = []
            
            if capacity_usage >= 0.95:
                status = HealthStatus.UNHEALTHY
                issues.append(f"Sandbox capacity critical: {active_sandboxes}/{max_concurrent_sandboxes}")
            elif capacity_usage >= 0.8:
                status = HealthStatus.DEGRADED
                issues.append(f"Sandbox capacity high: {active_sandboxes}/{max_concurrent_sandboxes}")
            
            return {
                'status': status.value,
                'active_sandboxes': active_sandboxes,
                'max_capacity': max_concurrent_sandboxes,
                'capacity_usage_percent': capacity_usage * 100,
                'issues': issues
            }
            
        except Exception as e:
            return {
                'status': HealthStatus.UNKNOWN.value,
                'error': str(e)
            }
    
    async def _check_telemetry_system(self) -> Dict[str, Any]:
        """Check telemetry collection system health"""
        
        try:
            # Check if telemetry collector is responsive
            historical_data = self.telemetry_collector.get_historical_data(10)
            
            status = HealthStatus.HEALTHY
            issues = []
            
            # Check if we have recent data
            if historical_data:
                latest_data = max(historical_data, key=lambda x: x.end_time)
                time_since_last = time.time() - latest_data.end_time
                
                if time_since_last > 300:  # 5 minutes
                    status = HealthStatus.DEGRADED
                    issues.append(f"No recent telemetry data: {time_since_last:.0f}s ago")
            else:
                status = HealthStatus.DEGRADED
                issues.append("No historical telemetry data available")
            
            return {
                'status': status.value,
                'historical_entries': len(historical_data),
                'active_collections': len(self.telemetry_collector.active_collections),
                'issues': issues
            }
            
        except Exception as e:
            return {
                'status': HealthStatus.UNKNOWN.value,
                'error': str(e)
            }
    
    async def _check_security_system(self) -> Dict[str, Any]:
        """Check security system status"""
        
        try:
            # This would integrate with actual security monitoring
            status = HealthStatus.HEALTHY
            issues = []
            
            # Check for recent security violations
            recent_violations = 0  # Would come from actual security system
            
            if recent_violations > 10:
                status = HealthStatus.UNHEALTHY
                issues.append(f"High security violation rate: {recent_violations}")
            elif recent_violations > 5:
                status = HealthStatus.DEGRADED
                issues.append(f"Elevated security violations: {recent_violations}")
            
            return {
                'status': status.value,
                'recent_violations': recent_violations,
                'issues': issues
            }
            
        except Exception as e:
            return {
                'status': HealthStatus.UNKNOWN.value,
                'error': str(e)
            }
    
    async def _check_performance(self) -> Dict[str, Any]:
        """Check system performance metrics"""
        
        try:
            # Get recent performance data
            historical_data = self.telemetry_collector.get_historical_data(50)
            
            status = HealthStatus.HEALTHY
            issues = []
            
            if historical_data:
                # Check average execution time
                avg_execution_time = sum(t.plugin_execution_time for t in historical_data if t.plugin_execution_time > 0) / len(historical_data)
                
                if avg_execution_time > 30:
                    status = HealthStatus.DEGRADED
                    issues.append(f"High average execution time: {avg_execution_time:.2f}s")
                
                # Check success rate
                success_rate = sum(1 for t in historical_data if not t.terminated_by_violation) / len(historical_data)
                
                if success_rate < 0.9:
                    status = HealthStatus.UNHEALTHY
                    issues.append(f"Low success rate: {success_rate:.1%}")
                elif success_rate < 0.95:
                    status = HealthStatus.DEGRADED
                    issues.append(f"Reduced success rate: {success_rate:.1%}")
            
            return {
                'status': status.value,
                'avg_execution_time': avg_execution_time if historical_data else 0,
                'success_rate': success_rate if historical_data else 0,
                'issues': issues
            }
            
        except Exception as e:
            return {
                'status': HealthStatus.UNKNOWN.value,
                'error': str(e)
            }
    
    def _calculate_overall_status(self, checks: Dict[str, Any]) -> HealthStatus:
        """Calculate overall health status from individual checks"""
        
        statuses = [HealthStatus(check['status']) for check in checks.values() if 'status' in check]
        
        if not statuses:
            return HealthStatus.UNKNOWN
        
        # If any check is unhealthy, overall is unhealthy
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        
        # If any check is degraded, overall is degraded
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        
        # If all checks are healthy, overall is healthy
        if all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        
        return HealthStatus.UNKNOWN
    
    def _create_health_summary(self, checks: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of health check results"""
        
        total_checks = len(checks)
        healthy_checks = sum(1 for check in checks.values() if check.get('status') == 'healthy')
        degraded_checks = sum(1 for check in checks.values() if check.get('status') == 'degraded')
        unhealthy_checks = sum(1 for check in checks.values() if check.get('status') == 'unhealthy')
        
        all_issues = []
        for check in checks.values():
            all_issues.extend(check.get('issues', []))
        
        return {
            'total_checks': total_checks,
            'healthy_checks': healthy_checks,
            'degraded_checks': degraded_checks,
            'unhealthy_checks': unhealthy_checks,
            'total_issues': len(all_issues),
            'critical_issues': [issue for issue in all_issues if 'critical' in issue.lower()]
        }
    
    def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health check history for specified time period"""
        
        cutoff_time = time.time() - (hours * 3600)
        return [health for health in self.health_history if health['timestamp'] >= cutoff_time]
```

## Summary

This monitoring guide provides comprehensive observability for the Enhanced Plugin Sandbox Isolation system:

1. **Multi-layer Telemetry**: Resource, security, performance, and business metrics
2. **Real-time Monitoring**: Live dashboards and alerting
3. **Performance Analysis**: KPIs, SLA tracking, trend analysis
4. **Health Monitoring**: Proactive health checks and status tracking
5. **Export Capabilities**: Multiple format support for integration

The monitoring system enables:
- **Proactive Issue Detection**: Early warning of problems
- **Performance Optimization**: Data-driven optimization decisions  
- **Capacity Planning**: Understanding resource usage patterns
- **SLA Compliance**: Meeting service level agreements
- **Operational Visibility**: Complete system observability
