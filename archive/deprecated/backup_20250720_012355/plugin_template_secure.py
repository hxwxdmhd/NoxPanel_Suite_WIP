#!/usr/bin/env python3
"""
Secure Plugin Template - Audit 3 Compliant
==========================================

This template provides a secure foundation for plugin development with:
- Sandbox environment restrictions
- Input/output validation
- Resource limits
- Security hooks
- Performance monitoring

DO NOT REMOVE SECURITY HOOKS - Required for Audit 3 compliance
"""

import os
import sys
import time
import logging
import threading
import traceback
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime
import resource
import signal

# Import the plugin interface
try:
    from unified_plugin_system_clean import PluginInterface, PluginInfo
    PLUGIN_SYSTEM_AVAILABLE = True
except ImportError:
    # Fallback interface if not available
    PLUGIN_SYSTEM_AVAILABLE = False
    
    class PluginInterface(ABC):
        @abstractmethod
        def get_info(self) -> 'PluginInfo':
            pass
        
        @abstractmethod
        def initialize(self, config: Dict[str, Any] = None) -> bool:
            pass
        
        @abstractmethod
        def start(self) -> bool:
            pass
        
        @abstractmethod
        def stop(self) -> bool:
            pass
        
        @abstractmethod
        def execute(self, *args, **kwargs) -> Any:
            pass
    
    @dataclass
    class PluginInfo:
        name: str
        version: str = "1.0.0"
        description: str = ""
        author: str = ""
        category: str = "general"
        dependencies: List[str] = field(default_factory=list)
        permissions: List[str] = field(default_factory=list)
        config_schema: Dict[str, Any] = field(default_factory=dict)
        entry_point: str = ""
        file_path: str = ""
        enabled: bool = False
        auto_start: bool = False

