#!/usr/bin/env python3
"""
Plugin Framework Foundation - Core Architecture

This module provides the foundational architecture for the modular plugin system
as outlined in ENHANCED_ROADMAP_v9.md. It integrates with the Enhanced Plugin
Sandbox Isolation system for secure plugin execution.

Key Features:
- Clean plugin interface with dependency management
- Secure plugin execution via sandbox integration
- Plugin registry and discovery system
- Plugin lifecycle management
- Development tools and SDK support
"""

import asyncio
import json
import logging
import importlib
import inspect
import hashlib
import shutil
import tempfile
import zipfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable, Type
from packaging import version as pkg_version

# Import Enhanced Plugin Sandbox Integration
try:
    from plugin_sandbox_isolation_enhanced import (
        EnhancedPluginSandbox,
        IsolationConfig,
        IsolationLevel
    )
    from plugin_framework_v2 import (
        PluginLimitsV2,
        PluginPermissionsV2,
        SecurityLevel
    )
    SANDBOX_AVAILABLE = True
except ImportError:
    logging.warning("Enhanced Plugin Sandbox not available - running in compatibility mode")
    SANDBOX_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ============================================================================
# Core Plugin Framework Types and Enums
# ============================================================================

class PluginState(Enum):
    """Plugin lifecycle states"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    DISABLED = "disabled"


class PluginType(Enum):
    """Plugin types supported by the framework"""
    SYSTEM = "system"           # System administration plugins
    NETWORK = "network"         # Network management plugins
    SECURITY = "security"       # Security and monitoring plugins  
    ANALYSIS = "analysis"       # Data analysis plugins
    INTEGRATION = "integration" # Third-party integration plugins
    UTILITY = "utility"         # Utility and helper plugins
    EXTENSION = "extension"     # Framework extensions


class DependencyType(Enum):
    """Types of plugin dependencies"""
    PLUGIN = "plugin"           # Depends on another plugin
    PYTHON_PACKAGE = "package"  # Requires Python package
    SYSTEM_BINARY = "binary"    # Requires system binary/tool
    SERVICE = "service"         # Requires external service
    FEATURE = "feature"         # Requires framework feature


@dataclass
class PluginDependency:
    """Represents a plugin dependency"""
    name: str
    type: DependencyType
    version_requirement: str = "*"  # Semantic versioning requirement
    optional: bool = False
    description: str = ""


@dataclass
class PluginMetadata:
    """Complete plugin metadata"""
    # Basic Information
    id: str                             # Unique plugin identifier
    name: str                          # Human-readable name
    version: str                       # Plugin version (semantic)
    description: str                   # Plugin description
    author: str                        # Plugin author
    email: str = ""                    # Author email
    website: str = ""                  # Plugin website/repository
    license: str = "MIT"               # Plugin license
    
    # Classification
    plugin_type: PluginType = PluginType.UTILITY
    category: str = ""                 # Sub-category within type
    tags: List[str] = field(default_factory=list)
    
    # Dependencies
    dependencies: List[PluginDependency] = field(default_factory=list)
    python_requires: str = ">=3.8"     # Python version requirement
    
    # Framework Integration
    framework_version: str = "1.0.0"   # Required framework version
    sandbox_required: bool = True       # Requires sandbox execution
    
    # Resource Requirements
    estimated_memory_mb: int = 64       # Estimated memory usage
    estimated_cpu_percent: float = 10.0 # Estimated CPU usage
    requires_network: bool = False      # Requires network access
    requires_filesystem: bool = False   # Requires filesystem access
    
    # Lifecycle
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Security
    checksum: str = ""                  # Plugin package checksum
    signature: str = ""                 # Digital signature
    trusted: bool = False               # Trusted plugin flag


@dataclass
class PluginInstallResult:
    """Result of plugin installation"""
    success: bool
    plugin_id: str
    message: str
    installed_files: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class PluginExecutionContext:
    """Execution context for plugin operations"""
    plugin_id: str
    sandbox_id: Optional[str] = None
    user_id: str = "system"
    session_id: str = ""
    environment: Dict[str, Any] = field(default_factory=dict)
    configuration: Dict[str, Any] = field(default_factory=dict)
    permissions: List[str] = field(default_factory=list)


# ============================================================================
# Base Plugin Interface
# ============================================================================

class BasePlugin(ABC):
    """
    Abstract base class for all plugins in the framework.
    
    All plugins must inherit from this class and implement the required methods.
    The framework provides lifecycle management, security, and execution context.
    """
    
    def __init__(self, metadata: PluginMetadata):
        self.metadata = metadata
        self.state = PluginState.UNLOADED
        self.context: Optional[PluginExecutionContext] = None
        self.config: Dict[str, Any] = {}
        self.logger = logging.getLogger(f"plugin.{metadata.id}")
        self._startup_time: Optional[datetime] = None
        self._error_count = 0
        self._execution_count = 0
    
    # ========================================================================
    # Required Plugin Interface Methods
    # ========================================================================
    
    @abstractmethod
    async def initialize(self, context: PluginExecutionContext) -> bool:
        """
        Initialize the plugin with given context.
        
        Args:
            context: Execution context with configuration and permissions
            
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def execute(self, operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a plugin operation.
        
        Args:
            operation: Name of the operation to perform
            parameters: Operation parameters
            
        Returns:
            Operation results dictionary
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """
        Cleanup plugin resources.
        
        Returns:
            True if cleanup successful, False otherwise
        """
        pass
    
    # ========================================================================
    # Optional Plugin Interface Methods
    # ========================================================================
    
    async def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate plugin configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        return []
    
    async def get_supported_operations(self) -> List[str]:
        """
        Get list of supported operations.
        
        Returns:
            List of operation names
        """
        return ["status", "info"]
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get current plugin status.
        
        Returns:
            Status information dictionary
        """
        return {
            "state": self.state.value,
            "startup_time": self._startup_time.isoformat() if self._startup_time else None,
            "execution_count": self._execution_count,
            "error_count": self._error_count,
            "metadata": {
                "id": self.metadata.id,
                "name": self.metadata.name,
                "version": self.metadata.version
            }
        }
    
    async def handle_error(self, error: Exception, operation: str = "") -> Dict[str, Any]:
        """
        Handle plugin errors.
        
        Args:
            error: Exception that occurred
            operation: Operation that failed
            
        Returns:
            Error response dictionary
        """
        self._error_count += 1
        self.logger.error(f"Plugin error in {operation}: {error}")
        
        return {
            "success": False,
            "error": {
                "type": type(error).__name__,
                "message": str(error),
                "operation": operation
            },
            "plugin_id": self.metadata.id
        }
    
    # ========================================================================
    # Plugin Lifecycle Management
    # ========================================================================
    
    async def _transition_state(self, new_state: PluginState) -> bool:
        """Internal method to transition plugin state"""
        
        valid_transitions = {
            PluginState.UNLOADED: [PluginState.LOADING, PluginState.ERROR],
            PluginState.LOADING: [PluginState.LOADED, PluginState.ERROR],
            PluginState.LOADED: [PluginState.INITIALIZING, PluginState.ERROR, PluginState.DISABLED],
            PluginState.INITIALIZING: [PluginState.ACTIVE, PluginState.ERROR],
            PluginState.ACTIVE: [PluginState.STOPPING, PluginState.ERROR, PluginState.DISABLED],
            PluginState.STOPPING: [PluginState.STOPPED, PluginState.ERROR],
            PluginState.STOPPED: [PluginState.LOADING, PluginState.DISABLED],
            PluginState.ERROR: [PluginState.LOADING, PluginState.DISABLED],
            PluginState.DISABLED: [PluginState.LOADING]
        }
        
        if new_state in valid_transitions.get(self.state, []):
            old_state = self.state
            self.state = new_state
            self.logger.info(f"Plugin state transition: {old_state.value} -> {new_state.value}")
            return True
        else:
            self.logger.warning(f"Invalid state transition: {self.state.value} -> {new_state.value}")
            return False
    
    def set_configuration(self, config: Dict[str, Any]):
        """Set plugin configuration"""
        self.config = config.copy()
        self.logger.info(f"Configuration updated: {len(config)} settings")
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get current plugin configuration"""
        return self.config.copy()


# ============================================================================
# Plugin Manager Core
# ============================================================================

class PluginManager:
    """
    Core plugin manager responsible for plugin lifecycle management,
    dependency resolution, and secure execution coordination.
    """
    
    def __init__(self, plugins_directory: Path = None, sandbox_config: IsolationConfig = None):
        self.plugins_directory = plugins_directory or Path("./plugins")
        self.plugins_directory.mkdir(parents=True, exist_ok=True)
        
        # Plugin tracking
        self.loaded_plugins: Dict[str, BasePlugin] = {}
        self.plugin_metadata: Dict[str, PluginMetadata] = {}
        self.plugin_dependencies: Dict[str, List[PluginDependency]] = {}
        
        # Sandbox integration
        self.sandbox_config = sandbox_config or IsolationConfig(level=IsolationLevel.STANDARD)
        self.active_sandboxes: Dict[str, EnhancedPluginSandbox] = {}
        
        # Plugin registry
        self.plugin_registry = PluginRegistry()
        
        # Statistics
        self.stats = {
            "loaded_plugins": 0,
            "active_plugins": 0,
            "total_executions": 0,
            "failed_executions": 0
        }
        
        self.logger = logging.getLogger("PluginManager")
        self.logger.info("Plugin Manager initialized")
    
    # ========================================================================
    # Plugin Loading and Unloading
    # ========================================================================
    
    async def load_plugin(self, plugin_path: Union[str, Path], plugin_config: Dict[str, Any] = None) -> bool:
        """
        Load a plugin from a file or directory.
        
        Args:
            plugin_path: Path to plugin file or directory
            plugin_config: Optional plugin configuration
            
        Returns:
            True if plugin loaded successfully, False otherwise
        """
        
        try:
            plugin_path = Path(plugin_path)
            self.logger.info(f"Loading plugin from: {plugin_path}")
            
            # Discover plugin metadata
            metadata = await self._discover_plugin_metadata(plugin_path)
            if not metadata:
                self.logger.error(f"Could not discover metadata for plugin: {plugin_path}")
                return False
            
            # Check if plugin already loaded
            if metadata.id in self.loaded_plugins:
                self.logger.warning(f"Plugin {metadata.id} already loaded")
                return True
            
            # Verify dependencies
            if not await self._verify_dependencies(metadata):
                self.logger.error(f"Dependency verification failed for plugin: {metadata.id}")
                return False
            
            # Import plugin module
            plugin_instance = await self._import_plugin(plugin_path, metadata)
            if not plugin_instance:
                self.logger.error(f"Failed to import plugin: {metadata.id}")
                return False
            
            # Validate plugin interface
            if not self._validate_plugin_interface(plugin_instance):
                self.logger.error(f"Plugin interface validation failed: {metadata.id}")
                return False
            
            # Set plugin configuration
            if plugin_config:
                plugin_instance.set_configuration(plugin_config)
            
            # Transition to loaded state
            if not await plugin_instance._transition_state(PluginState.LOADED):
                self.logger.error(f"Failed to transition plugin to loaded state: {metadata.id}")
                return False
            
            # Register plugin
            self.loaded_plugins[metadata.id] = plugin_instance
            self.plugin_metadata[metadata.id] = metadata
            self.plugin_registry.register_plugin(metadata)
            
            self.stats["loaded_plugins"] += 1
            self.logger.info(f"Successfully loaded plugin: {metadata.id} v{metadata.version}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading plugin {plugin_path}: {e}")
            return False
    
    async def unload_plugin(self, plugin_id: str) -> bool:
        """
        Unload a plugin and cleanup resources.
        
        Args:
            plugin_id: ID of plugin to unload
            
        Returns:
            True if plugin unloaded successfully, False otherwise
        """
        
        try:
            if plugin_id not in self.loaded_plugins:
                self.logger.warning(f"Plugin {plugin_id} not loaded")
                return True
            
            plugin = self.loaded_plugins[plugin_id]
            
            # Stop plugin if active
            if plugin.state == PluginState.ACTIVE:
                if not await self.stop_plugin(plugin_id):
                    self.logger.warning(f"Failed to stop plugin {plugin_id} during unload")
            
            # Cleanup plugin resources
            try:
                await plugin.cleanup()
            except Exception as e:
                self.logger.warning(f"Plugin cleanup error for {plugin_id}: {e}")
            
            # Cleanup sandbox if exists
            if plugin_id in self.active_sandboxes:
                try:
                    await self.active_sandboxes[plugin_id].__aexit__(None, None, None)
                    del self.active_sandboxes[plugin_id]
                except Exception as e:
                    self.logger.warning(f"Sandbox cleanup error for {plugin_id}: {e}")
            
            # Remove from tracking
            del self.loaded_plugins[plugin_id]
            if plugin_id in self.plugin_metadata:
                del self.plugin_metadata[plugin_id]
            
            self.plugin_registry.unregister_plugin(plugin_id)
            
            self.stats["loaded_plugins"] -= 1
            if plugin.state == PluginState.ACTIVE:
                self.stats["active_plugins"] -= 1
            
            self.logger.info(f"Successfully unloaded plugin: {plugin_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error unloading plugin {plugin_id}: {e}")
            return False
    
    # ========================================================================
    # Plugin Execution Management
    # ========================================================================
    
    async def start_plugin(self, plugin_id: str, context: PluginExecutionContext = None) -> bool:
        """
        Start (initialize and activate) a plugin.
        
        Args:
            plugin_id: ID of plugin to start
            context: Execution context
            
        Returns:
            True if plugin started successfully, False otherwise
        """
        
        try:
            if plugin_id not in self.loaded_plugins:
                self.logger.error(f"Plugin {plugin_id} not loaded")
                return False
            
            plugin = self.loaded_plugins[plugin_id]
            
            if plugin.state == PluginState.ACTIVE:
                self.logger.info(f"Plugin {plugin_id} already active")
                return True
            
            # Transition to initializing
            if not await plugin._transition_state(PluginState.INITIALIZING):
                return False
            
            # Create execution context if not provided
            if context is None:
                context = PluginExecutionContext(
                    plugin_id=plugin_id,
                    environment={"framework_version": "1.0.0"},
                    configuration=plugin.get_configuration()
                )
            
            # Create sandbox for plugin if required
            if plugin.metadata.sandbox_required and SANDBOX_AVAILABLE:
                sandbox = await self._create_plugin_sandbox(plugin)
                context.sandbox_id = sandbox.sandbox_id if hasattr(sandbox, 'sandbox_id') else plugin_id
                self.active_sandboxes[plugin_id] = sandbox
            
            # Initialize plugin
            plugin.context = context
            
            # Execute initialization in sandbox if available
            if plugin_id in self.active_sandboxes:
                async with self.active_sandboxes[plugin_id]:
                    initialization_success = await plugin.initialize(context)
            else:
                initialization_success = await plugin.initialize(context)
            
            if not initialization_success:
                self.logger.error(f"Plugin initialization failed: {plugin_id}")
                await plugin._transition_state(PluginState.ERROR)
                return False
            
            # Transition to active
            if not await plugin._transition_state(PluginState.ACTIVE):
                return False
            
            plugin._startup_time = datetime.now()
            self.stats["active_plugins"] += 1
            
            self.logger.info(f"Successfully started plugin: {plugin_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting plugin {plugin_id}: {e}")
            if plugin_id in self.loaded_plugins:
                await self.loaded_plugins[plugin_id]._transition_state(PluginState.ERROR)
            return False
    
    async def stop_plugin(self, plugin_id: str) -> bool:
        """
        Stop an active plugin.
        
        Args:
            plugin_id: ID of plugin to stop
            
        Returns:
            True if plugin stopped successfully, False otherwise
        """
        
        try:
            if plugin_id not in self.loaded_plugins:
                self.logger.error(f"Plugin {plugin_id} not loaded")
                return False
            
            plugin = self.loaded_plugins[plugin_id]
            
            if plugin.state != PluginState.ACTIVE:
                self.logger.info(f"Plugin {plugin_id} not active")
                return True
            
            # Transition to stopping
            if not await plugin._transition_state(PluginState.STOPPING):
                return False
            
            # Cleanup plugin
            try:
                await plugin.cleanup()
            except Exception as e:
                self.logger.warning(f"Plugin cleanup error for {plugin_id}: {e}")
            
            # Cleanup sandbox
            if plugin_id in self.active_sandboxes:
                try:
                    await self.active_sandboxes[plugin_id].__aexit__(None, None, None)
                    del self.active_sandboxes[plugin_id]
                except Exception as e:
                    self.logger.warning(f"Sandbox cleanup error for {plugin_id}: {e}")
            
            # Transition to stopped
            if not await plugin._transition_state(PluginState.STOPPED):
                return False
            
            self.stats["active_plugins"] -= 1
            
            self.logger.info(f"Successfully stopped plugin: {plugin_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping plugin {plugin_id}: {e}")
            return False
    
    async def execute_plugin_operation(self, plugin_id: str, operation: str, 
                                     parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute an operation on a plugin.
        
        Args:
            plugin_id: ID of plugin to execute operation on
            operation: Name of operation to execute
            parameters: Operation parameters
            
        Returns:
            Operation result dictionary
        """
        
        try:
            if plugin_id not in self.loaded_plugins:
                return {
                    "success": False,
                    "error": f"Plugin {plugin_id} not loaded"
                }
            
            plugin = self.loaded_plugins[plugin_id]
            
            if plugin.state != PluginState.ACTIVE:
                return {
                    "success": False,
                    "error": f"Plugin {plugin_id} not active (state: {plugin.state.value})"
                }
            
            parameters = parameters or {}
            self.stats["total_executions"] += 1
            plugin._execution_count += 1
            
            # Execute operation in sandbox if available
            if plugin_id in self.active_sandboxes:
                result = await self.active_sandboxes[plugin_id].execute_plugin_safe(
                    plugin.execute, operation, parameters
                )
            else:
                result = await plugin.execute(operation, parameters)
            
            # Ensure result is properly formatted
            if not isinstance(result, dict):
                result = {"result": result}
            
            if "success" not in result:
                result["success"] = True
            
            result["plugin_id"] = plugin_id
            result["operation"] = operation
            
            return result
            
        except Exception as e:
            self.stats["failed_executions"] += 1
            self.logger.error(f"Error executing {operation} on plugin {plugin_id}: {e}")
            
            if plugin_id in self.loaded_plugins:
                return await self.loaded_plugins[plugin_id].handle_error(e, operation)
            else:
                return {
                    "success": False,
                    "error": {
                        "type": type(e).__name__,
                        "message": str(e),
                        "operation": operation
                    },
                    "plugin_id": plugin_id
                }
    
    # ========================================================================
    # Plugin Discovery and Metadata
    # ========================================================================
    
    async def _discover_plugin_metadata(self, plugin_path: Path) -> Optional[PluginMetadata]:
        """Discover plugin metadata from plugin path"""
        
        try:
            # Look for plugin.json metadata file
            if plugin_path.is_dir():
                metadata_file = plugin_path / "plugin.json"
            else:
                metadata_file = plugin_path.parent / f"{plugin_path.stem}.json"
            
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata_dict = json.load(f)
                
                # Convert dictionary to PluginMetadata
                return self._dict_to_metadata(metadata_dict)
            
            # Try to discover metadata from Python module
            return await self._discover_metadata_from_module(plugin_path)
            
        except Exception as e:
            self.logger.error(f"Error discovering plugin metadata: {e}")
            return None
    
    def _dict_to_metadata(self, metadata_dict: Dict[str, Any]) -> PluginMetadata:
        """Convert dictionary to PluginMetadata object"""
        
        # Handle dependencies
        dependencies = []
        for dep_dict in metadata_dict.get("dependencies", []):
            dependencies.append(PluginDependency(
                name=dep_dict["name"],
                type=DependencyType(dep_dict["type"]),
                version_requirement=dep_dict.get("version_requirement", "*"),
                optional=dep_dict.get("optional", False),
                description=dep_dict.get("description", "")
            ))
        
        # Handle plugin type
        plugin_type = PluginType.UTILITY
        if "plugin_type" in metadata_dict:
            plugin_type = PluginType(metadata_dict["plugin_type"])
        
        return PluginMetadata(
            id=metadata_dict["id"],
            name=metadata_dict["name"],
            version=metadata_dict["version"],
            description=metadata_dict.get("description", ""),
            author=metadata_dict.get("author", "Unknown"),
            email=metadata_dict.get("email", ""),
            website=metadata_dict.get("website", ""),
            license=metadata_dict.get("license", "MIT"),
            plugin_type=plugin_type,
            category=metadata_dict.get("category", ""),
            tags=metadata_dict.get("tags", []),
            dependencies=dependencies,
            python_requires=metadata_dict.get("python_requires", ">=3.8"),
            framework_version=metadata_dict.get("framework_version", "1.0.0"),
            sandbox_required=metadata_dict.get("sandbox_required", True),
            estimated_memory_mb=metadata_dict.get("estimated_memory_mb", 64),
            estimated_cpu_percent=metadata_dict.get("estimated_cpu_percent", 10.0),
            requires_network=metadata_dict.get("requires_network", False),
            requires_filesystem=metadata_dict.get("requires_filesystem", False)
        )
    
    async def _discover_metadata_from_module(self, plugin_path: Path) -> Optional[PluginMetadata]:
        """Try to discover metadata from Python module docstrings and attributes"""
        
        try:
            # This would involve importing the module and inspecting it
            # For now, return a basic metadata structure
            return PluginMetadata(
                id=plugin_path.stem,
                name=plugin_path.stem.replace("_", " ").title(),
                version="1.0.0",
                description="Plugin discovered from module",
                author="Unknown"
            )
            
        except Exception as e:
            self.logger.error(f"Error discovering metadata from module: {e}")
            return None
    
    # ========================================================================
    # Dependency Management
    # ========================================================================
    
    async def _verify_dependencies(self, metadata: PluginMetadata) -> bool:
        """Verify plugin dependencies are satisfied"""
        
        try:
            for dependency in metadata.dependencies:
                if not await self._check_dependency(dependency):
                    if not dependency.optional:
                        self.logger.error(f"Required dependency not satisfied: {dependency.name}")
                        return False
                    else:
                        self.logger.warning(f"Optional dependency not satisfied: {dependency.name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying dependencies: {e}")
            return False
    
    async def _check_dependency(self, dependency: PluginDependency) -> bool:
        """Check if a specific dependency is satisfied"""
        
        try:
            if dependency.type == DependencyType.PLUGIN:
                # Check if plugin is loaded
                return dependency.name in self.loaded_plugins
            
            elif dependency.type == DependencyType.PYTHON_PACKAGE:
                # Check if Python package is available
                try:
                    importlib.import_module(dependency.name)
                    return True
                except ImportError:
                    return False
            
            elif dependency.type == DependencyType.SYSTEM_BINARY:
                # Check if system binary is available
                return shutil.which(dependency.name) is not None
            
            elif dependency.type == DependencyType.SERVICE:
                # This would involve checking if external service is available
                # For now, assume services are available
                return True
            
            elif dependency.type == DependencyType.FEATURE:
                # Check if framework feature is available
                return True  # For now, assume all features are available
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking dependency {dependency.name}: {e}")
            return False
    
    # ========================================================================
    # Sandbox Integration
    # ========================================================================
    
    async def _create_plugin_sandbox(self, plugin: BasePlugin) -> 'EnhancedPluginSandbox':
        """Create sandbox for plugin execution"""
        
        if not SANDBOX_AVAILABLE:
            raise RuntimeError("Enhanced Plugin Sandbox not available")
        
        # Configure limits based on plugin metadata
        limits = PluginLimitsV2(
            max_memory_mb=plugin.metadata.estimated_memory_mb,
            max_execution_time_seconds=60,  # Default timeout
            max_cpu_percent=plugin.metadata.estimated_cpu_percent,
            max_network_connections=10 if plugin.metadata.requires_network else 0
        )
        
        # Configure permissions
        permissions = PluginPermissionsV2(
            security_level=SecurityLevel.MEDIUM,
            can_access_filesystem=plugin.metadata.requires_filesystem,
            can_access_network=plugin.metadata.requires_network
        )
        
        # Create sandbox
        sandbox = EnhancedPluginSandbox(limits, permissions, self.sandbox_config)
        return sandbox
    
    # ========================================================================
    # Plugin Import and Validation
    # ========================================================================
    
    async def _import_plugin(self, plugin_path: Path, metadata: PluginMetadata) -> Optional[BasePlugin]:
        """Import plugin module and create instance"""
        
        try:
            if plugin_path.is_dir():
                # Directory-based plugin
                main_file = plugin_path / "__init__.py"
                if not main_file.exists():
                    main_file = plugin_path / "main.py"
                
                if not main_file.exists():
                    self.logger.error(f"No main plugin file found in {plugin_path}")
                    return None
                
                spec = importlib.util.spec_from_file_location(metadata.id, main_file)
            else:
                # Single file plugin
                spec = importlib.util.spec_from_file_location(metadata.id, plugin_path)
            
            if spec is None:
                self.logger.error(f"Could not create module spec for {plugin_path}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find plugin class
            plugin_class = None
            for name in dir(module):
                obj = getattr(module, name)
                if (inspect.isclass(obj) and 
                    issubclass(obj, BasePlugin) and 
                    obj != BasePlugin):
                    plugin_class = obj
                    break
            
            if plugin_class is None:
                self.logger.error(f"No plugin class found in {plugin_path}")
                return None
            
            # Create plugin instance
            plugin_instance = plugin_class(metadata)
            return plugin_instance
            
        except Exception as e:
            self.logger.error(f"Error importing plugin {plugin_path}: {e}")
            return None
    
    def _validate_plugin_interface(self, plugin: BasePlugin) -> bool:
        """Validate that plugin implements required interface"""
        
        try:
            # Check required methods
            required_methods = ['initialize', 'execute', 'cleanup']
            for method_name in required_methods:
                if not hasattr(plugin, method_name):
                    self.logger.error(f"Plugin missing required method: {method_name}")
                    return False
                
                method = getattr(plugin, method_name)
                if not callable(method):
                    self.logger.error(f"Plugin method not callable: {method_name}")
                    return False
            
            # Check that plugin inherits from BasePlugin
            if not isinstance(plugin, BasePlugin):
                self.logger.error("Plugin does not inherit from BasePlugin")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating plugin interface: {e}")
            return False
    
    # ========================================================================
    # Plugin Information and Statistics
    # ========================================================================
    
    def get_loaded_plugins(self) -> Dict[str, Dict[str, Any]]:
        """Get information about loaded plugins"""
        
        plugins_info = {}
        for plugin_id, plugin in self.loaded_plugins.items():
            plugins_info[plugin_id] = {
                "metadata": {
                    "id": plugin.metadata.id,
                    "name": plugin.metadata.name,
                    "version": plugin.metadata.version,
                    "type": plugin.metadata.plugin_type.value,
                    "author": plugin.metadata.author
                },
                "state": plugin.state.value,
                "execution_count": plugin._execution_count,
                "error_count": plugin._error_count,
                "startup_time": plugin._startup_time.isoformat() if plugin._startup_time else None,
                "has_sandbox": plugin_id in self.active_sandboxes
            }
        
        return plugins_info
    
    def get_plugin_statistics(self) -> Dict[str, Any]:
        """Get plugin manager statistics"""
        
        return {
            **self.stats,
            "plugin_states": {
                state.value: sum(1 for p in self.loaded_plugins.values() if p.state == state)
                for state in PluginState
            },
            "plugin_types": {
                plugin_type.value: sum(1 for p in self.loaded_plugins.values() 
                                     if p.metadata.plugin_type == plugin_type)
                for plugin_type in PluginType
            },
            "active_sandboxes": len(self.active_sandboxes)
        }
    
    async def get_plugin_status(self, plugin_id: str) -> Dict[str, Any]:
        """Get detailed status for a specific plugin"""
        
        if plugin_id not in self.loaded_plugins:
            return {
                "error": f"Plugin {plugin_id} not loaded"
            }
        
        plugin = self.loaded_plugins[plugin_id]
        status = await plugin.get_status()
        
        # Add manager-specific information
        status.update({
            "has_sandbox": plugin_id in self.active_sandboxes,
            "sandbox_id": plugin.context.sandbox_id if plugin.context else None,
            "supported_operations": await plugin.get_supported_operations()
        })
        
        return status


# ============================================================================
# Plugin Registry System
# ============================================================================

class PluginRegistry:
    """Plugin registry for discovery and management"""
    
    def __init__(self, registry_file: Path = None):
        self.registry_file = registry_file or Path("./plugin_registry.json")
        self.registered_plugins: Dict[str, PluginMetadata] = {}
        self._load_registry()
    
    def register_plugin(self, metadata: PluginMetadata):
        """Register a plugin in the registry"""
        
        self.registered_plugins[metadata.id] = metadata
        self._save_registry()
        logger.info(f"Registered plugin: {metadata.id}")
    
    def unregister_plugin(self, plugin_id: str):
        """Unregister a plugin from the registry"""
        
        if plugin_id in self.registered_plugins:
            del self.registered_plugins[plugin_id]
            self._save_registry()
            logger.info(f"Unregistered plugin: {plugin_id}")
    
    def find_plugins(self, plugin_type: PluginType = None, category: str = None) -> List[PluginMetadata]:
        """Find plugins by type or category"""
        
        results = []
        for metadata in self.registered_plugins.values():
            if plugin_type and metadata.plugin_type != plugin_type:
                continue
            if category and metadata.category != category:
                continue
            results.append(metadata)
        
        return results
    
    def get_plugin_metadata(self, plugin_id: str) -> Optional[PluginMetadata]:
        """Get metadata for a specific plugin"""
        
        return self.registered_plugins.get(plugin_id)
    
    def _load_registry(self):
        """Load registry from file"""
        
        try:
            if self.registry_file.exists():
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    registry_data = json.load(f)
                
                for plugin_id, metadata_dict in registry_data.items():
                    # Convert back to PluginMetadata (simplified for now)
                    self.registered_plugins[plugin_id] = PluginMetadata(
                        id=metadata_dict["id"],
                        name=metadata_dict["name"],
                        version=metadata_dict["version"],
                        description=metadata_dict.get("description", ""),
                        author=metadata_dict.get("author", "Unknown")
                    )
                
                logger.info(f"Loaded {len(self.registered_plugins)} plugins from registry")
                
        except Exception as e:
            logger.warning(f"Error loading plugin registry: {e}")
    
    def _save_registry(self):
        """Save registry to file"""
        
        try:
            registry_data = {}
            for plugin_id, metadata in self.registered_plugins.items():
                registry_data[plugin_id] = {
                    "id": metadata.id,
                    "name": metadata.name,
                    "version": metadata.version,
                    "description": metadata.description,
                    "author": metadata.author,
                    "plugin_type": metadata.plugin_type.value
                }
            
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(registry_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving plugin registry: {e}")


# ============================================================================
# Main Plugin Framework Class
# ============================================================================

class PluginFramework:
    """
    Main Plugin Framework class that coordinates all plugin operations.
    
    This is the primary interface for plugin management, providing simplified
    methods for common operations while maintaining the full flexibility of
    the underlying systems.
    """
    
    def __init__(self, plugins_directory: Path = None, config: Dict[str, Any] = None):
        """
        Initialize the Plugin Framework.
        
        Args:
            plugins_directory: Directory containing plugins
            config: Framework configuration
        """
        
        self.config = config or {}
        
        # Initialize core components
        sandbox_config = IsolationConfig(
            level=IsolationLevel(self.config.get("sandbox_isolation_level", "standard")),
            enable_real_time_monitoring=self.config.get("enable_monitoring", True)
        )
        
        self.plugin_manager = PluginManager(plugins_directory, sandbox_config)
        self.logger = logging.getLogger("PluginFramework")
        self.logger.info("Plugin Framework initialized")
    
    # ========================================================================
    # High-level Plugin Operations
    # ========================================================================
    
    async def load_plugin(self, plugin_id: str) -> bool:
        """
        Load and start a plugin.
        
        Args:
            plugin_id: Plugin identifier or path
            
        Returns:
            True if successful, False otherwise
        """
        
        try:
            # Try to find plugin in plugins directory
            plugin_path = self.plugin_manager.plugins_directory / plugin_id
            if not plugin_path.exists():
                plugin_path = Path(plugin_id)
            
            if not plugin_path.exists():
                self.logger.error(f"Plugin not found: {plugin_id}")
                return False
            
            # Load plugin
            if not await self.plugin_manager.load_plugin(plugin_path):
                return False
            
            # Start plugin
            plugin_metadata = None
            for metadata in self.plugin_manager.plugin_metadata.values():
                if metadata.id == plugin_id or plugin_path.name == plugin_id:
                    plugin_metadata = metadata
                    break
            
            if plugin_metadata:
                return await self.plugin_manager.start_plugin(plugin_metadata.id)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error loading plugin {plugin_id}: {e}")
            return False
    
    async def install_plugin(self, plugin_package: str) -> PluginInstallResult:
        """
        Install a plugin from a package file or URL.
        
        Args:
            plugin_package: Path to plugin package or URL
            
        Returns:
            Installation result
        """
        
        try:
            self.logger.info(f"Installing plugin package: {plugin_package}")
            
            # This would implement the full plugin installation process
            # For now, return a placeholder result
            
            return PluginInstallResult(
                success=False,
                plugin_id="",
                message="Plugin installation not yet implemented",
                errors=["Installation system under development"]
            )
            
        except Exception as e:
            self.logger.error(f"Error installing plugin package: {e}")
            return PluginInstallResult(
                success=False,
                plugin_id="",
                message="Installation failed",
                errors=[str(e)]
            )
    
    def create_plugin_template(self, plugin_type: str) -> str:
        """
        Generate a plugin template for development.
        
        Args:
            plugin_type: Type of plugin to create template for
            
        Returns:
            Template code as string
        """
        
        try:
            plugin_type_enum = PluginType(plugin_type.lower())
            
            template = f"""#!/usr/bin/env python3
\"\"\"
{plugin_type.title()} Plugin Template

This template provides a starting point for developing a {plugin_type} plugin
for the Plugin Framework Foundation.
\"\"\"

import asyncio
from typing import Dict, List, Any
from plugin_framework_core import BasePlugin, PluginMetadata, PluginType, PluginExecutionContext


class My{plugin_type.title()}Plugin(BasePlugin):
    \"\"\"Example {plugin_type} plugin implementation\"\"\"
    
    def __init__(self):
        metadata = PluginMetadata(
            id="my_{plugin_type}_plugin",
            name="My {plugin_type.title()} Plugin",
            version="1.0.0",
            description="A sample {plugin_type} plugin",
            author="Plugin Developer",
            plugin_type=PluginType.{plugin_type_enum.name},
            sandbox_required=True
        )
        super().__init__(metadata)
    
    async def initialize(self, context: PluginExecutionContext) -> bool:
        \"\"\"Initialize the plugin\"\"\"
        
        self.logger.info("Initializing {plugin_type} plugin")
        
        # Plugin initialization logic here
        
        return True
    
    async def execute(self, operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Execute plugin operation\"\"\"
        
        self.logger.info(f"Executing operation: {{operation}}")
        
        if operation == "example_operation":
            return await self._example_operation(parameters)
        elif operation == "status":
            return await self.get_status()
        else:
            return {{
                "success": False,
                "error": f"Unknown operation: {{operation}}"
            }}
    
    async def cleanup(self) -> bool:
        \"\"\"Cleanup plugin resources\"\"\"
        
        self.logger.info("Cleaning up {plugin_type} plugin")
        
        # Cleanup logic here
        
        return True
    
    async def get_supported_operations(self) -> List[str]:
        \"\"\"Get list of supported operations\"\"\"
        
        return ["example_operation", "status"]
    
    async def _example_operation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Example operation implementation\"\"\"
        
        return {{
            "success": True,
            "message": "Example operation completed successfully",
            "parameters": parameters
        }}


# Plugin entry point
def create_plugin() -> BasePlugin:
    \"\"\"Create and return plugin instance\"\"\"
    return My{plugin_type.title()}Plugin()
"""
            
            return template
            
        except Exception as e:
            self.logger.error(f"Error creating plugin template: {e}")
            return f"# Error creating template: {e}"
    
    # ========================================================================
    # Plugin Information and Management
    # ========================================================================
    
    async def list_plugins(self) -> Dict[str, Any]:
        """List all loaded plugins with their status"""
        
        return self.plugin_manager.get_loaded_plugins()
    
    async def get_plugin_info(self, plugin_id: str) -> Dict[str, Any]:
        """Get detailed information about a plugin"""
        
        return await self.plugin_manager.get_plugin_status(plugin_id)
    
    async def execute_operation(self, plugin_id: str, operation: str, 
                              parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute an operation on a plugin"""
        
        return await self.plugin_manager.execute_plugin_operation(plugin_id, operation, parameters)
    
    def get_framework_statistics(self) -> Dict[str, Any]:
        """Get framework statistics"""
        
        stats = self.plugin_manager.get_plugin_statistics()
        stats.update({
            "framework_version": "1.0.0",
            "sandbox_available": SANDBOX_AVAILABLE,
            "plugins_directory": str(self.plugin_manager.plugins_directory)
        })
        
        return stats


# ============================================================================
# Example Usage and Testing
# ============================================================================

async def main():
    """Example usage of the Plugin Framework"""
    
    print("🔌 Plugin Framework Foundation - Example Usage")
    print("=" * 60)
    
    # Initialize framework
    framework = PluginFramework()
    
    # Generate example plugin template
    print("\n📝 Creating example plugin template:")
    template = framework.create_plugin_template("utility")
    print("Template created successfully!")
    
    # Get framework statistics
    print("\n📊 Framework Statistics:")
    stats = framework.get_framework_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # List loaded plugins
    print("\n🔌 Loaded Plugins:")
    plugins = await framework.list_plugins()
    if plugins:
        for plugin_id, info in plugins.items():
            print(f"  - {plugin_id}: {info['metadata']['name']} v{info['metadata']['version']}")
    else:
        print("  No plugins currently loaded")
    
    print("\n✅ Plugin Framework Foundation demonstration complete!")


if __name__ == "__main__":
    asyncio.run(main())
