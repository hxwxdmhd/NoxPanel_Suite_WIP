#!/usr/bin/env python3
"""
Plugin Manifest System - Audit 3 Compliant
==========================================

This system provides standardized plugin manifest files:
- Plugin.json manifest specification
- Manifest validation and parsing
- Dependency resolution
- Configuration schema validation
- Security requirement specification
- API compatibility checking

Essential for production-ready plugin ecosystem
"""

import os
import json
import jsonschema
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import re
import hashlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PluginAPIVersion(Enum):
    """Plugin API version compatibility"""
    V1_0 = "1.0"
    V1_1 = "1.1"
    V2_0 = "2.0"

class PluginLicenseType(Enum):
    """Plugin license types"""
    MIT = "MIT"
    APACHE_2_0 = "Apache-2.0"
    GPL_3_0 = "GPL-3.0"
    BSD_3_CLAUSE = "BSD-3-Clause"
    PROPRIETARY = "Proprietary"
    CUSTOM = "Custom"

@dataclass
class PluginDependency:
    """Plugin dependency specification"""
    name: str
    version: str = "*"
    optional: bool = False
    reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginDependency':
        return cls(**data)

@dataclass
class PluginPermission:
    """Plugin permission specification"""
    name: str
    description: str
    required: bool = True
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginPermission':
        return cls(**data)

@dataclass
class PluginConfigOption:
    """Plugin configuration option"""
    name: str
    type: str  # string, integer, boolean, float, array, object
    default: Any = None
    description: str = ""
    required: bool = False
    validation: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginConfigOption':
        return cls(**data)

@dataclass
class PluginEndpoint:
    """Plugin API endpoint specification"""
    path: str
    method: str  # GET, POST, PUT, DELETE
    description: str = ""
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    response_schema: Dict[str, Any] = field(default_factory=dict)
    requires_auth: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginEndpoint':
        return cls(**data)

@dataclass
class PluginManifest:
    """
    Complete plugin manifest specification
    """
    # Basic Information
    name: str
    version: str
    description: str
    author: str
    email: str = ""
    website: str = ""
    repository: str = ""
    license: PluginLicenseType = PluginLicenseType.MIT
    
    # Compatibility
    api_version: PluginAPIVersion = PluginAPIVersion.V1_0
    python_version: str = ">=3.8"
    platform: List[str] = field(default_factory=lambda: ["any"])
    
    # Entry Points
    main_module: str = ""
    entry_point: str = "main"
    init_function: str = "initialize"
    cleanup_function: str = "cleanup"
    
    # Dependencies
    dependencies: List[PluginDependency] = field(default_factory=list)
    system_dependencies: List[str] = field(default_factory=list)
    
    # Configuration
    config_options: List[PluginConfigOption] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    
    # Security
    permissions: List[PluginPermission] = field(default_factory=list)
    security_level: str = "LOW"
    sandbox_required: bool = True
    network_access: bool = False
    file_access: List[str] = field(default_factory=list)
    
    # API
    provides_api: bool = False
    api_endpoints: List[PluginEndpoint] = field(default_factory=list)
    
    # Resources
    max_memory: int = 52428800  # 50MB default
    max_cpu: float = 10.0  # 10% default
    max_execution_time: int = 30  # 30 seconds default
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    category: str = "utility"
    keywords: List[str] = field(default_factory=list)
    
    # Lifecycle
    auto_start: bool = False
    restart_policy: str = "never"  # never, on-failure, always
    health_check: Dict[str, Any] = field(default_factory=dict)
    
    # Documentation
    readme: str = ""
    changelog: str = ""
    documentation_url: str = ""
    examples: List[str] = field(default_factory=list)
    
    # Validation
    manifest_version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert enums to strings
        data['license'] = self.license.value
        data['api_version'] = self.api_version.value
        # Convert datetime objects to ISO strings
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginManifest':
        """Create from dictionary"""
        # Convert string enums back to enum objects
        if 'license' in data:
            data['license'] = PluginLicenseType(data['license'])
        if 'api_version' in data:
            data['api_version'] = PluginAPIVersion(data['api_version'])
        
        # Convert ISO strings back to datetime objects
        for date_field in ['created_at', 'updated_at']:
            if date_field in data and isinstance(data[date_field], str):
                data[date_field] = datetime.fromisoformat(data[date_field])
        
        # Convert nested objects
        if 'dependencies' in data:
            data['dependencies'] = [
                PluginDependency.from_dict(dep) if isinstance(dep, dict) else dep
                for dep in data['dependencies']
            ]
        
        if 'permissions' in data:
            data['permissions'] = [
                PluginPermission.from_dict(perm) if isinstance(perm, dict) else perm
                for perm in data['permissions']
            ]
        
        if 'config_options' in data:
            data['config_options'] = [
                PluginConfigOption.from_dict(opt) if isinstance(opt, dict) else opt
                for opt in data['config_options']
            ]
        
        if 'api_endpoints' in data:
            data['api_endpoints'] = [
                PluginEndpoint.from_dict(ep) if isinstance(ep, dict) else ep
                for ep in data['api_endpoints']
            ]
        
        return cls(**data)

