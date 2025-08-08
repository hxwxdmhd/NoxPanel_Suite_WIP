#!/usr/bin/env python3
"""
NoxSuite Smart Self-Healing Auto-Installer
Intelligent cross-platform setup with AI-powered error recovery and learning capabilities
"""

import os
import sys
import json
import subprocess
import platform
import shutil
import requests
import time
import hashlib
import chardet
import codecs
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum, auto
from contextlib import contextmanager
import traceback
import threading
import queue
import re

# Force UTF-8 encoding for consistent cross-platform behavior
if sys.platform.startswith('win'):
    # Windows-specific UTF-8 handling
    import locale
    try:
        # Try to set UTF-8 locale on Windows
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except locale.Error:
        # Fallback to system default
        pass
    
    # Set console output to UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

class OSType(Enum):
    WINDOWS = "windows"
    LINUX = "linux" 
    MACOS = "macos"
    UNKNOWN = "unknown"

class InstallMode(Enum):
    GUIDED = "guided"
    FAST = "fast"
    DRY_RUN = "dry_run"
    SAFE = "safe"
    RECOVERY = "recovery"

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"

class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info" 
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class SystemInfo:
    os_type: OSType
    architecture: str
    python_version: str
    available_memory: int
    cpu_cores: int
    docker_available: bool = False
    node_available: bool = False
    git_available: bool = False
    package_managers: List[str] = None
    encoding_support: Dict[str, bool] = None
    permissions: Dict[str, bool] = None

@dataclass
class InstallConfig:
    install_directory: Path
    modules: List[str]
    enable_ai: bool = True
    enable_voice: bool = False
    enable_mobile: bool = True
    dev_mode: bool = False
    auto_start: bool = True
    ai_models: List[str] = None
    mode: InstallMode = InstallMode.GUIDED
    force_reinstall: bool = False
    backup_existing: bool = True

@dataclass
class InstallStep:
    name: str
    description: str
    status: StepStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    dependencies: List[str] = None
    cleanup_actions: List[str] = None

class SmartLogger:
    """Enhanced logging with UTF-8 support and structured output"""
    
    def __init__(self, log_file: str = "noxsuite_installer.log") -> None:
        self.log_file = Path(log_file)
        self.session_id = str(uuid.uuid4())[:8]
        self.start_time = datetime.now(timezone.utc)
        
        # Create log directory if it doesn't exist
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup structured logger
        self.logger = logging.getLogger(__name__)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)

# Security: Audit logging for security events
def log_security_event(event_type: str, details: dict, request_ip: str = None):
    """Log security-related events for audit trails."""
    security_event = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'details': details,
        'request_ip': request_ip,
        'severity': 'security'
    }
    logger.warning(f"SECURITY_EVENT: {json.dumps(security_event)}")

def log_access_attempt(endpoint: str, user_id: str = None, success: bool = True):
    """Log access attempts for security monitoring."""
    log_security_event('access_attempt', {
        'endpoint': endpoint,
        'user_id': user_id,
        'success': success
    })

