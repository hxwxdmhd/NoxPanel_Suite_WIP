#!/usr/bin/env python3
"""
SysAdmin Copilot - AI-Powered System Administration Assistant

This module implements the core SysAdmin Copilot functionality as outlined in 
ENHANCED_ROADMAP_v9.md Priority #1. It provides AI-powered assistance for system 
administration tasks with deep integration into the Heimnetz framework.

Key Features:
- Automated task execution with AI suggestions
- Script generation for PowerShell, Bash, and Python
- Patch management with AI-assisted analysis
- Configuration management and optimization
- System health monitoring with AI insights
- Step-by-step troubleshooting assistance
"""

import asyncio
import json
import logging
import subprocess
import platform
import psutil
import hashlib
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ============================================================================
# SysAdmin Copilot Core Types and Enums
# ============================================================================

class TaskType(Enum):
    """Types of system administration tasks"""
    MAINTENANCE = "maintenance"         # System maintenance tasks
    MONITORING = "monitoring"          # System monitoring and health checks
    SECURITY = "security"              # Security-related tasks
    CONFIGURATION = "configuration"    # Configuration management
    TROUBLESHOOTING = "troubleshooting" # Problem diagnosis and resolution
    PATCH_MANAGEMENT = "patch_management" # System updates and patches
    PERFORMANCE = "performance"        # Performance optimization
    BACKUP = "backup"                  # Backup and recovery operations


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REQUIRES_CONFIRMATION = "requires_confirmation"


class ScriptType(Enum):
    """Supported script types"""
    POWERSHELL = "powershell"
    BASH = "bash"
    PYTHON = "python"
    CMD = "cmd"
    BATCH = "batch"


class SystemOS(Enum):
    """Supported operating systems"""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    UNIX = "unix"


@dataclass
class SystemContext:
    """System context information for AI decision making"""
    os_type: SystemOS
    os_version: str
    hostname: str
    cpu_count: int
    memory_total_gb: float
    disk_usage: Dict[str, float]  # Drive: usage percentage
    network_interfaces: List[str]
    running_services: List[str]
    installed_software: List[str]
    last_update: datetime
    uptime_hours: float
    current_user: str
    is_admin: bool


@dataclass
class Task:
    """System administration task"""
    id: str
    name: str
    description: str
    task_type: TaskType
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    
    # Execution details
    commands: List[str] = field(default_factory=list)
    script_content: str = ""
    script_type: Optional[ScriptType] = None
    
    # Requirements and dependencies
    requires_admin: bool = False
    requires_confirmation: bool = True
    prerequisites: List[str] = field(default_factory=list)
    
    # AI context
    ai_confidence: float = 0.0  # 0.0 to 1.0
    ai_reasoning: str = ""
    alternative_approaches: List[str] = field(default_factory=list)
    
    # Execution tracking
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_seconds: float = 0.0
    
    # Results
    success: bool = False
    output: str = ""
    error_message: str = ""
    exit_code: int = -1


@dataclass
class ScriptTemplate:
    """Template for generating scripts"""
    name: str
    description: str
    script_type: ScriptType
    template_content: str
    parameters: Dict[str, str] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


@dataclass
class TroubleshootingStep:
    """Step in troubleshooting process"""
    step_number: int
    title: str
    description: str
    command: str = ""
    expected_output: str = ""
    success_criteria: str = ""
    failure_actions: List[str] = field(default_factory=list)


@dataclass
class SystemHealthMetrics:
    """System health metrics"""
    timestamp: datetime
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    network_io_mbps: Tuple[float, float]  # (sent, received)
    process_count: int
    uptime_hours: float
    temperature_celsius: Optional[float] = None
    health_score: float = 100.0  # 0-100
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


# ============================================================================
# System Context Manager
# ============================================================================

