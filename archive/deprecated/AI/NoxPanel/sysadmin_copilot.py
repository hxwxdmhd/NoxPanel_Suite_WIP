#!/usr/bin/env python3
"""
🤖 ULTIMATE SUITE v9.0 - SYSADMIN COPILOT
========================================

AI-powered system administration assistant with deep integration
for automated task execution, script generation, and system management.

Features:
- Intelligent task automation and suggestions
- Multi-platform script generation (PowerShell, Bash, Python)
- System health monitoring and optimization
- Proactive maintenance recommendations
- Step-by-step troubleshooting assistance
"""

import os
import sys
import json
import platform
import subprocess
import psutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import logging
import asyncio
import tempfile
from enum import Enum

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ScriptType(Enum):
    POWERSHELL = "powershell"
    BASH = "bash"
    PYTHON = "python"
    BATCH = "batch"

@dataclass
class SystemMetrics:
    """System performance and health metrics"""
    cpu_percent: float
    memory_percent: float
    disk_usage: Dict[str, float]
    network_io: Dict[str, int]
    process_count: int
    uptime_seconds: int
    load_average: Optional[List[float]] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class SysAdminTask:
    """Represents a system administration task"""
    id: str
    name: str
    description: str
    task_type: str
    priority: TaskPriority
    estimated_duration: int  # minutes
    
    # Task configuration
    target_system: str = "localhost"
    requires_sudo: bool = False
    script_content: Optional[str] = None
    script_type: Optional[ScriptType] = None
    
    # Execution tracking
    status: TaskStatus = TaskStatus.PENDING
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class ScriptTemplate:
    """Template for generating system administration scripts"""
    name: str
    description: str
    script_type: ScriptType
    template: str
    parameters: List[Dict[str, str]]
    category: str
    platform: List[str]  # windows, linux, macos
    