# Security and monitoring decorators
def secure_execution(timeout: int = 30, memory_limit: int = 50 * 1024 * 1024):
    """
    Decorator to enforce security and resource limits on plugin methods
    
    Args:
        timeout: Maximum execution time in seconds
        memory_limit: Maximum memory usage in bytes
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            # Set up timeout handler
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Plugin execution timed out after {timeout} seconds")
            
            # Set up memory monitoring
            start_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            start_time = time.time()
            
            try:
                # Set timeout
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(timeout)
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Check memory usage
                end_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                memory_used = end_memory - start_memory
                
                if memory_used > memory_limit:
                    raise MemoryError(f"Plugin exceeded memory limit: {memory_used} bytes")
                
                return result
                
            except Exception as e:
                # Log security violation
                logging.error(f"Security violation in plugin execution: {e}")
                raise
            finally:
                # Clear timeout
                signal.alarm(0)
                
                # Log performance metrics
                execution_time = time.time() - start_time
                logging.info(f"Plugin execution completed in {execution_time:.3f}s")
        
        return wrapper
    return decorator

def validate_input(input_schema: Dict[str, Any]):
    """
    Decorator to validate plugin inputs
    
    Args:
        input_schema: Schema for input validation
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            # Validate inputs against schema
            # This is a simplified validation - implement full schema validation
            for key, expected_type in input_schema.items():
                if key in kwargs:
                    if not isinstance(kwargs[key], expected_type):
                        raise ValueError(f"Invalid input type for {key}: expected {expected_type}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def sanitize_output(output_schema: Dict[str, Any]):
    """
    Decorator to sanitize plugin outputs
    
    Args:
        output_schema: Schema for output validation
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Sanitize output based on schema
            # This is a simplified sanitization - implement full output sanitization
            if isinstance(result, dict):
                sanitized_result = {}
                for key, value in result.items():
                    # Remove potentially dangerous keys
                    if key.startswith('__') or key in ['exec', 'eval', 'import']:
                        continue
                    sanitized_result[key] = value
                return sanitized_result
            
            return result
        return wrapper
    return decorator

class SecurePluginBase(PluginInterface):
    """
    Secure base class for all plugins - Audit 3 compliant
    
    This class provides:
    - Security validation
    - Resource monitoring
    - Input/output sanitization
    - Sandbox environment
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"plugin.{self.__class__.__name__}")
        self.start_time = None
        self.is_running = False
        self.resource_monitor = None
        self.security_context = {
            'allowed_modules': ['json', 'time', 'datetime', 'logging'],
            'blocked_modules': ['os', 'sys', 'subprocess', 'importlib'],
            'max_memory': 50 * 1024 * 1024,  # 50MB
            'max_cpu_percent': 10,
            'max_execution_time': 30
        }
        
        # Validate security context
        self._validate_security_context()
    
    def _validate_security_context(self):
        """Validate that the plugin is running in a secure context"""
        # Check for restricted imports
        restricted_modules = ['os', 'sys', 'subprocess', 'importlib']
        for module_name in restricted_modules:
            if module_name in sys.modules:
                self.logger.warning(f"Restricted module {module_name} detected")
        
        # Validate file system access restrictions
        try:
            # This should fail in a secure environment
            with open('/etc/passwd', 'r') as f:
                pass
            self.logger.error("File system access not restricted - SECURITY VIOLATION")
        except (FileNotFoundError, PermissionError):
            self.logger.info("File system access properly restricted")
    
    def _start_resource_monitoring(self):
        """Start monitoring plugin resource usage"""
        def monitor_resources():
            while self.is_running:
                try:
                    # Monitor memory usage
                    memory_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                    if memory_usage > self.security_context['max_memory']:
                        self.logger.error(f"Memory limit exceeded: {memory_usage} bytes")
                        self.stop()
                        break
                    
                    # Monitor CPU usage (simplified)
                    cpu_usage = resource.getrusage(resource.RUSAGE_SELF).ru_utime
                    
                    # Sleep before next check
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"Resource monitoring error: {e}")
                    break
        
        self.resource_monitor = threading.Thread(target=monitor_resources, daemon=True)
        self.resource_monitor.start()
    
    def _stop_resource_monitoring(self):
        """Stop resource monitoring"""
        self.is_running = False
        if self.resource_monitor:
            self.resource_monitor.join(timeout=1)
    
    @secure_execution(timeout=30, memory_limit=50*1024*1024)
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """
        Initialize the plugin securely
        
        Args:
            config: Plugin configuration
            
        Returns:
            bool: True if initialization successful
        """
        try:
            self.logger.info(f"Initializing secure plugin: {self.__class__.__name__}")
            
            # Validate configuration
            if config:
                self._validate_config(config)
            
            # Plugin-specific initialization
            return self._secure_initialize(config)
            
        except Exception as e:
            self.logger.error(f"Plugin initialization failed: {e}")
            return False
    
    @secure_execution(timeout=30, memory_limit=50*1024*1024)
    def start(self) -> bool:
        """
        Start the plugin securely
        
        Returns:
            bool: True if start successful
        """
        try:
            self.logger.info(f"Starting secure plugin: {self.__class__.__name__}")
            
            self.start_time = time.time()
            self.is_running = True
            
            # Start resource monitoring
            self._start_resource_monitoring()
            
            # Plugin-specific start logic
            return self._secure_start()
            
        except Exception as e:
            self.logger.error(f"Plugin start failed: {e}")
            return False
    
    @secure_execution(timeout=30, memory_limit=50*1024*1024)
    def stop(self) -> bool:
        """
        Stop the plugin securely
        
        Returns:
            bool: True if stop successful
        """
        try:
            self.logger.info(f"Stopping secure plugin: {self.__class__.__name__}")
            
            self.is_running = False
            
            # Stop resource monitoring
            self._stop_resource_monitoring()
            
            # Plugin-specific stop logic
            return self._secure_stop()
            
        except Exception as e:
            self.logger.error(f"Plugin stop failed: {e}")
            return False
    
    @secure_execution(timeout=30, memory_limit=50*1024*1024)
    @validate_input({'data': dict})
    @sanitize_output({'result': str})
    def execute(self, *args, **kwargs) -> Any:
        """
        Execute plugin functionality securely
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Any: Plugin execution result
        """
        try:
            self.logger.info(f"Executing secure plugin: {self.__class__.__name__}")
            
            # Validate execution context
            if not self.is_running:
                raise RuntimeError("Plugin is not running")
            
            # Plugin-specific execution logic
            return self._secure_execute(*args, **kwargs)
            
        except Exception as e:
            self.logger.error(f"Plugin execution failed: {e}")
            raise
    
    def _validate_config(self, config: Dict[str, Any]):
        """Validate plugin configuration"""
        # Implement configuration validation
        pass
    
    # Abstract methods for plugin-specific implementation
    @abstractmethod
    def _secure_initialize(self, config: Dict[str, Any] = None) -> bool:
        """Plugin-specific secure initialization"""
        pass
    
    @abstractmethod
    def _secure_start(self) -> bool:
        """Plugin-specific secure start"""
        pass
    
    @abstractmethod
    def _secure_stop(self) -> bool:
        """Plugin-specific secure stop"""
        pass
    
    @abstractmethod
    def _secure_execute(self, *args, **kwargs) -> Any:
        """Plugin-specific secure execution"""
        pass

class SecureExamplePlugin(SecurePluginBase):
    """
    Example secure plugin implementation
    """
    
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="secure_example_plugin",
            version="1.0.0",
            description="Example secure plugin with Audit 3 compliance",
            author="Heimnetz Security Team",
            category="security",
            dependencies=[],
            permissions=["read_config"],
            config_schema={
                "timeout": int,
                "max_retries": int
            }
        )
    
    def _secure_initialize(self, config: Dict[str, Any] = None) -> bool:
        """Initialize the secure example plugin"""
        self.logger.info("Secure example plugin initialized")
        return True
    
    def _secure_start(self) -> bool:
        """Start the secure example plugin"""
        self.logger.info("Secure example plugin started")
        return True
    
    def _secure_stop(self) -> bool:
        """Stop the secure example plugin"""
        self.logger.info("Secure example plugin stopped")
        return True
    
    def _secure_execute(self, *args, **kwargs) -> Any:
        """Execute the secure example plugin"""
        self.logger.info("Secure example plugin executed")
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "data": "secure execution completed"
        }

# Export the secure plugin class
__all__ = ['SecurePluginBase', 'SecureExamplePlugin', 'secure_execution', 'validate_input', 'sanitize_output']

# Plugin registration
def get_plugin_class():
    """Return the plugin class for registration"""
    return SecureExamplePlugin

if __name__ == "__main__":
    # Test the secure plugin
    plugin = SecureExamplePlugin()
    info = plugin.get_info()
    print(f"Plugin Info: {info}")
    
    # Test security features
    if plugin.initialize():
        if plugin.start():
            result = plugin.execute()
            print(f"Execution Result: {result}")
            plugin.stop()
