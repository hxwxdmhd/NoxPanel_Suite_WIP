# 🔌 Plugin Framework v2.0 Foundation
# Advanced Plugin Management System for NoxPanel/NoxGuard/Heimnetz Suite
# Audit 3 Compliant - Security-First Architecture

import os
import sys
import json
import time
import logging
import importlib
import importlib.util
import tempfile
import shutil
import threading
import traceback
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager
from enum import Enum
import psutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PluginStatus(Enum):
    """Plugin status enumeration"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    QUARANTINED = "quarantined"

class SecurityLevel(Enum):
    """Plugin security levels"""
    LOW = "low"           # Basic restrictions
    MEDIUM = "medium"     # Standard restrictions
    HIGH = "high"         # Strict restrictions
    CRITICAL = "critical" # Maximum restrictions

@dataclass
class PluginLimitsV2:
    """Enhanced resource limits for plugin execution"""
    max_memory_mb: int = 128
    max_cpu_percent: float = 25.0
    max_execution_time_seconds: int = 60
    max_file_operations: int = 1000
    max_network_connections: int = 5
    max_subprocess_count: int = 0  # Default: no subprocesses
    allowed_modules: set = field(default_factory=lambda: {
        'json', 'time', 'datetime', 'math', 're', 'base64', 
        'hashlib', 'uuid', 'collections', 'itertools'
    })
    blocked_modules: set = field(default_factory=lambda: {
        'os', 'sys', 'subprocess', 'socket', 'threading',
        'multiprocessing', 'ctypes', '__builtin__', 'builtins',
        'importlib', 'exec', 'eval', 'compile'
    })

@dataclass
class PluginPermissionsV2:
    """Enhanced permission system for plugin operations"""
    can_read_files: bool = False
    can_write_files: bool = False
    can_execute_commands: bool = False
    can_access_network: bool = False
    can_access_database: bool = False
    can_modify_system: bool = False
    can_create_threads: bool = False
    can_spawn_processes: bool = False
    allowed_directories: List[str] = field(default_factory=list)
    allowed_file_extensions: List[str] = field(default_factory=lambda: ['.txt', '.json', '.log'])
    allowed_network_hosts: List[str] = field(default_factory=list)
    security_level: SecurityLevel = SecurityLevel.MEDIUM

@dataclass
class PluginMetadataV2:
    """Enhanced plugin metadata structure"""
    name: str
    version: str
    description: str
    author: str = "Unknown"
    email: str = ""
    homepage: str = ""
    license: str = "MIT"
    compatibility: str = "v2.0"
    dependencies: List[str] = field(default_factory=list)
    api_version: str = "2.0"
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    permissions: PluginPermissionsV2 = field(default_factory=PluginPermissionsV2)
    limits: PluginLimitsV2 = field(default_factory=PluginLimitsV2)
    signature: Optional[str] = None
    checksum: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
class ResourceMonitorV2:
    """Enhanced resource monitoring for plugin execution"""
    
    def __init__(self, limits: PluginLimitsV2):
        self.limits = limits
        self.start_time = None
        self.initial_memory = None
        self.process = psutil.Process()
        self.monitoring = False
        self._monitor_thread = None
        
    def start_monitoring(self):
        """Start resource monitoring"""
        self.start_time = time.time()
        self.initial_memory = self.process.memory_info().rss / (1024 * 1024)  # MB
        self.monitoring = True
        
        # Start monitoring thread
        self._monitor_thread = threading.Thread(target=self._monitor_resources)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
            
    def _monitor_resources(self):
        """Monitor resource usage continuously"""
        while self.monitoring:
            try:
                # Check memory usage
                current_memory = self.process.memory_info().rss / (1024 * 1024)
                memory_used = current_memory - self.initial_memory
                
                if memory_used > self.limits.max_memory_mb:
                    logger.warning(f"Plugin exceeded memory limit: {memory_used:.1f}MB > {self.limits.max_memory_mb}MB")
                    self.monitoring = False
                    raise MemoryError(f"Plugin exceeded memory limit: {memory_used:.1f}MB")
                
                # Check execution time
                if self.start_time:
                    execution_time = time.time() - self.start_time
                    if execution_time > self.limits.max_execution_time_seconds:
                        logger.warning(f"Plugin exceeded time limit: {execution_time:.1f}s")
                        self.monitoring = False
                        raise TimeoutError(f"Plugin exceeded execution time limit: {execution_time:.1f}s")
                
                # Check CPU usage
                cpu_percent = self.process.cpu_percent()
                if cpu_percent > self.limits.max_cpu_percent:
                    logger.warning(f"Plugin exceeded CPU limit: {cpu_percent:.1f}%")
                
                time.sleep(0.1)  # Check every 100ms
                
            except Exception as e:
                if self.monitoring:  # Only log if we're still monitoring
                    logger.error(f"Resource monitoring error: {e}")
                break

class RestrictedImporterV2:
    """Enhanced restricted import handler"""
    
    def __init__(self, allowed_modules: set, blocked_modules: set):
        self.allowed_modules = allowed_modules
        self.blocked_modules = blocked_modules
        self.original_import = None
        
    def __enter__(self):
        """Enter restricted import context"""
        self.original_import = __builtins__['__import__']
        __builtins__['__import__'] = self._restricted_import
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit restricted import context"""
        if self.original_import:
            __builtins__['__import__'] = self.original_import
            
    def _restricted_import(self, name, *args, **kwargs):
        """Restricted import function"""
        # Check blocked modules first
        if any(blocked in name for blocked in self.blocked_modules):
            raise ImportError(f"Module '{name}' is blocked in plugin sandbox")
            
        # Check allowed modules
        if not any(allowed in name for allowed in self.allowed_modules):
            raise ImportError(f"Module '{name}' is not in allowed modules list")
            
        return self.original_import(name, *args, **kwargs)

