#!/usr/bin/env python3
"""
NoxSuite System Monitor Component for Langflow
Comprehensive system monitoring with intelligent alerting
"""
from typing import Optional, Dict, Any, List
from langflow.custom import CustomComponent
from langflow.field_typing import Text, DropDown, Data, Bool, Number
import psutil
import requests
import docker
import json
from datetime import datetime

class NoxSuiteSystemMonitor(CustomComponent):
    display_name = "NoxSuite System Monitor"
    description = "Comprehensive system monitoring with performance metrics and alerting"
    icon = "📊"
    
    inputs = [
        DropDown(
            name="monitor_type",
            display_name="Monitor Type",
            options=["full_system", "performance", "services", "alerts", "resources"],
            value="full_system",
            info="Choose the type of monitoring to perform"
        ),
        Number(
            name="cpu_threshold",
            display_name="CPU Alert Threshold (%)",
            value=80.0,
            info="CPU usage percentage to trigger alerts"
        ),
        Number(
            name="memory_threshold", 
            display_name="Memory Alert Threshold (%)",
            value=85.0,
            info="Memory usage percentage to trigger alerts"
        ),
        Bool(
            name="include_docker",
            display_name="Include Docker Metrics",
            value=True,
            info="Include Docker container metrics in monitoring"
        )
    ]
    
    outputs = [
        Data(name="monitor_result", display_name="Monitoring Result"),
        Text(name="system_status", display_name="System Status"),
        Text(name="alerts", display_name="System Alerts")
    ]
    
    def build(
        self,
        monitor_type: str,
        cpu_threshold: float = 80.0,
        memory_threshold: float = 85.0,
        include_docker: bool = True
    ) -> Dict[str, Any]:
        """Execute system monitoring operations"""
        try:
            result = {
                "timestamp": datetime.now().isoformat(),
                "monitor_type": monitor_type,
                "thresholds": {
                    "cpu": cpu_threshold,
                    "memory": memory_threshold
                }
            }
            
            alerts = []
            
            if monitor_type == "full_system":
                return self._full_system_monitor(result, alerts, cpu_threshold, memory_threshold, include_docker)
                
            elif monitor_type == "performance":
                return self._performance_monitor(result, alerts, cpu_threshold, memory_threshold)
                
            elif monitor_type == "services":
                return self._services_monitor(result, alerts, include_docker)
                
            elif monitor_type == "alerts":
                return self._alerts_monitor(result, cpu_threshold, memory_threshold, include_docker)
                
            elif monitor_type == "resources":
                return self._resources_monitor(result, alerts)
                
            else:
                return {
                    "monitor_result": {"error": f"Unknown monitor type: {monitor_type}"},
                    "system_status": "error",
                    "alerts": f"Unsupported monitor type: {monitor_type}"
                }
                
        except Exception as e:
            error_msg = f"System monitor error: {str(e)}"
            return {
                "monitor_result": {"error": error_msg, "timestamp": datetime.now().isoformat()},
                "system_status": "error",
                "alerts": error_msg
            }
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get basic system metrics"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": psutil.virtual_memory()._asdict(),
            "disk": psutil.disk_usage('/')._asdict(),
            "network": psutil.net_io_counters()._asdict(),
            "processes": len(psutil.pids()),
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }
    
    def _get_docker_metrics(self) -> Dict[str, Any]:
        """Get Docker container metrics"""
        try:
            client = docker.from_env()
            containers = client.containers.list(all=True)
            
            docker_metrics = {
                "total_containers": len(containers),
                "running_containers": len([c for c in containers if c.status == "running"]),
                "noxsuite_containers": []
            }
            
            for container in containers:
                if 'noxsuite' in container.name:
                    try:
                        stats = container.stats(stream=False)
                        docker_metrics["noxsuite_containers"].append({
                            "name": container.name,
                            "status": container.status,
                            "image": container.image.tags[0] if container.image.tags else "unknown",
                            "cpu_usage": self._calculate_cpu_percent(stats),
                            "memory_usage": self._calculate_memory_usage(stats)
                        })
                    except:
                        docker_metrics["noxsuite_containers"].append({
                            "name": container.name,
                            "status": container.status,
                            "image": container.image.tags[0] if container.image.tags else "unknown",
                            "cpu_usage": "unavailable",
                            "memory_usage": "unavailable"
                        })
            
            return docker_metrics
            
        except Exception as e:
            return {"error": f"Docker metrics unavailable: {str(e)}"}
    
    def _calculate_cpu_percent(self, stats: Dict) -> float:
        """Calculate CPU usage percentage from Docker stats"""
        try:
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
            
            if system_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"]) * 100
                return round(cpu_percent, 2)
            return 0.0
        except:
            return 0.0
    
    def _calculate_memory_usage(self, stats: Dict) -> Dict[str, Any]:
        """Calculate memory usage from Docker stats"""
        try:
            memory_usage = stats["memory_stats"]["usage"]
            memory_limit = stats["memory_stats"]["limit"]
            memory_percent = (memory_usage / memory_limit) * 100
            
            return {
                "usage_bytes": memory_usage,
                "limit_bytes": memory_limit,
                "usage_percent": round(memory_percent, 2)
            }
        except:
            return {"usage_bytes": 0, "limit_bytes": 0, "usage_percent": 0.0}
    
    def _check_service_health(self) -> Dict[str, Any]:
        """Check health of key services"""
        services = {
            "langflow": {"url": "http://localhost:7860/health", "status": "unknown"},
            "nginx": {"url": "http://localhost:8080", "status": "unknown"}
        }
        
        for service_name, service_info in services.items():
            try:
                response = requests.get(service_info["url"], timeout=5)
                service_info["status"] = "healthy" if response.status_code == 200 else "degraded"
                service_info["response_time"] = response.elapsed.total_seconds()
            except:
                service_info["status"] = "unhealthy"
                service_info["response_time"] = None
        
        return services
    
    def _full_system_monitor(self, result: Dict, alerts: List, cpu_threshold: float, memory_threshold: float, include_docker: bool) -> Dict[str, Any]:
        """Comprehensive system monitoring"""
        # Get system metrics
        system_metrics = self._get_system_metrics()
        result["system_metrics"] = system_metrics
        
        # Check for alerts
        if system_metrics["cpu_percent"] > cpu_threshold:
            alerts.append(f"High CPU usage: {system_metrics['cpu_percent']:.1f}% (threshold: {cpu_threshold}%)")
        
        if system_metrics["memory"]["percent"] > memory_threshold:
            alerts.append(f"High memory usage: {system_metrics['memory']['percent']:.1f}% (threshold: {memory_threshold}%)")
        
        # Get Docker metrics if requested
        if include_docker:
            docker_metrics = self._get_docker_metrics()
            result["docker_metrics"] = docker_metrics
            
            if "noxsuite_containers" in docker_metrics:
                unhealthy_containers = [c for c in docker_metrics["noxsuite_containers"] if c["status"] != "running"]
                if unhealthy_containers:
                    alerts.append(f"Unhealthy containers: {[c['name'] for c in unhealthy_containers]}")
        
        # Get service health
        services = self._check_service_health()
        result["services"] = services
        
        unhealthy_services = [name for name, info in services.items() if info["status"] != "healthy"]
        if unhealthy_services:
            alerts.append(f"Unhealthy services: {unhealthy_services}")
        
        # Determine overall status
        if alerts:
            status = "warning" if len(alerts) <= 2 else "critical"
        else:
            status = "healthy"
        
        return {
            "monitor_result": result,
            "system_status": status,
            "alerts": "; ".join(alerts) if alerts else "No alerts"
        }
    
    def _performance_monitor(self, result: Dict, alerts: List, cpu_threshold: float, memory_threshold: float) -> Dict[str, Any]:
        """Performance-focused monitoring"""
        system_metrics = self._get_system_metrics()
        
        performance_data = {
            "cpu": {
                "current": system_metrics["cpu_percent"],
                "threshold": cpu_threshold,
                "status": "normal" if system_metrics["cpu_percent"] < cpu_threshold else "high"
            },
            "memory": {
                "current": system_metrics["memory"]["percent"],
                "threshold": memory_threshold,
                "status": "normal" if system_metrics["memory"]["percent"] < memory_threshold else "high"
            },
            "disk": {
                "usage_percent": round((system_metrics["disk"]["used"] / system_metrics["disk"]["total"]) * 100, 1),
                "free_gb": round(system_metrics["disk"]["free"] / (1024**3), 2)
            }
        }
        
        result["performance"] = performance_data
        
        # Performance alerts
        if performance_data["cpu"]["status"] == "high":
            alerts.append(f"High CPU: {performance_data['cpu']['current']:.1f}%")
        if performance_data["memory"]["status"] == "high":
            alerts.append(f"High Memory: {performance_data['memory']['current']:.1f}%")
        
        status = "optimal" if not alerts else "degraded"
        
        return {
            "monitor_result": result,
            "system_status": status,
            "alerts": "; ".join(alerts) if alerts else "Performance optimal"
        }
    
    def _services_monitor(self, result: Dict, alerts: List, include_docker: bool) -> Dict[str, Any]:
        """Services-focused monitoring"""
        services = self._check_service_health()
        result["services"] = services
        
        if include_docker:
            docker_metrics = self._get_docker_metrics()
            result["docker_services"] = docker_metrics
        
        # Service alerts
        for service_name, service_info in services.items():
            if service_info["status"] != "healthy":
                alerts.append(f"{service_name}: {service_info['status']}")
        
        status = "operational" if not alerts else "degraded"
        
        return {
            "monitor_result": result,
            "system_status": status,
            "alerts": "; ".join(alerts) if alerts else "All services operational"
        }
    
    def _alerts_monitor(self, result: Dict, cpu_threshold: float, memory_threshold: float, include_docker: bool) -> Dict[str, Any]:
        """Alert-focused monitoring"""
        alerts = []
        
        # Quick system check
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        
        if cpu_percent > cpu_threshold:
            alerts.append(f"CPU: {cpu_percent:.1f}% > {cpu_threshold}%")
        if memory_percent > memory_threshold:
            alerts.append(f"Memory: {memory_percent:.1f}% > {memory_threshold}%")
        
        # Quick service check
        try:
            response = requests.get("http://localhost:7860/health", timeout=3)
            if response.status_code != 200:
                alerts.append(f"Langflow unhealthy: HTTP {response.status_code}")
        except:
            alerts.append("Langflow unreachable")
        
        result["alert_summary"] = {
            "total_alerts": len(alerts),
            "severity": "none" if not alerts else "low" if len(alerts) == 1 else "high"
        }
        
        return {
            "monitor_result": result,
            "system_status": "alert_mode",
            "alerts": "; ".join(alerts) if alerts else "No alerts detected"
        }
    
    def _resources_monitor(self, result: Dict, alerts: List) -> Dict[str, Any]:
        """Resource-focused monitoring"""
        system_metrics = self._get_system_metrics()
        
        resources = {
            "cpu_cores": psutil.cpu_count(),
            "memory_total_gb": round(system_metrics["memory"]["total"] / (1024**3), 2),
            "disk_total_gb": round(system_metrics["disk"]["total"] / (1024**3), 2),
            "network_sent_mb": round(system_metrics["network"]["bytes_sent"] / (1024**2), 2),
            "network_recv_mb": round(system_metrics["network"]["bytes_recv"] / (1024**2), 2),
            "process_count": system_metrics["processes"]
        }
        
        result["resources"] = resources
        
        # Resource alerts
        if resources["memory_total_gb"] < 4:
            alerts.append("Low system memory (< 4GB)")
        if resources["process_count"] > 500:
            alerts.append(f"High process count: {resources['process_count']}")
        
        return {
            "monitor_result": result,
            "system_status": "monitored",
            "alerts": "; ".join(alerts) if alerts else "Resource usage normal"
        }
