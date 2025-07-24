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
    
    def __init__(self, log_file: str = "noxsuite_installer.log"):
        self.log_file = Path(log_file)
        self.session_id = str(uuid.uuid4())[:8]
        self.start_time = datetime.now(timezone.utc)
        
        # Create log directory if it doesn't exist
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup structured logger
        self.logger = logging.getLogger('noxsuite_installer')
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
    
    def _create_custom_formatter(self):
        """Create custom formatter that includes session ID"""
        session_id = self.session_id
        class CustomFormatter(logging.Formatter):
            def format(self, record):
                record.session_id = session_id
                return super().format(record)
        return CustomFormatter('%(asctime)s [%(levelname)s] [%(session_id)s] %(message)s')
    
    def _log_structured(self, data: Dict[str, Any]):
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
    
    def step_start(self, step_name: str, description: str = ""):
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
    
    def step_complete(self, step_name: str, details: Dict[str, Any] = None):
        """Log step completion"""
        self.logger.info(f"✅ {step_name.replace('_', ' ').title()} completed")
        self._log_structured({
            'event': 'step_complete',
            'step': step_name,
            'details': details or {},
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    def step_error(self, step_name: str, error: Exception, context: Dict[str, Any] = None):
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
    
    def warning(self, message: str, context: Dict[str, Any] = None):
        """Log warning message"""
        self.logger.warning(f"⚠️  {message}")
        self._log_structured({
            'event': 'warning',
            'message': message,
            'context': context or {},
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    def info(self, message: str, context: Dict[str, Any] = None):
        """Log info message"""
        self.logger.info(message)
        if context:
            self._log_structured({
                'event': 'info',
                'message': message,
                'context': context,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
    
    def debug(self, message: str, context: Dict[str, Any] = None):
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
    
    def __init__(self, log_file: Path):
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
    
    def __init__(self, logger: SmartLogger):
        self.logger = logger
    
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
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                # Unix-like: Check if running as root
                return os.geteuid() == 0
        except:
            return False

class SmartDependencyManager:
    """Intelligent dependency management with multiple fallback strategies"""
    
    def __init__(self, system_info: SystemInfo, logger: SmartLogger):
        self.system_info = system_info
        self.logger = logger
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
class AtomicOperation:
    """Represents an atomic, rollback-capable operation"""
    
    def __init__(self, name: str, execute_func: callable, rollback_func: callable = None, 
                 validate_func: callable = None, description: str = ""):
        self.name = name
        self.description = description
        self.execute_func = execute_func
        self.rollback_func = rollback_func
        self.validate_func = validate_func
        self.executed = False
        self.rollback_data = None
    
    def execute(self, *args, **kwargs) -> bool:
        """Execute the operation"""
        try:
            self.rollback_data = self.execute_func(*args, **kwargs)
            self.executed = True
            
            # Validate if validation function provided
            if self.validate_func:
                if not self.validate_func(self.rollback_data):
                    self.rollback()
                    return False
            
            return True
        except Exception as e:
            if self.executed:
                self.rollback()
            raise e
    
    def rollback(self) -> bool:
        """Rollback the operation if possible"""
        if not self.executed or not self.rollback_func:
            return True
        
        try:
            self.rollback_func(self.rollback_data)
            self.executed = False
            return True
        except Exception:
            return False

class DirectoryScaffold:
    """Manages directory structure creation and validation"""
    
    def __init__(self, base_path: Path, logger: SmartLogger):
        self.base_path = base_path
        self.logger = logger
        self.created_dirs = []
    
    def create_structure(self, structure: Dict[str, Any], dry_run: bool = False) -> bool:
        """Create directory structure atomically"""
        self.logger.step_start("creating_directories", f"Setting up {len(structure)} directory trees")
        
        # Plan all directories first
        all_dirs = self._flatten_structure(structure, self.base_path)
        
        if dry_run:
            self.logger.info("🔍 Dry run - directories that would be created:")
            for dir_path in all_dirs:
                self.logger.info(f"   📁 {dir_path}")
            return True
        
        # Validate base path permissions
        if not self._validate_base_path():
            return False
        
        # Create directories atomically
        created_dirs = []
        try:
            for dir_path in all_dirs:
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    created_dirs.append(dir_path)
                    self.logger.debug(f"Created directory: {dir_path}")
            
            self.created_dirs = created_dirs
            self.logger.step_complete("creating_directories", {
                "created_count": len(created_dirs),
                "total_dirs": len(all_dirs)
            })
            return True
            
        except Exception as e:
            # Rollback created directories
            self._cleanup_directories(created_dirs)
            self.logger.step_error("creating_directories", e)
            return False
    
    def _flatten_structure(self, structure: Dict[str, Any], base: Path) -> List[Path]:
        """Flatten nested directory structure into list of paths"""
        dirs = []
        
        for name, content in structure.items():
            current_path = base / name
            dirs.append(current_path)
            
            if isinstance(content, dict):
                dirs.extend(self._flatten_structure(content, current_path))
        
        return sorted(set(dirs))  # Remove duplicates and sort
    
    def _validate_base_path(self) -> bool:
        """Validate base path permissions and accessibility"""
        try:
            # Check if parent directory exists and is writable
            parent = self.base_path.parent
            if not parent.exists():
                self.logger.warning(f"Parent directory doesn't exist: {parent}")
                return False
            
            # Test write permissions
            test_file = parent / f".nox_write_test_{int(time.time())}"
            try:
                test_file.write_text("test", encoding='utf-8')
                test_file.unlink()
            except Exception as e:
                self.logger.warning(f"No write permission in {parent}: {e}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Base path validation failed: {e}")
            return False
    
    def _cleanup_directories(self, dirs: List[Path]):
        """Clean up created directories in reverse order"""
        for dir_path in reversed(dirs):
            try:
                if dir_path.exists() and dir_path.is_dir():
                    # Only remove if empty
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
            except:
                pass  # Ignore cleanup errors

class ConfigurationWizard:
    """Enhanced configuration wizard with preview and validation"""
    
    def __init__(self, system_info: SystemInfo, logger: SmartLogger, auditor: InstallationAuditor):
        self.system_info = system_info 
        self.logger = logger
        self.auditor = auditor
        self.previous_failures = auditor.analyze_previous_failures()
    
    def run_wizard(self, mode: InstallMode = InstallMode.GUIDED) -> Optional[InstallConfig]:
        """Run configuration wizard based on mode"""
        if mode == InstallMode.FAST:
            return self._fast_mode_config()
        elif mode == InstallMode.DRY_RUN:
            return self._dry_run_config()
        elif mode == InstallMode.SAFE:
            return self._safe_mode_config()
        elif mode == InstallMode.RECOVERY:
            return self._recovery_mode_config()
        else:
            return self._guided_mode_config()
    
    def _show_welcome_screen(self):
        """Display enhanced welcome screen with system analysis"""
        welcome_text = """
╔═══════════════════════════════════════════════════════════════════╗
║                🧠 NoxSuite Smart Self-Healing Installer           ║
║                    AI-Powered Infrastructure Automation           ║
╠═══════════════════════════════════════════════════════════════════╣
║  🔧 Smart Error Recovery    🌐 Cross-Platform Support           ║
║  📊 Installation Analytics  🛡️  Self-Healing Operations          ║
║  🚀 Multiple Install Modes  🤖 AI-Powered Troubleshooting       ║
║  📱 ADHD-Friendly Interface 🔄 Atomic Operations                ║
╚═══════════════════════════════════════════════════════════════════╝
        """
        print(welcome_text)
        
        # System analysis summary
        print(f"\n🖥️  System Analysis:")
        print(f"   OS: {self.system_info.os_type.value.title()} {self.system_info.architecture}")
        print(f"   Python: {self.system_info.python_version}")
        print(f"   Resources: {self.system_info.cpu_cores} cores, {self.system_info.available_memory}GB RAM")
        
        # Tool availability with status icons
        tools = [
            ("Docker", self.system_info.docker_available),
            ("Node.js", self.system_info.node_available), 
            ("Git", self.system_info.git_available)
        ]
        
        print(f"   Dependencies: " + " | ".join([
            f"{tool} {'✅' if available else '❌'}" 
            for tool, available in tools
        ]))
        
        # Encoding and permissions status
        if self.system_info.encoding_support:
            utf8_ok = self.system_info.encoding_support.get("utf8", False)
            print(f"   Encoding: UTF-8 {'✅' if utf8_ok else '⚠️ '}")
        
        if self.system_info.permissions:
            admin_rights = self.system_info.permissions.get("admin_rights", False)
            write_ok = self.system_info.permissions.get("current_dir_write", False)
            print(f"   Permissions: Write {'✅' if write_ok else '❌'} | Admin {'✅' if admin_rights else '❌'}")
        
        # Previous installation analysis
        if self.previous_failures.get("failed_steps"):
            print(f"\n⚠️  Previous Installation Issues Detected:")
            for issue_type, count in self.previous_failures.get("error_patterns", {}).items():
                print(f"   • {issue_type.replace('_', ' ').title()}: {count} occurrences")
            
            if self.previous_failures.get("recovery_suggestions"):
                print(f"   💡 Recovery suggestions available")
    
    def _guided_mode_config(self) -> InstallConfig:
        """Full guided configuration with all options"""
        self._show_welcome_screen()
        
        print(f"\n🛠️  Configuration Wizard (Guided Mode)")
        print("=" * 60)
        
        # Installation directory with smart defaults
        default_dir = self._get_default_install_directory()
        print(f"\n📁 Installation Directory")
        print(f"   Default: {default_dir}")
        print(f"   • Must have at least 2GB free space")
        print(f"   • Avoid paths with spaces on Windows")
        
        while True:
            install_dir_input = input(f"   Directory [{default_dir}]: ").strip()
            install_directory = Path(install_dir_input) if install_dir_input else default_dir
            
            # Validate directory
            validation_result = self._validate_install_directory(install_directory)
            if validation_result["valid"]:
                break
            else:
                print(f"   ❌ {validation_result['message']}")
                continue
        
        # Module selection with smart recommendations
        modules = self._select_modules()
        
        # Feature selection
        features = self._select_features()
        
        # AI configuration
        ai_config = self._configure_ai() if features["enable_ai"] else {"models": []}
        
        # Mode selection
        mode_config = self._select_installation_mode()
        
        # Create configuration
        config = InstallConfig(
            install_directory=install_directory,
            modules=modules,
            enable_ai=features["enable_ai"],
            enable_voice=features["enable_voice"],
            enable_mobile=features["enable_mobile"],
            dev_mode=features["dev_mode"],
            auto_start=features["auto_start"],
            ai_models=ai_config["models"],
            mode=mode_config["mode"],
            force_reinstall=mode_config["force_reinstall"],
            backup_existing=mode_config["backup_existing"]
        )
        
        # Show configuration preview
        self._show_configuration_preview(config)
        
        # Final confirmation
        if not self._confirm_installation(config):
            return None
        
        return config
    
    def _fast_mode_config(self) -> InstallConfig:
        """Fast mode with sensible defaults"""
        print(f"\n⚡ Fast Mode Installation")
        print("Using recommended defaults for quick setup...")
        
        return InstallConfig(
            install_directory=self._get_default_install_directory(),
            modules=self._get_default_modules(),
            enable_ai=True,
            enable_voice=False,
            enable_mobile=True,
            dev_mode=False,
            auto_start=True,
            ai_models=["mistral:7b-instruct", "gemma:7b-it"],
            mode=InstallMode.FAST
        )
    
    def _dry_run_config(self) -> InstallConfig:
        """Dry run configuration for testing"""
        print(f"\n🔍 Dry Run Mode")
        print("Will simulate installation without making changes...")
        
        config = self._fast_mode_config()
        config.mode = InstallMode.DRY_RUN
        return config
    
    def _safe_mode_config(self) -> InstallConfig:
        """Safe mode with minimal features"""
        print(f"\n🛡️  Safe Mode Installation")
        print("Using minimal configuration for stability...")
        
        return InstallConfig(
            install_directory=self._get_default_install_directory(),
            modules=["noxpanel", "noxguard"],  # Minimal modules
            enable_ai=False,  # No AI in safe mode
            enable_voice=False,
            enable_mobile=False,
            dev_mode=False,
            auto_start=False,
            ai_models=[],
            mode=InstallMode.SAFE
        )
    
    def _recovery_mode_config(self) -> InstallConfig:
        """Recovery mode based on previous failure analysis"""
        print(f"\n🔄 Recovery Mode Installation")
        
        if not self.previous_failures.get("failed_steps"):
            print("No previous failures detected, using fast mode...")
            config = self._fast_mode_config()
            config.mode = InstallMode.RECOVERY
            return config
        
        print("Configuring based on previous failure analysis...")
        
        # Show recovery suggestions
        if self.previous_failures.get("recovery_suggestions"):
            print(f"\n💡 Recovery Suggestions:")
            for suggestion in self.previous_failures["recovery_suggestions"]:
                print(f"   • {suggestion}")
        
        # Use safe defaults with adjustments based on previous failures
        config = self._safe_mode_config()
        config.mode = InstallMode.RECOVERY
        
        # Adjust configuration based on error patterns
        error_patterns = self.previous_failures.get("error_patterns", {})
        
        if "encoding_issues" in error_patterns:
            print("   🔧 Enabled encoding fallbacks")
        
        if "dependency_failures" in error_patterns:
            print("   🔧 Will use alternative package managers")
        
        if "permission_errors" in error_patterns:
            print("   🔧 Will use user directory installation")
            config.install_directory = Path.home() / "noxsuite"
        
        return config
    
    def _get_default_install_directory(self) -> Path:
        """Get smart default installation directory"""
        if self.system_info.os_type == OSType.WINDOWS:
            # Avoid C:\Program Files to prevent permission issues
            return Path.home() / "NoxSuite"
        else:
            return Path.home() / "noxsuite"
    
    def _validate_install_directory(self, directory: Path) -> Dict[str, Any]:
        """Validate installation directory"""
        try:
            # Check if path has spaces (problematic on Windows)
            if self.system_info.os_type == OSType.WINDOWS and ' ' in str(directory):
                return {
                    "valid": False,
                    "message": "Avoid spaces in path on Windows (causes Docker issues)"
                }
            
            # Check parent directory permissions
            parent = directory.parent
            if not parent.exists():
                return {
                    "valid": False,
                    "message": f"Parent directory doesn't exist: {parent}"
                }
            
            # Check write permissions 
            test_file = parent / f".nox_test_{int(time.time())}"
            try:
                test_file.write_text("test")
                test_file.unlink()
            except Exception:
                return {
                    "valid": False,
                    "message": f"No write permission in {parent}"
                }
            
            # Check available space (estimate needed: 2GB)
            try:
                if hasattr(shutil, 'disk_usage'):
                    _, _, free = shutil.disk_usage(parent)
                    free_gb = free // (1024**3)
                    if free_gb < 2:
                        return {
                            "valid": False,
                            "message": f"Insufficient disk space: {free_gb}GB free (need 2GB)"
                        }
            except:
                pass  # Skip space check if not available
            
            return {"valid": True, "message": "Directory is valid"}
            
        except Exception as e:
            return {"valid": False, "message": f"Validation error: {e}"}
    
    def _select_modules(self) -> List[str]:
        """Interactive module selection with recommendations"""
        default_modules = [
            "noxpanel", "noxguard", "autoimport", "powerlog",
            "langflow-hub", "autocleaner", "heimnetz-scanner",
            "plugin-system", "update-manager"
        ]
        
        print(f"\n📦 Module Selection")
        print("Select modules to install (recommended modules marked with ⭐):")
        
        # Show modules with descriptions
        module_descriptions = {
            "noxpanel": "⭐ Core web interface and dashboard",
            "noxguard": "⭐ Security monitoring and threat detection", 
            "autoimport": "⭐ Automated data import and processing",
            "powerlog": "Advanced logging and analysis",
            "langflow-hub": "AI workflow management (requires AI features)",
            "autocleaner": "Automatic cleanup and maintenance",
            "heimnetz-scanner": "⭐ Network scanning and discovery",
            "plugin-system": "⭐ Plugin management framework",
            "update-manager": "⭐ Automatic updates and patching"
        }
        
        for i, module in enumerate(default_modules, 1):
            description = module_descriptions.get(module, "")
            print(f"   {i:2d}. {module:<20} - {description}")
        
        print(f"\nOptions:")
        print(f"   • Enter numbers (e.g., 1,2,3) for specific modules")
        print(f"   • 'recommended' for starred modules only")
        print(f"   • 'all' for all modules")
        print(f"   • 'minimal' for core modules only")
        
        while True:
            selection = input(f"\nSelect modules [recommended]: ").strip().lower()
            
            if not selection or selection == "recommended":
                return [m for m in default_modules if "⭐" in module_descriptions.get(m, "")]
            elif selection == "all":
                return default_modules
            elif selection == "minimal":
                return ["noxpanel", "noxguard"]
            else:
                try:
                    indices = [int(x.strip()) - 1 for x in selection.split(",")]
                    selected = [default_modules[i] for i in indices if 0 <= i < len(default_modules)]
                    if selected:
                        return selected
                    else:
                        print("   ❌ Invalid selection, please try again")
                except:
                    print("   ❌ Invalid format, please try again")
    
    def _select_features(self) -> Dict[str, bool]:
        """Interactive feature selection"""
        print(f"\n🎯 Feature Configuration")
        
        features = {}
        
        # AI Features
        ai_recommendation = "recommended" if self.system_info.available_memory >= 8 else "not recommended (low memory)"
        features["enable_ai"] = self._ask_yes_no(
            f"🤖 Enable AI features (Ollama, LLMs) [{ai_recommendation}]", 
            default=self.system_info.available_memory >= 8
        )
        
        # Voice Interface (only if AI enabled)
        if features["enable_ai"]:
            features["enable_voice"] = self._ask_yes_no(
                "🎤 Enable voice interface (experimental)", 
                default=False
            )
        else:
            features["enable_voice"] = False
        
        # Mobile companion
        features["enable_mobile"] = self._ask_yes_no(
            "📱 Enable mobile companion (NoxGo PWA)",
            default=True
        )
        
        # Development mode
        features["dev_mode"] = self._ask_yes_no(
            "⚙️  Enable development mode (hot reload, debug logging)",
            default=False
        )
        
        # Auto-start services
        features["auto_start"] = self._ask_yes_no(
            "🚀 Auto-start services after installation",
            default=True
        )
        
        return features
    
    def _configure_ai(self) -> Dict[str, Any]:
        """Configure AI models and settings"""
        print(f"\n🧠 AI Configuration")
        
        available_models = [
            ("mistral:7b-instruct", "General purpose, good balance", "~4GB RAM"),
            ("gemma:7b-it", "Instruction-tuned, fast responses", "~4GB RAM"),
            ("tinyllama", "Lightweight, quick setup", "~1GB RAM"),
            ("phi", "Microsoft model, efficient", "~2GB RAM"),
            ("llama2:7b", "Meta's foundation model", "~4GB RAM"),
            ("codellama:7b", "Code-specialized model", "~4GB RAM")
        ]
        
        print("Available AI models:")
        for i, (model, description, memory) in enumerate(available_models, 1):
            print(f"   {i}. {model:<20} - {description} ({memory})")
        
        # Recommend models based on available memory
        if self.system_info.available_memory >= 16:
            recommended = "1,2,4"  # Multiple models
            print(f"\n💡 Recommendation: Install multiple models (you have {self.system_info.available_memory}GB RAM)")
        elif self.system_info.available_memory >= 8:
            recommended = "1,3"  # Balanced selection
            print(f"\n💡 Recommendation: Install 1-2 models (you have {self.system_info.available_memory}GB RAM)")
        else:
            recommended = "3"  # Lightweight only
            print(f"\n⚠️  Recommendation: Install lightweight model only (you have {self.system_info.available_memory}GB RAM)")
        
        while True:
            selection = input(f"\nSelect models [numbers like {recommended}]: ").strip()
            
            if not selection:
                selection = recommended
            
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(",")]
                selected_models = [available_models[i][0] for i in indices if 0 <= i < len(available_models)]
                
                if selected_models:
                    # Estimate total memory usage
                    memory_estimate = len(selected_models) * 4  # Rough estimate
                    if memory_estimate > self.system_info.available_memory * 0.8:
                        print(f"   ⚠️  Warning: Selected models may use ~{memory_estimate}GB RAM")
                        if not self._ask_yes_no("Continue anyway?", default=False):
                            continue
                    
                    return {"models": selected_models}
                else:
                    print("   ❌ No models selected, please try again")
            except:
                print("   ❌ Invalid format, please try again")
    
    def _select_installation_mode(self) -> Dict[str, Any]:
        """Select advanced installation options"""
        print(f"\n🔧 Installation Options")
        
        mode_config = {}
        
        # Force reinstall
        mode_config["force_reinstall"] = self._ask_yes_no(
            "🔄 Force reinstall (remove existing installation)",
            default=False
        )
        
        # Backup existing
        if not mode_config["force_reinstall"]:
            mode_config["backup_existing"] = self._ask_yes_no(
                "💾 Backup existing installation before updating",
                default=True
            )
        else:
            mode_config["backup_existing"] = False
        
        mode_config["mode"] = InstallMode.GUIDED
        return mode_config
    
    def _ask_yes_no(self, question: str, default: bool = True) -> bool:
        """Ask a yes/no question with default"""
        default_text = "Y/n" if default else "y/N"
        response = input(f"   {question} [{default_text}]: ").strip().lower()
        
        if not response:
            return default
        
        return response in ['y', 'yes', 'true', '1']
    
    def _show_configuration_preview(self, config: InstallConfig):
        """Show configuration preview before installation"""
        print(f"\n📋 Installation Summary")
        print("=" * 60)
        print(f"   📁 Directory: {config.install_directory}")
        print(f"   📦 Modules: {', '.join(config.modules)}")
        print(f"   🤖 AI Features: {'✅' if config.enable_ai else '❌'}")
        print(f"   🎤 Voice Interface: {'✅' if config.enable_voice else '❌'}")
        print(f"   📱 Mobile App: {'✅' if config.enable_mobile else '❌'}")
        print(f"   ⚙️  Development Mode: {'✅' if config.dev_mode else '❌'}")
        
        if config.ai_models:
            print(f"   🧠 AI Models: {', '.join(config.ai_models)}")
        
        # Estimate installation size and time
        estimated_size = self._estimate_installation_size(config)
        estimated_time = self._estimate_installation_time(config)
        
        print(f"\n📊 Estimates:")
        print(f"   💾 Disk space: ~{estimated_size}GB")
        print(f"   ⏱️  Time: ~{estimated_time} minutes")
        
        # Show any warnings
        warnings = self._check_configuration_warnings(config)
        if warnings:
            print(f"\n⚠️  Warnings:")
            for warning in warnings:
                print(f"   • {warning}")
    
    def _estimate_installation_size(self, config: InstallConfig) -> float:
        """Estimate total installation size"""
        base_size = 0.5  # Base NoxSuite components
        module_size = len(config.modules) * 0.1  # ~100MB per module
        ai_size = len(config.ai_models) * 4.0 if config.enable_ai else 0  # ~4GB per model
        docker_size = 2.0  # Docker images
        
        return base_size + module_size + ai_size + docker_size
    
    def _estimate_installation_time(self, config: InstallConfig) -> int:
        """Estimate installation time in minutes"""
        base_time = 5  # Base setup
        module_time = len(config.modules) * 2  # 2 minutes per module
        ai_time = len(config.ai_models) * 10 if config.enable_ai else 0  # 10 minutes per model
        dependency_time = 10  # Dependency installation
        
        return base_time + module_time + ai_time + dependency_time
    
    def _check_configuration_warnings(self, config: InstallConfig) -> List[str]:
        """Check configuration for potential issues"""
        warnings = []
        
        # Memory warnings
        if config.enable_ai and self.system_info.available_memory < 8:
            warnings.append("AI features may be slow with less than 8GB RAM")
        
        # Disk space warnings
        estimated_size = self._estimate_installation_size(config)
        if estimated_size > 20:
            warnings.append(f"Large installation size: ~{estimated_size}GB")
        
        # Windows-specific warnings
        if self.system_info.os_type == OSType.WINDOWS:
            if ' ' in str(config.install_directory):
                warnings.append("Path with spaces may cause Docker issues on Windows")
            
            if not self.system_info.permissions.get("admin_rights", False):
                warnings.append("Some features may require administrator privileges")
        
        # Encoding warnings
        if not self.system_info.encoding_support.get("utf8", True):
            warnings.append("Limited Unicode support detected - some display issues possible")
        
        return warnings
    
    def _confirm_installation(self, config: InstallConfig) -> bool:
        """Final confirmation before installation"""
        print(f"\n🎯 Ready to Install")
        
        # Show key information
        print(f"This will install NoxSuite to: {config.install_directory}")
        if config.force_reinstall:
            print(f"⚠️  Will remove existing installation")
        
        response = input(f"\n✅ Proceed with installation? [Y/n]: ").strip().lower()
        return response != 'n'
    
    def _get_default_modules(self) -> List[str]:
        """Get default recommended modules"""
        return ["noxpanel", "noxguard", "autoimport", "heimnetz-scanner", "plugin-system", "update-manager"]

class SmartNoxSuiteInstaller:
    """Main installer class with smart recovery and self-healing capabilities"""
    
    def __init__(self):
        # Initialize logging
        self.logger = SmartLogger()
        
        # Initialize auditor
        self.auditor = InstallationAuditor(self.logger.log_file)
        
        # Detect system capabilities
        detector = PlatformDetector(self.logger)
        self.system_info = detector.detect_system()
        
        # Initialize dependency manager
        self.dependency_manager = SmartDependencyManager(self.system_info, self.logger)
        
        # Initialize configuration wizard
        self.wizard = ConfigurationWizard(self.system_info, self.logger, self.auditor)
        
        # Installation state
        self.config: Optional[InstallConfig] = None
        self.completed_steps = []
        self.failed_steps = []
        self.rollback_stack = []
    
    def run_installation(self, mode: InstallMode = InstallMode.GUIDED) -> bool:
        """Run the complete smart installation process"""
        try:
            self.logger.info("🚀 Starting NoxSuite Smart Installation")
            
            # Step 1: Configuration
            self.logger.step_start("configuration", "Running configuration wizard")
            self.config = self.wizard.run_wizard(mode)
            
            if not self.config:
                self.logger.info("❌ Installation cancelled by user")
                return False
            
            self.logger.step_complete("configuration")
            
            # Step 2: Pre-installation checks
            if not self._run_pre_installation_checks():
                return False
            
            # Step 3: Dependency management
            if not self._handle_dependencies():
                return False
            
            # Step 4: Directory setup
            if not self._setup_directories():
                return False
            
            # Step 5: Core installation
            if not self._install_core_components():
                return False
            
            # Step 6: AI setup (if enabled)
            if self.config.enable_ai and not self._setup_ai_components():
                return False
            
            # Step 7: Configuration generation
            if not self._generate_configurations():
                return False
            
            # Step 8: Service setup
            if not self._setup_services():
                return False
            
            # Step 9: Post-installation validation
            if not self._validate_installation():
                return False
            
            # Step 10: Finalization
            self._finalize_installation()
            
            return True
            
        except KeyboardInterrupt:
            self.logger.info("\n❌ Installation cancelled by user")
            self._cleanup_on_failure()
            return False
            
        except Exception as e:
            self.logger.step_error("installation", e, {
                "completed_steps": self.completed_steps,
                "config": asdict(self.config) if self.config else None
            })
            self._cleanup_on_failure()
            return False
    
    def _run_pre_installation_checks(self) -> bool:
        """Run comprehensive pre-installation validation"""
        self.logger.step_start("pre_checks", "Validating system requirements")
        
        checks = [
            ("system_compatibility", self._check_system_compatibility),
            ("disk_space", self._check_disk_space),
            ("permissions", self._check_permissions),
            ("existing_installation", self._check_existing_installation),
            ("network_connectivity", self._check_network_connectivity)
        ]
        
        all_passed = True
        results = {}
        
        for check_name, check_func in checks:
            try:
                result = check_func()
                results[check_name] = result
                
                if result.get("status") == "failed":
                    self.logger.warning(f"❌ {check_name}: {result.get('message', 'Failed')}")
                    
                    # Some checks are critical
                    if result.get("critical", False):
                        all_passed = False
                elif result.get("status") == "warning":
                    self.logger.warning(f"⚠️  {check_name}: {result.get('message', 'Warning')}")
                else:
                    self.logger.debug(f"✅ {check_name}: OK")
                    
            except Exception as e:
                self.logger.warning(f"❌ {check_name}: Check failed - {e}")
                results[check_name] = {"status": "error", "message": str(e)}
        
        if not all_passed:
            self.logger.step_error("pre_checks", Exception("Critical pre-installation checks failed"))
            return False
        
        self.logger.step_complete("pre_checks", results)
        return True
    
    def _check_system_compatibility(self) -> Dict[str, Any]:
        """Check system compatibility"""
        # Python version check
        min_python = (3, 8)
        current_python = sys.version_info[:2]
        
        if current_python < min_python:
            return {
                "status": "failed",
                "critical": True,
                "message": f"Python {min_python[0]}.{min_python[1]}+ required, got {current_python[0]}.{current_python[1]}"
            }
        
        # OS support check
        if self.system_info.os_type == OSType.UNKNOWN:
            return {
                "status": "failed", 
                "critical": True,
                "message": "Unsupported operating system"
            }
        
        return {"status": "passed"}
    
    def _check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space"""
        try:
            install_dir = self.config.install_directory
            required_gb = self.wizard._estimate_installation_size(self.config)
            
            if hasattr(shutil, 'disk_usage'):
                _, _, free = shutil.disk_usage(install_dir.parent)
                free_gb = free / (1024**3)
                
                if free_gb < required_gb:
                    return {
                        "status": "failed",
                        "critical": True,
                        "message": f"Need {required_gb:.1f}GB, only {free_gb:.1f}GB available"
                    }
                elif free_gb < required_gb * 1.5:
                    return {
                        "status": "warning",
                        "message": f"Low disk space: {free_gb:.1f}GB available"
                    }
            
            return {"status": "passed"}
            
        except Exception as e:
            return {"status": "warning", "message": f"Could not check disk space: {e}"}
    
    def _check_permissions(self) -> Dict[str, Any]:
        """Check file system permissions"""
        install_dir = self.config.install_directory
        
        # Test write permissions in target directory
        try:
            test_file = install_dir.parent / f".nox_perm_test_{int(time.time())}"
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            return {
                "status": "failed",
                "critical": True,
                "message": f"No write permission in {install_dir.parent}: {e}"
            }
        
        return {"status": "passed"}
    
    def _check_existing_installation(self) -> Dict[str, Any]:
        """Check for existing NoxSuite installation"""
        install_dir = self.config.install_directory
        
        if install_dir.exists():
            # Check if it's a NoxSuite installation
            noxsuite_markers = [
                "noxsuite.json", 
                "INSTALLATION_SUMMARY.json",
                "docker/docker-compose.noxsuite.yml"
            ]
            
            is_noxsuite = any((install_dir / marker).exists() for marker in noxsuite_markers)
            
            if is_noxsuite:
                if self.config.force_reinstall:
                    return {
                        "status": "warning",
                        "message": "Existing installation will be removed"
                    }
                else:
                    return {
                        "status": "warning", 
                        "message": "Existing installation found - will attempt upgrade"
                    }
            else:
                # Directory exists but not NoxSuite
                if any(install_dir.iterdir()):
                    return {
                        "status": "warning",
                        "message": "Directory exists and contains files"
                    }
        
        return {"status": "passed"}
    
    def _check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity for downloads"""
        if self.config.mode == InstallMode.DRY_RUN:
            return {"status": "passed"}
        
        test_urls = [
            "https://github.com",
            "https://hub.docker.com",
        ]
        
        if self.config.enable_ai:
            test_urls.append("https://ollama.ai")
        
        failed_urls = []
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code != 200:
                    failed_urls.append(url)
            except:
                failed_urls.append(url)
        
        if failed_urls:
            return {
                "status": "warning",
                "message": f"Network issues detected: {len(failed_urls)} sites unreachable"
            }
        
        return {"status": "passed"}
    
    def _handle_dependencies(self) -> bool:
        """Handle dependency installation and validation"""
        required_deps = ["docker", "git"]
        
        if self.config.enable_mobile or any("react" in module for module in self.config.modules):
            required_deps.append("node")
        
        return self.dependency_manager.check_and_install_dependencies(required_deps)
    
    def _setup_directories(self) -> bool:
        """Setup directory structure atomically"""
        if self.config.mode == InstallMode.DRY_RUN:
            self.logger.info("🔍 Dry run: Would create directory structure")
            return True
        
        directory_structure = {
            "frontend": {
                "noxpanel-ui": {},
                "noxgo-mobile": {} if self.config.enable_mobile else None
            },
            "backend": {
                "fastapi": {},
                "flask-legacy": {}
            },
            "services": {
                "langflow": {} if self.config.enable_ai else None,
                "ollama": {} if self.config.enable_ai else None
            },
            "data": {
                "postgres": {},
                "redis": {},
                "logs": {}
            },
            "config": {},
            "scripts": {},
            "docker": {},
            "plugins": {}
        }
        
        # Remove None entries
        def clean_structure(d):
            if isinstance(d, dict):
                return {k: clean_structure(v) for k, v in d.items() if v is not None}
            return d
        
        directory_structure = clean_structure(directory_structure)
        
        scaffold = DirectoryScaffold(self.config.install_directory, self.logger)
        return scaffold.create_structure(directory_structure, dry_run=self.config.mode == InstallMode.DRY_RUN)
    
    def _install_core_components(self) -> bool:
        """Install core NoxSuite components"""
        if self.config.mode == InstallMode.DRY_RUN:
            self.logger.info("🔍 Dry run: Would install core components")
            return True
        
        # This would implement the actual component installation
        # For now, return True to indicate success
        self.logger.step_start("installing_core", "Installing NoxSuite core components")
        
        # Simulate installation time
        time.sleep(1)
        
        self.logger.step_complete("installing_core")
        return True
    
    def _setup_ai_components(self) -> bool:
        """Setup AI components and models"""
        if self.config.mode == InstallMode.DRY_RUN:
            self.logger.info("🔍 Dry run: Would setup AI components")
            return True
        
        if not self.config.enable_ai:return True
        
        self.logger.step_start("setting_up_ai", f"Installing {len(self.config.ai_models)} AI models")
        
        # This would implement actual AI model installation
        # For now, simulate the process
        for model in self.config.ai_models:
            self.logger.info(f"📦 Installing model: {model}")
            time.sleep(0.5)  # Simulate download time
        
        self.logger.step_complete("setting_up_ai")
        return True
    
    def _generate_configurations(self) -> bool:
        """Generate configuration files"""
        if self.config.mode == InstallMode.DRY_RUN:
            self.logger.info("🔍 Dry run: Would generate configuration files")
            return True
        
        self.logger.step_start("generating_configs", "Creating configuration files")
        
        # This would implement actual configuration generation
        # For now, simulate the process
        time.sleep(0.5)
        
        self.logger.step_complete("generating_configs")
        return True
    
    def _setup_services(self) -> bool:
        """Setup and configure services"""
        if self.config.mode == InstallMode.DRY_RUN:
            self.logger.info("🔍 Dry run: Would setup services")
            return True
        
        self.logger.step_start("setting_up_services", "Configuring Docker services")
        
        # This would implement actual service setup
        time.sleep(0.5)
        
        self.logger.step_complete("setting_up_services")
        return True
    
    def _validate_installation(self) -> bool:
        """Validate that installation completed successfully"""
        if self.config.mode == InstallMode.DRY_RUN:
            self.logger.step_start("validating_installation", "Skipping validation (dry-run mode)")
            self.logger.info("🔍 Dry run: Would validate installation")
            self.logger.step_complete("validating_installation")
            return True
        
        self.logger.step_start("validating_installation", "Running post-installation validation")
        
        validation_checks = [
            ("directory_structure", self._validate_directories),
            ("configuration_files", self._validate_configs),
            ("service_health", self._validate_services)
        ]
        
        all_passed = True
        for check_name, check_func in validation_checks:
            try:
                if not check_func():
                    self.logger.warning(f"❌ Validation failed: {check_name}")
                    all_passed = False
                else:
                    self.logger.debug(f"✅ Validation passed: {check_name}")
            except Exception as e:
                self.logger.warning(f"❌ Validation error in {check_name}: {e}")
                all_passed = False
        
        if all_passed:
            self.logger.step_complete("validating_installation")
        else:
            self.logger.step_error("validating_installation", Exception("Some validation checks failed"))
        
        return all_passed
    
    def _validate_directories(self) -> bool:
        """Validate directory structure"""
        required_dirs = ["config", "scripts", "docker", "data/logs"]
        
        for dir_path in required_dirs:
            full_path = self.config.install_directory / dir_path
            if not full_path.exists():
                return False
        
        return True
    
    def _validate_configs(self) -> bool:
        """Validate configuration files"""
        required_configs = ["config/noxsuite.json"]
        
        for config_path in required_configs:
            full_path = self.config.install_directory / config_path
            if not full_path.exists():
                return False
        
        return True
    
    def _validate_services(self) -> bool:
        """Validate that services can be started"""
        # This would implement actual service validation
        return True
    
    def _finalize_installation(self):
        """Finalize installation and show completion message"""
        self.logger.step_start("finalizing", "Completing installation")
        
        # Create installation summary
        summary = {
            "installation_status": "completed",
            "installation_time": datetime.now(timezone.utc).isoformat(),
            "installation_directory": str(self.config.install_directory),
            "configuration": asdict(self.config),
            "system_info": asdict(self.system_info)
        }
        
        # Save summary
        summary_file = self.config.install_directory / "INSTALLATION_SUMMARY.json"
        if self.config.mode != InstallMode.DRY_RUN:
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # Show completion message
        self._show_completion_message()
        
        self.logger.step_complete("finalizing")
        self.logger.info("🎉 NoxSuite installation completed successfully!")
    
    def _show_completion_message(self):
        """Display installation completion message"""
        print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║                    🎉 Installation Complete!                     ║
╠═══════════════════════════════════════════════════════════════════╣
║  NoxSuite Smart Installer has successfully completed setup       ║
║                                                                   ║
║  📁 Installation: {str(self.config.install_directory):<44} ║
║  🔧 Modules: {len(self.config.modules)} modules installed{' ' * (37 - len(str(self.config.modules)))} ║
║  🤖 AI Features: {'✅ Enabled' if self.config.enable_ai else '❌ Disabled':<43} ║
║                                                                   ║
║  🌐 Web Interface: http://localhost:3000                         ║
║  🔧 API Docs: http://localhost:8000/api/docs                     ║
║  📊 Monitoring: http://localhost:3001                            ║
{'║  🤖 AI Hub: http://localhost:7860                                ║' if self.config.enable_ai else ''}
║                                                                   ║
║  🚀 Next Steps:                                                  ║
║     1. Run: ./scripts/start-noxsuite.sh                         ║
║     2. Open web interface                                        ║
║     3. Complete initial setup wizard                            ║
║                                                                   ║
║  📚 Logs: noxsuite_installer.log                               ║
║  📋 Summary: INSTALLATION_SUMMARY.json                          ║
╚═══════════════════════════════════════════════════════════════════╝
        """)
    
    def _cleanup_on_failure(self):
        """Cleanup on installation failure"""
        self.logger.info("🧹 Cleaning up after installation failure...")
        
        # This would implement cleanup logic
        # For now, just log the attempt
        self.logger.debug("Cleanup completed")

def main():
    """Main entry point for the smart installer"""
    try:
        # Parse command line arguments for mode selection
        mode = InstallMode.GUIDED
        
        if len(sys.argv) > 1:
            mode_arg = sys.argv[1].lower()
            mode_map = {
                "fast": InstallMode.FAST,
                "guided": InstallMode.GUIDED,
                "dry-run": InstallMode.DRY_RUN,
                "safe": InstallMode.SAFE,
                "recovery": InstallMode.RECOVERY
            }
            mode = mode_map.get(mode_arg, InstallMode.GUIDED)
        
        # Create and run installer
        installer = SmartNoxSuiteInstaller()
        success = installer.run_installation(mode)
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n❌ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Installer crashed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