class SystemContextManager:
    """
    Manages system context information for AI decision making.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("SystemContextManager")
        self._cached_context: Optional[SystemContext] = None
        self._cache_expiry: Optional[datetime] = None
        self._cache_duration = timedelta(minutes=5)  # Cache for 5 minutes
    
    async def get_system_context(self, force_refresh: bool = False) -> SystemContext:
        """
        Get comprehensive system context.
        
        Args:
            force_refresh: Force refresh of cached data
            
        Returns:
            SystemContext object with current system information
        """
        
        try:
            # Check cache validity
            if (not force_refresh and 
                self._cached_context and 
                self._cache_expiry and 
                datetime.now() < self._cache_expiry):
                return self._cached_context
            
            self.logger.info("Gathering system context information...")
            
            # Determine OS type
            os_name = platform.system().lower()
            if os_name == "windows":
                os_type = SystemOS.WINDOWS
            elif os_name == "linux":
                os_type = SystemOS.LINUX
            elif os_name == "darwin":
                os_type = SystemOS.MACOS
            else:
                os_type = SystemOS.UNIX
            
            # Get system information
            context = SystemContext(
                os_type=os_type,
                os_version=platform.platform(),
                hostname=platform.node(),
                cpu_count=psutil.cpu_count(),
                memory_total_gb=round(psutil.virtual_memory().total / (1024**3), 2),
                disk_usage=await self._get_disk_usage(),
                network_interfaces=await self._get_network_interfaces(),
                running_services=await self._get_running_services(),
                installed_software=await self._get_installed_software(),
                last_update=await self._get_last_update_time(),
                uptime_hours=round((datetime.now() - datetime.fromtimestamp(psutil.boot_time())).total_seconds() / 3600, 2),
                current_user=await self._get_current_user(),
                is_admin=await self._is_admin_user()
            )
            
            # Cache the context
            self._cached_context = context
            self._cache_expiry = datetime.now() + self._cache_duration
            
            self.logger.info(f"System context gathered: {context.os_type.value} {context.os_version}")
            return context
            
        except Exception as e:
            self.logger.error(f"Error gathering system context: {e}")
            # Return basic context
            return SystemContext(
                os_type=SystemOS.WINDOWS if platform.system() == "Windows" else SystemOS.LINUX,
                os_version=platform.platform(),
                hostname=platform.node(),
                cpu_count=1,
                memory_total_gb=1.0,
                disk_usage={},
                network_interfaces=[],
                running_services=[],
                installed_software=[],
                last_update=datetime.now(),
                uptime_hours=0.0,
                current_user="unknown",
                is_admin=False
            )
    
    async def _get_disk_usage(self) -> Dict[str, float]:
        """Get disk usage for all drives"""
        
        disk_usage = {}
        try:
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.device] = round((usage.used / usage.total) * 100, 2)
                except PermissionError:
                    continue
        except Exception as e:
            self.logger.warning(f"Error getting disk usage: {e}")
        
        return disk_usage
    
    async def _get_network_interfaces(self) -> List[str]:
        """Get network interface names"""
        
        try:
            interfaces = list(psutil.net_if_addrs().keys())
            return interfaces
        except Exception as e:
            self.logger.warning(f"Error getting network interfaces: {e}")
            return []
    
    async def _get_running_services(self) -> List[str]:
        """Get list of running services"""
        
        services = []
        try:
            # Get running processes as a proxy for services
            for proc in psutil.process_iter(['name']):
                try:
                    services.append(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Limit to unique service names
            return list(set(services))[:50]  # Limit to 50 for performance
            
        except Exception as e:
            self.logger.warning(f"Error getting running services: {e}")
            return []
    
    async def _get_installed_software(self) -> List[str]:
        """Get list of installed software"""
        
        # This would be more sophisticated in a real implementation
        # For now, return a basic list
        return ["python", "powershell", "cmd"]
    
    async def _get_last_update_time(self) -> datetime:
        """Get last system update time"""
        
        try:
            if platform.system() == "Windows":
                # Windows update check would go here
                return datetime.now() - timedelta(days=7)  # Placeholder
            else:
                # Linux update check would go here
                return datetime.now() - timedelta(days=3)  # Placeholder
        except Exception:
            return datetime.now() - timedelta(days=30)  # Default
    
    async def _get_current_user(self) -> str:
        """Get current user name"""
        
        try:
            import getpass
            return getpass.getuser()
        except Exception:
            return "unknown"
    
    async def _is_admin_user(self) -> bool:
        """Check if current user has admin privileges"""
        
        try:
            if platform.system() == "Windows":
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                import os
                return os.geteuid() == 0
        except Exception:
            return False


# ============================================================================
# Script Generator
# ============================================================================

class ScriptGenerator:
    """
    AI-powered script generation for various system administration tasks.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ScriptGenerator")
        self.templates = self._load_script_templates()
    
    def _load_script_templates(self) -> Dict[str, ScriptTemplate]:
        """Load script templates"""
        
        templates = {}
        
        # PowerShell templates
        templates["system_info_ps"] = ScriptTemplate(
            name="System Information",
            description="Get comprehensive system information",
            script_type=ScriptType.POWERSHELL,
            template_content='''
# System Information Script
Write-Host "=== System Information ===" -ForegroundColor Green

# Basic system info
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, TotalPhysicalMemory, CsProcessors

# Disk usage
Write-Host "`n=== Disk Usage ===" -ForegroundColor Yellow
Get-WmiObject -Class Win32_LogicalDisk | Select-Object DeviceID, @{Name="Size(GB)";Expression={[math]::Round($_.Size/1GB,2)}}, @{Name="FreeSpace(GB)";Expression={[math]::Round($_.FreeSpace/1GB,2)}}, @{Name="PercentFree";Expression={[math]::Round(($_.FreeSpace/$_.Size)*100,2)}}

# Running services
Write-Host "`n=== Top 10 Running Services ===" -ForegroundColor Cyan
Get-Service | Where-Object {$_.Status -eq "Running"} | Select-Object Name, Status -First 10

# Network configuration
Write-Host "`n=== Network Configuration ===" -ForegroundColor Magenta
Get-NetIPAddress | Where-Object {$_.IPAddress -notlike "169.254*" -and $_.IPAddress -notlike "fe80*"} | Select-Object InterfaceAlias, IPAddress, PrefixLength
''',
            tags=["system", "information", "diagnostics"]
        )
        
        templates["cleanup_temp_ps"] = ScriptTemplate(
            name="Cleanup Temporary Files",
            description="Clean up temporary files and folders",
            script_type=ScriptType.POWERSHELL,
            template_content='''
# Temporary Files Cleanup Script
Write-Host "=== Cleaning Temporary Files ===" -ForegroundColor Green

$tempPaths = @(
    "$env:TEMP",
    "$env:TMP",
    "C:\\Windows\\Temp",
    "$env:LOCALAPPDATA\\Temp"
)

$totalCleaned = 0

foreach ($path in $tempPaths) {
    if (Test-Path $path) {
        Write-Host "Cleaning: $path" -ForegroundColor Yellow
        try {
            $beforeSize = (Get-ChildItem $path -Recurse -File | Measure-Object -Property Length -Sum).Sum
            Get-ChildItem $path -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
            $afterSize = (Get-ChildItem $path -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            $cleaned = $beforeSize - $afterSize
            $totalCleaned += $cleaned
            Write-Host "Cleaned: $([math]::Round($cleaned/1MB,2)) MB from $path" -ForegroundColor Green
        } catch {
            Write-Host "Error cleaning $path: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

Write-Host "Total cleaned: $([math]::Round($totalCleaned/1MB,2)) MB" -ForegroundColor Cyan
''',
            tags=["cleanup", "maintenance", "disk space"]
        )
        
        # Bash templates
        templates["system_info_bash"] = ScriptTemplate(
            name="System Information",
            description="Get comprehensive system information",
            script_type=ScriptType.BASH,
            template_content='''#!/bin/bash
# System Information Script
echo "=== System Information ==="

# Basic system info
echo "Hostname: $(hostname)"
echo "OS: $(uname -s) $(uname -r)"
echo "Architecture: $(uname -m)"
echo "Uptime: $(uptime)"

# Memory information
echo -e "\n=== Memory Usage ==="
free -h

# Disk usage
echo -e "\n=== Disk Usage ==="
df -h

# CPU information
echo -e "\n=== CPU Information ==="
lscpu | grep -E "(Architecture|CPU\\(s\\)|Model name|CPU MHz)"

# Network interfaces
echo -e "\n=== Network Interfaces ==="
ip addr show | grep -E "(inet |inet6 )" | head -10

# Running processes (top 10 by memory)
echo -e "\n=== Top 10 Memory Consumers ==="
ps aux --sort=-%mem | head -11
''',
            tags=["system", "information", "linux", "diagnostics"]
        )
        
        # Python templates
        templates["health_monitor_py"] = ScriptTemplate(
            name="System Health Monitor",
            description="Monitor system health and performance",
            script_type=ScriptType.PYTHON,
            template_content='''#!/usr/bin/env python3
"""
System Health Monitor
Monitors system performance and generates health report
"""

import psutil
import time
from datetime import datetime

def get_system_health():
    """Get current system health metrics"""
    
    # CPU usage (average over 1 second)
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # Memory usage
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    
    # Disk usage
    disk = psutil.disk_usage('/')
    disk_percent = (disk.used / disk.total) * 100
    
    # Network I/O
    net_io = psutil.net_io_counters()
    
    # Running processes
    process_count = len(psutil.pids())
    
    # System uptime
    boot_time = psutil.boot_time()
    uptime = time.time() - boot_time
    
    return {
        'timestamp': datetime.now(),
        'cpu_percent': cpu_percent,
        'memory_percent': memory_percent,
        'disk_percent': disk_percent,
        'network_sent_mb': net_io.bytes_sent / (1024*1024),
        'network_recv_mb': net_io.bytes_recv / (1024*1024),
        'process_count': process_count,
        'uptime_hours': uptime / 3600
    }

def generate_health_report(metrics):
    """Generate health report from metrics"""
    
    print("=== System Health Report ===")
    print(f"Timestamp: {metrics['timestamp']}")
    print(f"CPU Usage: {metrics['cpu_percent']:.1f}%")
    print(f"Memory Usage: {metrics['memory_percent']:.1f}%")
    print(f"Disk Usage: {metrics['disk_percent']:.1f}%")
    print(f"Network Sent: {metrics['network_sent_mb']:.1f} MB")
    print(f"Network Received: {metrics['network_recv_mb']:.1f} MB")
    print(f"Running Processes: {metrics['process_count']}")
    print(f"System Uptime: {metrics['uptime_hours']:.1f} hours")
    
    # Health assessment
    issues = []
    if metrics['cpu_percent'] > 80:
        issues.append("High CPU usage detected")
    if metrics['memory_percent'] > 85:
        issues.append("High memory usage detected")
    if metrics['disk_percent'] > 90:
        issues.append("Low disk space warning")
    
    if issues:
        print("\\n=== Health Issues ===")
        for issue in issues:
            print(f"⚠️  {issue}")
    else:
        print("\\n✅ System health is good")

if __name__ == "__main__":
    metrics = get_system_health()
    generate_health_report(metrics)
''',
            tags=["monitoring", "health", "performance", "python"]
        )
        
        return templates
    
    async def generate_script(self, description: str, target_os: SystemOS, 
                            script_type: Optional[ScriptType] = None) -> Tuple[str, ScriptType, float]:
        """
        Generate script based on natural language description.
        
        Args:
            description: Natural language description of desired task
            target_os: Target operating system
            script_type: Preferred script type (optional)
            
        Returns:
            Tuple of (script_content, script_type, confidence)
        """
        
        try:
            self.logger.info(f"Generating script for: {description}")
            
            # Determine best script type if not specified
            if script_type is None:
                if target_os == SystemOS.WINDOWS:
                    script_type = ScriptType.POWERSHELL
                else:
                    script_type = ScriptType.BASH
            
            # Analyze description and find matching template
            best_template = await self._find_best_template(description, script_type)
            
            if best_template:
                # Use template as base
                script_content = best_template.template_content.strip()
                confidence = 0.8
                
                self.logger.info(f"Generated script using template: {best_template.name}")
                
            else:
                # Generate custom script
                script_content = await self._generate_custom_script(description, target_os, script_type)
                confidence = 0.6
                
                self.logger.info("Generated custom script")
            
            return script_content, script_type, confidence
            
        except Exception as e:
            self.logger.error(f"Error generating script: {e}")
            
            # Return basic error handling script
            if script_type == ScriptType.POWERSHELL:
                fallback_script = 'Write-Host "Script generation failed. Please check the task description." -ForegroundColor Red'
            else:
                fallback_script = 'echo "Script generation failed. Please check the task description."'
            
            return fallback_script, script_type or ScriptType.BASH, 0.3
    
    async def _find_best_template(self, description: str, script_type: ScriptType) -> Optional[ScriptTemplate]:
        """Find the best matching template for the description"""
        
        description_lower = description.lower()
        best_match = None
        best_score = 0.0
        
        for template in self.templates.values():
            if template.script_type != script_type:
                continue
            
            # Simple keyword matching
            score = 0.0
            for tag in template.tags:
                if tag in description_lower:
                    score += 1.0
            
            # Check template name and description
            if any(word in description_lower for word in template.name.lower().split()):
                score += 2.0
            
            if any(word in description_lower for word in template.description.lower().split()):
                score += 1.0
            
            if score > best_score:
                best_score = score
                best_match = template
        
        return best_match if best_score > 0 else None
    
    async def _generate_custom_script(self, description: str, target_os: SystemOS, 
                                    script_type: ScriptType) -> str:
        """Generate custom script based on description"""
        
        # This is a simplified implementation
        # In a real system, this would use an LLM or more sophisticated analysis
        
        description_lower = description.lower()
        
        if script_type == ScriptType.POWERSHELL:
            if "system" in description_lower and "info" in description_lower:
                return '''
Write-Host "System Information" -ForegroundColor Green
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion
Get-Process | Select-Object Name, CPU -First 10
'''
            elif "clean" in description_lower or "temp" in description_lower:
                return '''
Write-Host "Cleaning temporary files..." -ForegroundColor Yellow
Remove-Item $env:TEMP\\* -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "Cleanup completed" -ForegroundColor Green
'''
            else:
                return '''
Write-Host "Custom task execution" -ForegroundColor Cyan
# Add your custom PowerShell commands here
'''
        
        else:  # Bash
            if "system" in description_lower and "info" in description_lower:
                return '''#!/bin/bash
echo "System Information"
uname -a
free -h
df -h
'''
            elif "clean" in description_lower or "temp" in description_lower:
                return '''#!/bin/bash
echo "Cleaning temporary files..."
rm -rf /tmp/*
echo "Cleanup completed"
'''
            else:
                return '''#!/bin/bash
echo "Custom task execution"
# Add your custom bash commands here
'''