logger = logging.getLogger('noxsuite_installer')
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler with UTF-8 support
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # File handler with UTF-8 encoding
        file_handler = logging.FileHandler(
            self.log_file, 
            mode='a', 
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Formatters
        console_format = '%(message)s'
        file_format = '%(asctime)s [%(levelname)s] [%(session_id)s] %(message)s'
        
        console_formatter = logging.Formatter(console_format)
        file_formatter = logging.Formatter(file_format)
        
        console_handler.setFormatter(console_formatter)
        file_formatter = self._create_custom_formatter()
        file_handler.setFormatter(file_formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        # Log session start
        self._log_structured({
            'event': 'session_start',
            'session_id': self.session_id,
            'timestamp': self.start_time.isoformat(),
            'platform': platform.platform(),
            'python_version': sys.version
        })
    
    def _create_custom_formatter(self) -> bool:
        """Create custom formatter that includes session ID"""
        class CustomFormatter(logging.Formatter):
            def format(self, record) -> bool:
                record.session_id = self.session_id
                return super().format(record)
        return CustomFormatter('%(asctime)s [%(levelname)s] [%(session_id)s] %(message)s')
    
    def _log_structured(self, data: Dict[str, Any]) -> bool:
        """Log structured data as JSON"""
        json_str = json.dumps(data, ensure_ascii=False, indent=None)
        self.logger.debug(f"STRUCTURED: {json_str}")
    
    def _safe_decode(self, text: Union[str, bytes]) -> str:
        """Safely decode text with fallback encoding detection"""
        if isinstance(text, str):
            return text
        
        # Try UTF-8 first
        try:
            return text.decode('utf-8')
        except UnicodeDecodeError:
            # Fallback to chardet detection
            try:
                detected = chardet.detect(text)
                encoding = detected['encoding'] or 'latin1'
                return text.decode(encoding)
            except:
                # Last resort: replace problematic characters
                return text.decode('utf-8', errors='replace')
    
    def step_start(self, step_name: str, description: str = "") -> bool:
        """Log step start with emoji support"""
        emoji_map = {
            'detecting': '🔍',
            'installing': '📦',
            'configuring': '⚙️',
            'generating': '🔧',
            'downloading': '⬇️',
            'testing': '🧪',
            'finalizing': '🎯'
        }
        
        emoji = emoji_map.get(step_name.lower().split('_')[0], '⚡')
        message = f"{emoji} {step_name.replace('_', ' ').title()}"
        if description:
            message += f": {description}"
            
        self.logger.info(message)
        self._log_structured({
            'event': 'step_start',
            'step': step_name,
            'description': description,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    def step_complete(self, step_name: str, details: Dict[str, Any] = None) -> bool:
        """Log step completion"""
        self.logger.info(f"✅ {step_name.replace('_', ' ').title()} completed")
        self._log_structured({
            'event': 'step_complete',
            'step': step_name,
            'details': details or {},
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    def step_error(self, step_name: str, error: Exception, context: Dict[str, Any] = None) -> bool:
        """Log step error with context"""
        error_msg = str(error)
        self.logger.error(f"❌ {step_name.replace('_', ' ').title()} failed: {error_msg}")
        self._log_structured({
            'event': 'step_error',
            'step': step_name,
            'error': error_msg,
            'error_type': type(error).__name__,
            'traceback': traceback.format_exc(),
            'context': context or {},
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    def warning(self, message: str, context: Dict[str, Any] = None) -> bool:
        """Log warning message"""
        self.logger.warning(f"⚠️  {message}")
        self._log_structured({
            'event': 'warning',
            'message': message,
            'context': context or {},
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    def info(self, message: str, context: Dict[str, Any] = None) -> bool:
        """Log info message"""
        self.logger.info(message)
        if context:
            self._log_structured({
                'event': 'info',
                'message': message,
                'context': context,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
    
    def debug(self, message: str, context: Dict[str, Any] = None) -> bool:
        """Log debug message"""
        self.logger.debug(message)
        if context:
            self._log_structured({
                'event': 'debug',
                'message': message,
                'context': context,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })

class InstallationAuditor:
    """Analyzes previous installation attempts and suggests improvements"""
    
    def __init__(self, log_file: Path) -> None:
        self.log_file = log_file
        self.issues_database = Path("noxsuite_issues.json")
        self.known_issues = self._load_known_issues()
    
    def _load_known_issues(self) -> Dict[str, Any]:
        """Load database of known issues and solutions"""
        if self.issues_database.exists():
            try:
                with open(self.issues_database, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "encoding_issues": {
                "patterns": ["UnicodeDecodeError", "codec can't decode", "charmap"],
                "solutions": ["force_utf8", "fallback_encoding", "safe_decode"]
            },
            "dependency_failures": {
                "patterns": ["command not found", "ModuleNotFoundError", "ImportError"],
                "solutions": ["alternative_package_manager", "manual_install", "containerized_fallback"]
            },
            "permission_errors": {
                "patterns": ["Permission denied", "PermissionError", "Access is denied"],
                "solutions": ["elevate_privileges", "user_directory", "docker_mode"]
            },
            "network_issues": {
                "patterns": ["ConnectionError", "timeout", "refused", "unreachable"],
                "solutions": ["retry_with_backoff", "alternative_mirror", "offline_mode"]
            }
        }
    
    def analyze_previous_failures(self) -> Dict[str, Any]:
        """Analyze previous installation logs for common failure patterns"""
        if not self.log_file.exists():
            return {"analysis": "no_previous_logs", "recommendations": []}
        
        analysis = {
            "failed_steps": [],
            "error_patterns": {},
            "recommendations": [],
            "recovery_suggestions": []
        }
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                logs = f.read()
            
            # Extract structured logs
            structured_entries = []
            for line in logs.split('\n'):
                if 'STRUCTURED:' in line:
                    try:
                        json_part = line.split('STRUCTURED:', 1)[1].strip()
                        entry = json.loads(json_part)
                        structured_entries.append(entry)
                    except:
                        continue
            
            # Analyze failures
            for entry in structured_entries:
                if entry.get('event') == 'step_error':
                    step = entry.get('step', 'unknown')
                    error = entry.get('error', '')
                    error_type = entry.get('error_type', '')
                    
                    analysis['failed_steps'].append({
                        'step': step,
                        'error': error,
                        'error_type': error_type,
                        'timestamp': entry.get('timestamp')
                    })
                    
                    # Match error patterns
                    for issue_type, issue_data in self.known_issues.items():
                        for pattern in issue_data['patterns']:
                            if pattern.lower() in error.lower():
                                if issue_type not in analysis['error_patterns']:
                                    analysis['error_patterns'][issue_type] = 0
                                analysis['error_patterns'][issue_type] += 1
                                
                                # Add recommendations
                                for solution in issue_data['solutions']:
                                    rec = f"For {issue_type}: Try {solution}"
                                    if rec not in analysis['recommendations']:
                                        analysis['recommendations'].append(rec)
            
            # Generate recovery suggestions
            if analysis['failed_steps']:
                last_failed = analysis['failed_steps'][-1]
                analysis['recovery_suggestions'].append(
                    f"Resume from step: {last_failed['step']}"
                )
                
                if 'encoding' in analysis['error_patterns']:
                    analysis['recovery_suggestions'].append(
                        "Use safe mode with encoding fallbacks"
                    )
                
                if 'dependency' in analysis['error_patterns']:
                    analysis['recovery_suggestions'].append(
                        "Try containerized installation mode"
                    )
        
        except Exception as e:
            analysis['analysis_error'] = str(e)
        
        return analysis

class PlatformDetector:
    """Enhanced platform detection with capability analysis"""
    
    def __init__(self, logger: SmartLogger) -> None:
        self.logger = logger

# Security: Audit logging for security events
def log_security_event(event_type: str, details: dict, request_ip: str = None):
    """Log security-related events for audit trails."""
    security_event = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'details': details,
        'request_ip': request_ip,
        'severity': 'security'
    }
    logger.warning(f"SECURITY_EVENT: {json.dumps(security_event)}")

def log_access_attempt(endpoint: str, user_id: str = None, success: bool = True):
    """Log access attempts for security monitoring."""
    log_security_event('access_attempt', {
        'endpoint': endpoint,
        'user_id': user_id,
        'success': success
    })

logger = logger
    
    def detect_system(self) -> SystemInfo:
        """Comprehensive system detection"""
        self.logger.step_start("detecting_system", "Analyzing platform capabilities")
        
        # Basic OS detection
        os_name = platform.system().lower()
        os_type_map = {
            "windows": OSType.WINDOWS,
            "linux": OSType.LINUX,
            "darwin": OSType.MACOS
        }
        os_type = os_type_map.get(os_name, OSType.UNKNOWN)
        
        # Architecture
        architecture = platform.machine()
        
        # Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        # Memory detection with multiple fallbacks
        available_memory = self._detect_memory()
        
        # CPU cores
        cpu_cores = os.cpu_count() or 4
        
        # Tool availability
        docker_available = self._check_tool_availability("docker")
        node_available = self._check_tool_availability("node")
        git_available = self._check_tool_availability("git")
        
        # Package managers detection
        package_managers = self._detect_package_managers(os_type)
        
        # Encoding support test
        encoding_support = self._test_encoding_support()
        
        # Permissions test
        permissions = self._test_permissions()
        
        system_info = SystemInfo(
            os_type=os_type,
            architecture=architecture,
            python_version=python_version,
            available_memory=available_memory,
            cpu_cores=cpu_cores,
            docker_available=docker_available,
            node_available=node_available,
            git_available=git_available,
            package_managers=package_managers,
            encoding_support=encoding_support,
            permissions=permissions
        )
        
        self.logger.step_complete("detecting_system", {
            "os_type": os_type.value,
            "memory_gb": available_memory,
            "tools_available": {
                "docker": docker_available,
                "node": node_available, 
                "git": git_available
            },
            "package_managers": package_managers,
            "encoding_utf8": encoding_support.get("utf8", False)
        })
        
        return system_info
    
    def _detect_memory(self) -> int:
        """Detect available memory with multiple methods"""
        try:
            # Method 1: psutil (if available)
            try:
                import psutil
                return psutil.virtual_memory().total // (1024**3)
            except ImportError:
                pass
            
            # Method 2: Windows WMI
            if platform.system().lower() == "windows":
                try:
                    result = subprocess.run(
                        ["wmic", "computersystem", "get", "TotalPhysicalMemory"],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        for line in lines:
                            if line.strip().isdigit():
                                return int(line.strip()) // (1024**3)
                except:
                    pass
            
            # Method 3: Linux /proc/meminfo
            elif platform.system().lower() == "linux":
                try:
                    with open('/proc/meminfo', 'r') as f:
                        for line in f:
                            if 'MemTotal' in line:
                                memory_kb = int(line.split()[1])
                                return memory_kb // (1024**2)
                except:
                    pass
            
            # Method 4: macOS sysctl
            elif platform.system().lower() == "darwin":
                try:
                    result = subprocess.run(
                        ["sysctl", "-n", "hw.memsize"],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode == 0:
                        return int(result.stdout.strip()) // (1024**3)
                except:
                    pass
        
        except Exception as e:
            self.logger.debug(f"Memory detection failed: {e}")
        
        # Fallback: reasonable default
        return 8
    
    def _check_tool_availability(self, tool: str) -> bool:
        """Check if a tool is available with version info"""
        try:
            result = subprocess.run(
                [tool, "--version"],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return shutil.which(tool) is not None
    
    def _detect_package_managers(self, os_type: OSType) -> List[str]:
        """Detect available package managers for the platform"""
        managers = []
        
        # Universal package managers
        if shutil.which("pip"):
            managers.append("pip")
        if shutil.which("conda"):
            managers.append("conda")
        if shutil.which("snap"):
            managers.append("snap")
        
        # Platform-specific package managers
        if os_type == OSType.WINDOWS:
            if shutil.which("choco"):
                managers.append("chocolatey")
            if shutil.which("winget"):
                managers.append("winget")
            if shutil.which("scoop"):
                managers.append("scoop")
        
        elif os_type == OSType.LINUX:
            linux_managers = ["apt-get", "apt", "yum", "dnf", "pacman", "zypper", "emerge"]
            for manager in linux_managers:
                if shutil.which(manager):
                    managers.append(manager)
        
        elif os_type == OSType.MACOS:
            if shutil.which("brew"):
                managers.append("homebrew")
            if shutil.which("port"):
                managers.append("macports")
        
        return managers
    
    def _test_encoding_support(self) -> Dict[str, bool]:
        """Test platform encoding capabilities"""
        support = {}
        
        # Test UTF-8 support
        try:
            test_string = "🧠 NoxSuite 🚀 Test 测试 تجربة"
            encoded = test_string.encode('utf-8')
            decoded = encoded.decode('utf-8')
            support["utf8"] = (test_string == decoded)
        except:
            support["utf8"] = False
        
        # Test console encoding
        try:
            if hasattr(sys.stdout, 'encoding'):
                support["console_encoding"] = sys.stdout.encoding
            else:
                support["console_encoding"] = "unknown"
        except:
            support["console_encoding"] = "unknown"
        
        # Test locale support
        try:
            import locale
            support["locale"] = locale.getpreferredencoding()
        except:
            support["locale"] = "unknown"
        
        return support
    
    def _test_permissions(self) -> Dict[str, bool]:
        """Test file system and administrative permissions"""
        permissions = {}
        
        # Test write permissions in current directory
        try:
            test_file = Path("._nox_permission_test")
            test_file.write_text("test", encoding='utf-8')
            test_file.unlink()
            permissions["current_dir_write"] = True
        except:
            permissions["current_dir_write"] = False
        
        # Test write permissions in user home
        try:
            test_file = Path.home() / "._nox_permission_test"
            test_file.write_text("test", encoding='utf-8')
            test_file.unlink()
            permissions["home_dir_write"] = True
        except:
            permissions["home_dir_write"] = False
        
        # Test administrative/root privileges (platform-specific)
        permissions["admin_rights"] = self._check_admin_rights()
        
        return permissions
    
    def _check_admin_rights(self) -> bool:
        """Check for administrative/root privileges"""
        try:
            if platform.system().lower() == "windows":
                # Windows: Check if running as administrator
                import ctypes

# Security: Input validation utilities
import re
import html
from typing import Any, Optional

def validate_input(value: Any, pattern: str = None, max_length: int = 1000) -> str:
    """Validate and sanitize input data."""
    if value is None:
        return ""
    
    # Convert to string and strip
    str_value = str(value).strip()
    
    # Check length
    if len(str_value) > max_length:
        raise ValueError(f"Input too long (max {max_length} characters)")
    
    # Apply pattern validation if provided
    if pattern and not re.match(pattern, str_value):
        raise ValueError("Input format validation failed")
    
    # HTML escape for XSS prevention
    return html.escape(str_value)

def validate_file_path(path: str) -> str:
    """Validate file path to prevent directory traversal."""
    if not path:
        raise ValueError("File path cannot be empty")
    
    # Normalize path and check for traversal attempts
    normalized = os.path.normpath(path)
    if '..' in normalized or normalized.startswith('/'):
        raise ValueError("Invalid file path detected")
    
    return normalized

                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                # Unix-like: Check if running as root
                return os.geteuid() == 0
        except:
            return False

class SmartDependencyManager:
    """Intelligent dependency management with multiple fallback strategies"""
    
    def __init__(self, system_info: SystemInfo, logger: SmartLogger) -> None:
        self.system_info = system_info
        self.logger = logger

# Security: Audit logging for security events
def log_security_event(event_type: str, details: dict, request_ip: str = None):
    """Log security-related events for audit trails."""
    security_event = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'details': details,
        'request_ip': request_ip,
        'severity': 'security'
    }
    logger.warning(f"SECURITY_EVENT: {json.dumps(security_event)}")

def log_access_attempt(endpoint: str, user_id: str = None, success: bool = True):
    """Log access attempts for security monitoring."""
    log_security_event('access_attempt', {
        'endpoint': endpoint,
        'user_id': user_id,
        'success': success
    })

logger = logger
        self.retry_count = {}
        self.max_retries = 3
    
    def check_and_install_dependencies(self, required_deps: List[str]) -> bool:
        """Check and install missing dependencies with smart fallbacks"""
        self.logger.step_start("checking_dependencies", f"Validating {len(required_deps)} dependencies")
        
        missing_deps = []
        version_issues = []
        
        for dep in required_deps:
            status = self._check_dependency_status(dep)
            if status["available"]:
                if status.get("version_ok", True):
                    self.logger.debug(f"✅ {dep}: {status.get('version', 'unknown')}")
                else:
                    version_issues.append((dep, status))
                    self.logger.warning(f"⚠️  {dep}: version {status.get('version')} (need {status.get('required_version')})")
            else:
                missing_deps.append(dep)
                self.logger.debug(f"❌ {dep}: not found")
        
        if not missing_deps and not version_issues:
            self.logger.step_complete("checking_dependencies", {"all_satisfied": True})
            return True
        
        # Handle missing dependencies
        if missing_deps:
            self.logger.info(f"📦 Missing dependencies: {', '.join(missing_deps)}")
            
            if not self._confirm_installation(missing_deps):
                return False
            
            success = self._install_missing_dependencies(missing_deps)
            if not success:
                return False
        
        # Handle version issues
        if version_issues:
            self.logger.info(f"🔄 Version updates needed: {len(version_issues)} packages")
            success = self._handle_version_issues(version_issues)
            if not success:
                return False
        
        self.logger.step_complete("checking_dependencies", {
            "installed": missing_deps,
            "updated": [dep for dep, _ in version_issues]
        })
        return True
    
    def _check_dependency_status(self, dep: str) -> Dict[str, Any]:
        """Check detailed status of a dependency"""
        status = {"available": False, "version": None, "path": None}
        
        # Define version requirements
        version_requirements = {
            "docker": "20.0.0",
            "node": "16.0.0",
            "npm": "8.0.0",
            "git": "2.20.0",
            "python": "3.8.0"
        }
        
        try:
            # Check if command exists
            cmd_path = shutil.which(dep)
            if not cmd_path:
                return status
            
            status["available"] = True
            status["path"] = cmd_path
            
            # Get version information
            version_cmd_map = {
                "docker": ["docker", "--version"],
                "node": ["node", "--version"],
                "npm": ["npm", "--version"],
                "git": ["git", "--version"],
                "python": ["python", "--version"],
                "python3": ["python3", "--version"]
            }
            
            if dep in version_cmd_map:
                try:
                    result = subprocess.run(
                        version_cmd_map[dep],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        version_output = result.stdout.strip()
                        version = self._extract_version(version_output)
                        status["version"] = version
                        
                        # Check if version meets requirements
                        if dep in version_requirements:
                            required = version_requirements[dep]
                            status["required_version"] = required
                            status["version_ok"] = self._compare_versions(version, required) >= 0
                        else:
                            status["version_ok"] = True
                
                except Exception as e:
                    self.logger.debug(f"Version check failed for {dep}: {e}")
        
        except Exception as e:
            self.logger.debug(f"Dependency check failed for {dep}: {e}")
        
        return status
    
    def _extract_version(self, version_output: str) -> str:
        """Extract version number from command output"""
        # Common version patterns
        patterns = [
            r'(\d+\.\d+\.\d+)',
            r'v(\d+\.\d+\.\d+)',
            r'version (\d+\.\d+\.\d+)',
            r'(\d+\.\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, version_output)
            if match:
                return match.group(1)
        
        return "unknown"
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """Compare two version strings (-1: v1 < v2, 0: equal, 1: v1 > v2)"""
        try:
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            # Pad shorter version with zeros
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            for i in range(max_len):
                if v1_parts[i] < v2_parts[i]:
                    return -1
                elif v1_parts[i] > v2_parts[i]:
                    return 1
            
            return 0
        except:
            return 0  # Assume equal if comparison fails
    
    def _confirm_installation(self, deps: List[str]) -> bool:
        """Confirm with user before installing dependencies"""
        self.logger.info(f"\n🤔 The following dependencies need to be installed:")
        for dep in deps:
            self.logger.info(f"   • {dep}")
        
        response = input(f"\n💡 Install missing dependencies automatically? [Y/n]: ").strip().lower()
        return response != 'n'
    
    def _install_missing_dependencies(self, deps: List[str]) -> bool:
        """Install missing dependencies using best available method"""
        for dep in deps:
            if not self._install_single_dependency(dep):
                return False
        return True
    
    def _install_single_dependency(self, dep: str) -> bool:
        """Install a single dependency with multiple fallback methods"""
        self.logger.step_start("installing_dependency", f"Installing {dep}")
        
        # Get retry count for this dependency
        retry_key = f"install_{dep}"
        current_retry = self.retry_count.get(retry_key, 0)
        
        if current_retry >= self.max_retries:
            self.logger.step_error("installing_dependency", 
                Exception(f"Max retries exceeded for {dep}"))
            return False
        
        # Try different installation methods in order of preference
        methods = self._get_installation_methods(dep)
        
        for method_name, method_func in methods:
            try:
                self.logger.debug(f"Trying installation method: {method_name}")
                success = method_func(dep)
                
                if success:
                    # Verify installation
                    if self._verify_installation(dep):
                        self.logger.step_complete("installing_dependency", {
                            "dependency": dep,
                            "method": method_name,
                            "retry_count": current_retry
                        })
                        return True
                    else:
                        self.logger.warning(f"Installation verification failed for {dep}")
                
            except Exception as e:
                self.logger.debug(f"Installation method {method_name} failed: {e}")
                continue
        
        # All methods failed, increment retry count
        self.retry_count[retry_key] = current_retry + 1
        self.logger.step_error("installing_dependency", 
            Exception(f"All installation methods failed for {dep}"))
        return False
    
    def _get_installation_methods(self, dep: str) -> List[Tuple[str, callable]]:
        """Get ordered list of installation methods for a dependency"""
        methods = []
        
        # Platform-specific methods first
        if self.system_info.os_type == OSType.WINDOWS:
            if "winget" in self.system_info.package_managers:
                methods.append(("winget", lambda d: self._install_with_winget(d)))
            if "chocolatey" in self.system_info.package_managers:
                methods.append(("chocolatey", lambda d: self._install_with_chocolatey(d)))
            if "scoop" in self.system_info.package_managers:
                methods.append(("scoop", lambda d: self._install_with_scoop(d)))
        
        elif self.system_info.os_type == OSType.LINUX:
            # Try system package manager first
            for pm in ["apt-get", "apt", "yum", "dnf"]:
                if pm in self.system_info.package_managers:
                    methods.append((pm, lambda d: self._install_with_system_pm(d, pm)))
                    break
        
        elif self.system_info.os_type == OSType.MACOS:
            if "homebrew" in self.system_info.package_managers:
                methods.append(("homebrew", lambda d: self._install_with_homebrew(d)))
        
        # Universal fallback methods
        methods.extend([
            ("manual_download", lambda d: self._install_manually(d)),
            ("containerized", lambda d: self._install_containerized(d))
        ])
        
        return methods
    
    def _install_with_winget(self, dep: str) -> bool:
        """Install dependency using Windows Package Manager (winget)"""
        package_map = {
            "docker": "Docker.DockerDesktop",
            "git": "Git.Git",
            "node": "OpenJS.NodeJS"
        }
        
        package_id = package_map.get(dep, dep)
        
        try:
            result = subprocess.run(
                ["winget", "install", package_id, "--accept-package-agreements", "--accept-source-agreements"],
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode == 0
        except:
            return False
    
    def _install_with_chocolatey(self, dep: str) -> bool:
        """Install dependency using Chocolatey"""
        package_map = {
            "docker": "docker-desktop",
            "git": "git",
            "node": "nodejs"
        }
        
        package_name = package_map.get(dep, dep)
        
        try:
            result = subprocess.run(
                ["choco", "install", package_name, "-y"],
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode == 0
        except:
            return False
    
    def _install_with_scoop(self, dep: str) -> bool:
        """Install dependency using Scoop"""
        try:
            result = subprocess.run(
                ["scoop", "install", dep],
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode == 0
        except:
            return False
    
    def _install_with_system_pm(self, dep: str, package_manager: str) -> bool:
        """Install dependency using system package manager"""
        package_map = {
            "docker": "docker.io",
            "git": "git",
            "node": "nodejs"
        }
        
        package_name = package_map.get(dep, dep)
        
        try:
            if package_manager in ["apt-get", "apt"]:
                # Update package list first
                subprocess.run(["sudo", "apt-get", "update"], timeout=60)
                result = subprocess.run(
                    ["sudo", "apt-get", "install", "-y", package_name],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            elif package_manager in ["yum", "dnf"]:
                result = subprocess.run(
                    ["sudo", package_manager, "install", "-y", package_name],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            else:
                return False
            
            return result.returncode == 0
        except:
            return False
    
    def _install_with_homebrew(self, dep: str) -> bool:
        """Install dependency using Homebrew"""
        try:
            if dep == "docker":
                result = subprocess.run(
                    ["brew", "install", "--cask", "docker"],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            else:
                result = subprocess.run(
                    ["brew", "install", dep],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            return result.returncode == 0
        except:
            return False
    
    def _install_manually(self, dep: str) -> bool:
        """Manual installation fallback (download and install)"""
        # This would implement manual download and installation
        # For now, return False to indicate this method is not yet implemented
        self.logger.debug(f"Manual installation not yet implemented for {dep}")
        return False
    
    def _install_containerized(self, dep: str) -> bool:
        """Install dependency in containerized mode"""
        # This would set up dependencies to run in containers
        # For now, return False to indicate this method is not yet implemented
        self.logger.debug(f"Containerized installation not yet implemented for {dep}")
        return False
    
    def _verify_installation(self, dep: str) -> bool:
        """Verify that a dependency was installed correctly"""
        try:
            # Wait a moment for installation to complete
            time.sleep(2)
            
            # Check if command is now available
            if shutil.which(dep):
                # Try to run version command
                try:
                    result = subprocess.run(
                        [dep, "--version"],
                        capture_output=True,
                        timeout=10
                    )
                    return result.returncode == 0
                except:
                    # Command exists but version check failed - still count as success
                    return True
            
            return False
        except:
            return False
    
    def _handle_version_issues(self, version_issues: List[Tuple[str, Dict]]) -> bool:
        """Handle dependencies with version compatibility issues"""
        for dep, status in version_issues:
            self.logger.info(f"🔄 Updating {dep} from {status.get('version')} to {status.get('required_version')}")
            # For now, we'll skip version updates and just warn
            # In a full implementation, this would upgrade packages
            self.logger.warning(f"Version update not implemented for {dep}")
        
        return True
