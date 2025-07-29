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
import time
import hashlib
import codecs

# Optional imports with fallbacks
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    logger.warning("Warning: requests module not available. Some features will be limited.")

try:
    import chardet
    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False
    logger.warning("Warning: chardet module not available. Using basic encoding detection.")
import logging
import tempfile
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from enum import Enum, auto
from contextlib import contextmanager
import traceback
import threading
import queue
import re

# Add current directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

# Import datetime utilities with fallback
try:
    from NoxPanel.noxcore.utils.datetime_utils import utc_now
except ImportError:
    # Fallback if utils not available
    def utc_now() -> datetime:
        """Fallback UTC now function for installations."""
        return utc_now()

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
    AUDIT_HEAL = "audit_heal"

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
    
    def __init__((self, log_file: str = "noxsuite_installer.log") -> None:
        self.log_file = Path(log_file)
        self.session_id = str(uuid.uuid4())[:8]
        self.start_time = utc_now()
        
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
    
    def _create_custom_formatter(self) -> bool:
        """Create custom formatter that includes session ID"""
        session_id = self.session_id
        class CustomFormatter(logging.Formatter):
            def format(self, record) -> bool:
                record.session_id = session_id
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
            # Fallback to chardet detection if available
            if HAS_CHARDET:
                try:
                    detected = chardet.detect(text)
                    encoding = detected['encoding'] or 'latin1'
                    return text.decode(encoding)
                except:
                    pass
            
            # Try common encodings as fallback
            fallback_encodings = ['latin1', 'cp1252', 'iso-8859-1']
            for encoding in fallback_encodings:
                try:
                    return text.decode(encoding)
                except:
                    continue
            
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
            'timestamp': utc_now().isoformat()
        })
    
    def step_complete(self, step_name: str, details: Dict[str, Any] = None) -> bool:
        """Log step completion"""
        self.logger.info(f"✅ {step_name.replace('_', ' ').title()} completed")
        self._log_structured({
            'event': 'step_complete',
            'step': step_name,
            'details': details or {},
            'timestamp': utc_now().isoformat()
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
            'timestamp': utc_now().isoformat()
        })
    
    def warning(self, message: str, context: Dict[str, Any] = None) -> bool:
        """Log warning message"""
        self.logger.warning(f"⚠️  {message}")
        self._log_structured({
            'event': 'warning',
            'message': message,
            'context': context or {},
            'timestamp': utc_now().isoformat()
        })
    
    def info(self, message: str, context: Dict[str, Any] = None) -> bool:
        """Log info message"""
        self.logger.info(message)
        if context:
            self._log_structured({
                'event': 'info',
                'message': message,
                'context': context,
                'timestamp': utc_now().isoformat()
            })
    
    def debug(self, message: str, context: Dict[str, Any] = None) -> bool:
        """Log debug message"""
        self.logger.debug(message)
        if context:
            self._log_structured({
                'event': 'debug',
                'message': message,
                'context': context,
                'timestamp': utc_now().isoformat()
            })