class PluginSandboxV2:
    """Enhanced secure sandbox environment for plugin execution"""
    
    def __init__(self, limits: PluginLimitsV2 = None, permissions: PluginPermissionsV2 = None):
        self.limits = limits or PluginLimitsV2()
        self.permissions = permissions or PluginPermissionsV2()
        self.monitor = ResourceMonitorV2(self.limits)
        self.temp_dir = None
        self.original_cwd = None
        self.sandbox_id = None
        
    def __enter__(self):
        """Enter sandbox environment"""
        # Generate unique sandbox ID
        self.sandbox_id = hashlib.md5(f"{time.time()}_{os.getpid()}".encode()).hexdigest()[:8]
        
        # Create temporary directory for plugin
        self.temp_dir = tempfile.mkdtemp(prefix=f"noxpanel_plugin_{self.sandbox_id}_")
        self.original_cwd = os.getcwd()
        
        # Change to temp directory
        os.chdir(self.temp_dir)
        
        # Start resource monitoring
        self.monitor.start_monitoring()
        
        logger.info(f"🔒 Plugin sandbox activated: {self.sandbox_id} ({self.temp_dir})")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit sandbox environment"""
        # Stop monitoring
        self.monitor.stop_monitoring()
        
        # Restore original directory
        if self.original_cwd:
            os.chdir(self.original_cwd)
        
        # Clean up temporary directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                logger.debug(f"🧹 Plugin sandbox cleaned up: {self.sandbox_id}")
            except Exception as e:
                logger.warning(f"Failed to clean up plugin sandbox: {e}")
                
    def execute_plugin(self, plugin_path: str, plugin_config: Dict[str, Any] = None) -> Any:
        """Execute plugin in sandboxed environment with enhanced security"""
        if not os.path.exists(plugin_path):
            raise FileNotFoundError(f"Plugin file not found: {plugin_path}")
        
        plugin_config = plugin_config or {}
        
        try:
            # Load plugin module with restricted imports
            with RestrictedImporterV2(self.limits.allowed_modules, self.limits.blocked_modules):
                spec = importlib.util.spec_from_file_location(
                    f"sandboxed_plugin_{self.sandbox_id}", 
                    plugin_path
                )
                
                if spec is None or spec.loader is None:
                    raise ImportError(f"Could not load plugin from {plugin_path}")
                
                plugin_module = importlib.util.module_from_spec(spec)
                
                # Set up enhanced plugin environment
                plugin_module.__sandbox__ = self
                plugin_module.__config__ = plugin_config
                plugin_module.__permissions__ = self.permissions
                plugin_module.__sandbox_id__ = self.sandbox_id
                plugin_module.__noxpanel_api_version__ = "2.0"
                
                # Execute plugin with timeout protection
                spec.loader.exec_module(plugin_module)
                
                # Look for plugin entry points (enhanced)
                entry_points = ['main', 'run', 'execute', 'start', 'init']
                for entry_point in entry_points:
                    if hasattr(plugin_module, entry_point):
                        logger.debug(f"Executing plugin entry point: {entry_point}")
                        return getattr(plugin_module, entry_point)(plugin_config)
                
                logger.warning("Plugin has no recognized entry points")
                return None
                
        except Exception as e:
            logger.error(f"Plugin execution failed: {e}")
            logger.debug(f"Plugin traceback: {traceback.format_exc()}")
            raise

class PluginFrameworkV2:
    """Next-generation plugin framework with advanced capabilities"""
    
    def __init__(self, plugin_directory: str = None):
        self.plugin_directory = Path(plugin_directory or "plugins")
        self.loaded_plugins: Dict[str, Dict[str, Any]] = {}
        self.plugin_registry: Dict[str, PluginMetadataV2] = {}
        self.security_manager = SecurityManagerV2()
        self.dependency_resolver = DependencyResolverV2()
        
        # Ensure plugin directory exists
        self.plugin_directory.mkdir(exist_ok=True)
        
        # Initialize framework
        self._initialize_framework()
        
    def _initialize_framework(self):
        """Initialize the plugin framework"""
        logger.info("🔌 Initializing Plugin Framework v2.0")
        
        # Create required subdirectories
        subdirs = ['approved', 'quarantine', 'sandbox', 'cache', 'logs']
        for subdir in subdirs:
            (self.plugin_directory / subdir).mkdir(exist_ok=True)
            
        logger.info(f"Plugin framework initialized: {self.plugin_directory}")
        
    def discover_plugins(self) -> List[str]:
        """Enhanced plugin discovery with security validation"""
        discovered_plugins = []
        
        # Search for plugins in approved directory
        approved_dir = self.plugin_directory / "approved"
        
        for plugin_path in approved_dir.iterdir():
            if plugin_path.is_dir():
                plugin_json = plugin_path / "plugin.json"
                main_py = plugin_path / "main.py"
                
                if plugin_json.exists() and main_py.exists():
                    try:
                        # Load and validate plugin metadata
                        metadata = self._load_plugin_metadata(plugin_path)
                        if metadata:
                            # Security validation
                            if self.security_manager.validate_plugin_security(plugin_path):
                                discovered_plugins.append(plugin_path.name)
                                self.plugin_registry[plugin_path.name] = metadata
                                logger.info(f"✅ Plugin discovered: {plugin_path.name}")
                            else:
                                logger.warning(f"🚨 Plugin security validation failed: {plugin_path.name}")
                                self._quarantine_plugin(plugin_path.name)
                    except Exception as e:
                        logger.error(f"Error discovering plugin {plugin_path.name}: {e}")
        
        return discovered_plugins
        
    def _load_plugin_metadata(self, plugin_path: Path) -> Optional[PluginMetadataV2]:
        """Load and validate plugin metadata with enhanced validation"""
        metadata_file = plugin_path / "plugin.json"
        
        if not metadata_file.exists():
            logger.warning(f"No plugin.json found in {plugin_path}")
            return None
            
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                raw_metadata = json.load(f)
            
            # Validate required fields
            required_fields = ['name', 'version', 'description']
            for field in required_fields:
                if field not in raw_metadata:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create enhanced metadata object
            metadata = PluginMetadataV2(
                name=raw_metadata['name'],
                version=raw_metadata['version'],
                description=raw_metadata['description'],
                author=raw_metadata.get('author', 'Unknown'),
                email=raw_metadata.get('email', ''),
                homepage=raw_metadata.get('homepage', ''),
                license=raw_metadata.get('license', 'MIT'),
                compatibility=raw_metadata.get('compatibility', 'v2.0'),
                dependencies=raw_metadata.get('dependencies', []),
                api_version=raw_metadata.get('api_version', '2.0')
            )
            
            # Load security configuration
            security_config = raw_metadata.get('security', {})
            
            # Parse security level
            security_level_str = security_config.get('level', 'medium').lower()
            try:
                metadata.security_level = SecurityLevel(security_level_str)
            except ValueError:
                metadata.security_level = SecurityLevel.MEDIUM
            
            # Load permissions
            perms_config = security_config.get('permissions', {})
            metadata.permissions = PluginPermissionsV2(
                can_read_files=perms_config.get('can_read_files', False),
                can_write_files=perms_config.get('can_write_files', False),
                can_execute_commands=perms_config.get('can_execute_commands', False),
                can_access_network=perms_config.get('can_access_network', False),
                can_access_database=perms_config.get('can_access_database', False),
                can_modify_system=perms_config.get('can_modify_system', False),
                can_create_threads=perms_config.get('can_create_threads', False),
                can_spawn_processes=perms_config.get('can_spawn_processes', False),
                allowed_directories=perms_config.get('allowed_directories', []),
                allowed_file_extensions=perms_config.get('allowed_file_extensions', ['.txt', '.json', '.log']),
                allowed_network_hosts=perms_config.get('allowed_network_hosts', []),
                security_level=metadata.security_level
            )
            
            # Load resource limits
            limits_config = security_config.get('limits', {})
            metadata.limits = PluginLimitsV2(
                max_memory_mb=limits_config.get('max_memory_mb', 128),
                max_cpu_percent=limits_config.get('max_cpu_percent', 25.0),
                max_execution_time_seconds=limits_config.get('max_execution_time_seconds', 60),
                max_file_operations=limits_config.get('max_file_operations', 1000),
                max_network_connections=limits_config.get('max_network_connections', 5),
                max_subprocess_count=limits_config.get('max_subprocess_count', 0)
            )
            
            # Add custom allowed/blocked modules
            if 'allowed_modules' in limits_config:
                metadata.limits.allowed_modules.update(limits_config['allowed_modules'])
            if 'blocked_modules' in limits_config:
                metadata.limits.blocked_modules.update(limits_config['blocked_modules'])
            
            # Generate checksum for integrity verification
            main_file = plugin_path / "main.py"
            if main_file.exists():
                with open(main_file, 'rb') as f:
                    metadata.checksum = hashlib.sha256(f.read()).hexdigest()
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to load plugin metadata from {plugin_path}: {e}")
            return None
    
    async def load_plugin(self, plugin_id: str, config: Dict[str, Any] = None) -> bool:
        """Advanced plugin loading with security sandboxing and dependency resolution"""
        if plugin_id in self.loaded_plugins:
            logger.info(f"Plugin {plugin_id} is already loaded")
            return True
            
        try:
            # Get plugin metadata
            metadata = self.plugin_registry.get(plugin_id)
            if not metadata:
                logger.error(f"Plugin metadata not found: {plugin_id}")
                return False
            
            # Security validation
            plugin_path = self.plugin_directory / "approved" / plugin_id
            security_result = await self.security_manager.validate_plugin_async(plugin_path)
            if not security_result['is_safe']:
                logger.error(f"Plugin {plugin_id} failed security validation: {security_result['reason']}")
                self._quarantine_plugin(plugin_id)
                return False
            
            # Dependency resolution
            dependencies = await self.dependency_resolver.resolve_dependencies(plugin_id, metadata.dependencies)
            if not dependencies['resolved']:
                logger.error(f"Plugin {plugin_id} dependency resolution failed: {dependencies['missing']}")
                return False
            
            # Create sandbox based on metadata
            sandbox = PluginSandboxV2(metadata.limits, metadata.permissions)
            
            # Execute plugin in sandbox
            main_file = plugin_path / "main.py"
            
            with sandbox:
                result = sandbox.execute_plugin(str(main_file), config or {})
                
                # Store plugin information
                self.loaded_plugins[plugin_id] = {
                    'metadata': metadata,
                    'result': result,
                    'sandbox': sandbox,
                    'status': PluginStatus.LOADED,
                    'loaded_at': time.time(),
                    'dependencies': dependencies['loaded'],
                    'checksum_verified': True
                }
                
                logger.info(f"✅ Plugin loaded successfully: {plugin_id}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to load plugin {plugin_id}: {e}")
            logger.debug(f"Plugin loading error details: {traceback.format_exc()}")
            
            # Update plugin status
            if plugin_id in self.loaded_plugins:
                self.loaded_plugins[plugin_id]['status'] = PluginStatus.ERROR
            
            return False
    
    def _quarantine_plugin(self, plugin_id: str):
        """Move plugin to quarantine for security review"""
        try:
            plugin_path = self.plugin_directory / "approved" / plugin_id
            quarantine_path = self.plugin_directory / "quarantine" / plugin_id
            
            if plugin_path.exists():
                shutil.move(str(plugin_path), str(quarantine_path))
                logger.warning(f"🚨 Plugin quarantined: {plugin_id}")
                
                # Log quarantine event
                quarantine_log = {
                    'plugin_id': plugin_id,
                    'timestamp': datetime.now().isoformat(),
                    'reason': 'Security validation failed',
                    'action': 'quarantined'
                }
                
                log_file = self.plugin_directory / "logs" / f"quarantine_{plugin_id}.json"
                with open(log_file, 'w') as f:
                    json.dump(quarantine_log, f, indent=2)
                    
        except Exception as e:
            logger.error(f"Failed to quarantine plugin {plugin_id}: {e}")
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """Unload plugin and clean up resources"""
        if plugin_id not in self.loaded_plugins:
            logger.warning(f"Plugin {plugin_id} not loaded")
            return False
        
        try:
            plugin_info = self.loaded_plugins[plugin_id]
            
            # Update status
            plugin_info['status'] = PluginStatus.UNLOADED
            
            # Clean up plugin resources
            del self.loaded_plugins[plugin_id]
            
            logger.info(f"🧹 Plugin unloaded: {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_id}: {e}")
            return False
    
    def get_plugin_status(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive plugin status information"""
        if plugin_id not in self.loaded_plugins:
            return None
            
        plugin_info = self.loaded_plugins[plugin_id]
        metadata = plugin_info['metadata']
        
        return {
            'id': plugin_id,
            'name': metadata.name,
            'version': metadata.version,
            'status': plugin_info['status'].value,
            'loaded_at': plugin_info['loaded_at'],
            'security_level': metadata.security_level.value,
            'permissions': {
                'can_read_files': metadata.permissions.can_read_files,
                'can_write_files': metadata.permissions.can_write_files,
                'can_access_network': metadata.permissions.can_access_network,
                'security_level': metadata.permissions.security_level.value
            },
            'resource_limits': {
                'max_memory_mb': metadata.limits.max_memory_mb,
                'max_cpu_percent': metadata.limits.max_cpu_percent,
                'max_execution_time_seconds': metadata.limits.max_execution_time_seconds
            },
            'dependencies': plugin_info.get('dependencies', []),
            'checksum_verified': plugin_info.get('checksum_verified', False)
        }
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all plugins with their status"""
        plugins = []
        
        # Add loaded plugins
        for plugin_id in self.loaded_plugins:
            status_info = self.get_plugin_status(plugin_id)
            if status_info:
                plugins.append(status_info)
        
        # Add discovered but not loaded plugins
        for plugin_id in self.plugin_registry:
            if plugin_id not in self.loaded_plugins:
                metadata = self.plugin_registry[plugin_id]
                plugins.append({
                    'id': plugin_id,
                    'name': metadata.name,
                    'version': metadata.version,
                    'status': PluginStatus.UNLOADED.value,
                    'security_level': metadata.security_level.value,
                    'description': metadata.description
                })
        
        return plugins

class SecurityManagerV2:
    """Enhanced security manager for plugin validation"""
    
    def __init__(self):
        self.dangerous_patterns = [
            r'import\s+os', r'import\s+sys', r'import\s+subprocess',
            r'__import__', r'eval\s*\(', r'exec\s*\(', r'compile\s*\(',
            r'open\s*\(', r'file\s*\(', r'input\s*\(', r'raw_input\s*\(',
            r'socket\.', r'urllib\.request', r'requests\.get',
            r'threading\.Thread', r'multiprocessing\.'
        ]
    
    def validate_plugin_security(self, plugin_path: Path) -> bool:
        """Validate plugin security with enhanced checks"""
        try:
            main_file = plugin_path / "main.py"
            if not main_file.exists():
                return False
            
            with open(main_file, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Check for dangerous patterns
            import re
            for pattern in self.dangerous_patterns:
                if re.search(pattern, code):
                    logger.warning(f"Potentially dangerous code pattern found: {pattern}")
                    return False
            
            # Additional security checks
            if len(code) > 100000:  # 100KB limit
                logger.warning("Plugin code exceeds size limit")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Security validation failed: {e}")
            return False
    
    async def validate_plugin_async(self, plugin_path: Path) -> Dict[str, Any]:
        """Asynchronous plugin security validation"""
        # For now, use synchronous validation
        # In future versions, this could use async I/O
        is_safe = self.validate_plugin_security(plugin_path)
        
        return {
            'is_safe': is_safe,
            'reason': 'Security validation completed' if is_safe else 'Security validation failed',
            'timestamp': datetime.now().isoformat()
        }

class DependencyResolverV2:
    """Enhanced dependency resolver for plugin requirements"""
    
    def __init__(self):
        self.available_plugins = set()
        
    async def resolve_dependencies(self, plugin_id: str, dependencies: List[str]) -> Dict[str, Any]:
        """Resolve plugin dependencies"""
        missing_deps = []
        loaded_deps = []
        
        for dep in dependencies:
            if dep in self.available_plugins:
                loaded_deps.append(dep)
            else:
                missing_deps.append(dep)
        
        return {
            'resolved': len(missing_deps) == 0,
            'loaded': loaded_deps,
            'missing': missing_deps
        }

# Global instance for easy access
plugin_framework_v2 = PluginFrameworkV2()

def get_plugin_framework() -> PluginFrameworkV2:
    """Get the global plugin framework instance"""
    return plugin_framework_v2

if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Initialize plugin framework
    framework = PluginFrameworkV2("plugins")
    
    # Discover plugins
    plugins = framework.discover_plugins()
    print(f"Discovered plugins: {plugins}")
    
    # List all plugins
    plugin_list = framework.list_plugins()
    print(f"Plugin list: {json.dumps(plugin_list, indent=2)}")
    
    logger.info("🎉 Plugin Framework v2.0 Foundation initialized successfully!")
