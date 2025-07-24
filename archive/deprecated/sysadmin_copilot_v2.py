# 🤖 SysAdmin Copilot v2.0 - Enhanced AI-Powered System Administration
# Integrated with Plugin Framework v2.0 for NoxPanel/NoxGuard/Heimnetz Suite
# Audit 3 Compliant - Security-First Administration

import os
import sys
import json
import asyncio
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field

# Add the project root to sys.path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from plugin_framework_v2 import (
        PluginFrameworkV2, PluginSandboxV2, PluginMetadataV2, 
        SecurityLevel, PluginPermissionsV2, PluginLimitsV2
    )
    PLUGIN_FRAMEWORK_AVAILABLE = True
except ImportError:
    PLUGIN_FRAMEWORK_AVAILABLE = False
    logging.warning("Plugin Framework v2.0 not available - running in standalone mode")

# Import original SysAdmin Copilot components  
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not available - some features may be limited")

# Define minimal required classes if original not available
class TaskPriority:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TaskStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ScriptType:
    PYTHON = "python"
    POWERSHELL = "powershell"
    BASH = "bash"

ORIGINAL_COPILOT_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CopilotPlugin:
    """Enhanced plugin definition for SysAdmin Copilot"""
    id: str
    name: str
    description: str
    category: str
    version: str = "1.0.0"
    author: str = "NoxPanel Team"
    requires_admin: bool = False
    supported_platforms: List[str] = field(default_factory=lambda: ["windows", "linux", "macos"])
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    script_content: str = ""
    script_type: str = "python"
    tags: List[str] = field(default_factory=list)
    execution_time_estimate: str = "1-5 minutes"
    created_at: datetime = field(default_factory=datetime.now)

class AdminTaskCategory:
    """Administrative task categories for better organization"""
    SYSTEM_MAINTENANCE = "system_maintenance"
    SECURITY_AUDIT = "security_audit"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    NETWORK_DIAGNOSTICS = "network_diagnostics"
    USER_MANAGEMENT = "user_management"
    SERVICE_MANAGEMENT = "service_management"
    MONITORING_SETUP = "monitoring_setup"
    BACKUP_RECOVERY = "backup_recovery"