# ============================================================================
# System Health Monitor
# ============================================================================

class SystemHealthMonitor:
    """
    Proactive system health monitoring with AI insights.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("SystemHealthMonitor")
        self.metrics_history: List[SystemHealthMetrics] = []
        self.max_history = 100  # Keep last 100 metrics
    
    async def collect_metrics(self) -> SystemHealthMetrics:
        """Collect current system health metrics"""
        
        try:
            # Basic metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Disk usage (primary disk)
            disk = psutil.disk_usage('/' if platform.system() != 'Windows' else 'C:')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network I/O
            net_io = psutil.net_io_counters()
            
            # System uptime
            boot_time = psutil.boot_time()
            uptime_hours = (datetime.now().timestamp() - boot_time) / 3600
            
            # Create metrics object
            metrics = SystemHealthMetrics(
                timestamp=datetime.now(),
                cpu_usage_percent=cpu_percent,
                memory_usage_percent=memory.percent,
                disk_usage_percent=disk_percent,
                network_io_mbps=(net_io.bytes_sent / (1024*1024), net_io.bytes_recv / (1024*1024)),
                process_count=len(psutil.pids()),
                uptime_hours=uptime_hours
            )
            
            # Analyze health
            await self._analyze_health(metrics)
            
            # Add to history
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history:
                self.metrics_history.pop(0)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            
            # Return minimal metrics
            return SystemHealthMetrics(
                timestamp=datetime.now(),
                cpu_usage_percent=0.0,
                memory_usage_percent=0.0,
                disk_usage_percent=0.0,
                network_io_mbps=(0.0, 0.0),
                process_count=0,
                uptime_hours=0.0
            )
    
    async def _analyze_health(self, metrics: SystemHealthMetrics):
        """Analyze health metrics and generate insights"""
        
        issues = []
        recommendations = []
        health_score = 100.0
        
        # CPU analysis
        if metrics.cpu_usage_percent > 90:
            issues.append("Critical CPU usage - system may be unresponsive")
            recommendations.append("Identify and terminate high-CPU processes")
            health_score -= 30
        elif metrics.cpu_usage_percent > 80:
            issues.append("High CPU usage detected")
            recommendations.append("Monitor CPU-intensive processes")
            health_score -= 15
        elif metrics.cpu_usage_percent > 70:
            recommendations.append("CPU usage is elevated - consider monitoring")
            health_score -= 5
        
        # Memory analysis
        if metrics.memory_usage_percent > 95:
            issues.append("Critical memory usage - system may become unstable")
            recommendations.append("Free up memory or add more RAM")
            health_score -= 25
        elif metrics.memory_usage_percent > 85:
            issues.append("High memory usage detected")
            recommendations.append("Close unnecessary applications")
            health_score -= 10
        elif metrics.memory_usage_percent > 75:
            recommendations.append("Memory usage is elevated - monitor closely")
            health_score -= 3
        
        # Disk analysis
        if metrics.disk_usage_percent > 95:
            issues.append("Critical disk space - system may fail")
            recommendations.append("Free up disk space immediately")
            health_score -= 20
        elif metrics.disk_usage_percent > 90:
            issues.append("Low disk space warning")
            recommendations.append("Clean up unnecessary files")
            health_score -= 10
        elif metrics.disk_usage_percent > 80:
            recommendations.append("Disk usage is high - consider cleanup")
            health_score -= 5
        
        # Uptime analysis
        if metrics.uptime_hours > 24 * 30:  # 30 days
            recommendations.append("Consider restarting system for optimal performance")
            health_score -= 2
        
        # Process analysis
        if metrics.process_count > 300:
            recommendations.append("High number of processes - system may be slow")
            health_score -= 3
        
        # Update metrics
        metrics.health_score = max(0, health_score)
        metrics.issues = issues
        metrics.recommendations = recommendations
    
    async def get_health_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get health trends over specified time period"""
        
        if not self.metrics_history:
            return {"error": "No historical data available"}
        
        # Filter metrics by time period
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {"error": f"No data available for last {hours} hours"}
        
        # Calculate trends
        cpu_values = [m.cpu_usage_percent for m in recent_metrics]
        memory_values = [m.memory_usage_percent for m in recent_metrics]
        disk_values = [m.disk_usage_percent for m in recent_metrics]
        
        trends = {
            "period_hours": hours,
            "data_points": len(recent_metrics),
            "cpu": {
                "average": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values),
                "current": cpu_values[-1] if cpu_values else 0
            },
            "memory": {
                "average": sum(memory_values) / len(memory_values),
                "max": max(memory_values),
                "min": min(memory_values),
                "current": memory_values[-1] if memory_values else 0
            },
            "disk": {
                "average": sum(disk_values) / len(disk_values),
                "max": max(disk_values),
                "min": min(disk_values),
                "current": disk_values[-1] if disk_values else 0
            },
            "health_score": recent_metrics[-1].health_score if recent_metrics else 0,
            "issues_count": len(recent_metrics[-1].issues) if recent_metrics else 0
        }
        
        return trends


