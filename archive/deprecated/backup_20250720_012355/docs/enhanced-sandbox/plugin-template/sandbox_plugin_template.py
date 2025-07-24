#!/usr/bin/env python3
"""
Plugin Development Template for Enhanced Plugin Sandbox Isolation

This template provides a complete structure for developing plugins that work
optimally with the Enhanced Plugin Sandbox Isolation system.
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Callable
from enum import Enum


# ============================================================================
# Plugin Metadata and Configuration
# ============================================================================

class PluginCategory(Enum):
    """Standard plugin categories"""
    DATA_PROCESSING = "data_processing"
    ANALYSIS = "analysis"
    TRANSFORMATION = "transformation"
    UTILITY = "utility"
    INTEGRATION = "integration"
    MONITORING = "monitoring"
    SECURITY = "security"


class ResourceRequirement(Enum):
    """Resource requirement levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class PluginTemplate:
    """Plugin template metadata"""
    name: str
    version: str
    description: str
    category: PluginCategory
    author: str
    memory_requirement: ResourceRequirement
    cpu_requirement: ResourceRequirement
    execution_time_estimate: float  # seconds
    requires_network: bool = False
    requires_filesystem: bool = False
    sandbox_compatible: bool = True
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


# ============================================================================
# Base Plugin Classes
# ============================================================================