class SysAdminCopilotV2:
    """Next-generation SysAdmin Copilot with Plugin Framework v2.0 integration"""
    
    def __init__(self, plugin_directory: str = None):
        self.version = "2.0.0"
        self.plugin_directory = Path(plugin_directory or "plugins/sysadmin")
        self.copilot_plugins: Dict[str, CopilotPlugin] = {}
        self.task_history: List[Dict[str, Any]] = []
        
        # Initialize plugin framework if available
        if PLUGIN_FRAMEWORK_AVAILABLE:
            self.plugin_framework = PluginFrameworkV2(str(self.plugin_directory))
            logger.info("✅ Plugin Framework v2.0 integrated successfully")
        else:
            self.plugin_framework = None
            logger.warning("⚠️ Plugin Framework v2.0 not available")
            
        # Initialize original copilot if available (disabled for now)
        self.original_copilot = None
        logger.info("ℹ️ SysAdmin Copilot v2.0 running in standalone mode")
        
        # Initialize enhanced components
        self._initialize_enhanced_components()
        self._load_builtin_plugins()
    
    def _initialize_enhanced_components(self):
        """Initialize enhanced SysAdmin components"""
        # Create plugin directory structure
        self.plugin_directory.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different plugin categories
        categories = [
            "maintenance", "security", "performance", "network", 
            "monitoring", "backup", "user-mgmt", "service-mgmt"
        ]
        
        for category in categories:
            category_dir = self.plugin_directory / category
            category_dir.mkdir(exist_ok=True)
        
        logger.info(f"📁 SysAdmin plugin directories initialized: {self.plugin_directory}")
    
    def _load_builtin_plugins(self):
        """Load built-in administrative plugins"""
        builtin_plugins = self._get_builtin_plugins()
        
        for plugin_data in builtin_plugins:
            plugin = CopilotPlugin(**plugin_data)
            self.copilot_plugins[plugin.id] = plugin
            
        logger.info(f"🔌 Loaded {len(builtin_plugins)} built-in SysAdmin plugins")
    
    def _get_builtin_plugins(self) -> List[Dict[str, Any]]:
        """Define built-in administrative plugins"""
        return [
            {
                "id": "system_health_analyzer",
                "name": "System Health Analyzer",
                "description": "Comprehensive system health analysis with recommendations",
                "category": AdminTaskCategory.SYSTEM_MAINTENANCE,
                "requires_admin": False,
                "security_level": SecurityLevel.LOW,
                "script_type": "python",
                "tags": ["health", "monitoring", "diagnostics"],
                "script_content": '''
import psutil
import json
from datetime import datetime

def analyze_system_health():
    """Analyze comprehensive system health"""
    health_data = {
        "timestamp": datetime.now().isoformat(),
        "cpu": {
            "usage_percent": psutil.cpu_percent(interval=1),
            "count": psutil.cpu_count(),
            "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        },
        "memory": {
            "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "usage_percent": psutil.virtual_memory().percent
        },
        "disk": {},
        "network": {
            "connections": len(psutil.net_connections()),
            "io_stats": psutil.net_io_counters()._asdict()
        },
        "processes": {
            "total": len(psutil.pids()),
            "running": len([p for p in psutil.process_iter() if p.status() == "running"])
        }
    }
    
    # Analyze disk usage for all partitions
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            health_data["disk"][partition.mountpoint] = {
                "total_gb": round(usage.total / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "usage_percent": round((usage.used / usage.total) * 100, 1)
            }
        except PermissionError:
            continue
    
    # Generate health score and recommendations
    recommendations = []
    health_score = 100
    
    if health_data["cpu"]["usage_percent"] > 80:
        recommendations.append("High CPU usage detected - consider optimizing processes")
        health_score -= 15
    
    if health_data["memory"]["usage_percent"] > 85:
        recommendations.append("High memory usage - consider closing unnecessary applications")
        health_score -= 20
    
    for mount, disk_info in health_data["disk"].items():
        if disk_info["usage_percent"] > 90:
            recommendations.append(f"Disk {mount} is {disk_info['usage_percent']}% full - cleanup needed")
            health_score -= 25
    
    health_data["analysis"] = {
        "health_score": max(0, health_score),
        "status": "excellent" if health_score >= 90 else 
                 "good" if health_score >= 70 else
                 "warning" if health_score >= 50 else "critical",
        "recommendations": recommendations
    }
    
    return health_data

def main(config=None):
    return analyze_system_health()
'''
            },
            {
                "id": "disk_cleanup_advanced",
                "name": "Advanced Disk Cleanup",
                "description": "Intelligent disk cleanup with safety checks",
                "category": AdminTaskCategory.SYSTEM_MAINTENANCE,
                "requires_admin": True,
                "security_level": SecurityLevel.MEDIUM,
                "script_type": "python",
                "tags": ["cleanup", "disk", "maintenance"],
                "execution_time_estimate": "5-15 minutes",
                "script_content": '''
import os
import shutil
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta

def safe_disk_cleanup():
    """Perform safe disk cleanup with detailed reporting"""
    cleanup_report = {
        "start_time": datetime.now().isoformat(),
        "locations_cleaned": [],
        "space_recovered_bytes": 0,
        "files_removed": 0,
        "errors": []
    }
    
    # Define safe cleanup locations
    cleanup_locations = []
    
    # Platform-specific cleanup locations
    if os.name == 'nt':  # Windows
        temp_dirs = [
            os.path.expandvars(r'%TEMP%'),
            os.path.expandvars(r'%WINDIR%\\Temp'),
            os.path.expandvars(r'%LOCALAPPDATA%\\Temp')
        ]
    else:  # Unix-like
        temp_dirs = [
            '/tmp',
            '/var/tmp',
            os.path.expanduser('~/.cache')
        ]
    
    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            cleanup_locations.append({
                "path": temp_dir,
                "type": "temp_files",
                "age_threshold_days": 7
            })
    
    # Perform cleanup
    for location in cleanup_locations:
        try:
            path = Path(location["path"])
            if not path.exists():
                continue
            
            files_removed = 0
            space_freed = 0
            cutoff_date = datetime.now() - timedelta(days=location["age_threshold_days"])
            
            for item in path.rglob("*"):
                try:
                    if item.is_file():
                        # Check file age
                        file_time = datetime.fromtimestamp(item.stat().st_mtime)
                        if file_time < cutoff_date:
                            file_size = item.stat().st_size
                            item.unlink()
                            files_removed += 1
                            space_freed += file_size
                except (PermissionError, FileNotFoundError, OSError) as e:
                    cleanup_report["errors"].append(f"Could not remove {item}: {e}")
            
            if files_removed > 0:
                cleanup_report["locations_cleaned"].append({
                    "path": str(path),
                    "files_removed": files_removed,
                    "space_freed_mb": round(space_freed / (1024 * 1024), 2)
                })
                cleanup_report["files_removed"] += files_removed
                cleanup_report["space_recovered_bytes"] += space_freed
                
        except Exception as e:
            cleanup_report["errors"].append(f"Error cleaning {location['path']}: {e}")
    
    cleanup_report["end_time"] = datetime.now().isoformat()
    cleanup_report["space_recovered_mb"] = round(cleanup_report["space_recovered_bytes"] / (1024 * 1024), 2)
    cleanup_report["space_recovered_gb"] = round(cleanup_report["space_recovered_bytes"] / (1024 * 1024 * 1024), 2)
    
    return cleanup_report

def main(config=None):
    return safe_disk_cleanup()
'''
            },
            {
                "id": "security_audit_basic",
                "name": "Basic Security Audit",
                "description": "Perform basic security audit and recommendations",
                "category": AdminTaskCategory.SECURITY_AUDIT,
                "requires_admin": False,
                "security_level": SecurityLevel.HIGH,
                "script_type": "python",
                "tags": ["security", "audit", "compliance"],
                "execution_time_estimate": "2-5 minutes",
                "script_content": '''
import os
import stat
import pwd
import grp
import json
from pathlib import Path
from datetime import datetime

def basic_security_audit():
    """Perform basic security audit"""
    audit_report = {
        "timestamp": datetime.now().isoformat(),
        "platform": os.name,
        "security_checks": [],
        "vulnerabilities": [],
        "recommendations": [],
        "overall_score": 100
    }
    
    # Check file permissions on sensitive directories
    sensitive_paths = []
    
    if os.name != 'nt':  # Unix-like systems
        sensitive_paths = ['/etc/passwd', '/etc/shadow', '/etc/sudoers', '/home']
    else:  # Windows
        sensitive_paths = ['C:\\\\Windows\\\\System32', 'C:\\\\Users']
    
    for path_str in sensitive_paths:
        path = Path(path_str)
        if path.exists():
            try:
                file_stat = path.stat()
                permissions = stat.filemode(file_stat.st_mode)
                
                check_result = {
                    "path": str(path),
                    "permissions": permissions,
                    "owner": "N/A",
                    "group": "N/A",
                    "status": "checked"
                }
                
                # Get owner/group info on Unix-like systems
                if os.name != 'nt':
                    try:
                        check_result["owner"] = pwd.getpwuid(file_stat.st_uid).pw_name
                        check_result["group"] = grp.getgrgid(file_stat.st_gid).gr_name
                    except (KeyError, OSError):
                        pass
                
                audit_report["security_checks"].append(check_result)
                
                # Check for world-writable files (security risk)
                if os.name != 'nt' and (file_stat.st_mode & stat.S_IWOTH):
                    audit_report["vulnerabilities"].append(f"World-writable file/directory: {path}")
                    audit_report["overall_score"] -= 10
                    
            except (PermissionError, OSError) as e:
                audit_report["security_checks"].append({
                    "path": str(path),
                    "status": "access_denied",
                    "error": str(e)
                })
    
    # Check for common security configurations
    security_recommendations = []
    
    # Check if running as root/admin (not recommended)
    if os.name != 'nt' and os.geteuid() == 0:
        audit_report["vulnerabilities"].append("Running as root user")
        security_recommendations.append("Avoid running applications as root user")
        audit_report["overall_score"] -= 15
    
    # Check for firewall status (basic check)
    if os.name != 'nt':
        # Check for common firewall tools
        firewall_tools = ['ufw', 'iptables', 'firewalld']
        firewall_active = False
        
        for tool in firewall_tools:
            if shutil.which(tool):
                firewall_active = True
                break
        
        if not firewall_active:
            security_recommendations.append("Consider enabling a firewall (ufw, iptables, or firewalld)")
            audit_report["overall_score"] -= 5
    
    # General security recommendations
    security_recommendations.extend([
        "Regularly update system packages and security patches",
        "Use strong, unique passwords for all accounts",
        "Enable automatic security updates where possible",
        "Review and audit user permissions regularly",
        "Monitor system logs for suspicious activity"
    ])
    
    audit_report["recommendations"] = security_recommendations
    
    # Determine overall security status
    if audit_report["overall_score"] >= 90:
        audit_report["security_status"] = "excellent"
    elif audit_report["overall_score"] >= 70:
        audit_report["security_status"] = "good"
    elif audit_report["overall_score"] >= 50:
        audit_report["security_status"] = "needs_improvement"
    else:
        audit_report["security_status"] = "critical"
    
    return audit_report

def main(config=None):
    import shutil
    return basic_security_audit()
'''
            },
            {
                "id": "network_diagnostics_pro",
                "name": "Professional Network Diagnostics",
                "description": "Comprehensive network connectivity and performance analysis",
                "category": AdminTaskCategory.NETWORK_DIAGNOSTICS,
                "requires_admin": False,
                "security_level": SecurityLevel.LOW,
                "script_type": "python",
                "tags": ["network", "diagnostics", "connectivity"],
                "execution_time_estimate": "3-10 minutes",
                "script_content": '''
import socket
import subprocess
import time
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

def ping_host(host, count=3, timeout=5):
    """Ping a host and return detailed results"""
    try:
        if os.name == 'nt':  # Windows
            cmd = ['ping', '-n', str(count), '-w', str(timeout * 1000), host]
        else:  # Unix-like
            cmd = ['ping', '-c', str(count), '-W', str(timeout), host]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout * count + 5)
        end_time = time.time()
        
        return {
            'host': host,
            'success': result.returncode == 0,
            'response_time_ms': round((end_time - start_time) * 1000, 2),
            'output': result.stdout,
            'error': result.stderr if result.returncode != 0 else None
        }
    except (subprocess.TimeoutExpired, Exception) as e:
        return {
            'host': host,
            'success': False,
            'error': str(e),
            'timeout': True
        }

def check_port(host, port, timeout=5):
    """Check if a port is open on a host"""
    try:
        start_time = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        end_time = time.time()
        sock.close()
        
        return {
            'host': host,
            'port': port,
            'open': result == 0,
            'response_time_ms': round((end_time - start_time) * 1000, 2)
        }
    except Exception as e:
        return {
            'host': host,
            'port': port,
            'open': False,
            'error': str(e)
        }

def get_network_interfaces():
    """Get network interface information"""
    interfaces = []
    try:
        import psutil
        for interface, addrs in psutil.net_if_addrs().items():
            interface_info = {
                'name': interface,
                'addresses': []
            }
            
            for addr in addrs:
                addr_info = {
                    'family': addr.family.name,
                    'address': addr.address,
                    'netmask': addr.netmask,
                    'broadcast': addr.broadcast
                }
                interface_info['addresses'].append(addr_info)
            
            interfaces.append(interface_info)
    except ImportError:
        interfaces.append({'error': 'psutil not available for interface enumeration'})
    
    return interfaces

def comprehensive_network_diagnostics():
    """Perform comprehensive network diagnostics"""
    diagnostics_report = {
        "timestamp": datetime.now().isoformat(),
        "network_interfaces": get_network_interfaces(),
        "connectivity_tests": {},
        "port_scans": {},
        "dns_tests": {},
        "performance_metrics": {}
    }
    
    # Test common public hosts
    test_hosts = [
        '8.8.8.8',          # Google DNS
        '1.1.1.1',          # Cloudflare DNS
        'google.com',       # Google
        'github.com',       # GitHub
        'microsoft.com',    # Microsoft
    ]
    
    print("Testing connectivity to common hosts...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        ping_futures = {executor.submit(ping_host, host): host for host in test_hosts}
        
        for future in as_completed(ping_futures):
            host = ping_futures[future]
            try:
                result = future.result()
                diagnostics_report["connectivity_tests"][host] = result
            except Exception as e:
                diagnostics_report["connectivity_tests"][host] = {
                    'host': host,
                    'success': False,
                    'error': str(e)
                }
    
    # Test common ports on a reliable host
    test_host = 'google.com'
    common_ports = [80, 443, 53, 22, 21, 25, 993, 995]
    
    print(f"Testing common ports on {test_host}...")
    with ThreadPoolExecutor(max_workers=8) as executor:
        port_futures = {executor.submit(check_port, test_host, port): port for port in common_ports}
        
        diagnostics_report["port_scans"][test_host] = {}
        for future in as_completed(port_futures):
            port = port_futures[future]
            try:
                result = future.result()
                diagnostics_report["port_scans"][test_host][str(port)] = result
            except Exception as e:
                diagnostics_report["port_scans"][test_host][str(port)] = {
                    'port': port,
                    'open': False,
                    'error': str(e)
                }
    
    # DNS resolution tests
    dns_test_domains = ['google.com', 'github.com', 'stackoverflow.com']
    
    print("Testing DNS resolution...")
    for domain in dns_test_domains:
        try:
            start_time = time.time()
            ip_addresses = socket.gethostbyname_ex(domain)
            end_time = time.time()
            
            diagnostics_report["dns_tests"][domain] = {
                'success': True,
                'ip_addresses': ip_addresses[2],
                'canonical_name': ip_addresses[0],
                'resolution_time_ms': round((end_time - start_time) * 1000, 2)
            }
        except socket.gaierror as e:
            diagnostics_report["dns_tests"][domain] = {
                'success': False,
                'error': str(e)
            }
    
    # Generate summary and recommendations
    successful_pings = sum(1 for test in diagnostics_report["connectivity_tests"].values() if test.get('success', False))
    total_ping_tests = len(diagnostics_report["connectivity_tests"])
    
    successful_dns = sum(1 for test in diagnostics_report["dns_tests"].values() if test.get('success', False))
    total_dns_tests = len(diagnostics_report["dns_tests"])
    
    diagnostics_report["summary"] = {
        'connectivity_success_rate': f"{successful_pings}/{total_ping_tests} ({(successful_pings/total_ping_tests*100):.1f}%)",
        'dns_success_rate': f"{successful_dns}/{total_dns_tests} ({(successful_dns/total_dns_tests*100):.1f}%)",
        'overall_status': 'good' if successful_pings >= total_ping_tests * 0.8 else 'issues_detected'
    }
    
    recommendations = []
    if successful_pings < total_ping_tests * 0.8:
        recommendations.append("Network connectivity issues detected - check internet connection")
    if successful_dns < total_dns_tests * 0.8:
        recommendations.append("DNS resolution issues detected - check DNS server configuration")
    if not recommendations:
        recommendations.append("Network connectivity appears to be functioning normally")
    
    diagnostics_report["recommendations"] = recommendations
    
    return diagnostics_report

def main(config=None):
    import os
    return comprehensive_network_diagnostics()
'''
            },
            {
                "id": "performance_optimizer",
                "name": "System Performance Optimizer",
                "description": "Analyze and optimize system performance",
                "category": AdminTaskCategory.PERFORMANCE_OPTIMIZATION,
                "requires_admin": True,
                "security_level": SecurityLevel.MEDIUM,
                "script_type": "python",
                "tags": ["performance", "optimization", "system"],
                "execution_time_estimate": "10-30 minutes",
                "script_content": '''
import os
import psutil
import json
from datetime import datetime
from collections import defaultdict

def analyze_system_performance():
    """Analyze system performance and provide optimization recommendations"""
    performance_report = {
        "timestamp": datetime.now().isoformat(),
        "system_info": {},
        "process_analysis": {},
        "resource_usage": {},
        "optimization_recommendations": [],
        "performance_score": 100
    }
    
    # Gather system information
    performance_report["system_info"] = {
        "platform": psutil.WINDOWS if os.name == 'nt' else "unix-like",
        "cpu_count": psutil.cpu_count(),
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
    }
    
    # Analyze resource usage
    cpu_percent = psutil.cpu_percent(interval=2)
    memory = psutil.virtual_memory()
    
    performance_report["resource_usage"] = {
        "cpu_usage_percent": cpu_percent,
        "memory_usage_percent": memory.percent,
        "memory_available_gb": round(memory.available / (1024**3), 2),
        "swap_usage_percent": psutil.swap_memory().percent
    }
    
    # Analyze top processes
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
        try:
            proc_info = proc.info
            if proc_info['cpu_percent'] is None:
                proc_info['cpu_percent'] = 0.0
            if proc_info['memory_percent'] is None:
                proc_info['memory_percent'] = 0.0
            processes.append(proc_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Sort by CPU usage
    top_cpu_processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:10]
    top_memory_processes = sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:10]
    
    performance_report["process_analysis"] = {
        "total_processes": len(processes),
        "top_cpu_processes": top_cpu_processes,
        "top_memory_processes": top_memory_processes
    }
    
    # Generate optimization recommendations
    recommendations = []
    
    if cpu_percent > 80:
        recommendations.append({
            "type": "cpu_optimization",
            "priority": "high",
            "description": f"High CPU usage detected ({cpu_percent:.1f}%)",
            "actions": [
                "Identify and optimize high-CPU processes",
                "Consider upgrading CPU or adding more cores",
                "Check for background processes consuming CPU"
            ]
        })
        performance_report["performance_score"] -= 20
    
    if memory.percent > 85:
        recommendations.append({
            "type": "memory_optimization",
            "priority": "high",
            "description": f"High memory usage detected ({memory.percent:.1f}%)",
            "actions": [
                "Close unnecessary applications",
                "Consider adding more RAM",
                "Check for memory leaks in applications"
            ]
        })
        performance_report["performance_score"] -= 15
    
    if psutil.swap_memory().percent > 50:
        recommendations.append({
            "type": "swap_optimization",
            "priority": "medium",
            "description": f"High swap usage detected ({psutil.swap_memory().percent:.1f}%)",
            "actions": [
                "Add more physical RAM",
                "Optimize applications to use less memory",
                "Consider SSD for swap file if using HDD"
            ]
        })
        performance_report["performance_score"] -= 10
    
    # Check for processes consuming excessive resources
    high_cpu_procs = [p for p in top_cpu_processes if p['cpu_percent'] > 25]
    if high_cpu_procs:
        proc_names = [p['name'] for p in high_cpu_procs[:3]]
        recommendations.append({
            "type": "process_optimization",
            "priority": "medium",
            "description": f"High-CPU processes detected: {', '.join(proc_names)}",
            "actions": [
                "Review if these processes are necessary",
                "Check for more efficient alternatives",
                "Consider process scheduling optimization"
            ]
        })
    
    # Disk usage analysis
    disk_recommendations = []
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            usage_percent = (usage.used / usage.total) * 100
            
            if usage_percent > 90:
                disk_recommendations.append(f"Disk {partition.mountpoint} is {usage_percent:.1f}% full")
                performance_report["performance_score"] -= 15
            elif usage_percent > 80:
                disk_recommendations.append(f"Disk {partition.mountpoint} is {usage_percent:.1f}% full - consider cleanup")
                performance_report["performance_score"] -= 5
        except PermissionError:
            continue
    
    if disk_recommendations:
        recommendations.append({
            "type": "disk_optimization",
            "priority": "high",
            "description": "Disk space issues detected",
            "actions": disk_recommendations + [
                "Run disk cleanup utilities",
                "Remove unnecessary files",
                "Consider disk expansion"
            ]
        })
    
    # General performance recommendations
    general_recommendations = {
        "type": "general_optimization",
        "priority": "low",
        "description": "General performance optimization suggestions",
        "actions": [
            "Keep system updated with latest patches",
            "Regularly restart system to clear memory",
            "Use SSD for system drive if possible",
            "Disable unnecessary startup programs",
            "Run regular system maintenance"
        ]
    }
    recommendations.append(general_recommendations)
    
    performance_report["optimization_recommendations"] = recommendations
    
    # Determine overall performance status
    if performance_report["performance_score"] >= 90:
        performance_report["performance_status"] = "excellent"
    elif performance_report["performance_score"] >= 70:
        performance_report["performance_status"] = "good"
    elif performance_report["performance_score"] >= 50:
        performance_report["performance_status"] = "needs_optimization"
    else:
        performance_report["performance_status"] = "critical"
    
    return performance_report

def main(config=None):
    return analyze_system_performance()
'''
            }
        ]
    
    async def get_system_health_comprehensive(self) -> Dict[str, Any]:
        """Get comprehensive system health using both original and enhanced methods"""
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "copilot_version": self.version,
            "sources": []
        }
        
        # Try to get health from original copilot
        if self.original_copilot:
            try:
                original_health = self.original_copilot.get_system_health()
                health_data["original_copilot"] = original_health
                health_data["sources"].append("original_copilot")
            except Exception as e:
                health_data["original_copilot_error"] = str(e)
        
        # Get enhanced health analysis
        try:
            enhanced_health = await self._run_plugin("system_health_analyzer")
            health_data["enhanced_analysis"] = enhanced_health
            health_data["sources"].append("enhanced_analysis")
        except Exception as e:
            health_data["enhanced_analysis_error"] = str(e)
        
        # Combine and normalize results
        if "original_copilot" in health_data and "enhanced_analysis" in health_data:
            # Combine scores
            original_score = health_data["original_copilot"].get("overall_score", 50)
            enhanced_score = health_data["enhanced_analysis"].get("analysis", {}).get("health_score", 50)
            health_data["combined_score"] = round((original_score + enhanced_score) / 2, 1)
        
        return health_data
    
    async def run_administrative_task(self, task_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run an administrative task using plugin system"""
        if task_id not in self.copilot_plugins:
            return {"error": f"Administrative task '{task_id}' not found"}
        
        plugin = self.copilot_plugins[task_id]
        
        # Log task execution
        task_record = {
            "task_id": task_id,
            "task_name": plugin.name,
            "started_at": datetime.now().isoformat(),
            "config": config or {},
            "user": "system"  # In production, this would be the actual user
        }
        
        try:
            result = await self._run_plugin(task_id, config)
            task_record["completed_at"] = datetime.now().isoformat()
            task_record["success"] = True
            task_record["result"] = result
            
            self.task_history.append(task_record)
            
            return {
                "success": True,
                "task_id": task_id,
                "result": result,
                "execution_time": (
                    datetime.fromisoformat(task_record["completed_at"]) - 
                    datetime.fromisoformat(task_record["started_at"])
                ).total_seconds()
            }
            
        except Exception as e:
            task_record["completed_at"] = datetime.now().isoformat()
            task_record["success"] = False
            task_record["error"] = str(e)
            
            self.task_history.append(task_record)
            
            return {
                "success": False,
                "task_id": task_id,
                "error": str(e)
            }
    
    async def _run_plugin(self, plugin_id: str, config: Dict[str, Any] = None) -> Any:
        """Execute a plugin in the appropriate sandbox"""
        if plugin_id not in self.copilot_plugins:
            raise ValueError(f"Plugin '{plugin_id}' not found")
        
        plugin = self.copilot_plugins[plugin_id]
        config = config or {}
        
        # If plugin framework is available, use sandboxed execution
        if self.plugin_framework:
            # Create temporary plugin file
            plugin_dir = self.plugin_directory / "temp" / plugin_id
            plugin_dir.mkdir(parents=True, exist_ok=True)
            
            # Create plugin.json metadata
            plugin_metadata = {
                "name": plugin.name,
                "version": plugin.version,
                "description": plugin.description,
                "security": {
                    "level": plugin.security_level.value,
                    "permissions": {
                        "can_read_files": True,
                        "can_write_files": plugin.requires_admin,
                        "can_execute_commands": plugin.requires_admin,
                        "can_access_network": "network" in plugin.tags
                    },
                    "limits": {
                        "max_memory_mb": 256 if plugin.requires_admin else 128,
                        "max_execution_time_seconds": 300 if "performance" in plugin.tags else 120
                    }
                }
            }
            
            with open(plugin_dir / "plugin.json", 'w') as f:
                json.dump(plugin_metadata, f, indent=2)
            
            # Create main.py with plugin code
            with open(plugin_dir / "main.py", 'w') as f:
                f.write(plugin.script_content)
            
            # Move to approved directory for loading
            approved_dir = self.plugin_framework.plugin_directory / "approved" / plugin_id
            if approved_dir.exists():
                import shutil
                shutil.rmtree(approved_dir)
            
            import shutil
            shutil.move(str(plugin_dir), str(approved_dir))
            
            # Load and execute plugin
            try:
                discovered = self.plugin_framework.discover_plugins()
                if plugin_id in discovered:
                    success = await self.plugin_framework.load_plugin(plugin_id, config)
                    if success:
                        plugin_info = self.plugin_framework.loaded_plugins[plugin_id]
                        return plugin_info['result']
                    else:
                        raise Exception("Plugin loading failed")
                else:
                    raise Exception("Plugin not discovered after creation")
            finally:
                # Clean up
                if approved_dir.exists():
                    import shutil
                    shutil.rmtree(approved_dir)
        
        else:
            # Fallback: direct execution (less secure)
            logger.warning("⚠️ Running plugin without sandbox - Plugin Framework v2.0 not available")
            
            # Create a temporary module and execute
            import tempfile
            import importlib.util
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(plugin.script_content)
                plugin_path = f.name
            
            try:
                spec = importlib.util.spec_from_file_location(f"temp_plugin_{plugin_id}", plugin_path)
                plugin_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(plugin_module)
                
                if hasattr(plugin_module, 'main'):
                    return plugin_module.main(config)
                else:
                    raise Exception("Plugin does not have a 'main' function")
            finally:
                os.unlink(plugin_path)
    
    def list_available_tasks(self, category: str = None) -> List[Dict[str, Any]]:
        """List all available administrative tasks"""
        tasks = []
        
        for plugin_id, plugin in self.copilot_plugins.items():
            if category is None or plugin.category == category:
                tasks.append({
                    "id": plugin_id,
                    "name": plugin.name,
                    "description": plugin.description,
                    "category": plugin.category,
                    "requires_admin": plugin.requires_admin,
                    "security_level": plugin.security_level.value,
                    "supported_platforms": plugin.supported_platforms,
                    "tags": plugin.tags,
                    "estimated_time": plugin.execution_time_estimate
                })
        
        return sorted(tasks, key=lambda x: (x["category"], x["name"]))
    
    def get_task_categories(self) -> List[Dict[str, Any]]:
        """Get available task categories with counts"""
        categories = {}
        
        for plugin in self.copilot_plugins.values():
            if plugin.category not in categories:
                categories[plugin.category] = {
                    "name": plugin.category,
                    "display_name": plugin.category.replace("_", " ").title(),
                    "count": 0,
                    "tasks": []
                }
            
            categories[plugin.category]["count"] += 1
            categories[plugin.category]["tasks"].append({
                "id": plugin.id,
                "name": plugin.name,
                "requires_admin": plugin.requires_admin
            })
        
        return list(categories.values())
    
    def get_task_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent task execution history"""
        return self.task_history[-limit:] if self.task_history else []
    
    async def suggest_maintenance_tasks(self) -> List[Dict[str, Any]]:
        """Get intelligent maintenance task suggestions"""
        suggestions = []
        
        try:
            # Get system health
            health_data = await self.get_system_health_comprehensive()
            
            # Analyze health data for suggestions
            if "enhanced_analysis" in health_data:
                analysis = health_data["enhanced_analysis"].get("analysis", {})
                health_score = analysis.get("health_score", 100)
                recommendations = analysis.get("recommendations", [])
                
                # Convert health recommendations to task suggestions
                for recommendation in recommendations:
                    if "disk" in recommendation.lower():
                        suggestions.append({
                            "task_id": "disk_cleanup_advanced",
                            "priority": "high",
                            "reason": recommendation,
                            "estimated_impact": "Free up 1-10GB of disk space"
                        })
                    elif "cpu" in recommendation.lower():
                        suggestions.append({
                            "task_id": "performance_optimizer",
                            "priority": "medium",
                            "reason": recommendation,
                            "estimated_impact": "Improve system responsiveness"
                        })
            
            # Always suggest regular maintenance
            suggestions.extend([
                {
                    "task_id": "system_health_analyzer",
                    "priority": "low",
                    "reason": "Regular health monitoring recommended",
                    "estimated_impact": "Early detection of system issues"
                },
                {
                    "task_id": "security_audit_basic",
                    "priority": "medium",
                    "reason": "Periodic security audit recommended",
                    "estimated_impact": "Identify security vulnerabilities"
                }
            ])
            
        except Exception as e:
            logger.error(f"Failed to generate maintenance suggestions: {e}")
        
        return suggestions
    
    async def generate_system_report(self) -> Dict[str, Any]:
        """Generate comprehensive system administration report"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "copilot_version": self.version,
            "report_id": hashlib.md5(f"{datetime.now().isoformat()}".encode()).hexdigest()[:8]
        }
        
        try:
            # System health
            report["system_health"] = await self.get_system_health_comprehensive()
            
            # Available tasks
            report["available_tasks"] = {
                "total_count": len(self.copilot_plugins),
                "categories": self.get_task_categories(),
                "recent_executions": len(self.task_history)
            }
            
            # Maintenance suggestions
            report["maintenance_suggestions"] = await self.suggest_maintenance_tasks()
            
            # Plugin framework status
            report["plugin_framework_status"] = {
                "available": PLUGIN_FRAMEWORK_AVAILABLE,
                "integrated": self.plugin_framework is not None,
                "plugin_count": len(self.plugin_framework.loaded_plugins) if self.plugin_framework else 0
            }
            
            # Task execution statistics
            if self.task_history:
                successful_tasks = len([t for t in self.task_history if t.get("success", False)])
                report["execution_statistics"] = {
                    "total_tasks_executed": len(self.task_history),
                    "successful_tasks": successful_tasks,
                    "success_rate_percent": round((successful_tasks / len(self.task_history)) * 100, 1),
                    "most_recent_task": self.task_history[-1]["started_at"]
                }
            
        except Exception as e:
            report["generation_error"] = str(e)
        
        return report

# Global instance for easy access
sysadmin_copilot_v2 = SysAdminCopilotV2()

async def main():
    """Example usage of SysAdmin Copilot v2.0"""
    logging.basicConfig(level=logging.INFO)
    
    copilot = SysAdminCopilotV2()
    
    print("🤖 SysAdmin Copilot v2.0 - Enhanced AI-Powered Administration")
    print("=" * 60)
    
    # List available tasks
    print("\n📋 Available Administrative Tasks:")
    categories = copilot.get_task_categories()
    for category in categories:
        print(f"  📁 {category['display_name']}: {category['count']} tasks")
        for task in category['tasks'][:2]:  # Show first 2 tasks per category
            admin_req = " [ADMIN]" if task['requires_admin'] else ""
            print(f"    • {task['name']}{admin_req}")
    
    # Run system health analysis
    print("\n🏥 System Health Analysis:")
    health_result = await copilot.get_system_health_comprehensive()
    if "enhanced_analysis" in health_result:
        analysis = health_result["enhanced_analysis"]["analysis"]
        print(f"  Health Score: {analysis['health_score']}/100")
        print(f"  Status: {analysis['status'].title()}")
        print(f"  Recommendations: {len(analysis['recommendations'])}")
    
    # Show maintenance suggestions
    print("\n💡 Maintenance Suggestions:")
    suggestions = await copilot.suggest_maintenance_tasks()
    for i, suggestion in enumerate(suggestions[:3], 1):
        print(f"  {i}. {suggestion['reason']} (Priority: {suggestion['priority']})")
    
    # Example task execution
    print("\n⚡ Running System Health Analyzer...")
    task_result = await copilot.run_administrative_task("system_health_analyzer")
    if task_result["success"]:
        print("  ✅ Task completed successfully")
        print(f"  ⏱️ Execution time: {task_result['execution_time']:.2f}s")
    else:
        print(f"  ❌ Task failed: {task_result['error']}")

if __name__ == "__main__":
    asyncio.run(main())
