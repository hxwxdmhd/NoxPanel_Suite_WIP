#!/usr/bin/env python3
"""
Sample Secure Plugin - Audit 3 Compliant
========================================

This is a sample plugin demonstrating the secure plugin framework:
- Proper manifest integration
- Security compliance
- Resource management
- Error handling
- Performance monitoring

Use this as a template for creating new plugins.
"""

import os
import sys
import json
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib
import threading
import psutil

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import the secure plugin base class
try:
    from plugin_template_secure import SecurePluginBase, PluginExecutionContext, PluginError
    from plugin_manifest_system import PluginManifest, PluginManifestManager
    from plugin_registry_db import PluginRegistryDatabase, PluginMetadata, PluginStatus, PluginCategory
except ImportError as e:
    logging.error(f"Failed to import plugin framework: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SampleSecurePlugin(SecurePluginBase):
    """
    Sample secure plugin implementation
    """
    
    def __init__(self):
        super().__init__()
        self.name = "sample_secure_plugin"
        self.version = "1.0.0"
        self.description = "Sample secure plugin demonstrating best practices"
        self.author = "Heimnetz Project"
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Plugin state
        self.is_initialized = False
        self.execution_count = 0
        self.last_execution = None
        self.plugin_data = {}
        
        # Configuration
        self.config = {
            "enabled": True,
            "max_iterations": 100,
            "delay_seconds": 1,
            "output_format": "json",
            "log_level": "INFO"
        }
        
        # Performance tracking
        self.performance_metrics = {
            "total_executions": 0,
            "avg_execution_time": 0.0,
            "max_execution_time": 0.0,
            "min_execution_time": float('inf'),
            "total_memory_usage": 0,
            "peak_memory_usage": 0
        }
    
    def initialize(self, context: PluginExecutionContext) -> bool:
        """
        Initialize the plugin
        
        Args:
            context: Plugin execution context
            
        Returns:
            bool: True if initialization successful
        """
        try:
            self.logger.info("Initializing Sample Secure Plugin")
            
            # Load configuration from context
            if context.config:
                self.config.update(context.config)
            
            # Set up logging level
            log_level = getattr(logging, self.config.get("log_level", "INFO"))
            self.logger.setLevel(log_level)
            
            # Initialize plugin data
            self.plugin_data = {
                "initialized_at": datetime.now().isoformat(),
                "process_id": os.getpid(),
                "thread_id": threading.get_ident(),
                "initial_memory": psutil.Process().memory_info().rss
            }
            
            # Validate configuration
            if not self._validate_config():
                raise PluginError("Invalid plugin configuration")
            
            # Check security requirements
            if not self._check_security_requirements():
                raise PluginError("Security requirements not met")
            
            self.is_initialized = True
            self.logger.info("Sample Secure Plugin initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize plugin: {e}")
            return False
    
    def execute(self, context: PluginExecutionContext) -> Dict[str, Any]:
        """
        Execute the plugin
        
        Args:
            context: Plugin execution context
            
        Returns:
            Dict[str, Any]: Execution results
        """
        if not self.is_initialized:
            raise PluginError("Plugin not initialized")
        
        if not self.config.get("enabled", True):
            return {"status": "disabled", "message": "Plugin is disabled"}
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        try:
            self.logger.info(f"Executing plugin (execution #{self.execution_count + 1})")
            
            # Validate input data
            input_data = context.input_data or {}
            if not self._validate_input(input_data):
                raise PluginError("Invalid input data")
            
            # Execute main logic
            result = self._execute_main_logic(input_data)
            
            # Process output
            output = self._process_output(result)
            
            # Update execution tracking
            execution_time = time.time() - start_time
            memory_usage = psutil.Process().memory_info().rss - start_memory
            
            self._update_performance_metrics(execution_time, memory_usage)
            
            self.execution_count += 1
            self.last_execution = datetime.now()
            
            self.logger.info(f"Plugin execution completed in {execution_time:.3f}s")
            
            return {
                "status": "success",
                "data": output,
                "execution_time": execution_time,
                "memory_usage": memory_usage,
                "execution_count": self.execution_count,
                "timestamp": self.last_execution.isoformat()
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Plugin execution failed: {e}")
            
            return {
                "status": "error",
                "error": str(e),
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
    
    def cleanup(self, context: PluginExecutionContext) -> bool:
        """
        Cleanup plugin resources
        
        Args:
            context: Plugin execution context
            
        Returns:
            bool: True if cleanup successful
        """
        try:
            self.logger.info("Cleaning up Sample Secure Plugin")
            
            # Save performance metrics
            self._save_performance_metrics()
            
            # Clear plugin data
            self.plugin_data.clear()
            
            # Reset state
            self.is_initialized = False
            self.execution_count = 0
            self.last_execution = None
            
            self.logger.info("Sample Secure Plugin cleanup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup plugin: {e}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get plugin information
        
        Returns:
            Dict[str, Any]: Plugin information
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "status": "initialized" if self.is_initialized else "uninitialized",
            "execution_count": self.execution_count,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "config": self.config,
            "performance_metrics": self.performance_metrics,
            "plugin_data": self.plugin_data
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate plugin configuration
        
        Args:
            config: Configuration to validate
            
        Returns:
            bool: True if configuration is valid
        """
        try:
            # Check required fields
            required_fields = ["enabled"]
            for field in required_fields:
                if field not in config:
                    self.logger.error(f"Missing required config field: {field}")
                    return False
            
            # Validate field types
            if not isinstance(config.get("enabled"), bool):
                self.logger.error("Config field 'enabled' must be boolean")
                return False
            
            if "max_iterations" in config:
                if not isinstance(config["max_iterations"], int) or config["max_iterations"] <= 0:
                    self.logger.error("Config field 'max_iterations' must be positive integer")
                    return False
            
            if "delay_seconds" in config:
                if not isinstance(config["delay_seconds"], (int, float)) or config["delay_seconds"] < 0:
                    self.logger.error("Config field 'delay_seconds' must be non-negative number")
                    return False
            
            if "output_format" in config:
                if config["output_format"] not in ["json", "text", "csv"]:
                    self.logger.error("Config field 'output_format' must be 'json', 'text', or 'csv'")
                    return False
            
            if "log_level" in config:
                if config["log_level"] not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                    self.logger.error("Config field 'log_level' must be valid logging level")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Config validation error: {e}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get plugin health status
        
        Returns:
            Dict[str, Any]: Health status information
        """
        try:
            process = psutil.Process()
            
            health_status = {
                "status": "healthy" if self.is_initialized else "unhealthy",
                "initialized": self.is_initialized,
                "execution_count": self.execution_count,
                "last_execution": self.last_execution.isoformat() if self.last_execution else None,
                "memory_usage": process.memory_info().rss,
                "cpu_percent": process.cpu_percent(),
                "uptime": (datetime.now() - datetime.fromisoformat(self.plugin_data.get("initialized_at", datetime.now().isoformat()))).total_seconds() if self.is_initialized else 0,
                "performance_metrics": self.performance_metrics
            }
            
            # Add health checks
            health_checks = []
            
            # Check memory usage
            if process.memory_info().rss > 50 * 1024 * 1024:  # 50MB
                health_checks.append("HIGH_MEMORY_USAGE")
            
            # Check execution frequency
            if self.execution_count > 1000:
                health_checks.append("HIGH_EXECUTION_COUNT")
            
            # Check performance
            if self.performance_metrics["avg_execution_time"] > 5.0:
                health_checks.append("SLOW_EXECUTION")
            
            health_status["health_checks"] = health_checks
            health_status["healthy"] = len(health_checks) == 0
            
            return health_status
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "healthy": False
            }
    
    def _validate_config(self) -> bool:
        """Validate current configuration"""
        return self.validate_config(self.config)
    
    def _check_security_requirements(self) -> bool:
        """Check security requirements"""
        try:
            # Check sandbox environment
            if not self.is_sandboxed():
                self.logger.warning("Plugin is not running in sandbox environment")
                return False
            
            # Check file access permissions
            restricted_paths = ["/etc", "/sys", "/proc", "/dev"]
            for path in restricted_paths:
                if os.path.exists(path) and os.access(path, os.W_OK):
                    self.logger.error(f"Unauthorized write access to: {path}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Security check failed: {e}")
            return False
    
    def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data"""
        try:
            # Basic input validation
            if not isinstance(input_data, dict):
                return False
            
            # Check for dangerous keys
            dangerous_keys = ["__class__", "__module__", "exec", "eval", "import"]
            for key in dangerous_keys:
                if key in input_data:
                    self.logger.error(f"Dangerous input key detected: {key}")
                    return False
            
            # Validate data types
            for key, value in input_data.items():
                if not isinstance(key, str):
                    self.logger.error(f"Non-string key detected: {key}")
                    return False
                
                # Check for overly large values
                if isinstance(value, str) and len(value) > 10000:
                    self.logger.error(f"String value too large for key: {key}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Input validation error: {e}")
            return False
    
    def _execute_main_logic(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute main plugin logic"""
        try:
            # Simulate plugin work
            max_iterations = self.config.get("max_iterations", 100)
            delay_seconds = self.config.get("delay_seconds", 1)
            
            results = []
            for i in range(min(max_iterations, 10)):  # Limit to 10 iterations for demo
                # Simulate processing
                time.sleep(delay_seconds / 1000)  # Convert to milliseconds
                
                # Generate sample data
                result = {
                    "iteration": i + 1,
                    "timestamp": datetime.now().isoformat(),
                    "data": f"Processed item {i + 1}",
                    "hash": hashlib.md5(f"item_{i}".encode()).hexdigest()[:8],
                    "input_echo": input_data.get("echo", "No echo data")
                }
                
                results.append(result)
            
            return {
                "results": results,
                "total_iterations": len(results),
                "processing_time": len(results) * delay_seconds / 1000,
                "input_summary": {
                    "keys": list(input_data.keys()),
                    "size": len(input_data)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Main logic execution failed: {e}")
            raise PluginError(f"Execution failed: {e}")
    
    def _process_output(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process and format output"""
        try:
            output_format = self.config.get("output_format", "json")
            
            if output_format == "json":
                return result
            elif output_format == "text":
                return {
                    "format": "text",
                    "content": str(result)
                }
            elif output_format == "csv":
                return {
                    "format": "csv",
                    "headers": list(result.keys()),
                    "data": list(result.values())
                }
            else:
                return result
                
        except Exception as e:
            self.logger.error(f"Output processing failed: {e}")
            return result
    
    def _update_performance_metrics(self, execution_time: float, memory_usage: int):
        """Update performance metrics"""
        try:
            self.performance_metrics["total_executions"] += 1
            
            # Update execution time metrics
            total_time = self.performance_metrics["avg_execution_time"] * (self.performance_metrics["total_executions"] - 1)
            self.performance_metrics["avg_execution_time"] = (total_time + execution_time) / self.performance_metrics["total_executions"]
            
            if execution_time > self.performance_metrics["max_execution_time"]:
                self.performance_metrics["max_execution_time"] = execution_time
            
            if execution_time < self.performance_metrics["min_execution_time"]:
                self.performance_metrics["min_execution_time"] = execution_time
            
            # Update memory metrics
            self.performance_metrics["total_memory_usage"] += memory_usage
            if memory_usage > self.performance_metrics["peak_memory_usage"]:
                self.performance_metrics["peak_memory_usage"] = memory_usage
                
        except Exception as e:
            self.logger.error(f"Failed to update performance metrics: {e}")
    
    def _save_performance_metrics(self):
        """Save performance metrics to file"""
        try:
            metrics_file = f"performance_metrics_{self.name}.json"
            with open(metrics_file, 'w') as f:
                json.dump(self.performance_metrics, f, indent=2)
            
            self.logger.info(f"Performance metrics saved to {metrics_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save performance metrics: {e}")

# Plugin entry point functions
def initialize(context: PluginExecutionContext) -> bool:
    """Plugin initialization entry point"""
    plugin = SampleSecurePlugin()
    return plugin.initialize(context)

def execute(context: PluginExecutionContext) -> Dict[str, Any]:
    """Plugin execution entry point"""
    plugin = SampleSecurePlugin()
    return plugin.execute(context)

def cleanup(context: PluginExecutionContext) -> bool:
    """Plugin cleanup entry point"""
    plugin = SampleSecurePlugin()
    return plugin.cleanup(context)

def get_info() -> Dict[str, Any]:
    """Plugin information entry point"""
    plugin = SampleSecurePlugin()
    return plugin.get_info()

def validate_config(config: Dict[str, Any]) -> bool:
    """Plugin configuration validation entry point"""
    plugin = SampleSecurePlugin()
    return plugin.validate_config(config)

def get_health_status() -> Dict[str, Any]:
    """Plugin health status entry point"""
    plugin = SampleSecurePlugin()
    return plugin.get_health_status()

# Main function for testing
def main():
    """Main function for testing the plugin"""
    try:
        # Create test context
        context = PluginExecutionContext(
            plugin_id="test_sample_secure_plugin",
            config={
                "enabled": True,
                "max_iterations": 5,
                "delay_seconds": 0.1,
                "output_format": "json",
                "log_level": "INFO"
            },
            input_data={
                "echo": "Hello from sample plugin!",
                "test_data": [1, 2, 3, 4, 5]
            }
        )
        
        # Test plugin
        print("Testing Sample Secure Plugin...")
        
        # Initialize
        if initialize(context):
            print("✓ Plugin initialized successfully")
            
            # Execute
            result = execute(context)
            print(f"✓ Plugin executed: {result['status']}")
            if result['status'] == 'success':
                print(f"  - Execution time: {result['execution_time']:.3f}s")
                print(f"  - Memory usage: {result['memory_usage']} bytes")
                print(f"  - Results: {len(result['data']['results'])} items")
            
            # Get info
            info = get_info()
            print(f"✓ Plugin info: {info['name']} v{info['version']}")
            
            # Get health status
            health = get_health_status()
            print(f"✓ Plugin health: {health['status']}")
            
            # Cleanup
            if cleanup(context):
                print("✓ Plugin cleanup completed")
        
        else:
            print("✗ Plugin initialization failed")
            
    except Exception as e:
        print(f"✗ Plugin test failed: {e}")
        logger.error(f"Plugin test error: {e}")

if __name__ == "__main__":
    main()
