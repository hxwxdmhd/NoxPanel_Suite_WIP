#!/usr/bin/env python3
"""
🔌 ULTIMATE SUITE v9.0 - PLUGIN FRAMEWORK FOUNDATION
==================================================

This module provides the foundation for the modular plugin framework,
enabling community and enterprise add-ons for the Ultimate Suite.

Features:
- Plugin discovery and loading
- Security sandbox for safe plugin execution
- Plugin dependency management
- Hot-reload capability for development
- Plugin marketplace integration
"""

import os
import sys
import json
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Any, Type, Callable
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import logging
from datetime import datetime
import hashlib
import zipfile
import tempfile
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@dataclass
class PluginManifest:
    """Plugin manifest containing metadata and configuration"""
    id: str
    name: str
    version: str
    description: str
    author: str
    website: Optional[str] = None
    license: str = "MIT"
    
    # Requirements
    min_suite_version: str = "8.0.0"
    max_suite_version: Optional[str] = None
    dependencies: List[str] = None
    python_requires: str = ">=3.8"
    
    # Plugin configuration
    entry_point: str = "main.py"
    plugin_class: str = "Plugin"
    category: str = "general"
    tags: List[str] = None
    
    # Security and permissions
    permissions: List[str] = None
    sandbox_enabled: bool = True
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.tags is None:
            self.tags = []
        if self.permissions is None:
            self.permissions = []

