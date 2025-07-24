#!/usr/bin/env python3
"""
Plugin Framework SDK - Development Tools and Utilities

This module provides development tools, utilities, and helper functions
for creating, testing, and debugging plugins in the Plugin Framework Foundation.

Key Features:
- Plugin development scaffolding
- Testing utilities and mock objects
- Debugging and profiling tools
- Plugin validation and linting
- Code generation helpers
- Integration testing framework
"""

import asyncio
import json
import logging
import inspect
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable, Type
from dataclasses import asdict

# Import core framework components
from plugin_framework_core import (
    BasePlugin, PluginManager, PluginFramework, PluginMetadata, 
    PluginType, PluginState, PluginDependency, DependencyType,
    PluginExecutionContext, PluginInstallResult
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ============================================================================
# Plugin Development SDK
# ============================================================================

class PluginSDK:
    """
    Plugin Development SDK providing tools and utilities for plugin creation.
    """
    
    def __init__(self, workspace_directory: Path = None):
        self.workspace_directory = workspace_directory or Path("./plugin_workspace")
        self.workspace_directory.mkdir(parents=True, exist_ok=True)
        
        self.templates_directory = self.workspace_directory / "templates"
        self.templates_directory.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger("PluginSDK")
        self.logger.info("Plugin SDK initialized")
    
    # ========================================================================
    # Plugin Scaffolding and Generation
    # ========================================================================
    
    def create_plugin_project(self, plugin_id: str, plugin_type: PluginType,
                             plugin_name: str = None, author: str = "Plugin Developer") -> Path:
        """
        Create a complete plugin project with scaffolding.
        
        Args:
            plugin_id: Unique plugin identifier
            plugin_type: Type of plugin to create
            plugin_name: Human-readable plugin name
            author: Plugin author name
            
        Returns:
            Path to created plugin project
        """
        
        try:
            plugin_name = plugin_name or plugin_id.replace("_", " ").title()
            
            # Create plugin directory
            plugin_dir = self.workspace_directory / plugin_id
            plugin_dir.mkdir(exist_ok=True)
            
            # Create directory structure
            (plugin_dir / "src").mkdir(exist_ok=True)
            (plugin_dir / "tests").mkdir(exist_ok=True)
            (plugin_dir / "docs").mkdir(exist_ok=True)
            (plugin_dir / "config").mkdir(exist_ok=True)
            
            # Generate plugin metadata
            metadata = self._generate_plugin_metadata(plugin_id, plugin_name, plugin_type, author)
            self._write_plugin_metadata(plugin_dir, metadata)
            
            # Generate main plugin file
            self._generate_main_plugin_file(plugin_dir, metadata)
            
            # Generate configuration files
            self._generate_plugin_config_files(plugin_dir, metadata)
            
            # Generate test files
            self._generate_plugin_test_files(plugin_dir, metadata)
            
            # Generate documentation
            self._generate_plugin_documentation(plugin_dir, metadata)
            
            # Generate setup and build files
            self._generate_plugin_build_files(plugin_dir, metadata)
            
            self.logger.info(f"Created plugin project: {plugin_dir}")
            return plugin_dir
            
        except Exception as e:
            self.logger.error(f"Error creating plugin project: {e}")
            raise
    
    def _generate_plugin_metadata(self, plugin_id: str, plugin_name: str, 
                                plugin_type: PluginType, author: str) -> PluginMetadata:
        """Generate plugin metadata"""
        
        return PluginMetadata(
            id=plugin_id,
            name=plugin_name,
            version="1.0.0",
            description=f"A {plugin_type.value} plugin for the Heimnetz system",
            author=author,
            plugin_type=plugin_type,
            framework_version="1.0.0",
            python_requires=">=3.8",
            sandbox_required=True,
            estimated_memory_mb=128,
            estimated_cpu_percent=10.0,
            requires_network=plugin_type in [PluginType.NETWORK, PluginType.INTEGRATION],
            requires_filesystem=plugin_type in [PluginType.SYSTEM, PluginType.UTILITY]
        )
    
    def _write_plugin_metadata(self, plugin_dir: Path, metadata: PluginMetadata):
        """Write plugin metadata to plugin.json"""
        
        metadata_file = plugin_dir / "plugin.json"
        
        # Convert metadata to dictionary
        metadata_dict = asdict(metadata)
        
        # Handle enum serialization
        metadata_dict["plugin_type"] = metadata.plugin_type.value
        metadata_dict["created_at"] = metadata.created_at.isoformat()
        metadata_dict["updated_at"] = metadata.updated_at.isoformat()
        
        # Handle dependencies
        metadata_dict["dependencies"] = [
            {
                "name": dep.name,
                "type": dep.type.value,
                "version_requirement": dep.version_requirement,
                "optional": dep.optional,
                "description": dep.description
            }
            for dep in metadata.dependencies
        ]
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata_dict, f, indent=2)
    
    def _generate_main_plugin_file(self, plugin_dir: Path, metadata: PluginMetadata):
        """Generate main plugin implementation file"""
        
        main_file = plugin_dir / "src" / "__init__.py"
        
        plugin_code = f'''#!/usr/bin/env python3
"""
{metadata.name} Plugin

{metadata.description}

Author: {metadata.author}
Version: {metadata.version}
Type: {metadata.plugin_type.value}
"""

import asyncio
import logging
from typing import Dict, List, Any
from pathlib import Path

# Import framework components
from plugin_framework_core import (
    BasePlugin, PluginMetadata, PluginType, PluginExecutionContext
)


class {metadata.id.replace("_", "").title()}Plugin(BasePlugin):
    """
    {metadata.name} - {metadata.description}
    """
    
    def __init__(self):
        # Plugin metadata is loaded from plugin.json
        metadata = PluginMetadata(
            id="{metadata.id}",
            name="{metadata.name}",
            version="{metadata.version}",
            description="{metadata.description}",
            author="{metadata.author}",
            plugin_type=PluginType.{metadata.plugin_type.name},
            sandbox_required={metadata.sandbox_required}
        )
        
        super().__init__(metadata)
        
        # Plugin-specific initialization
        self.config_data = {{}}
        self.initialized = False
    
    async def initialize(self, context: PluginExecutionContext) -> bool:
        """
        Initialize the {metadata.name} plugin.
        
        Args:
            context: Plugin execution context
            
        Returns:
            True if initialization successful, False otherwise
        """
        
        try:
            self.logger.info(f"Initializing {{self.metadata.name}} plugin")
            
            # Load plugin configuration
            self.config_data = context.configuration
            
            # Validate configuration
            config_errors = await self.validate_configuration(self.config_data)
            if config_errors:
                self.logger.error(f"Configuration validation failed: {{config_errors}}")
                return False
            
            # Plugin-specific initialization logic
            await self._initialize_plugin_resources()
            
            self.initialized = True
            self.logger.info(f"{{self.metadata.name}} plugin initialized successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing plugin: {{e}}")
            return False
    
    async def execute(self, operation: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a plugin operation.
        
        Args:
            operation: Name of the operation to perform
            parameters: Operation parameters
            
        Returns:
            Operation results dictionary
        """
        
        try:
            self.logger.info(f"Executing operation: {{operation}}")
            
            if not self.initialized:
                return {{
                    "success": False,
                    "error": "Plugin not initialized"
                }}
            
            # Route operation to appropriate handler
            if operation == "get_status":
                return await self._get_plugin_status()
            elif operation == "get_info":
                return await self._get_plugin_info()
            elif operation == "configure":
                return await self._configure_plugin(parameters)
            elif operation == "run_diagnostic":
                return await self._run_diagnostic()
            elif operation == "example_operation":
                return await self._example_operation(parameters)
            else:
                return {{
                    "success": False,
                    "error": f"Unknown operation: {{operation}}"
                }}
                
        except Exception as e:
            return await self.handle_error(e, operation)
    
    async def cleanup(self) -> bool:
        """
        Cleanup plugin resources.
        
        Returns:
            True if cleanup successful, False otherwise
        """
        
        try:
            self.logger.info(f"Cleaning up {{self.metadata.name}} plugin")
            
            # Plugin-specific cleanup logic
            await self._cleanup_plugin_resources()
            
            self.initialized = False
            self.logger.info("Plugin cleanup completed successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error during plugin cleanup: {{e}}")
            return False
    
    async def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate plugin configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        
        errors = []
        
        # Example configuration validation
        # Add your specific validation logic here
        
        return errors
    
    async def get_supported_operations(self) -> List[str]:
        """
        Get list of supported operations.
        
        Returns:
            List of operation names
        """
        
        return [
            "get_status",
            "get_info", 
            "configure",
            "run_diagnostic",
            "example_operation"
        ]
    
    # ========================================================================
    # Plugin-Specific Implementation Methods
    # ========================================================================
    
    async def _initialize_plugin_resources(self):
        """Initialize plugin-specific resources"""
        
        # Add your plugin initialization logic here
        pass
    
    async def _cleanup_plugin_resources(self):
        """Cleanup plugin-specific resources"""
        
        # Add your plugin cleanup logic here
        pass
    
    async def _get_plugin_status(self) -> Dict[str, Any]:
        """Get current plugin status"""
        
        base_status = await self.get_status()
        
        # Add plugin-specific status information
        base_status.update({{
            "initialized": self.initialized,
            "config_loaded": bool(self.config_data)
        }})
        
        return {{
            "success": True,
            "status": base_status
        }}
    
    async def _get_plugin_info(self) -> Dict[str, Any]:
        """Get plugin information"""
        
        return {{
            "success": True,
            "info": {{
                "plugin_id": self.metadata.id,
                "name": self.metadata.name,
                "version": self.metadata.version,
                "description": self.metadata.description,
                "author": self.metadata.author,
                "type": self.metadata.plugin_type.value,
                "supported_operations": await self.get_supported_operations()
            }}
        }}
    
    async def _configure_plugin(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Configure plugin with new parameters"""
        
        try:
            # Validate new configuration
            errors = await self.validate_configuration(parameters)
            if errors:
                return {{
                    "success": False,
                    "error": "Configuration validation failed",
                    "errors": errors
                }}
            
            # Apply configuration
            self.config_data.update(parameters)
            
            return {{
                "success": True,
                "message": "Plugin configured successfully"
            }}
            
        except Exception as e:
            return {{
                "success": False,
                "error": f"Configuration failed: {{e}}"
            }}
    
    async def _run_diagnostic(self) -> Dict[str, Any]:
        """Run plugin diagnostic checks"""
        
        diagnostics = {{
            "plugin_health": "healthy",
            "initialization_status": "initialized" if self.initialized else "not_initialized",
            "configuration_status": "loaded" if self.config_data else "not_loaded",
            "error_count": self._error_count,
            "execution_count": self._execution_count
        }}
        
        return {{
            "success": True,
            "diagnostics": diagnostics
        }}
    
    async def _example_operation(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Example operation implementation"""
        
        # This is a template operation - replace with your actual logic
        
        return {{
            "success": True,
            "message": "Example operation completed successfully",
            "parameters_received": parameters,
            "timestamp": datetime.now().isoformat()
        }}


# ============================================================================
# Plugin Entry Point
# ============================================================================

def create_plugin() -> BasePlugin:
    """
    Create and return plugin instance.
    
    This function is called by the Plugin Framework to instantiate the plugin.
    
    Returns:
        Plugin instance
    """
    
    return {metadata.id.replace("_", "").title()}Plugin()


# ============================================================================
# Plugin Testing Support
# ============================================================================

async def test_plugin():
    """Test the plugin functionality"""
    
    print(f"Testing {{metadata.name}} Plugin")
    print("=" * 40)
    
    # Create plugin instance
    plugin = create_plugin()
    
    # Create test context
    context = PluginExecutionContext(
        plugin_id=plugin.metadata.id,
        environment={{"framework_version": "1.0.0"}},
        configuration={{
            "debug_mode": True,
            "log_level": "INFO"
        }}
    )
    
    try:
        # Test initialization
        print("\\n🔄 Testing plugin initialization...")
        init_result = await plugin.initialize(context)
        print(f"Initialization result: {{init_result}}")
        
        # Test operations
        print("\\n🔄 Testing plugin operations...")
        
        operations = await plugin.get_supported_operations()
        print(f"Supported operations: {{operations}}")
        
        for operation in operations[:3]:  # Test first few operations
            print(f"\\n  Testing operation: {{operation}}")
            result = await plugin.execute(operation, {{}})
            print(f"  Result: {{result.get('success', False)}}")
        
        # Test cleanup
        print("\\n🔄 Testing plugin cleanup...")
        cleanup_result = await plugin.cleanup()
        print(f"Cleanup result: {{cleanup_result}}")
        
        print("\\n✅ Plugin testing completed successfully!")
        
    except Exception as e:
        print(f"\\n❌ Plugin testing failed: {{e}}")


if __name__ == "__main__":
    # Run plugin tests when executed directly
    asyncio.run(test_plugin())
'''
        
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(plugin_code)
    
    def _generate_plugin_config_files(self, plugin_dir: Path, metadata: PluginMetadata):
        """Generate plugin configuration files"""
        
        # Default configuration
        default_config = plugin_dir / "config" / "default.json"
        config_data = {
            "plugin_id": metadata.id,
            "debug_mode": False,
            "log_level": "INFO",
            "max_memory_mb": metadata.estimated_memory_mb,
            "timeout_seconds": 30,
            "retry_attempts": 3
        }
        
        with open(default_config, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
        
        # Configuration schema
        schema_file = plugin_dir / "config" / "schema.json"
        schema_data = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": f"{metadata.name} Configuration",
            "type": "object",
            "properties": {
                "plugin_id": {"type": "string"},
                "debug_mode": {"type": "boolean"},
                "log_level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]},
                "max_memory_mb": {"type": "integer", "minimum": 64},
                "timeout_seconds": {"type": "integer", "minimum": 1},
                "retry_attempts": {"type": "integer", "minimum": 0}
            },
            "required": ["plugin_id"]
        }
        
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f, indent=2)
    
    def _generate_plugin_test_files(self, plugin_dir: Path, metadata: PluginMetadata):
        """Generate plugin test files"""
        
        test_file = plugin_dir / "tests" / "test_plugin.py"
        
        test_code = f'''#!/usr/bin/env python3
"""
Unit tests for {metadata.name} Plugin

This file contains comprehensive tests for the plugin functionality.
"""

import asyncio
import pytest
import sys
from pathlib import Path

# Add plugin source to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from plugin_framework_core import PluginExecutionContext
from __init__ import create_plugin, {metadata.id.replace("_", "").title()}Plugin


class TestPlugin:
    """Test cases for {metadata.name} plugin"""
    
    @pytest.fixture
    async def plugin(self):
        """Create plugin instance for testing"""
        return create_plugin()
    
    @pytest.fixture
    def context(self):
        """Create test execution context"""
        return PluginExecutionContext(
            plugin_id="{metadata.id}",
            environment={{"framework_version": "1.0.0"}},
            configuration={{
                "debug_mode": True,
                "log_level": "DEBUG"
            }}
        )
    
    async def test_plugin_creation(self, plugin):
        """Test plugin instance creation"""
        assert plugin is not None
        assert isinstance(plugin, {metadata.id.replace("_", "").title()}Plugin)
        assert plugin.metadata.id == "{metadata.id}"
        assert plugin.metadata.name == "{metadata.name}"
        assert plugin.metadata.version == "{metadata.version}"
    
    async def test_plugin_initialization(self, plugin, context):
        """Test plugin initialization"""
        result = await plugin.initialize(context)
        assert result is True
        assert plugin.initialized is True
        assert plugin.context is not None
    
    async def test_plugin_operations(self, plugin, context):
        """Test plugin operations"""
        # Initialize plugin
        await plugin.initialize(context)
        
        # Test supported operations
        operations = await plugin.get_supported_operations()
        assert isinstance(operations, list)
        assert len(operations) > 0
        
        # Test get_status operation
        result = await plugin.execute("get_status", {{}})
        assert result["success"] is True
        assert "status" in result
        
        # Test get_info operation
        result = await plugin.execute("get_info", {{}})
        assert result["success"] is True
        assert "info" in result
        assert result["info"]["plugin_id"] == "{metadata.id}"
    
    async def test_plugin_configuration(self, plugin, context):
        """Test plugin configuration"""
        # Initialize plugin
        await plugin.initialize(context)
        
        # Test configuration validation
        valid_config = {{"debug_mode": False, "log_level": "INFO"}}
        errors = await plugin.validate_configuration(valid_config)
        assert len(errors) == 0
        
        # Test configuration update
        result = await plugin.execute("configure", valid_config)
        assert result["success"] is True
    
    async def test_plugin_cleanup(self, plugin, context):
        """Test plugin cleanup"""
        # Initialize plugin
        await plugin.initialize(context)
        assert plugin.initialized is True
        
        # Test cleanup
        result = await plugin.cleanup()
        assert result is True
        assert plugin.initialized is False
    
    async def test_plugin_error_handling(self, plugin, context):
        """Test plugin error handling"""
        # Initialize plugin
        await plugin.initialize(context)
        
        # Test unknown operation
        result = await plugin.execute("unknown_operation", {{}})
        assert result["success"] is False
        assert "error" in result
    
    async def test_plugin_diagnostics(self, plugin, context):
        """Test plugin diagnostic functionality"""
        # Initialize plugin
        await plugin.initialize(context)
        
        # Run diagnostics
        result = await plugin.execute("run_diagnostic", {{}})
        assert result["success"] is True
        assert "diagnostics" in result
        assert result["diagnostics"]["plugin_health"] == "healthy"


# ============================================================================
# Integration Tests
# ============================================================================

class TestPluginIntegration:
    """Integration tests for plugin with framework"""
    
    async def test_plugin_with_framework(self):
        """Test plugin integration with framework"""
        from plugin_framework_core import PluginFramework
        
        # This would test the plugin within the actual framework
        # Implementation depends on framework testing utilities
        pass


# ============================================================================
# Performance Tests
# ============================================================================

class TestPluginPerformance:
    """Performance tests for plugin"""
    
    async def test_initialization_time(self, plugin, context):
        """Test plugin initialization performance"""
        import time
        
        start_time = time.time()
        result = await plugin.initialize(context)
        end_time = time.time()
        
        initialization_time = end_time - start_time
        
        assert result is True
        assert initialization_time < 5.0  # Should initialize within 5 seconds
    
    async def test_operation_execution_time(self, plugin, context):
        """Test operation execution performance"""
        import time
        
        # Initialize plugin
        await plugin.initialize(context)
        
        # Test operation performance
        start_time = time.time()
        result = await plugin.execute("get_status", {{}})
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        assert result["success"] is True
        assert execution_time < 1.0  # Should execute within 1 second


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
'''
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_code)
        
        # Generate pytest configuration
        pytest_config = plugin_dir / "tests" / "pytest.ini"
        with open(pytest_config, 'w', encoding='utf-8') as f:
            f.write(f"""[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
""")
    
    def _generate_plugin_documentation(self, plugin_dir: Path, metadata: PluginMetadata):
        """Generate plugin documentation"""
        
        readme_file = plugin_dir / "README.md"
        
        readme_content = f'''# {metadata.name} Plugin

{metadata.description}

## Overview

- **Plugin ID**: {metadata.id}
- **Version**: {metadata.version}
- **Type**: {metadata.plugin_type.value}
- **Author**: {metadata.author}
- **Framework Version**: {metadata.framework_version}

## Features

- Feature 1: Description of feature 1
- Feature 2: Description of feature 2
- Feature 3: Description of feature 3

## Installation

1. Copy the plugin directory to your plugins folder
2. Configure the plugin using the configuration files in `config/`
3. Load the plugin using the Plugin Framework

## Configuration

The plugin can be configured using the following parameters:

```json
{{
  "plugin_id": "{metadata.id}",
  "debug_mode": false,
  "log_level": "INFO",
  "max_memory_mb": {metadata.estimated_memory_mb},
  "timeout_seconds": 30
}}
```

See `config/schema.json` for the complete configuration schema.

## Usage

### Supported Operations

- `get_status`: Get current plugin status
- `get_info`: Get plugin information
- `configure`: Update plugin configuration
- `run_diagnostic`: Run diagnostic checks
- `example_operation`: Example operation implementation

### Example Usage

```python
import asyncio
from plugin_framework_core import PluginFramework

async def main():
    framework = PluginFramework()
    
    # Load the plugin
    await framework.load_plugin("{metadata.id}")
    
    # Execute operations
    result = await framework.execute_operation("{metadata.id}", "get_status")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

## Development

### Running Tests

```bash
cd tests/
python -m pytest -v
```

### Code Structure

```
{metadata.id}/
├── src/                    # Plugin source code
│   └── __init__.py        # Main plugin implementation
├── tests/                  # Test files
│   ├── test_plugin.py     # Unit tests
│   └── pytest.ini        # Pytest configuration
├── config/                 # Configuration files
│   ├── default.json       # Default configuration
│   └── schema.json        # Configuration schema
├── docs/                   # Documentation
│   └── README.md          # This file
├── plugin.json            # Plugin metadata
├── requirements.txt       # Python dependencies
└── setup.py              # Plugin setup script
```

## API Reference

### Plugin Class: `{metadata.id.replace("_", "").title()}Plugin`

The main plugin class implementing the BasePlugin interface.

#### Methods

- `initialize(context)`: Initialize the plugin
- `execute(operation, parameters)`: Execute plugin operations
- `cleanup()`: Cleanup plugin resources
- `validate_configuration(config)`: Validate configuration
- `get_supported_operations()`: Get supported operations list

## License

This plugin is licensed under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for your changes
5. Run the test suite
6. Submit a pull request

## Support

For support and questions, please contact: {metadata.author}
'''
        
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    def _generate_plugin_build_files(self, plugin_dir: Path, metadata: PluginMetadata):
        """Generate plugin build and setup files"""
        
        # Requirements file
        requirements_file = plugin_dir / "requirements.txt"
        with open(requirements_file, 'w', encoding='utf-8') as f:
            f.write(f"""# {metadata.name} Plugin Requirements

# Core framework (ensure compatibility)
# plugin-framework-core>=1.0.0

# Plugin-specific dependencies
# Add your dependencies here

# Development dependencies (optional)
pytest>=6.0.0
pytest-asyncio>=0.18.0
""")
        
        # Setup script
        setup_file = plugin_dir / "setup.py"
        setup_content = f'''#!/usr/bin/env python3
"""
Setup script for {metadata.name} Plugin
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read plugin metadata
import json
with open("plugin.json", "r") as f:
    metadata = json.load(f)

# Read README for long description
readme_file = Path("README.md")
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name=metadata["id"].replace("_", "-"),
    version=metadata["version"],
    description=metadata["description"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=metadata["author"],
    author_email=metadata.get("email", ""),
    url=metadata.get("website", ""),
    packages=find_packages(where="src"),
    package_dir={{"": "src"}},
    python_requires=metadata.get("python_requires", ">=3.8"),
    install_requires=[
        # Add runtime dependencies here
    ],
    extras_require={{
        "dev": [
            "pytest>=6.0.0",
            "pytest-asyncio>=0.18.0",
        ]
    }},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="plugin framework heimnetz",
    include_package_data=True,
    package_data={{
        "": ["*.json", "*.md", "*.txt"]
    }},
)
'''
        
        with open(setup_file, 'w', encoding='utf-8') as f:
            f.write(setup_content)
        
        # Makefile for common operations
        makefile = plugin_dir / "Makefile"
        makefile_content = f'''# {metadata.name} Plugin Makefile

.PHONY: help install test clean build package

help:
\t@echo "Available targets:"
\t@echo "  install    - Install plugin dependencies"
\t@echo "  test       - Run plugin tests"
\t@echo "  clean      - Clean build artifacts"
\t@echo "  build      - Build plugin package"
\t@echo "  package    - Create distribution package"

install:
\tpip install -r requirements.txt
\tpip install -e .[dev]

test:
\tcd tests && python -m pytest -v

clean:
\trm -rf build/ dist/ *.egg-info/
\tfind . -type d -name __pycache__ -delete
\tfind . -type f -name "*.pyc" -delete

build:
\tpython setup.py build

package:
\tpython setup.py sdist bdist_wheel
'''
        
        with open(makefile, 'w', encoding='utf-8') as f:
            f.write(makefile_content)
    
    # ========================================================================
    # Plugin Testing and Validation
    # ========================================================================
    
    async def validate_plugin(self, plugin_path: Path) -> Dict[str, Any]:
        """
        Validate a plugin for framework compliance.
        
        Args:
            plugin_path: Path to plugin directory
            
        Returns:
            Validation results dictionary
        """
        
        try:
            validation_results = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "info": {
                    "plugin_path": str(plugin_path),
                    "validation_time": datetime.now().isoformat()
                }
            }
            
            # Check plugin structure
            structure_results = await self._validate_plugin_structure(plugin_path)
            validation_results["errors"].extend(structure_results["errors"])
            validation_results["warnings"].extend(structure_results["warnings"])
            
            # Check plugin metadata
            metadata_results = await self._validate_plugin_metadata(plugin_path)
            validation_results["errors"].extend(metadata_results["errors"])
            validation_results["warnings"].extend(metadata_results["warnings"])
            
            # Check plugin code
            code_results = await self._validate_plugin_code(plugin_path)
            validation_results["errors"].extend(code_results["errors"])
            validation_results["warnings"].extend(code_results["warnings"])
            
            # Set overall validity
            validation_results["valid"] = len(validation_results["errors"]) == 0
            
            self.logger.info(f"Plugin validation completed for: {plugin_path}")
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error validating plugin: {e}")
            return {
                "valid": False,
                "errors": [f"Validation failed: {e}"],
                "warnings": [],
                "info": {"plugin_path": str(plugin_path)}
            }
    
    async def _validate_plugin_structure(self, plugin_path: Path) -> Dict[str, List[str]]:
        """Validate plugin directory structure"""
        
        errors = []
        warnings = []
        
        # Check required files
        required_files = ["plugin.json"]
        for file_name in required_files:
            if not (plugin_path / file_name).exists():
                errors.append(f"Missing required file: {file_name}")
        
        # Check for plugin implementation
        src_dir = plugin_path / "src"
        if src_dir.exists():
            if not (src_dir / "__init__.py").exists():
                warnings.append("No __init__.py found in src directory")
        else:
            # Look for main plugin file in root
            py_files = list(plugin_path.glob("*.py"))
            if not py_files:
                errors.append("No Python files found in plugin directory")
        
        # Check for documentation
        if not (plugin_path / "README.md").exists():
            warnings.append("No README.md found - consider adding documentation")
        
        return {"errors": errors, "warnings": warnings}
    
    async def _validate_plugin_metadata(self, plugin_path: Path) -> Dict[str, List[str]]:
        """Validate plugin metadata"""
        
        errors = []
        warnings = []
        
        metadata_file = plugin_path / "plugin.json"
        if not metadata_file.exists():
            errors.append("plugin.json not found")
            return {"errors": errors, "warnings": warnings}
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Check required fields
            required_fields = ["id", "name", "version", "description", "author"]
            for field in required_fields:
                if field not in metadata:
                    errors.append(f"Missing required metadata field: {field}")
            
            # Validate version format
            if "version" in metadata:
                version = metadata["version"]
                if not self._is_valid_version(version):
                    warnings.append(f"Version '{version}' may not follow semantic versioning")
            
            # Check plugin type
            if "plugin_type" in metadata:
                valid_types = [t.value for t in PluginType]
                if metadata["plugin_type"] not in valid_types:
                    errors.append(f"Invalid plugin_type: {metadata['plugin_type']}")
            
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in plugin.json: {e}")
        except Exception as e:
            errors.append(f"Error reading plugin.json: {e}")
        
        return {"errors": errors, "warnings": warnings}
    
    async def _validate_plugin_code(self, plugin_path: Path) -> Dict[str, List[str]]:
        """Validate plugin code"""
        
        errors = []
        warnings = []
        
        # Find Python files
        python_files = []
        if (plugin_path / "src").exists():
            python_files.extend((plugin_path / "src").glob("**/*.py"))
        else:
            python_files.extend(plugin_path.glob("*.py"))
        
        if not python_files:
            errors.append("No Python files found")
            return {"errors": errors, "warnings": warnings}
        
        # Basic syntax checking
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                # Try to compile the code
                compile(code, str(py_file), 'exec')
                
            except SyntaxError as e:
                errors.append(f"Syntax error in {py_file.name}: {e}")
            except Exception as e:
                warnings.append(f"Issue reading {py_file.name}: {e}")
        
        return {"errors": errors, "warnings": warnings}
    
    def _is_valid_version(self, version: str) -> bool:
        """Check if version follows semantic versioning"""
        
        import re
        
        # Simple semantic versioning regex
        semver_pattern = r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
        
        return re.match(semver_pattern, version) is not None
    
    # ========================================================================
    # Plugin Packaging and Distribution
    # ========================================================================
    
    def package_plugin(self, plugin_path: Path, output_directory: Path = None) -> Path:
        """
        Package a plugin for distribution.
        
        Args:
            plugin_path: Path to plugin directory
            output_directory: Directory to output package to
            
        Returns:
            Path to created package
        """
        
        try:
            output_directory = output_directory or self.workspace_directory / "packages"
            output_directory.mkdir(parents=True, exist_ok=True)
            
            # Read plugin metadata
            metadata_file = plugin_path / "plugin.json"
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            plugin_id = metadata["id"]
            version = metadata["version"]
            
            # Create package filename
            package_filename = f"{plugin_id}-{version}.zip"
            package_path = output_directory / package_filename
            
            # Create zip package
            with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in plugin_path.rglob("*"):
                    if file_path.is_file():
                        # Skip certain files/directories
                        skip_patterns = [
                            "__pycache__",
                            "*.pyc",
                            ".git",
                            ".pytest_cache",
                            "build",
                            "dist"
                        ]
                        
                        skip = False
                        for pattern in skip_patterns:
                            if pattern in str(file_path):
                                skip = True
                                break
                        
                        if not skip:
                            arc_name = file_path.relative_to(plugin_path)
                            zipf.write(file_path, arc_name)
            
            self.logger.info(f"Created plugin package: {package_path}")
            return package_path
            
        except Exception as e:
            self.logger.error(f"Error packaging plugin: {e}")
            raise
    
    def extract_plugin_package(self, package_path: Path, target_directory: Path = None) -> Path:
        """
        Extract a plugin package.
        
        Args:
            package_path: Path to plugin package zip file
            target_directory: Directory to extract to
            
        Returns:
            Path to extracted plugin directory
        """
        
        try:
            target_directory = target_directory or self.workspace_directory / "extracted"
            target_directory.mkdir(parents=True, exist_ok=True)
            
            # Extract package
            with zipfile.ZipFile(package_path, 'r') as zipf:
                zipf.extractall(target_directory)
            
            # Find plugin directory (should contain plugin.json)
            for item in target_directory.iterdir():
                if item.is_dir() and (item / "plugin.json").exists():
                    self.logger.info(f"Extracted plugin to: {item}")
                    return item
            
            # If no subdirectory found, the target directory is the plugin directory
            if (target_directory / "plugin.json").exists():
                return target_directory
            
            raise ValueError("No valid plugin found in package")
            
        except Exception as e:
            self.logger.error(f"Error extracting plugin package: {e}")
            raise