class SandboxPlugin(ABC):
    """
    Abstract base class for sandbox-compatible plugins.
    
    All plugins should inherit from this class to ensure proper
    sandbox integration and error handling.
    """
    
    def __init__(self, metadata: PluginTemplate):
        self.metadata = metadata
        self.execution_start_time: Optional[float] = None
        self.execution_end_time: Optional[float] = None
        self._logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup plugin-specific logger"""
        logger = logging.getLogger(f"plugin.{self.metadata.name}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.metadata.name} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    @abstractmethod
    async def execute(self, environment: Dict[str, Any], *args, **kwargs) -> Dict[str, Any]:
        """
        Main plugin execution method.
        
        Args:
            environment: Sandbox environment context
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Dict containing plugin results
        """
        pass
    
    def pre_execute(self, environment: Dict[str, Any]) -> bool:
        """
        Pre-execution hook for validation and setup.
        
        Returns:
            True if plugin can proceed, False otherwise
        """
        self.execution_start_time = time.time()
        self._logger.info(f"Starting plugin execution: {self.metadata.name}")
        return True
    
    def post_execute(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post-execution hook for cleanup and result processing.
        
        Args:
            result: Execution result from execute method
        
        Returns:
            Processed result
        """
        self.execution_end_time = time.time()
        execution_time = self.execution_end_time - self.execution_start_time
        
        self._logger.info(f"Plugin execution completed in {execution_time:.3f}s")
        
        # Add metadata to result
        result.update({
            "_plugin_metadata": {
                "name": self.metadata.name,
                "version": self.metadata.version,
                "category": self.metadata.category.value,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
        })
        
        return result
    
    def handle_error(self, error: Exception) -> Dict[str, Any]:
        """
        Error handling hook.
        
        Args:
            error: Exception that occurred during execution
        
        Returns:
            Error result dictionary
        """
        self._logger.error(f"Plugin execution failed: {error}")
        
        return {
            "status": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "_plugin_metadata": {
                "name": self.metadata.name,
                "version": self.metadata.version,
                "failed_at": datetime.now().isoformat()
            }
        }
    
    async def safe_execute(self, environment: Dict[str, Any], *args, **kwargs) -> Dict[str, Any]:
        """
        Safe execution wrapper with error handling.
        """
        try:
            # Pre-execution validation
            if not self.pre_execute(environment):
                return {
                    "status": "error",
                    "error_message": "Pre-execution validation failed"
                }
            
            # Execute plugin
            result = await self.execute(environment, *args, **kwargs)
            
            # Post-execution processing
            return self.post_execute(result)
        
        except Exception as e:
            return self.handle_error(e)


# ============================================================================
# Specialized Plugin Templates
# ============================================================================

class DataProcessingPlugin(SandboxPlugin):
    """Template for data processing plugins"""
    
    def __init__(self, name: str, version: str, description: str, author: str):
        metadata = PluginTemplate(
            name=name,
            version=version,
            description=description,
            category=PluginCategory.DATA_PROCESSING,
            author=author,
            memory_requirement=ResourceRequirement.MEDIUM,
            cpu_requirement=ResourceRequirement.MEDIUM,
            execution_time_estimate=10.0,
            requires_filesystem=False,
            requires_network=False
        )
        super().__init__(metadata)
    
    @abstractmethod
    async def process_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process input data and return processed results"""
        pass
    
    async def execute(self, environment: Dict[str, Any], data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute data processing"""
        if not isinstance(data, list):
            raise ValueError("Input data must be a list")
        
        processed_data = await self.process_data(data)
        
        return {
            "status": "success",
            "input_count": len(data),
            "output_count": len(processed_data),
            "processed_data": processed_data
        }


class AnalysisPlugin(SandboxPlugin):
    """Template for analysis plugins"""
    
    def __init__(self, name: str, version: str, description: str, author: str):
        metadata = PluginTemplate(
            name=name,
            version=version,
            description=description,
            category=PluginCategory.ANALYSIS,
            author=author,
            memory_requirement=ResourceRequirement.MEDIUM,
            cpu_requirement=ResourceRequirement.HIGH,
            execution_time_estimate=15.0
        )
        super().__init__(metadata)
    
    @abstractmethod
    async def analyze(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze input data and return analysis results"""
        pass
    
    async def execute(self, environment: Dict[str, Any], data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute analysis"""
        if not isinstance(data, list):
            raise ValueError("Input data must be a list")
        
        analysis_result = await self.analyze(data)
        
        return {
            "status": "success",
            "data_analyzed": len(data),
            "analysis": analysis_result
        }


class UtilityPlugin(SandboxPlugin):
    """Template for utility plugins"""
    
    def __init__(self, name: str, version: str, description: str, author: str):
        metadata = PluginTemplate(
            name=name,
            version=version,
            description=description,
            category=PluginCategory.UTILITY,
            author=author,
            memory_requirement=ResourceRequirement.LOW,
            cpu_requirement=ResourceRequirement.LOW,
            execution_time_estimate=5.0
        )
        super().__init__(metadata)


# ============================================================================
# Example Plugin Implementations
# ============================================================================

class DataValidatorPlugin(DataProcessingPlugin):
    """Example: Data validation plugin"""
    
    def __init__(self):
        super().__init__(
            name="data_validator",
            version="1.0.0",
            description="Validates data records according to specified schema",
            author="Plugin Template"
        )
        self.validation_rules = {}
    
    def set_validation_rules(self, rules: Dict[str, Dict[str, Any]]):
        """Set validation rules for data fields"""
        self.validation_rules = rules
    
    async def process_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate each data record"""
        validated_data = []
        
        for record in data:
            validated_record = {**record}
            validation_errors = []
            
            for field, rules in self.validation_rules.items():
                if field in record:
                    value = record[field]
                    
                    # Type validation
                    if 'type' in rules and not isinstance(value, rules['type']):
                        validation_errors.append(f"{field}: expected {rules['type'].__name__}")
                    
                    # Range validation for numbers
                    if 'min' in rules and isinstance(value, (int, float)) and value < rules['min']:
                        validation_errors.append(f"{field}: value below minimum {rules['min']}")
                    
                    if 'max' in rules and isinstance(value, (int, float)) and value > rules['max']:
                        validation_errors.append(f"{field}: value above maximum {rules['max']}")
                    
                    # Length validation for strings
                    if 'max_length' in rules and isinstance(value, str) and len(value) > rules['max_length']:
                        validation_errors.append(f"{field}: length exceeds maximum {rules['max_length']}")
                
                elif rules.get('required', False):
                    validation_errors.append(f"{field}: required field missing")
            
            validated_record['_validation'] = {
                "is_valid": len(validation_errors) == 0,
                "errors": validation_errors
            }
            
            validated_data.append(validated_record)
        
        return validated_data


class StatisticsAnalyzerPlugin(AnalysisPlugin):
    """Example: Statistical analysis plugin"""
    
    def __init__(self):
        super().__init__(
            name="statistics_analyzer",
            version="1.0.0",
            description="Performs statistical analysis on numerical data fields",
            author="Plugin Template"
        )
    
    async def analyze(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform statistical analysis"""
        if not data:
            return {"message": "No data to analyze"}
        
        # Find numerical fields
        numerical_fields = set()
        for record in data:
            for key, value in record.items():
                if isinstance(value, (int, float)):
                    numerical_fields.add(key)
        
        statistics = {}
        
        for field in numerical_fields:
            values = [record.get(field) for record in data if isinstance(record.get(field), (int, float))]
            
            if values:
                statistics[field] = {
                    "count": len(values),
                    "sum": sum(values),
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "range": max(values) - min(values)
                }
                
                # Calculate variance and standard deviation
                mean = statistics[field]["mean"]
                variance = sum((x - mean) ** 2 for x in values) / len(values)
                statistics[field]["variance"] = variance
                statistics[field]["std_dev"] = variance ** 0.5
        
        return {
            "total_records": len(data),
            "numerical_fields": list(numerical_fields),
            "statistics": statistics
        }


class TextProcessorPlugin(DataProcessingPlugin):
    """Example: Text processing plugin"""
    
    def __init__(self):
        super().__init__(
            name="text_processor",
            version="1.0.0",
            description="Processes text fields in data records",
            author="Plugin Template"
        )
    
    async def process_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process text fields"""
        processed_data = []
        
        for record in data:
            processed_record = {**record}
            text_analysis = {}
            
            for key, value in record.items():
                if isinstance(value, str):
                    # Basic text analysis
                    text_analysis[key] = {
                        "length": len(value),
                        "word_count": len(value.split()),
                        "uppercase_count": sum(1 for c in value if c.isupper()),
                        "lowercase_count": sum(1 for c in value if c.islower()),
                        "digit_count": sum(1 for c in value if c.isdigit()),
                        "processed_text": value.strip().lower()
                    }
            
            if text_analysis:
                processed_record["_text_analysis"] = text_analysis
            
            processed_data.append(processed_record)
        
        return processed_data


class ConfigurableUtilityPlugin(UtilityPlugin):
    """Example: Configurable utility plugin"""
    
    def __init__(self):
        super().__init__(
            name="configurable_utility",
            version="1.0.0",
            description="Configurable utility plugin for various operations",
            author="Plugin Template"
        )
        self.config = {}
    
    def set_config(self, config: Dict[str, Any]):
        """Set plugin configuration"""
        self.config = config
    
    async def execute(self, environment: Dict[str, Any], operation: str, data: Any) -> Dict[str, Any]:
        """Execute configurable operation"""
        if operation == "format_json":
            return {
                "status": "success",
                "operation": operation,
                "result": json.dumps(data, indent=self.config.get("json_indent", 2))
            }
        
        elif operation == "count_items":
            if isinstance(data, (list, dict, str)):
                return {
                    "status": "success",
                    "operation": operation,
                    "result": len(data)
                }
            else:
                return {
                    "status": "error",
                    "operation": operation,
                    "error": "Data type not countable"
                }
        
        elif operation == "timestamp_data":
            return {
                "status": "success",
                "operation": operation,
                "result": {
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                    "timezone": self.config.get("timezone", "UTC")
                }
            }
        
        else:
            return {
                "status": "error",
                "operation": operation,
                "error": f"Unknown operation: {operation}"
            }


# ============================================================================
# Plugin Registration and Factory
# ============================================================================

class PluginRegistry:
    """Registry for managing available plugins"""
    
    def __init__(self):
        self._plugins: Dict[str, SandboxPlugin] = {}
    
    def register(self, plugin: SandboxPlugin):
        """Register a plugin"""
        self._plugins[plugin.metadata.name] = plugin
        logging.info(f"Registered plugin: {plugin.metadata.name} v{plugin.metadata.version}")
    
    def get(self, name: str) -> Optional[SandboxPlugin]:
        """Get a plugin by name"""
        return self._plugins.get(name)
    
    def list_plugins(self) -> Dict[str, PluginTemplate]:
        """List all registered plugins"""
        return {name: plugin.metadata for name, plugin in self._plugins.items()}
    
    def get_by_category(self, category: PluginCategory) -> List[SandboxPlugin]:
        """Get plugins by category"""
        return [plugin for plugin in self._plugins.values() 
                if plugin.metadata.category == category]


# Global plugin registry
plugin_registry = PluginRegistry()


def register_plugin(plugin: SandboxPlugin):
    """Decorator/function to register a plugin"""
    plugin_registry.register(plugin)
    return plugin


# ============================================================================
# Testing Utilities
# ============================================================================

async def test_plugin(plugin: SandboxPlugin, test_data: Any) -> Dict[str, Any]:
    """Test a plugin with provided data"""
    test_environment = {
        "testing": True,
        "test_timestamp": datetime.now().isoformat()
    }
    
    print(f"Testing plugin: {plugin.metadata.name}")
    print(f"Description: {plugin.metadata.description}")
    print(f"Category: {plugin.metadata.category.value}")
    print("-" * 50)
    
    result = await plugin.safe_execute(test_environment, test_data)
    
    print(f"Result: {json.dumps(result, indent=2, default=str)}")
    
    return result


async def demo_plugins():
    """Demonstrate example plugins"""
    
    print("🚀 Plugin Development Template - Demo")
    print("=" * 50)
    
    # Register example plugins
    data_validator = DataValidatorPlugin()
    stats_analyzer = StatisticsAnalyzerPlugin()
    text_processor = TextProcessorPlugin()
    utility_plugin = ConfigurableUtilityPlugin()
    
    register_plugin(data_validator)
    register_plugin(stats_analyzer)
    register_plugin(text_processor)
    register_plugin(utility_plugin)
    
    # Sample data for testing
    sample_data = [
        {"id": 1, "name": "Alice", "age": 25, "score": 85.5, "description": "Data Scientist"},
        {"id": 2, "name": "Bob", "age": 30, "score": 92.0, "description": "Software Engineer"},
        {"id": 3, "name": "Charlie", "age": 28, "score": 78.5, "description": "Product Manager"},
        {"id": 4, "age": 35, "score": 88.0, "description": "Team Lead"},  # Missing name
        {"id": 5, "name": "Eve", "age": "invalid", "score": 95.5, "description": "UX Designer"}  # Invalid age
    ]
    
    # Test data validation plugin
    print("🔍 Testing Data Validator Plugin")
    data_validator.set_validation_rules({
        "name": {"type": str, "required": True, "max_length": 50},
        "age": {"type": int, "required": True, "min": 18, "max": 100},
        "score": {"type": float, "min": 0.0, "max": 100.0},
        "id": {"type": int, "required": True}
    })
    await test_plugin(data_validator, sample_data)
    
    print("\n" + "="*60 + "\n")
    
    # Test statistics analyzer plugin
    print("📊 Testing Statistics Analyzer Plugin")
    await test_plugin(stats_analyzer, sample_data)
    
    print("\n" + "="*60 + "\n")
    
    # Test text processor plugin
    print("📝 Testing Text Processor Plugin")
    await test_plugin(text_processor, sample_data)
    
    print("\n" + "="*60 + "\n")
    
    # Test utility plugin
    print("🔧 Testing Configurable Utility Plugin")
    utility_plugin.set_config({"json_indent": 4, "timezone": "UTC"})
    await test_plugin(utility_plugin, "timestamp_data", {"test": "data"})
    
    # List all registered plugins
    print("\n📋 Registered Plugins:")
    plugins = plugin_registry.list_plugins()
    for name, metadata in plugins.items():
        print(f"  - {name} v{metadata.version} ({metadata.category.value})")
        print(f"    {metadata.description}")


if __name__ == "__main__":
    asyncio.run(demo_plugins())