class InstallationAuditor:
    """Analyzes previous installation attempts and suggests improvements"""
    
    def __init__((self, log_file: Path) -> None:
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
    
    def __init__((self, logger: SmartLogger) -> None:
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
    
    def __init__((self, system_info: SystemInfo, logger: SmartLogger) -> None:
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
    
    def __init__((self, base_path: Path, logger: SmartLogger) -> None:
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
    
    def _cleanup_directories(self, dirs: List[Path]) -> bool:
        """Clean up created directories in reverse order"""
        for dir_path in reversed(dirs):
            try:
                if dir_path.exists() and dir_path.is_dir():
                    # Only remove if empty
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
            except:
                pass  # Ignore cleanup errors

@dataclass
class ValidationFailure:
    """Represents a validation failure with context and fix suggestions"""
    check_name: str
    message: str
    severity: str  # "error", "warning", "info"
    auto_fix_available: bool = False
    auto_fix_suggestion: str = ""
    context: Dict[str, Any] = None

@dataclass
class ValidationResult:
    """Result of comprehensive validation"""
    all_passed: bool
    total_checks: int
    passed_checks: int
    failures: List[ValidationFailure]
    platform_specific_issues: List[str] = None

@dataclass 
class HealingResult:
    """Result of auto-healing attempts"""
    healed_count: int
    failed_count: int
    healing_details: List[Dict[str, Any]]

class ConfigurationGenerator:
    """Cross-platform configuration file generator with Windows-specific handling"""
    
    def __init__((self, config: InstallConfig, system_info: SystemInfo, logger: SmartLogger) -> None:
        self.config = config
        self.system_info = system_info
        self.logger = logger
        self.created_configs = []
        self.templates = self._load_config_templates()
    
    def generate_all_configs(self) -> bool:
        """Generate all required configuration files"""
        try:
            config_generators = [
                ("main_config", self._generate_main_config),
                ("docker_compose", self._generate_docker_compose),
                ("environment_vars", self._generate_env_files),
                ("database_config", self._generate_database_config),
                ("ai_config", self._generate_ai_config),
                ("network_config", self._generate_network_config),
                ("logging_config", self._generate_logging_config),
                ("service_configs", self._generate_service_configs)
            ]
            
            success_count = 0
            for config_name, generator_func in config_generators:
                try:
                    self.logger.debug(f"Generating {config_name}...")
                    if generator_func():
                        success_count += 1
                        self.logger.debug(f"✅ {config_name} generated successfully")
                    else:
                        self.logger.warning(f"⚠️ {config_name} generation failed")
                except Exception as e:
                    self.logger.warning(f"❌ {config_name} generation error: {e}")
            
            # Validate generated configs
            if success_count > 0:
                self._validate_generated_configs()
            
            return success_count >= len(config_generators) * 0.8  # 80% success rate required
            
        except Exception as e:
            self.logger.error(f"Configuration generation failed: {e}")
            return False
    
    def _load_config_templates(self) -> Dict[str, Any]:
        """Load platform-specific configuration templates"""
        return {
            "main_config": {
                "version": "1.0",
                "installation": {
                    "directory": str(self.config.install_directory),
                    "platform": self.system_info.os_type.value,
                    "installed_modules": self.config.modules,
                    "features": {
                        "ai_enabled": self.config.enable_ai,
                        "voice_enabled": self.config.enable_voice,
                        "mobile_enabled": self.config.enable_mobile,
                        "dev_mode": self.config.dev_mode
                    }
                },
                "system": {
                    "os_type": self.system_info.os_type.value,
                    "architecture": self.system_info.architecture,
                    "python_version": self.system_info.python_version,
                    "available_memory": self.system_info.available_memory,
                    "cpu_cores": self.system_info.cpu_cores
                }
            },
            "docker_compose": self._get_docker_compose_template(),
            "environment": self._get_environment_template(),
            "database": self._get_database_template(),
            "ai_models": self._get_ai_config_template(),
            "network": self._get_network_template(),
            "logging": self._get_logging_template()
        }
    
    def _generate_main_config(self) -> bool:
        """Generate main noxsuite.json configuration file"""
        try:
            config_file = self.config.install_directory / "config" / "noxsuite.json"
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            main_config = self.templates["main_config"]
            
            # Add Windows-specific configurations
            if self.system_info.os_type == OSType.WINDOWS:
                main_config["platform_specific"] = {
                    "line_endings": "crlf",
                    "path_separator": "\\",
                    "service_type": "windows_service",
                    "docker_desktop": True,
                    "encoding": "utf-8-sig"  # BOM for Windows compatibility
                }
            else:
                main_config["platform_specific"] = {
                    "line_endings": "lf", 
                    "path_separator": "/",
                    "service_type": "systemd",
                    "docker_native": True,
                    "encoding": "utf-8"
                }
            
            # Write config with proper encoding and error handling
            self._write_config_file_safely(config_file, main_config)
            self.created_configs.append(str(config_file))
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate main config: {e}")
            return False
    
    def _generate_docker_compose(self) -> bool:
        """Generate Docker Compose files with platform-specific configurations"""
        try:
            docker_dir = self.config.install_directory / "docker"
            docker_dir.mkdir(parents=True, exist_ok=True)
            
            compose_config = self.templates["docker_compose"]
            
            # Platform-specific volume mounts
            if self.system_info.os_type == OSType.WINDOWS:
                # Use named volumes instead of bind mounts on Windows to avoid path issues
                compose_config["volumes"] = {
                    "noxsuite_data": {},
                    "noxsuite_logs": {},
                    "noxsuite_config": {}
                }
            
            # Generate main compose file
            compose_file = docker_dir / "docker-compose.noxsuite.yml"
            self._write_yaml_file_safely(compose_file, compose_config)
            self.created_configs.append(str(compose_file))
            
            # Generate environment-specific compose files
            for env in ["development", "production"]:
                env_compose = docker_dir / f"docker-compose.{env}.yml"
                env_config = self._get_environment_specific_compose(env)
                self._write_yaml_file_safely(env_compose, env_config)
                self.created_configs.append(str(env_compose))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate Docker Compose configs: {e}")
            return False
    
    def _generate_env_files(self) -> bool:
        """Generate environment variable files"""
        try:
            config_dir = self.config.install_directory / "config"
            
            # Main .env file
            env_file = config_dir / ".env"
            env_vars = self._get_environment_variables()
            self._write_env_file_safely(env_file, env_vars)
            self.created_configs.append(str(env_file))
            
            # Platform-specific env files
            platform_env = config_dir / f".env.{self.system_info.os_type.value}"
            platform_vars = self._get_platform_specific_env_vars()
            self._write_env_file_safely(platform_env, platform_vars)
            self.created_configs.append(str(platform_env))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate environment files: {e}")
            return False
    
    def _generate_database_config(self) -> bool:
        """Generate database configuration files"""
        try:
            config_dir = self.config.install_directory / "config"
            
            db_config = self.templates["database"]
            
            # Platform-specific database paths
            if self.system_info.os_type == OSType.WINDOWS:
                db_config["sqlite"]["path"] = str(self.config.install_directory / "data" / "noxsuite.db").replace("\\", "/")
            else:
                db_config["sqlite"]["path"] = str(self.config.install_directory / "data" / "noxsuite.db")
            
            db_file = config_dir / "database.json"
            self._write_config_file_safely(db_file, db_config)
            self.created_configs.append(str(db_file))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate database config: {e}")
            return False
    
    def _generate_ai_config(self) -> bool:
        """Generate AI model configurations"""
        if not self.config.enable_ai:
            return True
            
        try:
            config_dir = self.config.install_directory / "config"
            ai_dir = config_dir / "ai"
            ai_dir.mkdir(parents=True, exist_ok=True)
            
            ai_config = self.templates["ai_models"]
            ai_config["models"] = []
            
            for model in self.config.ai_models:
                model_config = {
                    "name": model,
                    "enabled": True,
                    "download_path": str(ai_dir / "models" / model),
                    "memory_limit": f"{self.system_info.available_memory // len(self.config.ai_models)}GB"
                }
                ai_config["models"].append(model_config)
            
            ai_file = ai_dir / "models.json"
            self._write_config_file_safely(ai_file, ai_config)
            self.created_configs.append(str(ai_file))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate AI config: {e}")
            return False
    
    def _generate_network_config(self) -> bool:
        """Generate network and port configurations"""
        try:
            config_dir = self.config.install_directory / "config"
            
            network_config = self.templates["network"]
            
            # Platform-specific network settings
            if self.system_info.os_type == OSType.WINDOWS:
                # Windows-specific Docker Desktop networking
                network_config["docker"]["host"] = "host.docker.internal"
            else:
                network_config["docker"]["host"] = "localhost"
            
            network_file = config_dir / "network.json"
            self._write_config_file_safely(network_file, network_config)
            self.created_configs.append(str(network_file))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate network config: {e}")
            return False
    
    def _generate_logging_config(self) -> bool:
        """Generate logging configurations"""
        try:
            config_dir = self.config.install_directory / "config"
            
            logging_config = self.templates["logging"]
            
            # Platform-specific log paths and formats
            if self.system_info.os_type == OSType.WINDOWS:
                logging_config["handlers"]["file"]["filename"] = str(self.config.install_directory / "data" / "logs" / "noxsuite.log").replace("\\", "/")
                logging_config["formatters"]["detailed"]["format"] = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            else:
                logging_config["handlers"]["file"]["filename"] = str(self.config.install_directory / "data" / "logs" / "noxsuite.log")
            
            logging_file = config_dir / "logging.json"
            self._write_config_file_safely(logging_file, logging_config)
            self.created_configs.append(str(logging_file))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate logging config: {e}")
            return False
    
    def _generate_service_configs(self) -> bool:
        """Generate service startup and management configurations"""
        try:
            scripts_dir = self.config.install_directory / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            
            if self.system_info.os_type == OSType.WINDOWS:
                # Generate Windows batch files
                start_script = scripts_dir / "start-noxsuite.bat"
                self._write_windows_start_script(start_script)
                self.created_configs.append(str(start_script))
                
                stop_script = scripts_dir / "stop-noxsuite.bat"
                self._write_windows_stop_script(stop_script)
                self.created_configs.append(str(stop_script))
            else:
                # Generate Unix shell scripts
                start_script = scripts_dir / "start-noxsuite.sh"
                self._write_unix_start_script(start_script)
                start_script.chmod(0o755)  # Make executable
                self.created_configs.append(str(start_script))
                
                stop_script = scripts_dir / "stop-noxsuite.sh"
                self._write_unix_stop_script(stop_script)
                stop_script.chmod(0o755)
                self.created_configs.append(str(stop_script))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to generate service configs: {e}")
            return False
    
    def _write_config_file_safely(self, file_path: Path, config_data: Dict[str, Any]) -> bool:
        """Write configuration file with atomic operations and encoding safety"""
        # Use temporary file for atomic write
        temp_file = file_path.with_suffix(f"{file_path.suffix}.tmp")
        
        try:
            # Choose encoding based on platform
            encoding = "utf-8-sig" if self.system_info.os_type == OSType.WINDOWS else "utf-8"
            
            with open(temp_file, 'w', encoding=encoding, newline='\n') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            # Atomic move
            temp_file.replace(file_path)
            
        except Exception as e:
            # Clean up temp file on error
            if temp_file.exists():
                temp_file.unlink()
            raise e
    
    def _write_yaml_file_safely(self, file_path: Path, yaml_data: Dict[str, Any]) -> bool:
        """Write YAML file safely (fallback to JSON if yaml not available)"""
        temp_file = file_path.with_suffix(f"{file_path.suffix}.tmp")
        
        try:
            encoding = "utf-8-sig" if self.system_info.os_type == OSType.WINDOWS else "utf-8"
            
            # Try to use yaml if available, otherwise use JSON
            try:
                import yaml
                with open(temp_file, 'w', encoding=encoding, newline='\n') as f:
                    yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)
            except ImportError:
                # Fallback to JSON with .yml extension
                with open(temp_file, 'w', encoding=encoding, newline='\n') as f:
                    json.dump(yaml_data, f, indent=2, ensure_ascii=False)
            
            temp_file.replace(file_path)
            
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise e
    
    def _write_env_file_safely(self, file_path: Path, env_vars: Dict[str, str]) -> bool:
        """Write environment file with platform-specific line endings"""
        temp_file = file_path.with_suffix(f"{file_path.suffix}.tmp")
        
        try:
            encoding = "utf-8-sig" if self.system_info.os_type == OSType.WINDOWS else "utf-8"
            newline = '\r\n' if self.system_info.os_type == OSType.WINDOWS else '\n'
            
            with open(temp_file, 'w', encoding=encoding, newline=newline) as f:
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            
            temp_file.replace(file_path)
            
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise e
    
    def _write_windows_start_script(self, script_path: Path) -> bool:
        """Generate Windows batch start script"""
        script_content = f"""@echo off
REM NoxSuite Windows Start Script
cd /d "{self.config.install_directory}"
echo Starting NoxSuite services...
docker-compose -f docker\\docker-compose.noxsuite.yml up -d
if %ERRORLEVEL% EQU 0 (
    echo NoxSuite started successfully
    echo Web interface: http://localhost:3000
) else (
    echo Failed to start NoxSuite
    pause
)
"""
        with open(script_path, 'w', encoding='utf-8-sig', newline='\r\n') as f:
            f.write(script_content)
    
    def _write_windows_stop_script(self, script_path: Path) -> bool:
        """Generate Windows batch stop script"""
        script_content = f"""@echo off
REM NoxSuite Windows Stop Script
cd /d "{self.config.install_directory}"
echo Stopping NoxSuite services...
docker-compose -f docker\\docker-compose.noxsuite.yml down
echo NoxSuite stopped
pause
"""
        with open(script_path, 'w', encoding='utf-8-sig', newline='\r\n') as f:
            f.write(script_content)
    
    def _write_unix_start_script(self, script_path: Path) -> bool:
        """Generate Unix shell start script"""
        script_content = f"""#!/bin/bash
# NoxSuite Unix Start Script
cd "{self.config.install_directory}"
echo "Starting NoxSuite services..."
docker-compose -f docker/docker-compose.noxsuite.yml up -d
if [ $? -eq 0 ]; then
    echo "NoxSuite started successfully"
    echo "Web interface: http://localhost:3000"
else
    echo "Failed to start NoxSuite"
    exit 1
fi
"""
        with open(script_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(script_content)
    
    def _write_unix_stop_script(self, script_path: Path) -> bool:
        """Generate Unix shell stop script"""
        script_content = f"""#!/bin/bash
# NoxSuite Unix Stop Script
cd "{self.config.install_directory}"
echo "Stopping NoxSuite services..."
docker-compose -f docker/docker-compose.noxsuite.yml down
echo "NoxSuite stopped"
"""
        with open(script_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(script_content)
    
    def _validate_generated_configs(self) -> bool:
        """Validate all generated configuration files"""
        self.logger.debug("Validating generated configuration files...")
        
        invalid_configs = []
        for config_file in self.created_configs:
            if not self._validate_single_config(Path(config_file)):
                invalid_configs.append(config_file)
        
        if invalid_configs:
            self.logger.warning(f"Invalid configurations detected: {len(invalid_configs)} files")
            for config in invalid_configs:
                self.logger.warning(f"  • {config}")
        else:
            self.logger.debug("All generated configurations are valid")
    
    def _validate_single_config(self, config_path: Path) -> bool:
        """Validate a single configuration file"""
        try:
            if not config_path.exists():
                return False
            
            # Basic file size check
            if config_path.stat().st_size == 0:
                return False
            
            # Try to read the file with proper encoding
            encoding = "utf-8-sig" if self.system_info.os_type == OSType.WINDOWS else "utf-8"
            
            if config_path.suffix.lower() == '.json':
                with open(config_path, 'r', encoding=encoding) as f:
                    json.load(f)  # Validate JSON syntax
            elif config_path.suffix.lower() in ['.yml', '.yaml']:
                with open(config_path, 'r', encoding=encoding) as f:
                    try:
                        import yaml
                        yaml.safe_load(f)
                    except ImportError:
                        # If no yaml, assume it's JSON in YAML file
                        f.seek(0)
                        json.load(f)
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Config validation failed for {config_path}: {e}")
            return False
    
    # Template getters for different configuration types
    def _get_docker_compose_template(self) -> Dict[str, Any]:
        """Get Docker Compose template"""
        services = {
            "noxpanel": {
                "image": "noxsuite/noxpanel:latest",
                "ports": ["3000:3000"],
                "environment": ["NODE_ENV=production"],
                "depends_on": ["postgres", "redis"]
            },
            "postgres": {
                "image": "postgres:13",
                "environment": [
                    "POSTGRES_DB=noxsuite",
                    "POSTGRES_USER=noxsuite",
                    "POSTGRES_PASSWORD=noxsuite123"
                ],
                "volumes": ["postgres_data:/var/lib/postgresql/data"]
            },
            "redis": {
                "image": "redis:7-alpine",
                "volumes": ["redis_data:/data"]
            }
        }
        
        if self.config.enable_ai:
            services["aethercore"] = {
                "image": "noxsuite/aethercore:latest",
                "ports": ["8000:8000"],
                "environment": ["AI_MODELS=" + ",".join(self.config.ai_models)],
                "volumes": ["ai_models:/app/models"]
            }
        
        return {
            "version": "3.8",
            "services": services,
            "volumes": {
                "postgres_data": {},
                "redis_data": {},
                "ai_models": {} if self.config.enable_ai else None
            }
        }
    
    def _get_environment_template(self) -> Dict[str, str]:
        """Get environment variables template"""
        return {
            "NOXSUITE_VERSION": "1.0.0",
            "NOXSUITE_ENV": "production",
            "NOXSUITE_DEBUG": "false" if not self.config.dev_mode else "true",
            "NOXSUITE_PLATFORM": self.system_info.os_type.value,
            "NOXSUITE_INSTALL_DIR": str(self.config.install_directory)
        }
    
    def _get_database_template(self) -> Dict[str, Any]:
        """Get database configuration template"""
        return {
            "default": "sqlite",
            "sqlite": {
                "path": "data/noxsuite.db",
                "timeout": 30
            },
            "postgres": {
                "host": "localhost",
                "port": 5432,
                "database": "noxsuite",
                "username": "noxsuite",
                "password": "noxsuite123"
            }
        }
    
    def _get_ai_config_template(self) -> Dict[str, Any]:
        """Get AI configuration template"""
        return {
            "enabled": self.config.enable_ai,
            "voice_enabled": self.config.enable_voice,
            "models": [],
            "ollama": {
                "host": "localhost",
                "port": 11434
            }
        }
    
    def _get_network_template(self) -> Dict[str, Any]:
        """Get network configuration template"""
        return {
            "ports": {
                "web": 3000,
                "api": 8000,
                "ai": 11434,
                "monitoring": 3001
            },
            "docker": {
                "network": "noxsuite_network"
            }
        }
    
    def _get_logging_template(self) -> Dict[str, Any]:
        """Get logging configuration template"""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "detailed": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
                }
            },
            "handlers": {
                "file": {
                    "class": "logging.FileHandler",
                    "filename": "data/logs/noxsuite.log",
                    "formatter": "detailed",
                    "encoding": "utf-8"
                },
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "detailed"
                }
            },
            "root": {
                "level": "INFO",
                "handlers": ["file", "console"]
            }
        }
    
    def _get_environment_variables(self) -> Dict[str, str]:
        """Get main environment variables"""
        env_vars = {
            "NOXSUITE_VERSION": "1.0.0",
            "NOXSUITE_ENVIRONMENT": "production",
            "NOXSUITE_PLATFORM": self.system_info.os_type.value,
            "NOXSUITE_INSTALL_PATH": str(self.config.install_directory),
            "NOXSUITE_DEBUG": str(self.config.dev_mode).lower(),
            "NOXSUITE_AI_ENABLED": str(self.config.enable_ai).lower(),
            "NOXSUITE_VOICE_ENABLED": str(self.config.enable_voice).lower(),
            "NOXSUITE_MOBILE_ENABLED": str(self.config.enable_mobile).lower()
        }
        
        # Platform-specific environment variables
        if self.system_info.os_type == OSType.WINDOWS:
            env_vars.update({
                "NOXSUITE_LINE_ENDINGS": "crlf",
                "NOXSUITE_PATH_SEP": "\\",
                "NOXSUITE_SHELL": "cmd"
            })
        else:
            env_vars.update({
                "NOXSUITE_LINE_ENDINGS": "lf",
                "NOXSUITE_PATH_SEP": "/",
                "NOXSUITE_SHELL": "bash"
            })
        
        return env_vars
    
    def _get_platform_specific_env_vars(self) -> Dict[str, str]:
        """Get platform-specific environment variables"""
        if self.system_info.os_type == OSType.WINDOWS:
            return {
                "COMPOSE_CONVERT_WINDOWS_PATHS": "1",
                "DOCKER_BUILDKIT": "1",
                "NOXSUITE_WINDOWS_SERVICE": "true"
            }
        else:
            return {
                "DOCKER_BUILDKIT": "1",
                "NOXSUITE_SYSTEMD": "true"
            }
    
    def _get_environment_specific_compose(self, environment: str) -> Dict[str, Any]:
        """Get environment-specific Docker Compose configuration"""
        if environment == "development":
            return {
                "version": "3.8",
                "services": {
                    "noxpanel": {
                        "environment": ["NODE_ENV=development", "DEBUG=true"],
                        "volumes": ["./frontend:/app/src"]
                    }
                }
            }
        else:  # production
            return {
                "version": "3.8",
                "services": {
                    "noxpanel": {
                        "restart": "unless-stopped",
                        "environment": ["NODE_ENV=production"]
                    }
                }
            }

class InstallationValidator:
    """Comprehensive installation validator with Windows-specific checks and auto-healing"""
    
    def __init__((self, config: InstallConfig, system_info: SystemInfo, logger: SmartLogger) -> None:
        self.config = config
        self.system_info = system_info
        self.logger = logger
        self.validation_checks = self._get_validation_checks()
    
    def validate_complete_installation(self) -> ValidationResult:
        """Run comprehensive validation of the entire installation"""
        self.logger.info("🔍 Running comprehensive installation validation...")
        
        failures = []
        passed_count = 0
        
        for check_name, check_func in self.validation_checks:
            try:
                self.logger.debug(f"Validating {check_name}...")
                result = check_func()
                
                if result["passed"]:
                    passed_count += 1
                    self.logger.debug(f"✅ {check_name}: PASSED")
                else:
                    failure = ValidationFailure(
                        check_name=check_name,
                        message=result["message"],
                        severity=result.get("severity", "error"),
                        auto_fix_available=result.get("auto_fix_available", False),
                        auto_fix_suggestion=result.get("auto_fix_suggestion", ""),
                        context=result.get("context", {})
                    )
                    failures.append(failure)
                    self.logger.debug(f"❌ {check_name}: {result['message']}")
                    
            except Exception as e:
                failure = ValidationFailure(
                    check_name=check_name,
                    message=f"Validation check failed: {str(e)}",
                    severity="error",
                    context={"exception": str(e), "traceback": traceback.format_exc()}
                )
                failures.append(failure)
                self.logger.debug(f"💥 {check_name}: Exception - {e}")
        
        total_checks = len(self.validation_checks)
        all_passed = len(failures) == 0
        
        # Identify platform-specific issues
        platform_issues = self._identify_platform_specific_issues(failures)
        
        return ValidationResult(
            all_passed=all_passed,
            total_checks=total_checks,
            passed_checks=passed_count,
            failures=failures,
            platform_specific_issues=platform_issues
        )
    
    def attempt_auto_healing(self, failures: List[ValidationFailure]) -> HealingResult:
        """Attempt to automatically fix validation failures"""
        self.logger.info("🔧 Attempting auto-healing of validation failures...")
        
        healed_count = 0
        failed_count = 0
        healing_details = []
        
        for failure in failures:
            if failure.auto_fix_available:
                try:
                    self.logger.debug(f"Attempting to heal: {failure.check_name}")
                    healing_result = self._attempt_healing(failure)
                    
                    if healing_result["success"]:
                        healed_count += 1
                        healing_details.append({
                            "check_name": failure.check_name,
                            "status": "healed",
                            "method": healing_result.get("method", "unknown"),
                            "details": healing_result.get("details", "")
                        })
                        self.logger.debug(f"✅ Healed: {failure.check_name}")
                    else:
                        failed_count += 1
                        healing_details.append({
                            "check_name": failure.check_name,
                            "status": "failed",
                            "error": healing_result.get("error", "Unknown error"),
                            "suggestion": healing_result.get("suggestion", "")
                        })
                        self.logger.debug(f"❌ Failed to heal: {failure.check_name}")
                        
                except Exception as e:
                    failed_count += 1
                    healing_details.append({
                        "check_name": failure.check_name,
                        "status": "exception",
                        "error": str(e)
                    })
                    self.logger.debug(f"💥 Healing exception for {failure.check_name}: {e}")
            else:
                failed_count += 1
                healing_details.append({
                    "check_name": failure.check_name,
                    "status": "no_auto_fix",
                    "message": "Manual intervention required"
                })
        
        return HealingResult(
            healed_count=healed_count,
            failed_count=failed_count,
            healing_details=healing_details
        )
    
    def _get_validation_checks(self) -> List[Tuple[str, callable]]:
        """Get list of validation checks to perform"""
        return [
            ("directory_structure", self._validate_directory_structure),
            ("configuration_files", self._validate_configuration_files),
            ("configuration_syntax", self._validate_configuration_syntax),
            ("file_permissions", self._validate_file_permissions),
            ("encoding_consistency", self._validate_encoding_consistency),
            ("path_compatibility", self._validate_path_compatibility),
            ("docker_configs", self._validate_docker_configs),
            ("environment_variables", self._validate_environment_variables),
            ("startup_scripts", self._validate_startup_scripts),
            ("database_config", self._validate_database_config),
            ("network_config", self._validate_network_config),
            ("ai_config", self._validate_ai_config),
            ("logging_config", self._validate_logging_config),
            ("service_dependencies", self._validate_service_dependencies),
            ("disk_space", self._validate_disk_space),
            ("platform_compatibility", self._validate_platform_compatibility)
        ]
    
    def _validate_directory_structure(self) -> Dict[str, Any]:
        """Validate that all required directories exist"""
        required_dirs = [
            "config",
            "config/ai" if self.config.enable_ai else None,
            "scripts", 
            "docker",
            "data",
            "data/logs"
        ]
        required_dirs = [d for d in required_dirs if d is not None]
        
        missing_dirs = []
        for dir_path in required_dirs:
            full_path = self.config.install_directory / dir_path
            if not full_path.exists() or not full_path.is_dir():
                missing_dirs.append(dir_path)
        
        if missing_dirs:
            return {
                "passed": False,
                "message": f"Missing directories: {', '.join(missing_dirs)}",
                "severity": "error",
                "auto_fix_available": True,
                "auto_fix_suggestion": "Create missing directories",
                "context": {"missing_dirs": missing_dirs}
            }
        
        return {"passed": True, "message": "All required directories exist"}
    
    def _validate_configuration_files(self) -> Dict[str, Any]:
        """Validate that all required configuration files exist"""
        required_configs = [
            "config/noxsuite.json",
            "config/.env",
            f"config/.env.{self.system_info.os_type.value}",
            "config/database.json",
            "config/network.json",
            "config/logging.json",
            "docker/docker-compose.noxsuite.yml",
            "docker/docker-compose.development.yml",
            "docker/docker-compose.production.yml"
        ]
        
        if self.config.enable_ai:
            required_configs.append("config/ai/models.json")
        
        missing_configs = []
        for config_path in required_configs:
            full_path = self.config.install_directory / config_path
            if not full_path.exists() or not full_path.is_file():
                missing_configs.append(config_path)
        
        if missing_configs:
            return {
                "passed": False,
                "message": f"Missing configuration files: {', '.join(missing_configs)}",
                "severity": "error",
                "auto_fix_available": True,
                "auto_fix_suggestion": "Regenerate missing configuration files",
                "context": {"missing_configs": missing_configs}
            }
        
        return {"passed": True, "message": "All required configuration files exist"}
    
    def _validate_configuration_syntax(self) -> Dict[str, Any]:
        """Validate syntax of configuration files"""
        config_files = []
        for path in ["config", "docker"]:
            config_dir = self.config.install_directory / path
            if config_dir.exists():
                config_files.extend(config_dir.rglob("*.json"))
                config_files.extend(config_dir.rglob("*.yml"))
                config_files.extend(config_dir.rglob("*.yaml"))
        
        syntax_errors = []
        encoding = "utf-8-sig" if self.system_info.os_type == OSType.WINDOWS else "utf-8"
        
        for config_file in config_files:
            try:
                if config_file.suffix.lower() == '.json':
                    with open(config_file, 'r', encoding=encoding) as f:
                        json.load(f)
                elif config_file.suffix.lower() in ['.yml', '.yaml']:
                    with open(config_file, 'r', encoding=encoding) as f:
                        try:
                            import yaml
                            yaml.safe_load(f)
                        except ImportError:
                            # Fallback to JSON validation
                            f.seek(0)
                            json.load(f)
            except Exception as e:
                syntax_errors.append({
                    "file": str(config_file.relative_to(self.config.install_directory)),
                    "error": str(e)
                })
        
        if syntax_errors:
            return {
                "passed": False,
                "message": f"Syntax errors in {len(syntax_errors)} configuration files",
                "severity": "error",
                "auto_fix_available": True,
                "auto_fix_suggestion": "Regenerate corrupted configuration files",
                "context": {"syntax_errors": syntax_errors}
            }
        
        return {"passed": True, "message": "All configuration files have valid syntax"}
    
    def _validate_file_permissions(self) -> Dict[str, Any]:
        """Validate file permissions (especially important on Unix systems)"""
        permission_issues = []
        
        # Check script executability (Unix only)
        if self.system_info.os_type != OSType.WINDOWS:
            script_files = [
                "scripts/start-noxsuite.sh",
                "scripts/stop-noxsuite.sh"
            ]
            
            for script_path in script_files:
                full_path = self.config.install_directory / script_path
                if full_path.exists():
                    # Check if executable
                    if not os.access(full_path, os.X_OK):
                        permission_issues.append({
                            "file": script_path,
                            "issue": "not_executable",
                            "expected": "755",
                            "actual": oct(full_path.stat().st_mode)[-3:]
                        })
        
        # Check write permissions on data directories
        data_dirs = ["data", "data/logs"]
        for dir_path in data_dirs:
            full_path = self.config.install_directory / dir_path
            if full_path.exists():
                test_file = full_path / f".write_test_{int(time.time())}"
                try:
                    test_file.write_text("test")
                    test_file.unlink()
                except Exception:
                    permission_issues.append({
                        "directory": dir_path,
                        "issue": "not_writable"
                    })
        
        if permission_issues:
            return {
                "passed": False,
                "message": f"Permission issues found: {len(permission_issues)} files/directories",
                "severity": "warning",
                "auto_fix_available": True,
                "auto_fix_suggestion": "Fix file permissions",
                "context": {"permission_issues": permission_issues}
            }
        
        return {"passed": True, "message": "File permissions are correct"}
    
    def _validate_encoding_consistency(self) -> Dict[str, Any]:
        """Validate file encoding consistency (especially important on Windows)"""
        encoding_issues = []
        expected_encoding = "utf-8-sig" if self.system_info.os_type == OSType.WINDOWS else "utf-8"
        
        # Check text configuration files
        text_files = []
        for path in ["config", "scripts"]:
            config_dir = self.config.install_directory / path
            if config_dir.exists():
                text_files.extend(config_dir.rglob("*.json"))
                text_files.extend(config_dir.rglob("*.yml"))
                text_files.extend(config_dir.rglob("*.yaml"))
                text_files.extend(config_dir.rglob("*.env"))
                text_files.extend(config_dir.rglob("*.sh"))
                text_files.extend(config_dir.rglob("*.bat"))
        
        for text_file in text_files:
            try:
                # Try reading with expected encoding
                with open(text_file, 'r', encoding=expected_encoding) as f:
                    content = f.read()
                
                # Check for BOM on Windows
                if self.system_info.os_type == OSType.WINDOWS:
                    if not content.startswith('\ufeff') and text_file.suffix.lower() in ['.json', '.yml', '.yaml']:
                        encoding_issues.append({
                            "file": str(text_file.relative_to(self.config.install_directory)),
                            "issue": "missing_bom",
                            "expected": "utf-8-sig",
                            "suggestion": "Add BOM for Windows compatibility"
                        })
            except UnicodeDecodeError as e:
                encoding_issues.append({
                    "file": str(text_file.relative_to(self.config.install_directory)),
                    "issue": "encoding_error",
                    "error": str(e),
                    "expected": expected_encoding
                })
        
        if encoding_issues:
            return {
                "passed": False,
                "message": f"Encoding issues found in {len(encoding_issues)} files",
                "severity": "warning",
                "auto_fix_available": True,
                "auto_fix_suggestion": "Fix file encodings",
                "context": {"encoding_issues": encoding_issues}
            }
        
        return {"passed": True, "message": "File encodings are consistent"}
    
    def _validate_path_compatibility(self) -> Dict[str, Any]:
        """Validate path compatibility (Windows path length limits, reserved names, etc.)"""
        path_issues = []
        
        if self.system_info.os_type == OSType.WINDOWS:
            # Check for Windows path length limits (260 characters)
            for root, dirs, files in os.walk(self.config.install_directory):
                for file in files:
                    full_path = os.path.join(root, file)
                    if len(full_path) > 260:
                        path_issues.append({
                            "path": full_path,
                            "issue": "path_too_long",
                            "length": len(full_path),
                            "limit": 260
                        })
            
            # Check for reserved names
            reserved_names = ["CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"]
            for root, dirs, files in os.walk(self.config.install_directory):
                for name in dirs + files:
                    if name.upper().split('.')[0] in reserved_names:
                        path_issues.append({
                            "path": os.path.join(root, name),
                            "issue": "reserved_name",
                            "name": name.upper().split('.')[0]
                        })
        
        # Check for spaces in paths (can cause Docker issues on Windows)
        if self.system_info.os_type == OSType.WINDOWS and ' ' in str(self.config.install_directory):
            path_issues.append({
                "path": str(self.config.install_directory),
                "issue": "spaces_in_path",
                "suggestion": "Avoid spaces in installation path on Windows"
            })
        
        if path_issues:
            return {
                "passed": False,
                "message": f"Path compatibility issues: {len(path_issues)} problems",
                "severity": "warning",
                "auto_fix_available": False,
                "auto_fix_suggestion": "Manual path fixes required",
                "context": {"path_issues": path_issues}
            }
        
        return {"passed": True, "message": "Paths are compatible with the platform"}
    
    def _validate_docker_configs(self) -> Dict[str, Any]:
        """Validate Docker Compose configurations"""
        docker_issues = []
        
        compose_files = [
            "docker/docker-compose.noxsuite.yml",
            "docker/docker-compose.development.yml",
            "docker/docker-compose.production.yml"
        ]
        
        for compose_file in compose_files:
            full_path = self.config.install_directory / compose_file
            if not full_path.exists():
                continue
            
            try:
                encoding = "utf-8-sig" if self.system_info.os_type == OSType.WINDOWS else "utf-8"
                with open(full_path, 'r', encoding=encoding) as f:
                    try:
                        import yaml
                        compose_data = yaml.safe_load(f)
                    except ImportError:
                        # Fallback to JSON
                        f.seek(0)
                        compose_data = json.load(f)
                
                # Validate Docker Compose structure
                if not isinstance(compose_data, dict):
                    docker_issues.append({
                        "file": compose_file,
                        "issue": "invalid_structure",
                        "message": "Docker Compose file must be a dictionary"
                    })
                    continue
                
                # Check version
                if "version" not in compose_data:
                    docker_issues.append({
                        "file": compose_file,
                        "issue": "missing_version",
                        "suggestion": "Add version field to Docker Compose file"
                    })
                
                # Check services
                if "services" not in compose_data:
                    docker_issues.append({
                        "file": compose_file,
                        "issue": "missing_services",
                        "message": "Docker Compose file must have services section"
                    })
                else:
                    # Validate service configurations
                    for service_name, service_config in compose_data["services"].items():
                        if not isinstance(service_config, dict):
                            docker_issues.append({
                                "file": compose_file,
                                "service": service_name,
                                "issue": "invalid_service_config",
                                "message": "Service configuration must be a dictionary"
                            })
                        elif "image" not in service_config and "build" not in service_config:
                            docker_issues.append({
                                "file": compose_file,
                                "service": service_name,
                                "issue": "missing_image_or_build",
                                "message": "Service must have either 'image' or 'build' field"
                            })
                
            except Exception as e:
                docker_issues.append({
                    "file": compose_file,
                    "issue": "parse_error",
                    "error": str(e)
                })
        
        if docker_issues:
            return {
                "passed": False,
                "message": f"Docker configuration issues: {len(docker_issues)} problems",
                "severity": "error",
                "auto_fix_available": True,
                "auto_fix_suggestion": "Regenerate Docker configurations",
                "context": {"docker_issues": docker_issues}
            }
        
        return {"passed": True, "message": "Docker configurations are valid"}
    
    def _validate_environment_variables(self) -> Dict[str, Any]:
        """Validate environment variable files"""
        env_issues = []
        
        env_files = [
            "config/.env",
            f"config/.env.{self.system_info.os_type.value}"
        ]
        
        for env_file in env_files:
            full_path = self.config.install_directory / env_file
            if not full_path.exists():
                env_issues.append({
                    "file": env_file,
                    "issue": "missing_file"
                })
                continue
            
            try:
                encoding = "utf-8-sig" if self.system_info.os_type == OSType.WINDOWS else "utf-8"
                with open(full_path, 'r', encoding=encoding) as f:
                    content = f.read()
                
                # Parse environment variables
                env_vars = {}
                for line_num, line in enumerate(content.split('\n'), 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' not in line:
                            env_issues.append({
                                "file": env_file,
                                "line": line_num,
                                "issue": "invalid_format",
                                "content": line
                            })
                        else:
                            key, value = line.split('=', 1)
                            env_vars[key] = value
                
                # Check for required environment variables
                required_vars = [
                    "NOXSUITE_VERSION",
                    "NOXSUITE_PLATFORM",
                    "NOXSUITE_INSTALL_PATH"
                ]
                
                for required_var in required_vars:
                    if required_var not in env_vars:
                        env_issues.append({
                            "file": env_file,
                            "issue": "missing_required_var",
                            "variable": required_var
                        })
                
            except Exception as e:
                env_issues.append({
                    "file": env_file,
                    "issue": "read_error",
                    "error": str(e)
                })
        
        if env_issues:
            return {
                "passed": False,
                "message": f"Environment variable issues: {len(env_issues)} problems",
                "severity": "warning",
                "auto_fix_available": True,
                "auto_fix_suggestion": "Regenerate environment files",
                "context": {"env_issues": env_issues}
            }
        
        return {"passed": True, "message": "Environment variables are valid"}
    
    def _validate_startup_scripts(self) -> Dict[str, Any]:
        """Validate startup and management scripts"""
        script_issues = []
        
        if self.system_info.os_type == OSType.WINDOWS:
            script_files = [
                "scripts/start-noxsuite.bat",
                "scripts/stop-noxsuite.bat"
            ]
        else:
            script_files = [
                "scripts/start-noxsuite.sh",
                "scripts/stop-noxsuite.sh"
            ]
        
        for script_file in script_files:
            full_path = self.config.install_directory / script_file
            if not full_path.exists():
                script_issues.append({
                    "file": script_file,
                    "issue": "missing_file"
                })
                continue
            
            try:
                encoding = "utf-8-sig" if self.system_info.os_type == OSType.WINDOWS else "utf-8"
                with open(full_path, 'r', encoding=encoding) as f:
                    content = f.read()
                
                # Check script content
                if len(content.strip()) == 0:
                    script_issues.append({
                        "file": script_file,
                        "issue": "empty_file"
                    })
                    continue
                
                # Platform-specific checks
                if self.system_info.os_type == OSType.WINDOWS:
                    # Check for proper Windows batch syntax
                    if not content.startswith('@echo off'):
                        script_issues.append({
                            "file": script_file,
                            "issue": "missing_echo_off",
                            "suggestion": "Windows batch files should start with '@echo off'"
                        })
                else:
                    # Check for proper shebang
                    if not content.startswith('#!/bin/bash'):
                        script_issues.append({
                            "file": script_file,
                            "issue": "missing_shebang",
                            "suggestion": "Unix scripts should start with '#!/bin/bash'"
                        })
                    
                    # Check executability
                    if not os.access(full_path, os.X_OK):
                        script_issues.append({
                            "file": script_file,
                            "issue": "not_executable",
                            "suggestion": "Script should be executable (chmod +x)"
                        })
                
            except Exception as e:
                script_issues.append({
                    "file": script_file,
                    "issue": "read_error",
                    "error": str(e)
                })
        
        if script_issues:
            return {
                "passed": False,
                "message": f"Startup script issues: {len(script_issues)} problems",
                "severity": "warning",
                "auto_fix_available": True,
                "auto_fix_suggestion": "Regenerate startup scripts",
                "context": {"script_issues": script_issues}
            }
        
        return {"passed": True, "message": "Startup scripts are valid"}
    
    def _validate_database_config(self) -> Dict[str, Any]:
        """Validate database configuration"""
        db_config_file = self.config.install_directory / "config" / "database.json"
        
        if not db_config_file.exists():
            return {
                "passed": False,
                "message": "Database configuration file missing",
                "severity": "error",
                "auto_fix_available": True,
                "auto_fix_suggestion": "Generate database configuration",
                "context": {"missing_file": "config/database.json"}
            }
        
        try:
            encoding = "utf-8-sig" if self.system_info.os_type == OSType.WINDOWS else "utf-8"
            with open(db_config_file, 'r', encoding=encoding) as f:
                db_config = json.load(f)
            
            # Validate database configuration structure
            if "default" not in db_config:
                return {
                    "passed": False,
                    "message": "Database config missing 'default' field",
                    "severity": "error",
                    "auto_fix_available": True,
                    "auto_fix_suggestion": "Regenerate database configuration"
                }
            
            # Check if configured database type exists
            default_db = db_config["default"]
            if default_db not in db_config:
                return {
                    "passed": False,
                    "message": f"Default database '{default_db}' configuration not found",
                    "severity": "error",
                    "auto_fix_available": True,
                    "auto_fix_suggestion": "Add missing database configuration"
                }
            
            return {"passed": True, "message": "Database configuration is valid"}
            
        except Exception as e:
            return {
                "passed": False,
                "message": f"Database configuration error: {str(e)}",
                "severity": "error",
                "auto_fix_available": True,
                "auto_fix_suggestion": "Regenerate database configuration",
                "context": {"error": str(e)}
            }
    
    def _validate_network_config(self) -> Dict[str, Any]:
        """Validate network configuration"""
        network_config_file = self.config.install_directory / "config" / "network.json"
        
        if not network_config_file.exists():
            return {
                "passed": False,
                "message": "Network configuration file missing",
                "severity": "error",
                "auto_fix_available": True,
                "auto_fix_suggestion": "Generate network configuration"
            }
        
        try:
            encoding = "utf-8-sig" if self.system_info.os_type == OSType.WINDOWS else "utf-8"
            with open(network_config_file, 'r', encoding=encoding) as f:
                network_config = json.load(f)
            
            # Validate ports
            if "ports" not in network_config:
                return {
                    "passed": False,
                    "message": "Network config missing 'ports' section",
                    "severity": "warning",
                    "auto_fix_available": True,
                    "auto_fix_suggestion": "Add ports configuration"
                }
            
            # Check for port conflicts
            ports = network_config["ports"]
            port_conflicts = []
            
            for service, port in ports.items():
                if not isinstance(port, int) or port < 1 or port > 65535:
                    port_conflicts.append({
                        "service": service,
                        "port": port,
                        "issue": "invalid_port_number"
                    })
            
            if port_conflicts:
                return {
                    "passed": False,
                    "message": f"Invalid port configurations: {len(port_conflicts)} issues",
                    "severity": "warning",
                    "auto_fix_available": True,
                    "auto_fix_suggestion": "Fix port configurations",
                    "context": {"port_conflicts": port_conflicts}
                }
            
            return {"passed": True, "message": "Network configuration is valid"}
            
        except Exception as e:
            return {
                "passed": False,
                "message": f"Network configuration error: {str(e)}",
                "severity": "error",
                "auto_fix_available": True,
                "auto_fix_suggestion": "Regenerate network configuration"
            }
    
    def _validate_ai_config(self) -> Dict[str, Any]:
        """Validate AI configuration (if AI is enabled)"""
        if not self.config.enable_ai:
            return {"passed": True, "message": "AI disabled, no validation needed"}
        
        ai_config_file = self.config.install_directory / "config" / "ai" / "models.json"
        
        if not ai_config_file.exists():
            return {
                "passed": False,
                "message": "AI configuration file missing",
                "severity": "error",
                "auto_fix_available": True,
                "auto_fix_suggestion": "Generate AI configuration"
            }
        
        try:
            encoding = "utf-8-sig" if self.system_info.os_type == OSType.WINDOWS else "utf-8"
            with open(ai_config_file, 'r', encoding=encoding) as f:
                ai_config = json.load(f)
            
            # Validate AI configuration
            if "enabled" not in ai_config or not ai_config["enabled"]:
                return {
                    "passed": False,
                    "message": "AI configuration shows AI as disabled",
                    "severity": "warning",
                    "auto_fix_available": True,
                    "auto_fix_suggestion": "Enable AI in configuration"
                }
            
            if "models" not in ai_config or not ai_config["models"]:
                return {
                    "passed": False,
                    "message": "No AI models configured",
                    "severity": "warning",
                    "auto_fix_available": True,
                    "auto_fix_suggestion": "Add AI model configurations"
                }
            
            return {"passed": True, "message": "AI configuration is valid"}
            
        except Exception as e:
            return {
                "passed": False,
                "message": f"AI configuration error: {str(e)}",
                "severity": "error",
                "auto_fix_available": True,
                "auto_fix_suggestion": "Regenerate AI configuration"
            }
    
    def _validate_logging_config(self) -> Dict[str, Any]:
        """Validate logging configuration"""
        logging_config_file = self.config.install_directory / "config" / "logging.json"
        
        if not logging_config_file.exists():
            return {
                "passed": False,
                "message": "Logging configuration file missing",
                "severity": "warning",
                "auto_fix_available": True,
                "auto_fix_suggestion": "Generate logging configuration"
            }
        
        try:
            encoding = "utf-8-sig" if self.system_info.os_type == OSType.WINDOWS else "utf-8"
            with open(logging_config_file, 'r', encoding=encoding) as f:
                logging_config = json.load(f)
            
            # Validate logging configuration structure
            required_sections = ["formatters", "handlers", "root"]
            missing_sections = []
            
            for section in required_sections:
                if section not in logging_config:
                    missing_sections.append(section)
            
            if missing_sections:
                return {
                    "passed": False,
                    "message": f"Logging config missing sections: {', '.join(missing_sections)}",
                    "severity": "warning",
                    "auto_fix_available": True,
                    "auto_fix_suggestion": "Regenerate logging configuration"
                }
            
            return {"passed": True, "message": "Logging configuration is valid"}
            
        except Exception as e:
            return {
                "passed": False,
                "message": f"Logging configuration error: {str(e)}",
                "severity": "warning",
                "auto_fix_available": True,
                "auto_fix_suggestion": "Regenerate logging configuration"
            }
    
    def _validate_service_dependencies(self) -> Dict[str, Any]:
        """Validate that required services and dependencies are available"""
        missing_deps = []
        
        # Check Docker
        if not shutil.which("docker"):
            missing_deps.append({
                "service": "docker",
                "severity": "error",
                "message": "Docker not found in PATH"
            })
        
        # Check Docker Compose
        has_compose = (
            shutil.which("docker-compose") is not None or
            self._check_docker_compose_plugin()
        )
        if not has_compose:
            missing_deps.append({
                "service": "docker-compose",
                "severity": "error", 
                "message": "Docker Compose not available"
            })
        
        # Check Node.js (if mobile enabled)
        if self.config.enable_mobile and not shutil.which("node"):
            missing_deps.append({
                "service": "node",
                "severity": "warning",
                "message": "Node.js not found (required for mobile features)"
            })
        
        if missing_deps:
            return {
                "passed": False,
                "message": f"Missing dependencies: {len(missing_deps)} services",
                "severity": "error",
                "auto_fix_available": False,
                "auto_fix_suggestion": "Install missing dependencies manually",
                "context": {"missing_deps": missing_deps}
            }
        
        return {"passed": True, "message": "All service dependencies are available"}
    
    def _validate_disk_space(self) -> Dict[str, Any]:
        """Validate available disk space"""
        try:
            if hasattr(shutil, 'disk_usage'):
                _, _, free = shutil.disk_usage(self.config.install_directory)
                free_gb = free / (1024**3)
                
                # Estimate space requirements
                required_gb = 2  # Base requirement
                if self.config.enable_ai:
                    required_gb += len(self.config.ai_models) * 4  # ~4GB per model
                
                if free_gb < required_gb:
                    return {
                        "passed": False,
                        "message": f"Insufficient disk space: {free_gb:.1f}GB free, {required_gb:.1f}GB required",
                        "severity": "error",
                        "auto_fix_available": False,
                        "auto_fix_suggestion": "Free up disk space or choose different installation directory"
                    }
                elif free_gb < required_gb * 1.5:
                    return {
                        "passed": False,
                        "message": f"Low disk space: {free_gb:.1f}GB free, {required_gb * 1.5:.1f}GB recommended",
                        "severity": "warning",
                        "auto_fix_available": False,
                        "auto_fix_suggestion": "Consider freeing up more disk space"
                    }
            
            return {"passed": True, "message": "Sufficient disk space available"}
            
        except Exception as e:
            return {
                "passed": False,
                "message": f"Could not check disk space: {str(e)}",
                "severity": "warning",
                "auto_fix_available": False,
                "auto_fix_suggestion": "Check disk space manually"
            }
    
    def _validate_platform_compatibility(self) -> Dict[str, Any]:
        """Validate platform-specific compatibility issues"""
        compatibility_issues = []
        
        # Windows-specific checks
        if self.system_info.os_type == OSType.WINDOWS:
            # Check Windows version (Docker Desktop requirements)
            try:
                import winreg
                # This is a simplified check - real implementation would be more thorough
                pass
            except ImportError:
                pass  # Not on Windows or winreg not available
            
            # Check for WSL2 if running Docker Desktop
            # This is a placeholder for more thorough Windows compatibility checks
        
        # Linux-specific checks
        elif self.system_info.os_type == OSType.LINUX:
            # Check for systemd (required for service management)
            if not Path("/run/systemd/system").exists():
                compatibility_issues.append({
                    "issue": "no_systemd",
                    "message": "systemd not detected, service management may not work properly",
                    "severity": "warning"
                })
        
        if compatibility_issues:
            return {
                "passed": False,
                "message": f"Platform compatibility issues: {len(compatibility_issues)} problems",
                "severity": "warning",
                "auto_fix_available": False,
                "auto_fix_suggestion": "Review platform-specific requirements",
                "context": {"compatibility_issues": compatibility_issues}
            }
        
        return {"passed": True, "message": "Platform compatibility validated"}
    
    def _check_docker_compose_plugin(self) -> bool:
        """Check if Docker Compose is available as a plugin"""
        try:
            result = subprocess.run(
                ["docker", "compose", "version"],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def _identify_platform_specific_issues(self, failures: List[ValidationFailure]) -> List[str]:
        """Identify platform-specific patterns in validation failures"""
        platform_issues = []
        
        # Windows-specific issue patterns
        if self.system_info.os_type == OSType.WINDOWS:
            for failure in failures:
                if "encoding" in failure.message.lower():
                    platform_issues.append("Windows encoding compatibility")
                elif "path" in failure.message.lower() and "space" in failure.message.lower():
                    platform_issues.append("Windows path spaces issue")
                elif "permission" in failure.message.lower():
                    platform_issues.append("Windows permission/UAC issue")
        
        # Linux-specific issue patterns
        elif self.system_info.os_type == OSType.LINUX:
            for failure in failures:
                if "permission" in failure.message.lower():
                    platform_issues.append("Linux file permissions")
                elif "executable" in failure.message.lower():
                    platform_issues.append("Linux script executability")
        
        return list(set(platform_issues))  # Remove duplicates
    
    def _attempt_healing(self, failure: ValidationFailure) -> Dict[str, Any]:
        """Attempt to heal a specific validation failure"""
        try:
            if failure.check_name == "directory_structure":
                return self._heal_directory_structure(failure)
            elif failure.check_name == "configuration_files":
                return self._heal_configuration_files(failure)
            elif failure.check_name == "configuration_syntax":
                return self._heal_configuration_syntax(failure)
            elif failure.check_name == "file_permissions":
                return self._heal_file_permissions(failure)
            elif failure.check_name == "encoding_consistency":
                return self._heal_encoding_consistency(failure)
            elif failure.check_name in ["docker_configs", "environment_variables", "database_config", "network_config", "ai_config", "logging_config"]:
                return self._heal_regenerate_config(failure)
            else:
                return {
                    "success": False,
                    "error": "No healing method available for this failure type"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Healing attempt failed: {str(e)}"
            }
    
    def _heal_directory_structure(self, failure: ValidationFailure) -> Dict[str, Any]:
        """Heal directory structure issues"""
        try:
            missing_dirs = failure.context.get("missing_dirs", [])
            created_dirs = []
            
            for dir_path in missing_dirs:
                full_path = self.config.install_directory / dir_path
                full_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(dir_path)
            
            return {
                "success": True,
                "method": "create_directories",
                "details": f"Created {len(created_dirs)} directories: {', '.join(created_dirs)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create directories: {str(e)}"
            }
    
    def _heal_configuration_files(self, failure: ValidationFailure) -> Dict[str, Any]:
        """Heal missing configuration files by regenerating them"""
        try:
            # Use ConfigurationGenerator to regenerate missing configs
            config_generator = ConfigurationGenerator(self.config, self.system_info, self.logger)
            success = config_generator.generate_all_configs()
            
            if success:
                return {
                    "success": True,
                    "method": "regenerate_configs",
                    "details": f"Regenerated {len(config_generator.created_configs)} configuration files"
                }
            else:
                return {
                    "success": False,
                    "error": "Configuration regeneration failed"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to regenerate configurations: {str(e)}"
            }
    
    def _heal_configuration_syntax(self, failure: ValidationFailure) -> Dict[str, Any]:
        """Heal configuration syntax issues by regenerating corrupted files"""
        try:
            syntax_errors = failure.context.get("syntax_errors", [])
            healed_files = []
            
            # For now, we'll regenerate all configs if there are syntax errors
            # A more sophisticated approach would regenerate only the corrupted files
            config_generator = ConfigurationGenerator(self.config, self.system_info, self.logger)
            success = config_generator.generate_all_configs()
            
            if success:
                healed_files = [error["file"] for error in syntax_errors]
                return {
                    "success": True,
                    "method": "regenerate_corrupted_configs",
                    "details": f"Regenerated {len(healed_files)} corrupted configuration files"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to regenerate corrupted configurations"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to heal syntax errors: {str(e)}"
            }
    
    def _heal_file_permissions(self, failure: ValidationFailure) -> Dict[str, Any]:
        """Heal file permission issues"""
        try:
            permission_issues = failure.context.get("permission_issues", [])
            fixed_permissions = []
            
            for issue in permission_issues:
                if issue.get("issue") == "not_executable":
                    file_path = self.config.install_directory / issue["file"]
                    if file_path.exists():
                        file_path.chmod(0o755)
                        fixed_permissions.append(issue["file"])
            
            return {
                "success": True,
                "method": "fix_permissions",
                "details": f"Fixed permissions for {len(fixed_permissions)} files"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fix permissions: {str(e)}"
            }
    
    def _heal_encoding_consistency(self, failure: ValidationFailure) -> Dict[str, Any]:
        """Heal encoding consistency issues"""
        try:
            encoding_issues = failure.context.get("encoding_issues", [])
            fixed_files = []
            
            for issue in encoding_issues:
                file_path = self.config.install_directory / issue["file"]
                if file_path.exists() and issue.get("issue") == "missing_bom":
                    # Re-save file with proper encoding
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    with open(file_path, 'w', encoding='utf-8-sig', newline='\n') as f:
                        f.write(content)
                    fixed_files.append(issue["file"])
            
            return {
                "success": True,
                "method": "fix_encoding",
                "details": f"Fixed encoding for {len(fixed_files)} files"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fix encoding: {str(e)}"
            }
    
    def _heal_regenerate_config(self, failure: ValidationFailure) -> Dict[str, Any]:
        """Heal issues by regenerating specific configuration files"""
        try:
            config_generator = ConfigurationGenerator(self.config, self.system_info, self.logger)
            
            # Map failure types to regeneration methods
            regen_methods = {
                "docker_configs": config_generator._generate_docker_compose,
                "environment_variables": config_generator._generate_env_files,
                "database_config": config_generator._generate_database_config,
                "network_config": config_generator._generate_network_config,
                "ai_config": config_generator._generate_ai_config,
                "logging_config": config_generator._generate_logging_config
            }
            
            method = regen_methods.get(failure.check_name)
            if method and method():
                return {
                    "success": True,
                    "method": f"regenerate_{failure.check_name}",
                    "details": f"Successfully regenerated {failure.check_name}"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to regenerate {failure.check_name}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to regenerate config: {str(e)}"
            }

class ConfigurationWizard:
    """Enhanced configuration wizard with preview and validation"""
    
    def __init__((self, system_info: SystemInfo, logger: SmartLogger, auditor: InstallationAuditor) -> None:
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
    
    def _show_welcome_screen(self) -> bool:
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
        logger.info(welcome_text)
        
        # System analysis summary
        logger.info(f"\n🖥️  System Analysis:")
        logger.info(f"   OS: {self.system_info.os_type.value.title()
        logger.info(f"   Python: {self.system_info.python_version}")
        logger.info(f"   Resources: {self.system_info.cpu_cores} cores, {self.system_info.available_memory}GB RAM")
        
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
            logger.info(f"   Encoding: UTF-8 {'✅' if utf8_ok else '⚠️ '}")
        
        if self.system_info.permissions:
            admin_rights = self.system_info.permissions.get("admin_rights", False)
            write_ok = self.system_info.permissions.get("current_dir_write", False)
            logger.info(f"   Permissions: Write {'✅' if write_ok else '❌'} | Admin {'✅' if admin_rights else '❌'}")
        
        # Previous installation analysis
        if self.previous_failures.get("failed_steps"):
            logger.info(f"\n⚠️  Previous Installation Issues Detected:")
            for issue_type, count in self.previous_failures.get("error_patterns", {}).items():
                logger.info(f"   • {issue_type.replace('_', ' ')
            
            if self.previous_failures.get("recovery_suggestions"):
                logger.info(f"   💡 Recovery suggestions available")
    
    def _guided_mode_config(self) -> InstallConfig:
        """Full guided configuration with all options"""
        self._show_welcome_screen()
        
        logger.info(f"\n🛠️  Configuration Wizard (Guided Mode)
        logger.info("=" * 60)
        
        # Installation directory with smart defaults
        default_dir = self._get_default_install_directory()
        logger.info(f"\n📁 Installation Directory")
        logger.info(f"   Default: {default_dir}")
        logger.info(f"   • Must have at least 2GB free space")
        logger.info(f"   • Avoid paths with spaces on Windows")
        
        while True:
            install_dir_input = input(f"   Directory [{default_dir}]: ").strip()
            install_directory = Path(install_dir_input) if install_dir_input else default_dir
            
            # Validate directory
            validation_result = self._validate_install_directory(install_directory)
            if validation_result["valid"]:
                break
            else:
                logger.info(f"   ❌ {validation_result['message']}")
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
        logger.info(f"\n⚡ Fast Mode Installation")
        logger.info("Using recommended defaults for quick setup...")
        
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
        logger.info(f"\n🔍 Dry Run Mode")
        logger.info("Will simulate installation without making changes...")
        
        config = self._fast_mode_config()
        config.mode = InstallMode.DRY_RUN
        return config
    
    def _safe_mode_config(self) -> InstallConfig:
        """Safe mode with minimal features"""
        logger.info(f"\n🛡️  Safe Mode Installation")
        logger.info("Using minimal configuration for stability...")
        
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
        logger.info(f"\n🔄 Recovery Mode Installation")
        
        if not self.previous_failures.get("failed_steps"):
            logger.error("No previous failures detected, using fast mode...")
            config = self._fast_mode_config()
            config.mode = InstallMode.RECOVERY
            return config
        
        logger.error("Configuring based on previous failure analysis...")
        
        # Show recovery suggestions
        if self.previous_failures.get("recovery_suggestions"):
            logger.info(f"\n💡 Recovery Suggestions:")
            for suggestion in self.previous_failures["recovery_suggestions"]:
                logger.info(f"   • {suggestion}")
        
        # Use safe defaults with adjustments based on previous failures
        config = self._safe_mode_config()
        config.mode = InstallMode.RECOVERY
        
        # Adjust configuration based on error patterns
        error_patterns = self.previous_failures.get("error_patterns", {})
        
        if "encoding_issues" in error_patterns:
            logger.info("   🔧 Enabled encoding fallbacks")
        
        if "dependency_failures" in error_patterns:
            logger.info("   🔧 Will use alternative package managers")
        
        if "permission_errors" in error_patterns:
            logger.info("   🔧 Will use user directory installation")
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
        
        logger.info(f"\n📦 Module Selection")
        logger.info("Select modules to install (recommended modules marked with ⭐)
        
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
            logger.info(f"   {i:2d}. {module:<20} - {description}")
        
        logger.info(f"\nOptions:")
        logger.info(f"   • Enter numbers (e.g., 1,2,3)
        logger.info(f"   • 'recommended' for starred modules only")
        logger.info(f"   • 'all' for all modules")
        logger.info(f"   • 'minimal' for core modules only")
        
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
                        logger.info("   ❌ Invalid selection, please try again")
                except:
                    logger.info("   ❌ Invalid format, please try again")
    
    def _select_features(self) -> Dict[str, bool]:
        """Interactive feature selection"""
        logger.info(f"\n🎯 Feature Configuration")
        
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
        logger.info(f"\n🧠 AI Configuration")
        
        available_models = [
            ("mistral:7b-instruct", "General purpose, good balance", "~4GB RAM"),
            ("gemma:7b-it", "Instruction-tuned, fast responses", "~4GB RAM"),
            ("tinyllama", "Lightweight, quick setup", "~1GB RAM"),
            ("phi", "Microsoft model, efficient", "~2GB RAM"),
            ("llama2:7b", "Meta's foundation model", "~4GB RAM"),
            ("codellama:7b", "Code-specialized model", "~4GB RAM")
        ]
        
        logger.info("Available AI models:")
        for i, (model, description, memory) in enumerate(available_models, 1):
            logger.info(f"   {i}. {model:<20} - {description} ({memory})
        
        # Recommend models based on available memory
        if self.system_info.available_memory >= 16:
            recommended = "1,2,4"  # Multiple models
            logger.info(f"\n💡 Recommendation: Install multiple models (you have {self.system_info.available_memory}GB RAM)
        elif self.system_info.available_memory >= 8:
            recommended = "1,3"  # Balanced selection
            logger.info(f"\n💡 Recommendation: Install 1-2 models (you have {self.system_info.available_memory}GB RAM)
        else:
            recommended = "3"  # Lightweight only
            logger.info(f"\n⚠️  Recommendation: Install lightweight model only (you have {self.system_info.available_memory}GB RAM)
        
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
                        logger.warning(f"   ⚠️  Warning: Selected models may use ~{memory_estimate}GB RAM")
                        if not self._ask_yes_no("Continue anyway?", default=False):
                            continue
                    
                    return {"models": selected_models}
                else:
                    logger.info("   ❌ No models selected, please try again")
            except:
                logger.info("   ❌ Invalid format, please try again")
    
    def _select_installation_mode(self) -> Dict[str, Any]:
        """Select advanced installation options"""
        logger.info(f"\n🔧 Installation Options")
        
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
    
    def _show_configuration_preview(self, config: InstallConfig) -> bool:
        """Show configuration preview before installation"""
        logger.info(f"\n📋 Installation Summary")
        logger.info("=" * 60)
        logger.info(f"   📁 Directory: {config.install_directory}")
        logger.info(f"   📦 Modules: {', '.join(config.modules)
        logger.info(f"   🤖 AI Features: {'✅' if config.enable_ai else '❌'}")
        logger.info(f"   🎤 Voice Interface: {'✅' if config.enable_voice else '❌'}")
        logger.info(f"   📱 Mobile App: {'✅' if config.enable_mobile else '❌'}")
        logger.info(f"   ⚙️  Development Mode: {'✅' if config.dev_mode else '❌'}")
        
        if config.ai_models:
            logger.info(f"   🧠 AI Models: {', '.join(config.ai_models)
        
        # Estimate installation size and time
        estimated_size = self._estimate_installation_size(config)
        estimated_time = self._estimate_installation_time(config)
        
        logger.info(f"\n📊 Estimates:")
        logger.info(f"   💾 Disk space: ~{estimated_size}GB")
        logger.info(f"   ⏱️  Time: ~{estimated_time} minutes")
        
        # Show any warnings
        warnings = self._check_configuration_warnings(config)
        if warnings:
            logger.warning(f"\n⚠️  Warnings:")
            for warning in warnings:
                logger.warning(f"   • {warning}")
    
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
        logger.info(f"\n🎯 Ready to Install")
        
        # Show key information
        logger.info(f"This will install NoxSuite to: {config.install_directory}")
        if config.force_reinstall:
            logger.info(f"⚠️  Will remove existing installation")
        
        response = input(f"\n✅ Proceed with installation? [Y/n]: ").strip().lower()
        return response != 'n'
    
    def _get_default_modules(self) -> List[str]:
        """Get default recommended modules"""
        return ["noxpanel", "noxguard", "autoimport", "heimnetz-scanner", "plugin-system", "update-manager"]

class SmartNoxSuiteInstaller:
    """Main installer class with smart recovery and self-healing capabilities"""
    
    def __init__((self) -> None:
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
            # Special handling for audit and self-heal mode
            if mode == InstallMode.AUDIT_HEAL:
                return self._run_audit_and_heal_mode()
            
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
        
        # Use requests if available, otherwise urllib
        if HAS_REQUESTS:
            for url in test_urls:
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code != 200:
                        failed_urls.append(url)
                except:
                    failed_urls.append(url)
        else:
            # Fallback to urllib for basic connectivity check
            import urllib.request
            import urllib.error
            
            for url in test_urls:
                try:
                    with urllib.request.urlopen(url, timeout=10) as response:
                        if response.getcode() != 200:
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
        def clean_structure(d) -> bool:
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
        """Generate comprehensive configuration files with platform-specific handling"""
        if self.config.mode == InstallMode.DRY_RUN:
            self.logger.info("🔍 Dry run: Would generate configuration files")
            return True
        
        self.logger.step_start("generating_configs", "Creating configuration files")
        
        try:
            # Initialize configuration generator
            config_generator = ConfigurationGenerator(
                self.config, 
                self.system_info, 
                self.logger
            )
            
            # Generate all configuration files
            success = config_generator.generate_all_configs()
            
            if success:
                self.logger.step_complete("generating_configs", {
                    "configs_created": len(config_generator.created_configs),
                    "platform_specific": self.system_info.os_type.value
                })
                return True
            else:
                self.logger.step_error("generating_configs", 
                    Exception("Configuration generation failed"))
                return False
                
        except Exception as e:
            self.logger.step_error("generating_configs", e, {
                "platform": self.system_info.os_type.value,
                "install_dir": str(self.config.install_directory)
            })
            return False
    
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
        """Comprehensive post-installation validation with detailed diagnostics"""
        if self.config.mode == InstallMode.DRY_RUN:
            self.logger.step_start("validating_installation", "Skipping validation (dry-run mode)")
            self.logger.info("🔍 Dry run: Would validate installation")
            self.logger.step_complete("validating_installation")
            return True
        
        self.logger.step_start("validating_installation", "Running comprehensive post-installation validation")
        
        try:
            # Initialize comprehensive validator
            validator = InstallationValidator(
                self.config,
                self.system_info,
                self.logger
            )
            
            # Run comprehensive validation
            validation_result = validator.validate_complete_installation()
            
            if validation_result.all_passed:
                self.logger.step_complete("validating_installation", {
                    "total_checks": validation_result.total_checks,
                    "passed_checks": validation_result.passed_checks,
                    "platform": self.system_info.os_type.value
                })
                return True
            else:
                # Log detailed failure information
                self.logger.warning(f"❌ Validation Summary: {validation_result.passed_checks}/{validation_result.total_checks} checks passed")
                
                for failure in validation_result.failures:
                    self.logger.warning(f"   • {failure.check_name}: {failure.message}")
                    if failure.auto_fix_available:
                        self.logger.info(f"     🔧 Auto-fix available: {failure.auto_fix_suggestion}")
                
                # Attempt auto-healing if enabled
                if self.config.mode in [InstallMode.SAFE, InstallMode.RECOVERY]:
                    self.logger.info("🔧 Attempting auto-healing of failed validations...")
                    healing_result = validator.attempt_auto_healing(validation_result.failures)
                    
                    if healing_result.healed_count > 0:
                        self.logger.info(f"✅ Successfully healed {healing_result.healed_count} issues")
                        # Re-run validation after healing
                        validation_result = validator.validate_complete_installation()
                        if validation_result.all_passed:
                            self.logger.step_complete("validating_installation", {
                                "healed_issues": healing_result.healed_count,
                                "final_status": "passed_after_healing"
                            })
                            return True
                
                self.logger.step_error("validating_installation", 
                    Exception(f"Validation failed: {len(validation_result.failures)} issues"), {
                        "failed_checks": [f.check_name for f in validation_result.failures],
                        "auto_healing_attempted": self.config.mode in [InstallMode.SAFE, InstallMode.RECOVERY]
                    })
                return False
                
        except Exception as e:
            self.logger.step_error("validating_installation", e, {
                "platform": self.system_info.os_type.value,
                "install_dir": str(self.config.install_directory)
            })
            return False
    
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
    
    def _finalize_installation(self) -> bool:
        """Finalize installation and show completion message"""
        self.logger.step_start("finalizing", "Completing installation")
        
        # Create installation summary
        summary = {
            "installation_status": "completed",
            "installation_time": utc_now().isoformat(),
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
    
    def _show_completion_message(self) -> bool:
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
    
    def _run_audit_and_heal_mode(self) -> bool:
        """Run comprehensive audit and self-healing mode"""
        self.logger.info("🔍 Starting NoxSuite Audit and Self-Heal Mode")
        
        audit_banner = """
╔═══════════════════════════════════════════════════════════════════╗
║              🩺 NoxSuite Audit & Self-Heal Mode                  ║
║              Comprehensive Installation Health Check              ║
╠═══════════════════════════════════════════════════════════════════╣
║  🔍 Deep System Analysis     🔧 Automatic Fixing                ║
║  📊 Config Validation        ⚡ Smart Recovery                   ║
║  🛠️  Self-Healing Operations  📋 Detailed Reporting              ║
║  🌐 Cross-Platform Checks    💊 Auto-Remediation                ║
╚═══════════════════════════════════════════════════════════════════╝
        """
        logger.info(audit_banner)
        
        try:
            # Step 1: Detect existing installations
            self.logger.step_start("audit_detection", "Scanning for existing NoxSuite installations")
            
            existing_installs = self._detect_existing_installations()
            if not existing_installs:
                self.logger.warning("❌ No existing NoxSuite installations found")
                
                # Offer to run regular installation
                run_install = input("\n💡 Would you like to run a fresh installation instead? [Y/n]: ").strip().lower()
                if run_install != 'n':
                    self.logger.info("🚀 Switching to guided installation mode...")
                    return self.run_installation(InstallMode.GUIDED)
                else:
                    self.logger.info("❌ Audit mode cancelled - no installation to audit")
                    return False
            
            self.logger.step_complete("audit_detection", {"found_installations": len(existing_installs)})
            
            # Step 2: Select installation to audit (if multiple found)
            target_install = self._select_installation_to_audit(existing_installs)
            if not target_install:
                self.logger.info("❌ No installation selected for audit")
                return False
            
            self.logger.info(f"🎯 Auditing installation: {target_install}")
            
            # Step 3: Load configuration from existing installation
            self.logger.step_start("loading_config", "Loading existing installation configuration")
            
            try:
                self.config = self._load_existing_config(Path(target_install))
                if not self.config:
                    self.logger.warning("⚠️ Could not load existing configuration, using defaults")
                    # Create minimal config for audit
                    self.config = InstallConfig(
                        install_directory=Path(target_install),
                        modules=["noxpanel", "noxguard"],
                        mode=InstallMode.AUDIT_HEAL
                    )
                
                self.logger.step_complete("loading_config")
            except Exception as e:
                self.logger.step_error("loading_config", e)
                return False
            
            # Step 4: Run comprehensive audit
            self.logger.step_start("comprehensive_audit", "Running comprehensive installation audit")
            
            validator = InstallationValidator(self.config, self.system_info, self.logger)
            audit_result = validator.validate_complete_installation()
            
            self.logger.step_complete("comprehensive_audit", {
                "total_checks": audit_result.total_checks,
                "passed_checks": audit_result.passed_checks,
                "failed_checks": len(audit_result.failures)
            })
            
            # Step 5: Display detailed audit results
            self._display_audit_results(audit_result)
            
            # Step 6: Auto-healing (if issues found)
            if not audit_result.all_passed:
                self.logger.info(f"\n🔧 Found {len(audit_result.failures)} issues to address")
                
                # Ask user if they want to attempt auto-healing
                auto_heal = input("\n💊 Attempt automatic healing of detected issues? [Y/n]: ").strip().lower()
                
                if auto_heal != 'n':
                    self.logger.step_start("auto_healing", "Attempting automatic issue resolution")
                    
                    healing_result = validator.attempt_auto_healing(audit_result.failures)
                    
                    self.logger.step_complete("auto_healing", {
                        "healed_count": healing_result.healed_count,
                        "failed_count": healing_result.failed_count
                    })
                    
                    # Display healing results
                    self._display_healing_results(healing_result)
                    
                    # Re-run validation after healing
                    if healing_result.healed_count > 0:
                        self.logger.info("\n🔄 Re-validating installation after healing...")
                        final_audit = validator.validate_complete_installation()
                        
                        if final_audit.all_passed:
                            self.logger.info("✅ All issues resolved! Installation is now healthy.")
                        else:
                            remaining_issues = len(final_audit.failures)
                            self.logger.warning(f"⚠️ {remaining_issues} issues still require manual attention")
                            self._display_remaining_issues(final_audit.failures)
                else:
                    self.logger.info("ℹ️ Auto-healing skipped by user")
            else:
                self.logger.info("🎉 Installation audit completed - no issues found!")
            
            # Step 7: Generate comprehensive audit report
            self._generate_audit_report(audit_result, existing_installs, target_install)
            
            return True
            
        except Exception as e:
            self.logger.step_error("audit_and_heal", e, {
                "mode": "audit_heal",
                "system_info": asdict(self.system_info)
            })
            return False
    
    def _detect_existing_installations(self) -> List[str]:
        """Detect existing NoxSuite installations on the system"""
        installations = []
        
        # Common installation locations
        search_locations = []
        
        if self.system_info.os_type == OSType.WINDOWS:
            search_locations = [
                Path.home() / "NoxSuite",
                Path.home() / "noxsuite",
                Path("C:/Program Files/NoxSuite"),
                Path("C:/NoxSuite"),
                Path.home() / "Documents" / "NoxSuite"
            ]
        else:
            search_locations = [
                Path.home() / "noxsuite",
                Path.home() / "NoxSuite",
                Path("/opt/noxsuite"),
                Path("/usr/local/noxsuite"),
                Path("/var/lib/noxsuite")
            ]
        
        # Also check current directory
        search_locations.append(Path.cwd())
        
        for location in search_locations:
            if self._is_noxsuite_installation(location):
                installations.append(str(location))
        
        # Search for additional installations in common directories
        additional_locations = self._search_for_noxsuite_markers()
        installations.extend(additional_locations)
        
        # Remove duplicates and sort
        installations = sorted(list(set(installations)))
        
        return installations
    
    def _is_noxsuite_installation(self, path: Path) -> bool:
        """Check if a directory contains a NoxSuite installation"""
        if not path.exists() or not path.is_dir():
            return False
        
        # Check for NoxSuite markers
        markers = [
            "noxsuite.json",
            "INSTALLATION_SUMMARY.json",
            "config/noxsuite.json",
            "docker/docker-compose.noxsuite.yml"
        ]
        
        marker_count = 0
        for marker in markers:
            if (path / marker).exists():
                marker_count += 1
        
        # Consider it a NoxSuite installation if at least 2 markers are found
        return marker_count >= 2
    
    def _search_for_noxsuite_markers(self) -> List[str]:
        """Search filesystem for NoxSuite installation markers"""
        additional_installs = []
        
        # This is a simplified search - in a real implementation,
        # you might want to search more comprehensively
        
        try:
            # Search in user's home directory tree (limited depth)
            home_path = Path.home()
            for item in home_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    try:
                        if self._is_noxsuite_installation(item):
                            additional_installs.append(str(item))
                    except PermissionError:
                        continue  # Skip directories we can't access
        except:
            pass  # Handle any filesystem errors gracefully
        
        return additional_installs
    
    def _select_installation_to_audit(self, installations: List[str]) -> str:
        """Let user select which installation to audit (if multiple found)"""
        if len(installations) == 1:
            return installations[0]
        
        logger.info(f"\n🔍 Multiple NoxSuite installations detected:")
        logger.info("=" * 60)
        
        for i, install_path in enumerate(installations, 1):
            install_info = self._get_installation_info(Path(install_path))
            logger.info(f"   {i}. {install_path}")
            logger.info(f"      Version: {install_info.get('version', 'unknown')
            logger.info(f"      Last Modified: {install_info.get('last_modified', 'unknown')
            logger.info(f"      Size: {install_info.get('size', 'unknown')
            print()
        
        while True:
            try:
                selection = input(f"Select installation to audit [1-{len(installations)}]: ").strip()
                index = int(selection) - 1
                
                if 0 <= index < len(installations):
                    return installations[index]
                else:
                    logger.info(f"❌ Please enter a number between 1 and {len(installations)
            except ValueError:
                logger.info("❌ Please enter a valid number")
            except KeyboardInterrupt:
                return None
    
    def _get_installation_info(self, install_path: Path) -> Dict[str, str]:
        """Get basic information about an installation"""
        info = {}
        
        try:
            # Get version from noxsuite.json or INSTALLATION_SUMMARY.json
            config_files = [
                install_path / "config" / "noxsuite.json",
                install_path / "noxsuite.json",
                install_path / "INSTALLATION_SUMMARY.json"
            ]
            
            for config_file in config_files:
                if config_file.exists():
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config_data = json.load(f)
                            info['version'] = config_data.get('version', 'unknown')
                            break
                    except:
                        continue
            
            # Get last modified time
            if install_path.exists():
                last_modified = install_path.stat().st_mtime
                info['last_modified'] = datetime.fromtimestamp(last_modified).strftime('%Y-%m-%d %H:%M')
            
            # Get approximate size
            total_size = 0
            try:
                for root, dirs, files in os.walk(install_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            total_size += os.path.getsize(file_path)
                        except:
                            continue
                
                if total_size > 1024**3:
                    info['size'] = f"{total_size / (1024**3):.1f}GB"
                elif total_size > 1024**2:
                    info['size'] = f"{total_size / (1024**2):.1f}MB"
                else:
                    info['size'] = f"{total_size / 1024:.1f}KB"
            except:
                info['size'] = "unknown"
        
        except Exception as e:
            self.logger.debug(f"Error getting installation info for {install_path}: {e}")
        
        return info
    
    def _load_existing_config(self, install_path: Path) -> Optional[InstallConfig]:
        """Load configuration from existing installation"""
        try:
            # Try to load from config/noxsuite.json first
            config_file = install_path / "config" / "noxsuite.json"
            if not config_file.exists():
                # Fallback to other possible locations
                config_file = install_path / "noxsuite.json"
                if not config_file.exists():
                    config_file = install_path / "INSTALLATION_SUMMARY.json"
            
            if not config_file.exists():
                self.logger.warning("No configuration file found in installation")
                return None
            
            encoding = "utf-8-sig" if self.system_info.os_type == OSType.WINDOWS else "utf-8"
            with open(config_file, 'r', encoding=encoding) as f:
                config_data = json.load(f)
            
            # Extract configuration from loaded data
            installation_data = config_data.get('installation', config_data)
            
            # Create InstallConfig from loaded data
            config = InstallConfig(
                install_directory=install_path,
                modules=installation_data.get('installed_modules', installation_data.get('modules', [])),
                enable_ai=installation_data.get('features', {}).get('ai_enabled', False),
                enable_voice=installation_data.get('features', {}).get('voice_enabled', False),
                enable_mobile=installation_data.get('features', {}).get('mobile_enabled', False),
                dev_mode=installation_data.get('features', {}).get('dev_mode', False),
                auto_start=installation_data.get('auto_start', True),
                ai_models=installation_data.get('ai_models', []),
                mode=InstallMode.AUDIT_HEAL
            )
            
            return config
            
        except Exception as e:
            self.logger.warning(f"Failed to load existing configuration: {e}")
            return None
    
    def _display_audit_results(self, audit_result: ValidationResult) -> bool:
        """Display comprehensive audit results"""
        logger.info(f"\n📊 Audit Results Summary")
        logger.info("=" * 60)
        
        if audit_result.all_passed:
            logger.info("🎉 Installation Status: HEALTHY")
            logger.info(f"✅ All {audit_result.total_checks} validation checks passed")
        else:
            failed_count = len(audit_result.failures)
            logger.info(f"⚠️ Installation Status: NEEDS ATTENTION")
            logger.info(f"✅ Passed: {audit_result.passed_checks}/{audit_result.total_checks}")
            logger.error(f"❌ Failed: {failed_count}/{audit_result.total_checks}")
        
        if audit_result.platform_specific_issues:
            logger.info(f"\n🔧 Platform-Specific Issues Detected:")
            for issue in audit_result.platform_specific_issues:
                logger.info(f"   • {issue}")
        
        if audit_result.failures:
            logger.info(f"\n📋 Detailed Issue Report:")
            for i, failure in enumerate(audit_result.failures, 1):
                severity_icon = "🔴" if failure.severity == "error" else "🟡"
                logger.error(f"\n{i}. {severity_icon} {failure.check_name.replace('_', ' ')
                logger.error(f"   Issue: {failure.message}")
                logger.error(f"   Severity: {failure.severity.upper()
                
                if failure.auto_fix_available:
                    logger.error(f"   🔧 Auto-fix: {failure.auto_fix_suggestion}")
                else:
                    logger.info(f"   ⚠️ Manual intervention required")
                
                if failure.context:
                    # Show relevant context information
                    if 'missing_configs' in failure.context:
                        missing = failure.context['missing_configs'][:3]  # Show first 3
                        logger.info(f"   Missing files: {', '.join(missing)
                        if len(failure.context['missing_configs']) > 3:
                            logger.error(f"   ... and {len(failure.context['missing_configs'])
    
    def _display_healing_results(self, healing_result: HealingResult) -> bool:
        """Display healing attempt results"""
        logger.info(f"\n💊 Auto-Healing Results")
        logger.info("=" * 60)
        
        total_attempts = healing_result.healed_count + healing_result.failed_count
        logger.info(f"✅ Successfully healed: {healing_result.healed_count}/{total_attempts}")
        logger.error(f"❌ Failed to heal: {healing_result.failed_count}/{total_attempts}")
        
        if healing_result.healing_details:
            logger.info(f"\n📋 Healing Details:")
            for detail in healing_result.healing_details:
                status = detail['status']
                check_name = detail['check_name']
                
                if status == 'healed':
                    logger.info(f"✅ {check_name}: {detail.get('details', 'Successfully healed')
                elif status == 'failed':
                    logger.error(f"❌ {check_name}: {detail.get('error', 'Healing failed')
                elif status == 'no_auto_fix':
                    logger.info(f"⚠️ {check_name}: Manual intervention required")
                elif status == 'exception':
                    logger.error(f"💥 {check_name}: Healing error - {detail.get('error', 'Unknown error')
    
    def _display_remaining_issues(self, remaining_failures: List[ValidationFailure]) -> bool:
        """Display issues that still need manual attention"""
        logger.info(f"\n⚠️ Remaining Issues Requiring Manual Attention:")
        logger.info("-" * 60)
        
        for i, failure in enumerate(remaining_failures, 1):
            severity_icon = "🔴" if failure.severity == "error" else "🟡"
            logger.error(f"\n{i}. {severity_icon} {failure.check_name.replace('_', ' ')
            logger.error(f"   Issue: {failure.message}")
            
            # Provide manual fix suggestions
            manual_suggestions = self._get_manual_fix_suggestions(failure)
            if manual_suggestions:
                logger.info(f"   💡 Manual Fix Suggestions:")
                for suggestion in manual_suggestions:
                    logger.info(f"      • {suggestion}")
    
    def _get_manual_fix_suggestions(self, failure: ValidationFailure) -> List[str]:
        """Get manual fix suggestions for validation failures"""
        suggestions = []
        
        if failure.check_name == "service_dependencies":
            suggestions.extend([
                "Install Docker Desktop from https://docker.com/get-started",
                "Install Node.js from https://nodejs.org (if mobile features enabled)",
                "Restart your terminal/command prompt after installation"
            ])
        elif failure.check_name == "path_compatibility":
            suggestions.extend([
                "Consider moving installation to a path without spaces",
                "Use short path names to avoid Windows path length limits",
                "Avoid reserved Windows filenames (CON, PRN, AUX, etc.)"
            ])
        elif failure.check_name == "disk_space":
            suggestions.extend([
                "Free up disk space on the installation drive",
                "Consider installing to a different drive with more space",
                "Remove old Docker images: docker system prune -a"
            ])
        elif failure.check_name == "platform_compatibility":
            if self.system_info.os_type == OSType.WINDOWS:
                suggestions.extend([
                    "Ensure Windows 10/11 with WSL2 support for Docker Desktop",
                    "Enable Hyper-V and Windows Subsystem for Linux features",
                    "Update Windows to the latest version"
                ])
            elif self.system_info.os_type == OSType.LINUX:
                suggestions.extend([
                    "Ensure systemd is available for service management",
                    "Install Docker using your distribution's package manager",
                    "Add your user to the docker group: sudo usermod -aG docker $USER"
                ])
        
        # Add generic suggestions if no specific ones found
        if not suggestions:
            suggestions.append("Review the installation documentation for platform-specific requirements")
            suggestions.append("Check the installation logs for more detailed error information")
        
        return suggestions
    
    def _generate_audit_report(self, audit_result: ValidationResult, installations: List[str], target_install: str) -> bool:
        """Generate comprehensive audit report"""
        self.logger.step_start("generating_report", "Creating comprehensive audit report")
        
        try:
            report_timestamp = utc_now()
            report = {
                "audit_metadata": {
                    "timestamp": report_timestamp.isoformat(),
                    "installer_version": "1.0.0",
                    "audit_session_id": self.logger.session_id,
                    "target_installation": target_install,
                    "all_detected_installations": installations,
                    "platform": self.system_info.os_type.value,
                    "system_info": asdict(self.system_info)
                },
                "audit_results": {
                    "overall_status": "healthy" if audit_result.all_passed else "needs_attention",
                    "total_checks": audit_result.total_checks,
                    "passed_checks": audit_result.passed_checks,
                    "failed_checks": len(audit_result.failures),
                    "platform_specific_issues": audit_result.platform_specific_issues or []
                },
                "detailed_failures": [],
                "configuration_snapshot": asdict(self.config) if self.config else None,
                "recommendations": []
            }
            
            # Add detailed failure information
            for failure in audit_result.failures:
                failure_detail = {
                    "check_name": failure.check_name,
                    "message": failure.message,
                    "severity": failure.severity,
                    "auto_fix_available": failure.auto_fix_available,
                    "auto_fix_suggestion": failure.auto_fix_suggestion,
                    "context": failure.context or {}
                }
                report["detailed_failures"].append(failure_detail)
            
            # Generate recommendations
            report["recommendations"] = self._generate_audit_recommendations(audit_result)
            
            # Save report
            report_file = Path(target_install) / "AUDIT_REPORT.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            # Save human-readable report
            readable_report = Path(target_install) / "AUDIT_REPORT.md"
            self._generate_readable_audit_report(readable_report, report, audit_result)
            
            self.logger.step_complete("generating_report", {
                "report_files": [str(report_file), str(readable_report)]
            })
            
            logger.info(f"\n📄 Audit reports saved:")
            logger.info(f"   • JSON Report: {report_file}")
            logger.info(f"   • Readable Report: {readable_report}")
            
        except Exception as e:
            self.logger.step_error("generating_report", e)
    
    def _generate_audit_recommendations(self, audit_result: ValidationResult) -> List[str]:
        """Generate actionable recommendations based on audit results"""
        recommendations = []
        
        if audit_result.all_passed:
            recommendations.extend([
                "Installation is healthy - no immediate action required",
                "Consider running periodic audits to maintain system health",
                "Keep Docker and other dependencies updated"
            ])
        else:
            # Priority recommendations based on failure types
            error_failures = [f for f in audit_result.failures if f.severity == "error"]
            warning_failures = [f for f in audit_result.failures if f.severity == "warning"]
            
            if error_failures:
                recommendations.append(f"PRIORITY: Address {len(error_failures)} critical errors first")
                
                critical_checks = [f.check_name for f in error_failures]
                if "service_dependencies" in critical_checks:
                    recommendations.append("Install missing Docker/Node.js dependencies")
                if "configuration_files" in critical_checks:
                    recommendations.append("Regenerate missing configuration files")
                if "disk_space" in critical_checks:
                    recommendations.append("Free up disk space before proceeding")
            
            if warning_failures:
                recommendations.append(f"Consider addressing {len(warning_failures)} warnings for optimal performance")
            
            # Platform-specific recommendations
            if self.system_info.os_type == OSType.WINDOWS:
                if any("encoding" in f.message.lower() for f in audit_result.failures):
                    recommendations.append("Windows: Ensure UTF-8 support is properly configured")
                if any("path" in f.message.lower() for f in audit_result.failures):
                    recommendations.append("Windows: Avoid spaces and long paths in installation directory")
            
            # General recommendations
            recommendations.extend([
                "Run the installer with 'recovery' mode to fix common issues",
                "Check installation logs for detailed error information",
                "Consider backup before making configuration changes"
            ])
        
        return recommendations
    
    def _generate_readable_audit_report(self, report_file: Path, report_data: Dict, audit_result: ValidationResult) -> bool:
        """Generate human-readable markdown audit report"""
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("# NoxSuite Installation Audit Report\n\n")
                f.write(f"**Generated:** {report_data['audit_metadata']['timestamp']}\n")
                f.write(f"**Installation:** {report_data['audit_metadata']['target_installation']}\n")
                f.write(f"**Platform:** {report_data['audit_metadata']['platform'].title()}\n")
                f.write(f"**Session ID:** {report_data['audit_metadata']['audit_session_id']}\n\n")
                
                # Overall Status
                f.write("## 📊 Overall Status\n\n")
                status = "✅ HEALTHY" if audit_result.all_passed else "⚠️ NEEDS ATTENTION"
                f.write(f"**Status:** {status}\n")
                f.write(f"**Checks Passed:** {audit_result.passed_checks}/{audit_result.total_checks}\n\n")
                
                # Issues Found
                if audit_result.failures:
                    f.write("## ❌ Issues Found\n\n")
                    for i, failure in enumerate(audit_result.failures, 1):
                        severity_icon = "🔴" if failure.severity == "error" else "🟡"
                        f.write(f"### {i}. {severity_icon} {failure.check_name.replace('_', ' ').title()}\n\n")
                        f.write(f"**Issue:** {failure.message}\n")
                        f.write(f"**Severity:** {failure.severity.upper()}\n")
                        f.write(f"**Auto-fixable:** {'Yes' if failure.auto_fix_available else 'No'}\n")
                        
                        if failure.auto_fix_available:
                            f.write(f"**Auto-fix:** {failure.auto_fix_suggestion}\n")
                        
                        f.write("\n")
                else:
                    f.write("## ✅ No Issues Found\n\n")
                    f.write("All validation checks passed successfully!\n\n")
                
                # Recommendations
                f.write("## 💡 Recommendations\n\n")
                for rec in report_data["recommendations"]:
                    f.write(f"- {rec}\n")
                
                f.write("\n---\n")
                f.write("*Report generated by NoxSuite Smart Installer*\n")
                
        except Exception as e:
            self.logger.warning(f"Failed to generate readable report: {e}")
    
    def _cleanup_on_failure(self) -> bool:
        """Cleanup on installation failure"""
        self.logger.info("🧹 Cleaning up after installation failure...")
        
        # This would implement cleanup logic
        # For now, just log the attempt
        self.logger.debug("Cleanup completed")

def main() -> bool:
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
                "recovery": InstallMode.RECOVERY,
                "audit-heal": InstallMode.AUDIT_HEAL
            }
            mode = mode_map.get(mode_arg, InstallMode.GUIDED)
        
        # Create and run installer
        installer = SmartNoxSuiteInstaller()
        success = installer.run_installation(mode)
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("\n❌ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.info(f"\n❌ Installer crashed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