class PluginManifestValidator:
    """
    Plugin manifest validation system
    """
    
    # JSON Schema for plugin manifest validation
    MANIFEST_SCHEMA = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["name", "version", "description", "author", "main_module"],
        "properties": {
            "name": {
                "type": "string",
                "pattern": "^[a-zA-Z0-9_-]+$",
                "minLength": 1,
                "maxLength": 100
            },
            "version": {
                "type": "string",
                "pattern": "^\\d+\\.\\d+\\.\\d+(-[a-zA-Z0-9.-]+)?$"
            },
            "description": {
                "type": "string",
                "minLength": 10,
                "maxLength": 500
            },
            "author": {
                "type": "string",
                "minLength": 1,
                "maxLength": 100
            },
            "email": {
                "type": "string",
                "format": "email"
            },
            "website": {
                "type": "string",
                "format": "uri"
            },
            "repository": {
                "type": "string",
                "format": "uri"
            },
            "license": {
                "type": "string",
                "enum": ["MIT", "Apache-2.0", "GPL-3.0", "BSD-3-Clause", "Proprietary", "Custom"]
            },
            "api_version": {
                "type": "string",
                "enum": ["1.0", "1.1", "2.0"]
            },
            "python_version": {
                "type": "string",
                "pattern": "^>=\\d+\\.\\d+$"
            },
            "platform": {
                "type": "array",
                "items": {"type": "string"}
            },
            "main_module": {
                "type": "string",
                "pattern": "^[a-zA-Z0-9_./]+\\.py$"
            },
            "entry_point": {
                "type": "string",
                "pattern": "^[a-zA-Z_][a-zA-Z0-9_]*$"
            },
            "dependencies": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {"type": "string"},
                        "version": {"type": "string"},
                        "optional": {"type": "boolean"},
                        "reason": {"type": "string"}
                    }
                }
            },
            "permissions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "description"],
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "required": {"type": "boolean"},
                        "risk_level": {
                            "type": "string",
                            "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                        }
                    }
                }
            },
            "config_options": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "type"],
                    "properties": {
                        "name": {"type": "string"},
                        "type": {
                            "type": "string",
                            "enum": ["string", "integer", "boolean", "float", "array", "object"]
                        },
                        "description": {"type": "string"},
                        "required": {"type": "boolean"},
                        "validation": {"type": "object"}
                    }
                }
            },
            "max_memory": {
                "type": "integer",
                "minimum": 1048576,  # 1MB minimum
                "maximum": 1073741824  # 1GB maximum
            },
            "max_cpu": {
                "type": "number",
                "minimum": 0.1,
                "maximum": 100.0
            },
            "max_execution_time": {
                "type": "integer",
                "minimum": 1,
                "maximum": 300  # 5 minutes maximum
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 10
            },
            "category": {
                "type": "string",
                "enum": ["service", "middleware", "security", "feature", "utility", "monitoring", "analytics"]
            },
            "manifest_version": {
                "type": "string",
                "pattern": "^\\d+\\.\\d+$"
            }
        }
    }
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def validate_manifest(self, manifest_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate plugin manifest against schema
        
        Args:
            manifest_data: Manifest data dictionary
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []
        
        try:
            # Validate against JSON schema
            jsonschema.validate(manifest_data, self.MANIFEST_SCHEMA)
            
            # Additional custom validations
            errors.extend(self._validate_dependencies(manifest_data))
            errors.extend(self._validate_permissions(manifest_data))
            errors.extend(self._validate_config_options(manifest_data))
            errors.extend(self._validate_file_paths(manifest_data))
            errors.extend(self._validate_resource_limits(manifest_data))
            
        except jsonschema.ValidationError as e:
            errors.append(f"Schema validation error: {e.message}")
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return len(errors) == 0, errors
    
    def _validate_dependencies(self, manifest_data: Dict[str, Any]) -> List[str]:
        """Validate plugin dependencies"""
        errors = []
        
        dependencies = manifest_data.get('dependencies', [])
        dep_names = set()
        
        for dep in dependencies:
            dep_name = dep.get('name', '')
            
            # Check for duplicate dependencies
            if dep_name in dep_names:
                errors.append(f"Duplicate dependency: {dep_name}")
            dep_names.add(dep_name)
            
            # Validate version constraints
            version = dep.get('version', '*')
            if version != '*' and not self._is_valid_version_constraint(version):
                errors.append(f"Invalid version constraint for {dep_name}: {version}")
        
        return errors
    
    def _validate_permissions(self, manifest_data: Dict[str, Any]) -> List[str]:
        """Validate plugin permissions"""
        errors = []
        
        permissions = manifest_data.get('permissions', [])
        perm_names = set()
        
        for perm in permissions:
            perm_name = perm.get('name', '')
            
            # Check for duplicate permissions
            if perm_name in perm_names:
                errors.append(f"Duplicate permission: {perm_name}")
            perm_names.add(perm_name)
            
            # Validate risk level combinations
            risk_level = perm.get('risk_level', 'LOW')
            required = perm.get('required', True)
            
            if risk_level in ['HIGH', 'CRITICAL'] and not required:
                errors.append(f"High-risk permission {perm_name} cannot be optional")
        
        return errors
    
    def _validate_config_options(self, manifest_data: Dict[str, Any]) -> List[str]:
        """Validate configuration options"""
        errors = []
        
        config_options = manifest_data.get('config_options', [])
        option_names = set()
        
        for option in config_options:
            option_name = option.get('name', '')
            
            # Check for duplicate options
            if option_name in option_names:
                errors.append(f"Duplicate config option: {option_name}")
            option_names.add(option_name)
            
            # Validate default values against type
            option_type = option.get('type', 'string')
            default_value = option.get('default')
            
            if default_value is not None:
                if not self._is_valid_type_value(option_type, default_value):
                    errors.append(f"Invalid default value for {option_name}: {default_value}")
        
        return errors
    
    def _validate_file_paths(self, manifest_data: Dict[str, Any]) -> List[str]:
        """Validate file paths"""
        errors = []
        
        # Check main module path
        main_module = manifest_data.get('main_module', '')
        if main_module and not main_module.endswith('.py'):
            errors.append(f"Main module must be a Python file: {main_module}")
        
        # Check file access paths
        file_access = manifest_data.get('file_access', [])
        for path in file_access:
            if os.path.isabs(path):
                errors.append(f"Absolute file paths not allowed: {path}")
            if '..' in path:
                errors.append(f"Parent directory access not allowed: {path}")
        
        return errors
    
    def _validate_resource_limits(self, manifest_data: Dict[str, Any]) -> List[str]:
        """Validate resource limits"""
        errors = []
        
        # Check memory limits
        max_memory = manifest_data.get('max_memory', 52428800)
        if max_memory > 1073741824:  # 1GB
            errors.append(f"Memory limit too high: {max_memory} bytes")
        
        # Check CPU limits
        max_cpu = manifest_data.get('max_cpu', 10.0)
        if max_cpu > 50.0:  # 50% maximum
            errors.append(f"CPU limit too high: {max_cpu}%")
        
        # Check execution time limits
        max_execution_time = manifest_data.get('max_execution_time', 30)
        if max_execution_time > 300:  # 5 minutes maximum
            errors.append(f"Execution time limit too high: {max_execution_time}s")
        
        return errors
    
    def _is_valid_version_constraint(self, version: str) -> bool:
        """Check if version constraint is valid"""
        # Simple version constraint validation
        patterns = [
            r'^\d+\.\d+\.\d+$',  # Exact version
            r'^>=\d+\.\d+\.\d+$',  # Greater than or equal
            r'^>\d+\.\d+\.\d+$',  # Greater than
            r'^<=\d+\.\d+\.\d+$',  # Less than or equal
            r'^<\d+\.\d+\.\d+$',  # Less than
            r'^~\d+\.\d+\.\d+$',  # Compatible version
            r'^\^\d+\.\d+\.\d+$',  # Caret version
        ]
        
        return any(re.match(pattern, version) for pattern in patterns)
    
    def _is_valid_type_value(self, type_name: str, value: Any) -> bool:
        """Check if value matches expected type"""
        type_map = {
            'string': str,
            'integer': int,
            'boolean': bool,
            'float': (int, float),
            'array': list,
            'object': dict
        }
        
        expected_type = type_map.get(type_name)
        if expected_type is None:
            return False
        
        return isinstance(value, expected_type)

class PluginManifestManager:
    """
    Plugin manifest management system
    """
    
    def __init__(self):
        self.validator = PluginManifestValidator()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def create_manifest(self, plugin_dir: str, manifest_data: Dict[str, Any]) -> bool:
        """
        Create plugin manifest file
        
        Args:
            plugin_dir: Plugin directory path
            manifest_data: Manifest data
            
        Returns:
            bool: True if creation successful
        """
        try:
            # Validate manifest data
            is_valid, errors = self.validator.validate_manifest(manifest_data)
            if not is_valid:
                self.logger.error(f"Invalid manifest data: {errors}")
                return False
            
            # Create manifest file
            manifest_path = os.path.join(plugin_dir, 'plugin.json')
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Created plugin manifest: {manifest_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create manifest: {e}")
            return False
    
    def load_manifest(self, plugin_dir: str) -> Optional[PluginManifest]:
        """
        Load plugin manifest from directory
        
        Args:
            plugin_dir: Plugin directory path
            
        Returns:
            Optional[PluginManifest]: Loaded manifest or None
        """
        try:
            manifest_path = os.path.join(plugin_dir, 'plugin.json')
            if not os.path.exists(manifest_path):
                self.logger.warning(f"No manifest file found: {manifest_path}")
                return None
            
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
            
            # Validate manifest
            is_valid, errors = self.validator.validate_manifest(manifest_data)
            if not is_valid:
                self.logger.error(f"Invalid manifest: {errors}")
                return None
            
            return PluginManifest.from_dict(manifest_data)
            
        except Exception as e:
            self.logger.error(f"Failed to load manifest from {plugin_dir}: {e}")
            return None
    
    def update_manifest(self, plugin_dir: str, updates: Dict[str, Any]) -> bool:
        """
        Update plugin manifest
        
        Args:
            plugin_dir: Plugin directory path
            updates: Updates to apply
            
        Returns:
            bool: True if update successful
        """
        try:
            manifest = self.load_manifest(plugin_dir)
            if not manifest:
                return False
            
            # Apply updates
            manifest_data = manifest.to_dict()
            manifest_data.update(updates)
            manifest_data['updated_at'] = datetime.now().isoformat()
            
            # Validate updated manifest
            is_valid, errors = self.validator.validate_manifest(manifest_data)
            if not is_valid:
                self.logger.error(f"Invalid updated manifest: {errors}")
                return False
            
            # Save updated manifest
            manifest_path = os.path.join(plugin_dir, 'plugin.json')
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Updated plugin manifest: {manifest_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update manifest: {e}")
            return False
    
    def generate_manifest_template(self, plugin_name: str) -> Dict[str, Any]:
        """
        Generate a manifest template
        
        Args:
            plugin_name: Plugin name
            
        Returns:
            Dict[str, Any]: Manifest template
        """
        return {
            "name": plugin_name,
            "version": "1.0.0",
            "description": f"Description for {plugin_name}",
            "author": "Your Name",
            "email": "your.email@example.com",
            "website": "https://your-website.com",
            "repository": "https://github.com/your-username/your-plugin",
            "license": "MIT",
            "api_version": "1.0",
            "python_version": ">=3.8",
            "platform": ["any"],
            "main_module": f"{plugin_name}.py",
            "entry_point": "main",
            "init_function": "initialize",
            "cleanup_function": "cleanup",
            "dependencies": [],
            "system_dependencies": [],
            "config_options": [
                {
                    "name": "enabled",
                    "type": "boolean",
                    "default": True,
                    "description": "Enable/disable the plugin",
                    "required": False
                }
            ],
            "permissions": [
                {
                    "name": "read_config",
                    "description": "Read plugin configuration",
                    "required": True,
                    "risk_level": "LOW"
                }
            ],
            "security_level": "LOW",
            "sandbox_required": True,
            "network_access": False,
            "file_access": [],
            "max_memory": 52428800,
            "max_cpu": 10.0,
            "max_execution_time": 30,
            "tags": [],
            "category": "utility",
            "keywords": [],
            "auto_start": False,
            "restart_policy": "never",
            "manifest_version": "1.0"
        }
    
    def validate_plugin_directory(self, plugin_dir: str) -> Tuple[bool, List[str]]:
        """
        Validate complete plugin directory structure
        
        Args:
            plugin_dir: Plugin directory path
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []
        
        try:
            # Check if directory exists
            if not os.path.exists(plugin_dir):
                errors.append(f"Plugin directory does not exist: {plugin_dir}")
                return False, errors
            
            # Check for manifest file
            manifest_path = os.path.join(plugin_dir, 'plugin.json')
            if not os.path.exists(manifest_path):
                errors.append("Missing plugin.json manifest file")
                return False, errors
            
            # Load and validate manifest
            manifest = self.load_manifest(plugin_dir)
            if not manifest:
                errors.append("Invalid or corrupted manifest file")
                return False, errors
            
            # Check for main module
            main_module_path = os.path.join(plugin_dir, manifest.main_module)
            if not os.path.exists(main_module_path):
                errors.append(f"Missing main module: {manifest.main_module}")
            
            # Check for README if specified
            if manifest.readme:
                readme_path = os.path.join(plugin_dir, manifest.readme)
                if not os.path.exists(readme_path):
                    errors.append(f"Missing README file: {manifest.readme}")
            
            # Check file access permissions
            for file_path in manifest.file_access:
                full_path = os.path.join(plugin_dir, file_path)
                if not os.path.exists(full_path):
                    errors.append(f"Missing file access path: {file_path}")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return False, errors

def main():
    """Main function for testing the manifest system"""
    manager = PluginManifestManager()
    
    # Generate template
    template = manager.generate_manifest_template("test_plugin")
    print("Generated manifest template:")
    print(json.dumps(template, indent=2))
    
    # Validate template
    validator = PluginManifestValidator()
    is_valid, errors = validator.validate_manifest(template)
    print(f"\nTemplate validation: {'VALID' if is_valid else 'INVALID'}")
    if errors:
        print("Errors:", errors)

if __name__ == "__main__":
    main()