class SystemHealthMonitor:
    """Monitors system health and performance metrics"""
    
    def __init__(self):
        self.metrics_history: List[SystemMetrics] = []
        self.alert_thresholds = {
            'cpu_high': 80.0,
            'memory_high': 85.0,
            'disk_high': 90.0,
            'load_high': 2.0
        }
        
    def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk_usage = {}
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.mountpoint] = (usage.used / usage.total) * 100
                except (PermissionError, OSError):
                    continue
                    
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
            
            # Process count
            process_count = len(psutil.pids())
            
            # Uptime
            uptime_seconds = int(time.time() - psutil.boot_time())
            
            # Load average (Unix-like systems only)
            load_average = None
            if hasattr(os, 'getloadavg'):
                load_average = list(os.getloadavg())
                
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_usage=disk_usage,
                network_io=network_io,
                process_count=process_count,
                uptime_seconds=uptime_seconds,
                load_average=load_average
            )
            
            # Store in history (keep last 100 entries)
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > 100:
                self.metrics_history.pop(0)
                
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            raise
            
    def analyze_health(self, metrics: SystemMetrics) -> Dict[str, Any]:
        """Analyze system health and generate recommendations"""
        issues = []
        recommendations = []
        overall_score = 100
        
        # CPU analysis
        if metrics.cpu_percent > self.alert_thresholds['cpu_high']:
            issues.append({
                'type': 'high_cpu',
                'severity': 'high' if metrics.cpu_percent > 95 else 'medium',
                'message': f'CPU usage is high: {metrics.cpu_percent:.1f}%',
                'value': metrics.cpu_percent
            })
            recommendations.append("Consider identifying and optimizing high-CPU processes")
            overall_score -= 15
            
        # Memory analysis
        if metrics.memory_percent > self.alert_thresholds['memory_high']:
            issues.append({
                'type': 'high_memory',
                'severity': 'high' if metrics.memory_percent > 95 else 'medium',
                'message': f'Memory usage is high: {metrics.memory_percent:.1f}%',
                'value': metrics.memory_percent
            })
            recommendations.append("Consider closing unnecessary applications or adding more RAM")
            overall_score -= 10
            
        # Disk analysis
        for mount, usage in metrics.disk_usage.items():
            if usage > self.alert_thresholds['disk_high']:
                issues.append({
                    'type': 'high_disk',
                    'severity': 'critical' if usage > 95 else 'high',
                    'message': f'Disk {mount} is {usage:.1f}% full',
                    'value': usage,
                    'mount': mount
                })
                recommendations.append(f"Clean up disk space on {mount} or expand storage")
                overall_score -= 20
                
        # Load average analysis (Unix-like systems)
        if metrics.load_average and len(metrics.load_average) > 0:
            load_1min = metrics.load_average[0]
            cpu_count = psutil.cpu_count()
            
            if load_1min > cpu_count * self.alert_thresholds['load_high']:
                issues.append({
                    'type': 'high_load',
                    'severity': 'medium',
                    'message': f'Load average is high: {load_1min:.2f}',
                    'value': load_1min
                })
                recommendations.append("System load is high, consider optimizing running processes")
                overall_score -= 10
                
        # Process count analysis
        if metrics.process_count > 500:
            issues.append({
                'type': 'high_process_count',
                'severity': 'low',
                'message': f'High number of processes: {metrics.process_count}',
                'value': metrics.process_count
            })
            recommendations.append("Consider reviewing and cleaning up unnecessary processes")
            overall_score -= 5
            
        return {
            'overall_score': max(0, overall_score),
            'health_status': 'excellent' if overall_score >= 90 else 
                           'good' if overall_score >= 70 else
                           'warning' if overall_score >= 50 else 'critical',
            'issues': issues,
            'recommendations': recommendations,
            'metrics': asdict(metrics)
        }
        
    def get_metrics_trend(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """Get metrics trend over specified duration"""
        if not self.metrics_history:
            return {'error': 'No metrics history available'}
            
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        
        relevant_metrics = []
        for metrics in self.metrics_history:
            metrics_time = datetime.fromisoformat(metrics.timestamp)
            if metrics_time >= cutoff_time:
                relevant_metrics.append(metrics)
                
        if not relevant_metrics:
            return {'error': 'No metrics in specified time range'}
            
        # Calculate trends
        cpu_values = [m.cpu_percent for m in relevant_metrics]
        memory_values = [m.memory_percent for m in relevant_metrics]
        
        return {
            'duration_minutes': duration_minutes,
            'sample_count': len(relevant_metrics),
            'cpu_trend': {
                'current': cpu_values[-1],
                'average': sum(cpu_values) / len(cpu_values),
                'min': min(cpu_values),
                'max': max(cpu_values),
                'trend': 'increasing' if cpu_values[-1] > cpu_values[0] else 'decreasing'
            },
            'memory_trend': {
                'current': memory_values[-1],
                'average': sum(memory_values) / len(memory_values),
                'min': min(memory_values),
                'max': max(memory_values),
                'trend': 'increasing' if memory_values[-1] > memory_values[0] else 'decreasing'
            }
        }

class ScriptGenerator:
    """Generates system administration scripts based on natural language descriptions"""
    
    def __init__(self):
        self.templates = self._load_script_templates()
        
    def _load_script_templates(self) -> Dict[str, ScriptTemplate]:
        """Load predefined script templates"""
        templates = {}
        
        # PowerShell templates
        templates['windows_disk_cleanup'] = ScriptTemplate(
            name="Windows Disk Cleanup",
            description="Clean up temporary files and system cache",
            script_type=ScriptType.POWERSHELL,
            template="""
# Windows Disk Cleanup Script
Write-Host "Starting disk cleanup..."

# Clean temp files
$tempPaths = @(
    "$env:TEMP\\*",
    "$env:WINDIR\\Temp\\*",
    "$env:LOCALAPPDATA\\Temp\\*"
)

foreach ($path in $tempPaths) {
    try {
        Remove-Item -Path $path -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "Cleaned: $path"
    } catch {
        Write-Warning "Could not clean: $path"
    }
}

# Run disk cleanup utility
cleanmgr /sagerun:1

Write-Host "Disk cleanup completed!"
""",
            parameters=[],
            category="maintenance",
            platform=["windows"]
        )
        
        templates['linux_system_update'] = ScriptTemplate(
            name="Linux System Update",
            description="Update system packages and clean package cache",
            script_type=ScriptType.BASH,
            template="""#!/bin/bash
# Linux System Update Script
echo "Starting system update..."

# Detect package manager
if command -v apt &> /dev/null; then
    # Debian/Ubuntu
    echo "Updating package lists..."
    sudo apt update
    
    echo "Upgrading packages..."
    sudo apt upgrade -y
    
    echo "Cleaning package cache..."
    sudo apt autoremove -y
    sudo apt autoclean
    
elif command -v yum &> /dev/null; then
    # RHEL/CentOS
    echo "Updating packages..."
    sudo yum update -y
    
    echo "Cleaning package cache..."
    sudo yum clean all
    
elif command -v dnf &> /dev/null; then
    # Fedora
    echo "Updating packages..."
    sudo dnf update -y
    
    echo "Cleaning package cache..."
    sudo dnf clean all
    
else
    echo "Unsupported package manager"
    exit 1
fi

echo "System update completed!"
""",
            parameters=[],
            category="maintenance",
            platform=["linux"]
        )
        
        templates['network_diagnostics'] = ScriptTemplate(
            name="Network Diagnostics",
            description="Perform comprehensive network connectivity tests",
            script_type=ScriptType.PYTHON,
            template="""#!/usr/bin/env python3
import subprocess
import socket
import time
from datetime import datetime

def ping_host(host, count=3):
    '''Ping a host and return results'''
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.run(['ping', '-n', str(count), host], 
                                  capture_output=True, text=True)
        else:  # Unix-like
            result = subprocess.run(['ping', '-c', str(count), host], 
                                  capture_output=True, text=True)
        
        return {
            'host': host,
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr
        }
    except Exception as e:
        return {
            'host': host,
            'success': False,
            'error': str(e)
        }

def check_port(host, port, timeout=5):
    '''Check if a port is open on a host'''
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def main():
    print(f"Network Diagnostics - {datetime.now()}")
    print("=" * 50)
    
    # Test common hosts
    test_hosts = ['8.8.8.8', 'google.com', 'github.com']
    
    for host in test_hosts:
        print(f"\\nTesting {host}...")
        result = ping_host(host)
        if result['success']:
            print(f"✓ {host} is reachable")
        else:
            print(f"✗ {host} is not reachable")
            
    # Test common ports
    test_ports = [80, 443, 53, 22]
    test_host = 'google.com'
    
    print(f"\\nTesting ports on {test_host}...")
    for port in test_ports:
        if check_port(test_host, port):
            print(f"✓ Port {port} is open")
        else:
            print(f"✗ Port {port} is closed or filtered")
            
    print("\\nNetwork diagnostics completed!")

if __name__ == "__main__":
    import os
    main()
""",
            parameters=[],
            category="diagnostics",
            platform=["windows", "linux", "macos"]
        )
        
        return templates
        
    def generate_script(self, description: str, target_platform: str = None, 
                       script_type: ScriptType = None) -> Dict[str, Any]:
        """Generate a script based on natural language description"""
        
        if target_platform is None:
            target_platform = platform.system().lower()
            if target_platform == "darwin":
                target_platform = "macos"
                
        # Simple keyword matching for demonstration
        # In a real implementation, this would use AI/NLP
        keywords_to_templates = {
            'cleanup': ['windows_disk_cleanup'],
            'clean': ['windows_disk_cleanup'],
            'update': ['linux_system_update'],
            'upgrade': ['linux_system_update'],
            'network': ['network_diagnostics'],
            'ping': ['network_diagnostics'],
            'connectivity': ['network_diagnostics']
        }
        
        description_lower = description.lower()
        matching_templates = []
        
        for keyword, template_ids in keywords_to_templates.items():
            if keyword in description_lower:
                for template_id in template_ids:
                    template = self.templates.get(template_id)
                    if template and target_platform in template.platform:
                        matching_templates.append((template_id, template))
                        
        if not matching_templates:
            return {
                'error': 'No matching script template found',
                'description': description,
                'suggestions': list(self.templates.keys())
            }
            
        # Return the first matching template
        template_id, template = matching_templates[0]
        
        return {
            'template_id': template_id,
            'name': template.name,
            'description': template.description,
            'script_type': template.script_type.value,
            'script_content': template.template.strip(),
            'platform': template.platform,
            'category': template.category,
            'estimated_runtime': self._estimate_runtime(template),
            'requires_admin': self._requires_admin_privileges(template)
        }
        
    def _estimate_runtime(self, template: ScriptTemplate) -> str:
        """Estimate script runtime based on template analysis"""
        # Simple heuristic based on script content
        content = template.template.lower()
        
        if 'update' in content or 'upgrade' in content:
            return "5-30 minutes"
        elif 'cleanup' in content or 'clean' in content:
            return "2-10 minutes"
        elif 'ping' in content or 'network' in content:
            return "30 seconds - 2 minutes"
        else:
            return "1-5 minutes"
            
    def _requires_admin_privileges(self, template: ScriptTemplate) -> bool:
        """Check if script requires administrator privileges"""
        content = template.template.lower()
        admin_keywords = ['sudo', 'admin', 'elevated', 'runas', 'cleanmgr']
        
        return any(keyword in content for keyword in admin_keywords)

class TaskExecutor:
    """Executes system administration tasks safely"""
    
    def __init__(self):
        self.running_tasks: Dict[str, subprocess.Popen] = {}
        
    async def execute_task(self, task: SysAdminTask, confirm: bool = True) -> Dict[str, Any]:
        """Execute a system administration task"""
        
        if confirm:
            logger.info(f"Task execution requires confirmation: {task.name}")
            # In a real implementation, this would wait for user confirmation
            
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now().isoformat()
        
        try:
            if task.script_type == ScriptType.POWERSHELL:
                return await self._execute_powershell(task)
            elif task.script_type == ScriptType.BASH:
                return await self._execute_bash(task)
            elif task.script_type == ScriptType.PYTHON:
                return await self._execute_python(task)
            else:
                raise ValueError(f"Unsupported script type: {task.script_type}")
                
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now().isoformat()
            
            return {
                'success': False,
                'error': str(e),
                'task_id': task.id
            }
            
    async def _execute_powershell(self, task: SysAdminTask) -> Dict[str, Any]:
        """Execute PowerShell script"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False) as f:
            f.write(task.script_content)
            script_path = f.name
            
        try:
            cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', script_path]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            task.status = TaskStatus.COMPLETED if process.returncode == 0 else TaskStatus.FAILED
            task.completed_at = datetime.now().isoformat()
            
            result = {
                'success': process.returncode == 0,
                'return_code': process.returncode,
                'stdout': stdout.decode('utf-8', errors='ignore'),
                'stderr': stderr.decode('utf-8', errors='ignore'),
                'task_id': task.id
            }
            
            task.result = result
            return result
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(script_path)
            except OSError:
                pass
                
    async def _execute_bash(self, task: SysAdminTask) -> Dict[str, Any]:
        """Execute Bash script"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(task.script_content)
            script_path = f.name
            
        try:
            # Make script executable
            os.chmod(script_path, 0o755)
            
            process = await asyncio.create_subprocess_exec(
                '/bin/bash', script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            task.status = TaskStatus.COMPLETED if process.returncode == 0 else TaskStatus.FAILED
            task.completed_at = datetime.now().isoformat()
            
            result = {
                'success': process.returncode == 0,
                'return_code': process.returncode,
                'stdout': stdout.decode('utf-8', errors='ignore'),
                'stderr': stderr.decode('utf-8', errors='ignore'),
                'task_id': task.id
            }
            
            task.result = result
            return result
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(script_path)
            except OSError:
                pass
                
    async def _execute_python(self, task: SysAdminTask) -> Dict[str, Any]:
        """Execute Python script"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(task.script_content)
            script_path = f.name
            
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            task.status = TaskStatus.COMPLETED if process.returncode == 0 else TaskStatus.FAILED
            task.completed_at = datetime.now().isoformat()
            
            result = {
                'success': process.returncode == 0,
                'return_code': process.returncode,
                'stdout': stdout.decode('utf-8', errors='ignore'),
                'stderr': stderr.decode('utf-8', errors='ignore'),
                'task_id': task.id
            }
            
            task.result = result
            return result
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(script_path)
            except OSError:
                pass

class SysAdminCopilot:
    """Main SysAdmin Copilot class combining all functionality"""
    
    def __init__(self, ai_manager=None):
        self.health_monitor = SystemHealthMonitor()
        self.script_generator = ScriptGenerator()
        self.task_executor = TaskExecutor()
        self.ai_manager = ai_manager
        
        self.task_history: List[SysAdminTask] = []
        self.maintenance_schedule: List[Dict[str, Any]] = []
        
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health analysis"""
        try:
            metrics = self.health_monitor.collect_metrics()
            analysis = self.health_monitor.analyze_health(metrics)
            return analysis
        except Exception as e:
            return {
                'error': f'Failed to get system health: {str(e)}',
                'health_status': 'unknown'
            }
            
    def suggest_maintenance_tasks(self) -> List[Dict[str, Any]]:
        """Suggest maintenance tasks based on system analysis"""
        suggestions = []
        
        try:
            health = self.get_system_health()
            
            # Based on health issues, suggest tasks
            for issue in health.get('issues', []):
                if issue['type'] == 'high_disk':
                    suggestions.append({
                        'task_type': 'disk_cleanup',
                        'priority': 'high',
                        'description': f"Clean up disk space on {issue.get('mount', 'system drive')}",
                        'estimated_impact': 'Recover 1-5GB of disk space'
                    })
                    
                elif issue['type'] == 'high_memory':
                    suggestions.append({
                        'task_type': 'memory_optimization',
                        'priority': 'medium',
                        'description': "Optimize memory usage by cleaning up processes",
                        'estimated_impact': 'Reduce memory usage by 10-20%'
                    })
                    
                elif issue['type'] == 'high_cpu':
                    suggestions.append({
                        'task_type': 'process_analysis',
                        'priority': 'medium',
                        'description': "Analyze and optimize high-CPU processes",
                        'estimated_impact': 'Reduce CPU usage and improve responsiveness'
                    })
                    
            # Always suggest regular maintenance
            suggestions.append({
                'task_type': 'system_update',
                'priority': 'low',
                'description': "Update system packages and security patches",
                'estimated_impact': 'Improve security and stability'
            })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to suggest maintenance tasks: {e}")
            return []
            
    async def generate_and_execute_script(self, description: str, 
                                        auto_execute: bool = False) -> Dict[str, Any]:
        """Generate a script from description and optionally execute it"""
        
        try:
            # Generate script
            script_result = self.script_generator.generate_script(description)
            
            if 'error' in script_result:
                return script_result
                
            # Create task
            task = SysAdminTask(
                id=f"task_{int(time.time())}",
                name=script_result['name'],
                description=description,
                task_type='generated_script',
                priority=TaskPriority.MEDIUM,
                estimated_duration=5,
                script_content=script_result['script_content'],
                script_type=ScriptType(script_result['script_type']),
                requires_sudo=script_result.get('requires_admin', False)
            )
            
            self.task_history.append(task)
            
            result = {
                'script_generated': True,
                'task_id': task.id,
                'script_info': script_result,
                'task_details': asdict(task)
            }
            
            # Execute if requested
            if auto_execute:
                execution_result = await self.task_executor.execute_task(task, confirm=False)
                result['execution_result'] = execution_result
                result['executed'] = True
            else:
                result['executed'] = False
                result['message'] = 'Script generated successfully. Use execute_task() to run it.'
                
            return result
            
        except Exception as e:
            return {
                'error': f'Failed to generate/execute script: {str(e)}',
                'script_generated': False,
                'executed': False
            }
            
    async def execute_task_by_id(self, task_id: str) -> Dict[str, Any]:
        """Execute a task by its ID"""
        task = next((t for t in self.task_history if t.id == task_id), None)
        
        if not task:
            return {'error': f'Task {task_id} not found'}
            
        return await self.task_executor.execute_task(task)
        
    def get_task_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get task execution history"""
        return [asdict(task) for task in self.task_history[-limit:]]
        
    def get_system_metrics_trend(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """Get system metrics trend"""
        return self.health_monitor.get_metrics_trend(duration_minutes)
        
    async def ai_assisted_troubleshooting(self, problem_description: str) -> Dict[str, Any]:
        """Use AI to provide troubleshooting assistance"""
        if not self.ai_manager:
            return {'error': 'AI manager not available'}
            
        try:
            # Get current system state
            health = self.get_system_health()
            
            # Create troubleshooting prompt
            prompt = f"""
            System Problem: {problem_description}
            
            Current System State:
            - Health Status: {health.get('health_status', 'unknown')}
            - CPU Usage: {health.get('metrics', {}).get('cpu_percent', 'unknown')}%
            - Memory Usage: {health.get('metrics', {}).get('memory_percent', 'unknown')}%
            - Issues Found: {len(health.get('issues', []))}
            
            Please provide:
            1. Likely causes of this problem
            2. Step-by-step troubleshooting steps
            3. Recommended solutions
            4. Prevention measures
            
            Format your response with clear sections and actionable steps.
            """
            
            # Query first available AI model
            for model_key in self.ai_manager.models:
                try:
                    ai_response = await self.ai_manager.query_model(model_key, prompt)
                    if 'error' not in ai_response:
                        return {
                            'ai_analysis': ai_response.get('response', ''),
                            'model_used': model_key,
                            'system_state': health,
                            'timestamp': datetime.now().isoformat()
                        }
                except Exception as e:
                    logger.warning(f"AI model {model_key} failed: {e}")
                    continue
                    
            return {'error': 'No AI models available for troubleshooting'}
            
        except Exception as e:
            return {'error': f'AI troubleshooting failed: {str(e)}'}

if __name__ == "__main__":
    # Example usage
    async def main():
        logging.basicConfig(level=logging.INFO)
        
        # Create SysAdmin Copilot
        copilot = SysAdminCopilot()
        
        # Get system health
        health = copilot.get_system_health()
        print(f"System Health: {json.dumps(health, indent=2)}")
        
        # Suggest maintenance tasks
        suggestions = copilot.suggest_maintenance_tasks()
        print(f"Maintenance Suggestions: {json.dumps(suggestions, indent=2)}")
        
        # Generate script example
        script_result = await copilot.generate_and_execute_script(
            "Clean up temporary files and system cache",
            auto_execute=False
        )
        print(f"Generated Script: {json.dumps(script_result, indent=2)}")
        
    asyncio.run(main())