# ============================================================================
# Plugin Development CLI
# ============================================================================

class PluginCLI:
    """Command-line interface for plugin development"""
    
    def __init__(self):
        self.sdk = PluginSDK()
        self.logger = logging.getLogger("PluginCLI")
    
    def create_plugin(self, plugin_id: str, plugin_type: str, 
                     author: str = "Plugin Developer") -> bool:
        """Create a new plugin project"""
        
        try:
            plugin_type_enum = PluginType(plugin_type.lower())
            plugin_dir = self.sdk.create_plugin_project(plugin_id, plugin_type_enum, author=author)
            
            print(f"✅ Created plugin project: {plugin_dir}")
            print(f"📝 Plugin ID: {plugin_id}")
            print(f"🏷️  Plugin Type: {plugin_type}")
            print(f"👤 Author: {author}")
            print("\n📋 Next steps:")
            print(f"   1. cd {plugin_dir}")
            print("   2. Implement your plugin logic in src/__init__.py")
            print("   3. Configure settings in config/default.json")
            print("   4. Run tests with: make test")
            print("   5. Package with: make package")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating plugin: {e}")
            return False
    
    async def validate_plugin(self, plugin_path: str) -> bool:
        """Validate a plugin"""
        
        try:
            plugin_path = Path(plugin_path)
            results = await self.sdk.validate_plugin(plugin_path)
            
            print(f"🔍 Plugin Validation Results for: {plugin_path}")
            print("=" * 50)
            
            if results["valid"]:
                print("✅ Plugin is valid!")
            else:
                print("❌ Plugin validation failed")
            
            if results["errors"]:
                print(f"\n❌ Errors ({len(results['errors'])}):")
                for error in results["errors"]:
                    print(f"   - {error}")
            
            if results["warnings"]:
                print(f"\n⚠️  Warnings ({len(results['warnings'])}):")
                for warning in results["warnings"]:
                    print(f"   - {warning}")
            
            return results["valid"]
            
        except Exception as e:
            print(f"❌ Error validating plugin: {e}")
            return False
    
    def package_plugin(self, plugin_path: str, output_dir: str = None) -> bool:
        """Package a plugin"""
        
        try:
            plugin_path = Path(plugin_path)
            output_dir = Path(output_dir) if output_dir else None
            
            package_path = self.sdk.package_plugin(plugin_path, output_dir)
            
            print(f"📦 Successfully packaged plugin: {package_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error packaging plugin: {e}")
            return False