class PluginInterface(ABC):
    """Abstract base class for all plugins"""
    
    def __init__(self, manifest: PluginManifest, suite_api: 'SuiteAPI'):
        self.manifest = manifest
        self.suite_api = suite_api
        self.enabled = False
        self.logger = logging.getLogger(f"plugin.{manifest.id}")
        
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin. Return True if successful."""
        pass
        
    @abstractmethod
    def cleanup(self) -> bool:
        """Cleanup plugin resources. Return True if successful."""
        pass
        
    def get_info(self) -> Dict[str, Any]:
        """Get plugin information"""
        return {
            'manifest': asdict(self.manifest),
            'enabled': self.enabled,
            'status': 'active' if self.enabled else 'inactive'
        }
        
    def enable(self) -> bool:
        """Enable the plugin"""
        try:
            if self.initialize():
                self.enabled = True
                self.logger.info(f"Plugin {self.manifest.id} enabled")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to enable plugin {self.manifest.id}: {e}")
            return False
            
    def disable(self) -> bool:
        """Disable the plugin"""
        try:
            if self.cleanup():
                self.enabled = False
                self.logger.info(f"Plugin {self.manifest.id} disabled")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to disable plugin {self.manifest.id}: {e}")
            return False

class SuiteAPI:
    """API interface for plugins to interact with the Ultimate Suite"""
    
    def __init__(self, webapp_instance=None):
        self.webapp = webapp_instance
        self.registered_endpoints = {}
        self.registered_ui_components = {}
        
    def register_endpoint(self, path: str, method: str, handler: Callable, plugin_id: str):
        """Register a new API endpoint from a plugin"""
        endpoint_id = f"{plugin_id}_{method}_{path.replace('/', '_')}"
        self.registered_endpoints[endpoint_id] = {
            'path': path,
            'method': method,
            'handler': handler,
            'plugin_id': plugin_id
        }
        
        # If webapp is available, register with Flask
        if self.webapp and hasattr(self.webapp, 'app'):
            if method.upper() == 'GET':
                self.webapp.app.route(path, methods=['GET'])(handler)
            elif method.upper() == 'POST':
                self.webapp.app.route(path, methods=['POST'])(handler)
                
        logger.info(f"Registered endpoint {method} {path} for plugin {plugin_id}")
        
    def register_ui_component(self, component_id: str, component_data: Dict, plugin_id: str):
        """Register a UI component from a plugin"""
        self.registered_ui_components[component_id] = {
            'data': component_data,
            'plugin_id': plugin_id
        }
        logger.info(f"Registered UI component {component_id} for plugin {plugin_id}")
        
    def get_network_devices(self) -> List[Dict]:
        """Get current network devices"""
        if self.webapp and hasattr(self.webapp, 'network_scanner'):
            return self.webapp.network_scanner._discover_devices("192.168.1.0/24")
        return []
        
    def get_ai_models(self) -> List[Dict]:
        """Get available AI models"""
        if self.webapp and hasattr(self.webapp, 'ai_manager'):
            return list(self.webapp.ai_manager.models.keys())
        return []
        
    def query_ai(self, model_key: str, prompt: str) -> Dict[str, Any]:
        """Query an AI model"""
        if self.webapp and hasattr(self.webapp, 'ai_manager'):
            import asyncio
            return asyncio.run(self.webapp.ai_manager.query_model(model_key, prompt))
        return {'error': 'AI not available'}
        
    def log_event(self, event_type: str, message: str, plugin_id: str):
        """Log an event from a plugin"""
        logger.info(f"[{plugin_id}] {event_type}: {message}")

class SecuritySandbox:
    """Security sandbox for safe plugin execution"""
    
    def __init__(self):
        self.allowed_modules = {
            'json', 'datetime', 'time', 'math', 're', 'base64',
            'hashlib', 'uuid', 'urllib.parse', 'collections'
        }
        self.blocked_modules = {
            'os', 'sys', 'subprocess', 'socket', 'threading',
            'multiprocessing', 'ctypes', '__builtin__', 'builtins'
        }
        
    def validate_plugin(self, plugin_path: Path) -> bool:
        """Validate plugin security"""
        try:
            # Read plugin code
            main_file = plugin_path / "main.py"
            if not main_file.exists():
                return False
                
            with open(main_file, 'r', encoding='utf-8') as f:
                code = f.read()
                
            # Basic security checks
            dangerous_patterns = [
                'import os', 'import sys', 'import subprocess',
                '__import__', 'eval(', 'exec(', 'compile(',
                'open(', 'file(', 'input(', 'raw_input('
            ]
            
            for pattern in dangerous_patterns:
                if pattern in code:
                    logger.warning(f"Potentially dangerous code found: {pattern}")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate plugin: {e}")
            return False
            
    @contextmanager
    def execute_in_sandbox(self, plugin_id: str):
        """Execute plugin code in a restricted environment"""
        # Store original values
        original_import = __builtins__['__import__']
        
        def restricted_import(name, *args, **kwargs):
            if name in self.blocked_modules:
                raise ImportError(f"Module {name} is blocked in sandbox")
            return original_import(name, *args, **kwargs)
            
        try:
            # Replace import function
            __builtins__['__import__'] = restricted_import
            yield
        finally:
            # Restore original import
            __builtins__['__import__'] = original_import

class PluginManager:
    """Main plugin manager for loading, managing, and executing plugins"""
    
    def __init__(self, plugins_dir: str = "plugins", suite_api: SuiteAPI = None):
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(exist_ok=True)
        
        self.suite_api = suite_api or SuiteAPI()
        self.security_sandbox = SecuritySandbox()
        
        self.loaded_plugins: Dict[str, PluginInterface] = {}
        self.plugin_manifests: Dict[str, PluginManifest] = {}
        
        logger.info(f"Plugin manager initialized with directory: {self.plugins_dir}")
        
    def discover_plugins(self) -> List[str]:
        """Discover available plugins in the plugins directory"""
        discovered = []
        
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir():
                manifest_file = plugin_dir / "plugin.json"
                if manifest_file.exists():
                    try:
                        with open(manifest_file, 'r', encoding='utf-8') as f:
                            manifest_data = json.load(f)
                            manifest = PluginManifest(**manifest_data)
                            self.plugin_manifests[manifest.id] = manifest
                            discovered.append(manifest.id)
                            logger.info(f"Discovered plugin: {manifest.id} v{manifest.version}")
                    except Exception as e:
                        logger.error(f"Failed to load manifest for {plugin_dir.name}: {e}")
                        
        return discovered
        
    def load_plugin(self, plugin_id: str) -> bool:
        """Load a specific plugin"""
        if plugin_id in self.loaded_plugins:
            logger.warning(f"Plugin {plugin_id} already loaded")
            return True
            
        if plugin_id not in self.plugin_manifests:
            logger.error(f"Plugin {plugin_id} not found")
            return False
            
        manifest = self.plugin_manifests[plugin_id]
        plugin_dir = self.plugins_dir / plugin_id
        
        try:
            # Security validation
            if manifest.sandbox_enabled and not self.security_sandbox.validate_plugin(plugin_dir):
                logger.error(f"Plugin {plugin_id} failed security validation")
                return False
                
            # Load plugin module
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_id}",
                plugin_dir / manifest.entry_point
            )
            
            if spec is None or spec.loader is None:
                logger.error(f"Could not load plugin {plugin_id}")
                return False
                
            module = importlib.util.module_from_spec(spec)
            
            # Execute in sandbox if enabled
            if manifest.sandbox_enabled:
                with self.security_sandbox.execute_in_sandbox(plugin_id):
                    spec.loader.exec_module(module)
            else:
                spec.loader.exec_module(module)
                
            # Get plugin class
            plugin_class = getattr(module, manifest.plugin_class)
            
            # Create plugin instance
            plugin_instance = plugin_class(manifest, self.suite_api)
            
            # Store plugin
            self.loaded_plugins[plugin_id] = plugin_instance
            
            logger.info(f"Successfully loaded plugin: {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_id}: {e}")
            return False
            
    def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin"""
        if plugin_id not in self.loaded_plugins:
            logger.warning(f"Plugin {plugin_id} not loaded")
            return True
            
        try:
            plugin = self.loaded_plugins[plugin_id]
            plugin.disable()
            del self.loaded_plugins[plugin_id]
            
            logger.info(f"Successfully unloaded plugin: {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_id}: {e}")
            return False
            
    def enable_plugin(self, plugin_id: str) -> bool:
        """Enable a loaded plugin"""
        if plugin_id not in self.loaded_plugins:
            # Try to load it first
            if not self.load_plugin(plugin_id):
                return False
                
        plugin = self.loaded_plugins[plugin_id]
        return plugin.enable()
        
    def disable_plugin(self, plugin_id: str) -> bool:
        """Disable a plugin"""
        if plugin_id not in self.loaded_plugins:
            logger.warning(f"Plugin {plugin_id} not loaded")
            return True
            
        plugin = self.loaded_plugins[plugin_id]
        return plugin.disable()
        
    def get_plugin_info(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a plugin"""
        if plugin_id in self.loaded_plugins:
            return self.loaded_plugins[plugin_id].get_info()
        elif plugin_id in self.plugin_manifests:
            return {
                'manifest': asdict(self.plugin_manifests[plugin_id]),
                'enabled': False,
                'status': 'not_loaded'
            }
        return None
        
    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        """List all discovered plugins"""
        plugins = {}
        
        for plugin_id in self.plugin_manifests:
            plugins[plugin_id] = self.get_plugin_info(plugin_id)
            
        return plugins
        
    def install_plugin(self, plugin_package: str) -> bool:
        """Install a plugin from a package file"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Extract plugin package
                with zipfile.ZipFile(plugin_package, 'r') as zip_file:
                    zip_file.extractall(temp_path)
                    
                # Find manifest
                manifest_file = temp_path / "plugin.json"
                if not manifest_file.exists():
                    logger.error("Plugin package missing manifest file")
                    return False
                    
                # Load and validate manifest
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    manifest_data = json.load(f)
                    manifest = PluginManifest(**manifest_data)
                    
                # Check if plugin already exists
                target_dir = self.plugins_dir / manifest.id
                if target_dir.exists():
                    logger.error(f"Plugin {manifest.id} already installed")
                    return False
                    
                # Security validation
                if manifest.sandbox_enabled and not self.security_sandbox.validate_plugin(temp_path):
                    logger.error(f"Plugin {manifest.id} failed security validation")
                    return False
                    
                # Copy plugin to plugins directory
                import shutil
                shutil.copytree(temp_path, target_dir)
                
                # Update manifest registry
                self.plugin_manifests[manifest.id] = manifest
                
                logger.info(f"Successfully installed plugin: {manifest.id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to install plugin: {e}")
            return False
            
    def create_plugin_template(self, plugin_id: str, plugin_name: str, author: str) -> bool:
        """Create a new plugin template for development"""
        plugin_dir = self.plugins_dir / plugin_id
        
        if plugin_dir.exists():
            logger.error(f"Plugin directory {plugin_id} already exists")
            return False
            
        try:
            plugin_dir.mkdir(parents=True)
            
            # Create manifest
            manifest = PluginManifest(
                id=plugin_id,
                name=plugin_name,
                version="1.0.0",
                description=f"A plugin for {plugin_name}",
                author=author,
                category="general",
                tags=["utility"],
                permissions=["network_read"]
            )
            
            with open(plugin_dir / "plugin.json", 'w', encoding='utf-8') as f:
                json.dump(asdict(manifest), f, indent=2)
                
            # Create main plugin file
            plugin_code = f'''"""
{plugin_name} Plugin
{'-' * (len(plugin_name) + 7)}

A sample plugin for the Ultimate Suite.
"""

from plugin_framework import PluginInterface, SuiteAPI
from typing import Dict, Any

class Plugin(PluginInterface):
    """Main plugin class for {plugin_name}"""
    
    def initialize(self) -> bool:
        """Initialize the plugin"""
        self.logger.info("Initializing {plugin_name} plugin")
        
        # Register API endpoint
        self.suite_api.register_endpoint(
            f"/api/plugins/{plugin_id}/status",
            "GET",
            self.get_status,
            self.manifest.id
        )
        
        return True
        
    def cleanup(self) -> bool:
        """Cleanup plugin resources"""
        self.logger.info("Cleaning up {plugin_name} plugin")
        return True
        
    def get_status(self):
        """API endpoint for plugin status"""
        return {{
            "status": "active",
            "plugin": self.manifest.id,
            "message": "{plugin_name} is running"
        }}
'''
            
            with open(plugin_dir / "main.py", 'w', encoding='utf-8') as f:
                f.write(plugin_code)
                
            # Create README
            readme_content = f'''# {plugin_name} Plugin

## Description
{manifest.description}

## Installation
1. Copy this directory to the Ultimate Suite plugins folder
2. Restart the Ultimate Suite
3. Enable the plugin through the web interface

## Usage
This plugin provides basic functionality template.

## API Endpoints
- `GET /api/plugins/{plugin_id}/status` - Get plugin status

## Author
{author}
'''
            
            with open(plugin_dir / "README.md", 'w', encoding='utf-8') as f:
                f.write(readme_content)
                
            logger.info(f"Created plugin template: {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create plugin template: {e}")
            return False

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Create plugin manager
    manager = PluginManager()
    
    # Discover plugins
    plugins = manager.discover_plugins()
    print(f"Discovered plugins: {plugins}")
    
    # Create example plugin
    if manager.create_plugin_template("example_plugin", "Example Plugin", "Ultimate Suite Team"):
        print("Created example plugin template")
        
    # List all plugins
    all_plugins = manager.list_plugins()
    print(f"All plugins: {json.dumps(all_plugins, indent=2)}")