# ============================================================================
# Task Execution Engine
# ============================================================================

class TaskExecutionEngine:
    """
    Executes system administration tasks with safety controls.
    """
    
    def __init__(self, context_manager: SystemContextManager):
        self.context_manager = context_manager
        self.logger = logging.getLogger("TaskExecutionEngine")
        self.active_tasks: Dict[str, Task] = {}
    
    async def execute_task(self, task: Task, confirm: bool = True) -> Task:
        """
        Execute a system administration task.
        
        Args:
            task: Task to execute
            confirm: Whether to require confirmation for dangerous operations
            
        Returns:
            Updated task with execution results
        """
        
        try:
            self.logger.info(f"Executing task: {task.name}")
            
            # Check if task requires confirmation
            if task.requires_confirmation and confirm:
                task.status = TaskStatus.REQUIRES_CONFIRMATION
                return task
            
            # Validate prerequisites
            if not await self._validate_prerequisites(task):
                task.status = TaskStatus.FAILED
                task.error_message = "Prerequisites not met"
                return task
            
            # Check admin requirements
            context = await self.context_manager.get_system_context()
            if task.requires_admin and not context.is_admin:
                task.status = TaskStatus.FAILED
                task.error_message = "Task requires administrator privileges"
                return task
            
            # Update task status
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            self.active_tasks[task.id] = task
            
            # Execute based on task type
            if task.script_content:
                await self._execute_script(task)
            elif task.commands:
                await self._execute_commands(task)
            else:
                task.status = TaskStatus.FAILED
                task.error_message = "No executable content in task"
                return task
            
            # Update completion time
            task.completed_at = datetime.now()
            task.execution_time_seconds = (task.completed_at - task.started_at).total_seconds()
            
            # Remove from active tasks
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]
            
            self.logger.info(f"Task completed: {task.name} ({'SUCCESS' if task.success else 'FAILED'})")
            
            return task
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
            
            if task.started_at:
                task.execution_time_seconds = (task.completed_at - task.started_at).total_seconds()
            
            # Remove from active tasks
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]
            
            self.logger.error(f"Task execution failed: {task.name} - {e}")
            
            return task
    
    async def _validate_prerequisites(self, task: Task) -> bool:
        """Validate task prerequisites"""
        
        if not task.prerequisites:
            return True
        
        context = await self.context_manager.get_system_context()
        
        for prerequisite in task.prerequisites:
            # Check various prerequisites
            if prerequisite.startswith("os:"):
                required_os = prerequisite.split(":", 1)[1]
                if context.os_type.value != required_os.lower():
                    self.logger.error(f"OS prerequisite not met: required {required_os}, got {context.os_type.value}")
                    return False
            
            elif prerequisite.startswith("admin"):
                if not context.is_admin:
                    self.logger.error("Admin privilege prerequisite not met")
                    return False
            
            elif prerequisite.startswith("disk_space:"):
                required_gb = float(prerequisite.split(":", 1)[1])
                # Check if any disk has enough free space (simplified)
                # In reality, would check specific disk requirements
                
        return True
    
    async def _execute_script(self, task: Task):
        """Execute script content"""
        
        try:
            # Create temporary script file
            script_extension = {
                ScriptType.POWERSHELL: ".ps1",
                ScriptType.BASH: ".sh",
                ScriptType.PYTHON: ".py",
                ScriptType.CMD: ".cmd",
                ScriptType.BATCH: ".bat"
            }.get(task.script_type, ".txt")
            
            with tempfile.NamedTemporaryFile(mode='w', suffix=script_extension, delete=False) as f:
                f.write(task.script_content)
                script_path = f.name
            
            try:
                # Determine execution command
                if task.script_type == ScriptType.POWERSHELL:
                    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path]
                elif task.script_type == ScriptType.PYTHON:
                    cmd = ["python", script_path]
                elif task.script_type == ScriptType.BASH:
                    cmd = ["bash", script_path]
                else:
                    cmd = [script_path]  # Direct execution for batch/cmd
                
                # Execute script
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                    cwd=Path.cwd()
                )
                
                task.output = result.stdout
                task.error_message = result.stderr
                task.exit_code = result.returncode
                task.success = result.returncode == 0
                task.status = TaskStatus.COMPLETED if task.success else TaskStatus.FAILED
                
            finally:
                # Clean up temporary file
                try:
                    Path(script_path).unlink()
                except Exception:
                    pass
            
        except subprocess.TimeoutExpired:
            task.status = TaskStatus.FAILED
            task.error_message = "Script execution timed out"
            task.exit_code = -1
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = f"Script execution error: {e}"
            task.exit_code = -1
    
    async def _execute_commands(self, task: Task):
        """Execute list of commands"""
        
        outputs = []
        overall_success = True
        
        for i, command in enumerate(task.commands):
            try:
                self.logger.info(f"Executing command {i+1}/{len(task.commands)}: {command}")
                
                result = subprocess.run(
                    command.split(),
                    capture_output=True,
                    text=True,
                    timeout=60,  # 1 minute timeout per command
                    cwd=Path.cwd()
                )
                
                command_output = f"Command: {command}\nExit Code: {result.returncode}\nOutput: {result.stdout}"
                if result.stderr:
                    command_output += f"\nError: {result.stderr}"
                
                outputs.append(command_output)
                
                if result.returncode != 0:
                    overall_success = False
                    
            except subprocess.TimeoutExpired:
                outputs.append(f"Command: {command}\nError: Timeout")
                overall_success = False
                
            except Exception as e:
                outputs.append(f"Command: {command}\nError: {e}")
                overall_success = False
        
        task.output = "\n\n".join(outputs)
        task.success = overall_success
        task.status = TaskStatus.COMPLETED if overall_success else TaskStatus.FAILED
    
    def get_active_tasks(self) -> List[Task]:
        """Get list of currently active tasks"""
        
        return list(self.active_tasks.values())
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel an active task"""
        
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            
            if task.started_at:
                task.execution_time_seconds = (task.completed_at - task.started_at).total_seconds()
            
            del self.active_tasks[task_id]
            
            self.logger.info(f"Task cancelled: {task.name}")
            return True
        
        return False


# ============================================================================
# SysAdmin Copilot Core
# ============================================================================

class SysAdminCopilot:
    """
    Main SysAdmin Copilot class providing AI-powered system administration assistance.
    """
    
    def __init__(self):
        self.context_manager = SystemContextManager()
        self.script_generator = ScriptGenerator()
        self.health_monitor = SystemHealthMonitor()
        self.task_executor = TaskExecutionEngine(self.context_manager)
        
        self.task_templates: Dict[str, Dict[str, Any]] = {}
        self.task_history: List[Task] = []
        
        self.logger = logging.getLogger("SysAdminCopilot")
        self.logger.info("SysAdmin Copilot initialized")
        
        # Initialize task templates
        self._initialize_task_templates()
    
    def _initialize_task_templates(self):
        """Initialize common task templates"""
        
        self.task_templates = {
            "system_info": {
                "name": "Get System Information",
                "description": "Gather comprehensive system information and status",
                "task_type": TaskType.MONITORING,
                "priority": TaskPriority.LOW,
                "requires_admin": False,
                "ai_confidence": 0.9
            },
            "disk_cleanup": {
                "name": "Disk Cleanup",
                "description": "Clean up temporary files and free disk space",
                "task_type": TaskType.MAINTENANCE,
                "priority": TaskPriority.MEDIUM,
                "requires_admin": True,
                "ai_confidence": 0.8
            },
            "health_check": {
                "name": "System Health Check",
                "description": "Perform comprehensive system health analysis",
                "task_type": TaskType.MONITORING,
                "priority": TaskPriority.MEDIUM,
                "requires_admin": False,
                "ai_confidence": 0.9
            },
            "security_scan": {
                "name": "Basic Security Scan",
                "description": "Perform basic security checks and analysis",
                "task_type": TaskType.SECURITY,
                "priority": TaskPriority.HIGH,
                "requires_admin": True,
                "ai_confidence": 0.7
            }
        }
    
    # ========================================================================
    # Task Suggestion and Management
    # ========================================================================
    
    async def suggest_tasks(self, context_description: str = "") -> List[Task]:
        """
        Analyze system state and suggest maintenance tasks.
        
        Args:
            context_description: Additional context for task suggestions
            
        Returns:
            List of suggested tasks
        """
        
        try:
            self.logger.info("Analyzing system and suggesting tasks...")
            
            # Get current system context
            context = await self.context_manager.get_system_context()
            
            # Collect health metrics
            health_metrics = await self.health_monitor.collect_metrics()
            
            # Generate task suggestions based on analysis
            suggestions = []
            
            # Always suggest basic health check
            suggestions.append(await self._create_task_from_template(
                "health_check", 
                context_description or "Regular system health monitoring"
            ))
            
            # Suggest disk cleanup if disk usage is high
            for drive, usage in context.disk_usage.items():
                if usage > 80:
                    suggestions.append(await self._create_task_from_template(
                        "disk_cleanup",
                        f"High disk usage detected on {drive} ({usage:.1f}%)"
                    ))
                    break
            
            # Suggest system info if no recent context
            if not context_description:
                suggestions.append(await self._create_task_from_template(
                    "system_info",
                    "Get current system status and information"
                ))
            
            # Suggest security scan if system hasn't been updated recently
            days_since_update = (datetime.now() - context.last_update).days
            if days_since_update > 7:
                suggestions.append(await self._create_task_from_template(
                    "security_scan",
                    f"System hasn't been updated in {days_since_update} days"
                ))
            
            # AI-based suggestions based on health issues
            if health_metrics.issues:
                for issue in health_metrics.issues:
                    if "CPU" in issue:
                        task = Task(
                            id=hashlib.md5(f"cpu_analysis_{datetime.now()}".encode()).hexdigest()[:8],
                            name="CPU Usage Analysis",
                            description="Analyze high CPU usage and identify problematic processes",
                            task_type=TaskType.TROUBLESHOOTING,
                            priority=TaskPriority.HIGH,
                            ai_confidence=0.8,
                            ai_reasoning=f"Suggested due to: {issue}"
                        )
                        
                        # Generate script for CPU analysis
                        context_os = context.os_type
                        script_content, script_type, confidence = await self.script_generator.generate_script(
                            "analyze CPU usage and show top CPU consuming processes",
                            context_os
                        )
                        
                        task.script_content = script_content
                        task.script_type = script_type
                        task.ai_confidence = min(task.ai_confidence, confidence)
                        
                        suggestions.append(task)
            
            self.logger.info(f"Generated {len(suggestions)} task suggestions")
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error suggesting tasks: {e}")
            return []
    
    async def _create_task_from_template(self, template_key: str, description: str) -> Task:
        """Create task from template"""
        
        template = self.task_templates.get(template_key, {})
        
        task = Task(
            id=hashlib.md5(f"{template_key}_{datetime.now()}".encode()).hexdigest()[:8],
            name=template.get("name", "Unknown Task"),
            description=description,
            task_type=TaskType(template.get("task_type", "maintenance")),
            priority=TaskPriority(template.get("priority", "medium")),
            requires_admin=template.get("requires_admin", False),
            ai_confidence=template.get("ai_confidence", 0.5)
        )
        
        # Generate script content
        context = await self.context_manager.get_system_context()
        script_content, script_type, confidence = await self.script_generator.generate_script(
            task.description,
            context.os_type
        )
        
        task.script_content = script_content
        task.script_type = script_type
        task.ai_confidence = min(task.ai_confidence, confidence)
        
        return task
    
    # ========================================================================
    # Script Generation Interface
    # ========================================================================
    
    async def generate_script(self, description: str, target_os: str = None) -> Dict[str, Any]:
        """
        Generate script from natural language description.
        
        Args:
            description: Natural language description of desired task
            target_os: Target operating system (optional)
            
        Returns:
            Dictionary containing script information
        """
        
        try:
            # Determine target OS
            if target_os:
                try:
                    os_type = SystemOS(target_os.lower())
                except ValueError:
                    # Default to current OS if invalid OS specified
                    context = await self.context_manager.get_system_context()
                    os_type = context.os_type
            else:
                context = await self.context_manager.get_system_context()
                os_type = context.os_type
            
            # Generate script
            script_content, script_type, confidence = await self.script_generator.generate_script(
                description, os_type
            )
            
            return {
                "success": True,
                "description": description,
                "target_os": os_type.value,
                "script_type": script_type.value,
                "script_content": script_content,
                "confidence": confidence,
                "estimated_execution_time": "< 1 minute",  # Placeholder
                "requires_admin": self._requires_admin_privileges(description),
                "safety_level": self._assess_safety_level(description, script_content)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating script: {e}")
            return {
                "success": False,
                "error": str(e),
                "description": description
            }
    
    def _requires_admin_privileges(self, description: str) -> bool:
        """Determine if task requires admin privileges"""
        
        admin_keywords = [
            "install", "uninstall", "service", "registry", "system", 
            "driver", "update", "patch", "firewall", "security", "admin"
        ]
        
        return any(keyword in description.lower() for keyword in admin_keywords)
    
    def _assess_safety_level(self, description: str, script_content: str) -> str:
        """Assess safety level of script"""
        
        dangerous_keywords = [
            "delete", "remove", "format", "registry", "system32",
            "rm -rf", "del /s", "rmdir"
        ]
        
        if any(keyword in description.lower() or keyword in script_content.lower() 
               for keyword in dangerous_keywords):
            return "high_risk"
        elif any(keyword in description.lower() for keyword in ["install", "update", "modify"]):
            return "medium_risk"
        else:
            return "low_risk"
    
    # ========================================================================
    # Task Execution Interface
    # ========================================================================
    
    async def execute_task(self, task: Task, confirm: bool = True) -> Task:
        """
        Execute a system administration task.
        
        Args:
            task: Task to execute
            confirm: Whether to require confirmation for dangerous operations
            
        Returns:
            Updated task with execution results
        """
        
        try:
            # Add to history
            self.task_history.append(task)
            
            # Execute task
            executed_task = await self.task_executor.execute_task(task, confirm)
            
            # Update history
            for i, hist_task in enumerate(self.task_history):
                if hist_task.id == executed_task.id:
                    self.task_history[i] = executed_task
                    break
            
            return executed_task
            
        except Exception as e:
            self.logger.error(f"Error executing task: {e}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            return task
    
    # ========================================================================
    # System Health and Monitoring
    # ========================================================================
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get current system health analysis with AI insights"""
        
        try:
            # Collect metrics
            metrics = await self.health_monitor.collect_metrics()
            
            # Get system context
            context = await self.context_manager.get_system_context()
            
            # Generate AI insights
            insights = await self._generate_health_insights(metrics, context)
            
            return {
                "timestamp": metrics.timestamp.isoformat(),
                "health_score": metrics.health_score,
                "metrics": {
                    "cpu_usage": metrics.cpu_usage_percent,
                    "memory_usage": metrics.memory_usage_percent,
                    "disk_usage": metrics.disk_usage_percent,
                    "process_count": metrics.process_count,
                    "uptime_hours": metrics.uptime_hours
                },
                "issues": metrics.issues,
                "recommendations": metrics.recommendations,
                "ai_insights": insights,
                "system_context": {
                    "os": context.os_type.value,
                    "hostname": context.hostname,
                    "is_admin": context.is_admin
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system health: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _generate_health_insights(self, metrics: SystemHealthMetrics, 
                                      context: SystemContext) -> List[str]:
        """Generate AI insights from health metrics"""
        
        insights = []
        
        # Performance insights
        if metrics.cpu_usage_percent > 50:
            insights.append(f"CPU usage at {metrics.cpu_usage_percent:.1f}% - consider monitoring background processes")
        
        if metrics.memory_usage_percent > 75:
            insights.append(f"Memory usage at {metrics.memory_usage_percent:.1f}% - may benefit from cleanup or more RAM")
        
        # Uptime insights
        if metrics.uptime_hours > 24 * 7:  # 1 week
            insights.append(f"System uptime is {metrics.uptime_hours/24:.1f} days - consider restart for optimal performance")
        
        # Context-based insights
        if context.os_type == SystemOS.WINDOWS:
            if metrics.process_count > 150:
                insights.append("High process count detected - typical for Windows but may indicate resource usage")
        else:
            if metrics.process_count > 200:
                insights.append("High process count detected - may indicate heavy system load")
        
        # Disk space insights
        if metrics.disk_usage_percent > 85:
            insights.append("Disk space is critically low - immediate cleanup recommended")
        elif metrics.disk_usage_percent > 70:
            insights.append("Disk space usage is high - consider cleanup maintenance")
        
        return insights
    
    # ========================================================================
    # Information and Statistics
    # ========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get SysAdmin Copilot statistics"""
        
        completed_tasks = [t for t in self.task_history if t.status == TaskStatus.COMPLETED]
        failed_tasks = [t for t in self.task_history if t.status == TaskStatus.FAILED]
        
        return {
            "total_tasks": len(self.task_history),
            "completed_tasks": len(completed_tasks),
            "failed_tasks": len(failed_tasks),
            "success_rate": len(completed_tasks) / len(self.task_history) if self.task_history else 0.0,
            "active_tasks": len(self.task_executor.get_active_tasks()),
            "average_execution_time": sum(t.execution_time_seconds for t in completed_tasks) / len(completed_tasks) if completed_tasks else 0.0,
            "task_types": {
                task_type.value: sum(1 for t in self.task_history if t.task_type == task_type)
                for task_type in TaskType
            }
        }
    
    def get_task_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get task execution history"""
        
        recent_tasks = self.task_history[-limit:] if limit else self.task_history
        
        return [
            {
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "type": task.task_type.value,
                "priority": task.priority.value,
                "status": task.status.value,
                "success": task.success,
                "created_at": task.created_at.isoformat(),
                "execution_time": task.execution_time_seconds,
                "ai_confidence": task.ai_confidence
            }
            for task in recent_tasks
        ]


# ============================================================================
# Example Usage and Testing
# ============================================================================

async def main():
    """Example usage of the SysAdmin Copilot"""
    
    print("🤖 SysAdmin Copilot - AI-Powered System Administration Assistant")
    print("=" * 80)
    
    # Initialize copilot
    copilot = SysAdminCopilot()
    
    # Get system health
    print("\n📊 System Health Analysis:")
    health = await copilot.get_system_health()
    print(f"Health Score: {health['health_score']:.1f}/100")
    print(f"CPU Usage: {health['metrics']['cpu_usage']:.1f}%")
    print(f"Memory Usage: {health['metrics']['memory_usage']:.1f}%")
    print(f"Disk Usage: {health['metrics']['disk_usage']:.1f}%")
    
    if health['issues']:
        print("\n⚠️  Issues Detected:")
        for issue in health['issues']:
            print(f"  - {issue}")
    
    if health['recommendations']:
        print("\n💡 Recommendations:")
        for rec in health['recommendations']:
            print(f"  - {rec}")
    
    # Get task suggestions
    print(f"\n🎯 Task Suggestions:")
    suggestions = await copilot.suggest_tasks("System maintenance check")
    
    for i, task in enumerate(suggestions[:3], 1):
        print(f"{i}. {task.name}")
        print(f"   Description: {task.description}")
        print(f"   Type: {task.task_type.value}")
        print(f"   AI Confidence: {task.ai_confidence:.1f}")
        print()
    
    # Generate a custom script
    print("📝 Script Generation Example:")
    script_result = await copilot.generate_script("Show running processes sorted by memory usage")
    
    if script_result['success']:
        print(f"Script Type: {script_result['script_type']}")
        print(f"Confidence: {script_result['confidence']:.1f}")
        print(f"Safety Level: {script_result['safety_level']}")
        print("Generated Script:")
        print("=" * 40)
        print(script_result['script_content'][:200] + "..." if len(script_result['script_content']) > 200 else script_result['script_content'])
        print("=" * 40)
    
    # Execute a simple task
    if suggestions:
        print(f"\n⚡ Executing Example Task: {suggestions[0].name}")
        
        # Execute first suggestion (typically health check)
        result = await copilot.execute_task(suggestions[0], confirm=False)
        
        print(f"Status: {result.status.value}")
        if result.success:
            print("✅ Task completed successfully!")
            if result.output:
                print("Output preview:")
                print(result.output[:300] + "..." if len(result.output) > 300 else result.output)
        else:
            print("❌ Task failed")
            if result.error_message:
                print(f"Error: {result.error_message}")
    
    # Show statistics
    print(f"\n📈 Copilot Statistics:")
    stats = copilot.get_statistics()
    print(f"Total Tasks: {stats['total_tasks']}")
    print(f"Success Rate: {stats['success_rate']:.1%}")
    print(f"Average Execution Time: {stats['average_execution_time']:.2f}s")
    
    print("\n🎉 SysAdmin Copilot demonstration complete!")


if __name__ == "__main__":
    asyncio.run(main())