# ============================================================================
# Example Usage and Testing
# ============================================================================

async def main():
    """Example usage of the Plugin SDK"""
    
    print("🛠️  Plugin Framework SDK - Example Usage")
    print("=" * 60)
    
    # Initialize SDK
    sdk = PluginSDK()
    
    # Create example plugin project
    print("\n📝 Creating example plugin project...")
    plugin_dir = sdk.create_plugin_project(
        plugin_id="example_utility_plugin",
        plugin_type=PluginType.UTILITY,
        plugin_name="Example Utility Plugin",
        author="SDK Example"
    )
    
    print(f"✅ Created plugin project: {plugin_dir}")
    
    # Validate the created plugin
    print(f"\n🔍 Validating plugin: {plugin_dir}")
    validation_results = await sdk.validate_plugin(plugin_dir)
    
    print(f"Validation result: {'✅ Valid' if validation_results['valid'] else '❌ Invalid'}")
    if validation_results["errors"]:
        print("Errors:")
        for error in validation_results["errors"]:
            print(f"  - {error}")
    
    # Package the plugin
    print(f"\n📦 Packaging plugin: {plugin_dir}")
    package_path = sdk.package_plugin(plugin_dir)
    
    print(f"✅ Package created: {package_path}")
    
    print("\n🎉 Plugin SDK demonstration complete!")


if __name__ == "__main__":
    asyncio.run(main())
