# 🧑‍💻 Developer Guide - Enhanced Plugin Sandbox Isolation

**Target Audience**: Plugin developers, system integrators, DevOps engineers  
**Prerequisites**: Python 3.9+, basic async/await knowledge  
**Estimated Reading Time**: 20 minutes  

This guide provides step-by-step instructions for implementing and using the Enhanced Plugin Sandbox Isolation system in your applications.

## 📋 Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Implementation](#basic-implementation)  
3. [Advanced Configuration](#advanced-configuration)
4. [Monitoring Integration](#monitoring-integration)
5. [Error Handling](#error-handling)
6. [Performance Optimization](#performance-optimization)
7. [Best Practices](#best-practices)
8. [Common Patterns](#common-patterns)

---

## 🚀 Getting Started

### Step 1: Environment Setup

```bash
# Ensure Python 3.9+ is installed
python --version

# Install required dependencies
pip install asyncio dataclasses typing psutil

# Optional: Install watchdog for filesystem monitoring
pip install watchdog
```

### Step 2: Import Required Components

```python
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

# Core sandbox components
from plugin_sandbox_isolation_enhanced import (
    EnhancedPluginSandbox,
    EnhancedPluginFramework,
    IsolationConfig,
    IsolationLevel,
    SandboxViolationType
)

# Framework integration
from plugin_framework_v2 import (
    PluginLimitsV2,
    PluginPermissionsV2,
    SecurityLevel
)
```

### Step 3: Verify Installation

```python
async def test_installation():
    """Verify enhanced sandbox system is working"""
    try:
        # Basic configuration
        config = IsolationConfig(level=IsolationLevel.MINIMAL)
        limits = PluginLimitsV2(max_memory_mb=64, max_execution_time_seconds=10)
        permissions = PluginPermissionsV2()
        
        # Create sandbox
        sandbox = EnhancedPluginSandbox(limits, permissions, config)
        
        async with sandbox:
            def test_plugin(env):
                return {"status": "success", "message": "Installation verified"}
            
            result = await sandbox.execute_plugin_safe(test_plugin)
            print("✅ Enhanced sandbox system working correctly")
            print(f"Result: {result}")
            
    except Exception as e:
        print(f"❌ Installation issue: {e}")

# Run verification
if __name__ == "__main__":
    asyncio.run(test_installation())
```

---

## 🏗️ Basic Implementation

### Step 1: Create Your First Sandbox

```python
async def basic_sandbox_example():
    """Basic sandbox implementation example"""
    
    # Configure resource limits
    limits = PluginLimitsV2(
        max_memory_mb=128,           # 128MB memory limit
        max_execution_time_seconds=30, # 30 second timeout
        max_cpu_percent=50.0         # 50% CPU limit
    )
    
    # Configure permissions
    permissions = PluginPermissionsV2(
        allow_file_access=True,
        allow_network_access=False,  # Block network access
        security_level=SecurityLevel.MEDIUM
    )
    
    # Configure isolation
    config = IsolationConfig(
        level=IsolationLevel.STANDARD,
        enable_real_time_monitoring=True,
        resource_check_interval_seconds=1.0
    )
    
    # Create sandbox instance
    sandbox = EnhancedPluginSandbox(limits, permissions, config)
    
    # Execute plugin safely
    async with sandbox:
        def my_plugin(environment):
            # Your plugin logic here
            data_processed = []
            for i in range(100):
                data_processed.append(f"Item {i}")
            
            return {
                "status": "success",
                "processed_items": len(data_processed),
                "environment": environment
            }
        
        # Execute plugin
        try:
            result = await sandbox.execute_plugin_safe(my_plugin)
            print(f"Plugin result: {result}")
            
            # Get telemetry data
            telemetry = sandbox.get_telemetry()
            print(f"Peak memory usage: {telemetry.peak_memory_mb}MB")
            print(f"Execution time: {telemetry.end_time - telemetry.start_time}")
            
        except Exception as e:
            print(f"Plugin execution failed: {e}")
```

### Step 2: Handle Plugin Parameters

```python
async def parameterized_plugin_example():
    """Example of passing parameters to plugins"""
    
    sandbox = EnhancedPluginSandbox(limits, permissions, config)
    
    async with sandbox:
        def data_processor(environment, input_data, processing_mode="standard"):
            """Plugin that processes input data"""
            
            if processing_mode == "fast":
                # Quick processing
                result = [item.upper() for item in input_data]
            elif processing_mode == "detailed":
                # Detailed processing
                result = [{"original": item, "processed": item.upper()} for item in input_data]
            else:
                # Standard processing
                result = input_data
            
            return {
                "status": "success",
                "mode": processing_mode,
                "input_count": len(input_data),
                "output_count": len(result),
                "data": result
            }
        
        # Execute with parameters
        input_data = ["apple", "banana", "cherry"]
        result = await sandbox.execute_plugin_safe(
            data_processor, 
            input_data, 
            processing_mode="detailed"
        )
        
        print(f"Processed {result['input_count']} items")
```

---

## ⚙️ Advanced Configuration

### Isolation Levels Explained

```python
# MINIMAL: Basic sandboxing with minimal overhead
minimal_config = IsolationConfig(
    level=IsolationLevel.MINIMAL,
    enable_real_time_monitoring=False,  # Disabled for performance
    resource_check_interval_seconds=5.0  # Less frequent checks
)

# STANDARD: Balanced isolation and performance (recommended)
standard_config = IsolationConfig(
    level=IsolationLevel.STANDARD,
    enable_real_time_monitoring=True,
    enable_process_isolation=True,
    enable_filesystem_isolation=True,
    resource_check_interval_seconds=1.0
)

# STRICT: Enhanced security with higher overhead
strict_config = IsolationConfig(
    level=IsolationLevel.STRICT,
    enable_real_time_monitoring=True,
    enable_process_isolation=True,
    enable_network_isolation=True,
    enable_filesystem_isolation=True,
    violation_threshold=2,  # Lower threshold
    quarantine_on_violation=True,
    resource_check_interval_seconds=0.5  # More frequent checks
)

# MAXIMUM: Maximum security, highest overhead
maximum_config = IsolationConfig(
    level=IsolationLevel.MAXIMUM,
    enable_real_time_monitoring=True,
    enable_process_isolation=True,
    enable_network_isolation=True, 
    enable_filesystem_isolation=True,
    violation_threshold=1,  # Zero tolerance
    quarantine_on_violation=True,
    auto_recovery_enabled=True,
    resource_check_interval_seconds=0.1,  # Very frequent checks
    max_sandbox_lifetime_minutes=30  # Shorter lifetime
)
```

### Custom Configuration Example

```python
async def custom_configuration_example():
    """Example of advanced custom configuration"""
    
    # Custom limits for specific use case
    custom_limits = PluginLimitsV2(
        max_memory_mb=256,              # Higher memory for data processing
        max_execution_time_seconds=60,  # Longer execution time
        max_cpu_percent=80.0,           # Allow higher CPU usage
        max_file_operations=1000,       # Limit file operations
        max_network_requests=0          # Disable network completely
    )
    
    # Restrictive permissions
    restricted_permissions = PluginPermissionsV2(
        allow_file_access=True,
        allow_network_access=False,
        allowed_modules=["json", "datetime", "math"],  # Only specific modules
        blocked_modules=["os", "subprocess", "sys"],   # Block dangerous modules
        security_level=SecurityLevel.HIGH
    )
    
    # Custom isolation configuration  
    custom_config = IsolationConfig(
        level=IsolationLevel.STRICT,
        enable_real_time_monitoring=True,
        enable_process_isolation=True,
        enable_network_isolation=True,
        enable_filesystem_isolation=True,
        auto_recovery_enabled=True,
        violation_threshold=3,
        quarantine_on_violation=True,
        resource_check_interval_seconds=0.5,
        max_sandbox_lifetime_minutes=45,
        watchdog_timeout_seconds=20
    )
    
    sandbox = EnhancedPluginSandbox(custom_limits, restricted_permissions, custom_config)
    
    async with sandbox:
        def secure_data_processor(env):
            """Secure plugin with restricted capabilities"""
            import json
            import math
            from datetime import datetime
            
            # Process data safely
            data = {
                "timestamp": datetime.now().isoformat(),
                "calculation": math.sqrt(42),
                "status": "processed"
            }
            
            return json.dumps(data)
        
        result = await sandbox.execute_plugin_safe(secure_data_processor)
        print(f"Secure processing result: {result}")
```

---

## 📊 Monitoring Integration

### Real-time Monitoring Setup

```python
async def monitoring_integration_example():
    """Example of comprehensive monitoring integration"""
    
    # Enable all monitoring features
    monitoring_config = IsolationConfig(
        level=IsolationLevel.STANDARD,
        enable_real_time_monitoring=True,
        telemetry_enabled=True,
        resource_check_interval_seconds=0.5
    )
    
    sandbox = EnhancedPluginSandbox(limits, permissions, monitoring_config)
    
    async with sandbox:
        def monitored_plugin(env):
            """Plugin that demonstrates monitoring capabilities"""
            import time
            
            # Simulate various operations
            data = []
            
            # Memory usage simulation
            for i in range(1000):
                data.append(f"Data item {i}" * 10)
            
            # CPU usage simulation
            time.sleep(0.5)
            
            # File operations simulation
            temp_file = "/tmp/test_file.txt"
            with open(temp_file, "w") as f:
                f.write("Test data")
            
            return {
                "status": "success",
                "data_size": len(data),
                "operations": ["memory", "cpu", "file"]
            }
        
        # Execute with monitoring
        result = await sandbox.execute_plugin_safe(monitored_plugin)
        
        # Analyze telemetry
        telemetry = sandbox.get_telemetry()
        
        print("📊 Telemetry Data:")
        print(f"  Peak Memory: {telemetry.peak_memory_mb:.2f}MB")
        print(f"  Peak CPU: {telemetry.peak_cpu_percent:.1f}%")
        print(f"  File Operations: {telemetry.file_operations_count}")
        print(f"  Execution Time: {telemetry.end_time - telemetry.start_time}")
        print(f"  Resource Samples: {len(telemetry.resource_samples)}")
        
        # Check for violations
        violations = sandbox.get_violations()
        if violations:
            print(f"⚠️ Detected {len(violations)} violations:")
            for violation in violations:
                print(f"  - {violation.type.value}: {violation.message}")
```

### Custom Monitoring Callbacks

```python
class CustomMonitoringHandler:
    """Custom handler for monitoring events"""
    
    def on_resource_sample(self, sample: Dict[str, Any]):
        """Called for each resource sample"""
        if sample.get('memory_mb', 0) > 100:
            print(f"⚠️ High memory usage: {sample['memory_mb']:.1f}MB")
    
    def on_violation_detected(self, violation):
        """Called when violation is detected"""
        print(f"🚨 Violation: {violation.type.value} - {violation.message}")
    
    def on_sandbox_cleanup(self, telemetry):
        """Called during sandbox cleanup"""
        print(f"🧹 Cleaning up sandbox: {telemetry.sandbox_id}")

async def custom_monitoring_example():
    """Example of custom monitoring integration"""
    
    handler = CustomMonitoringHandler()
    
    # Configure with custom handler
    sandbox = EnhancedPluginSandbox(
        limits, permissions, config,
        monitoring_handler=handler  # If supported by implementation
    )
    
    async with sandbox:
        result = await sandbox.execute_plugin_safe(my_plugin)
```

---

## ⚠️ Error Handling

### Comprehensive Error Handling

```python
from plugin_sandbox_isolation_enhanced import (
    SandboxException,
    SandboxInitializationError,
    PluginExecutionError,
    SecurityViolationError,
    ResourceLimitExceededError
)

async def error_handling_example():
    """Comprehensive error handling example"""
    
    try:
        sandbox = EnhancedPluginSandbox(limits, permissions, config)
        
        async with sandbox:
            def problematic_plugin(env):
                # Simulate various types of problems
                import time
                import os
                
                # Memory leak simulation
                large_data = ["data" * 1000] * 10000  # Lots of memory
                
                # Long execution
                time.sleep(60)  # Exceeds time limit
                
                # Forbidden operation
                os.system("rm -rf /")  # Blocked by permissions
                
                return {"status": "success"}
            
            result = await sandbox.execute_plugin_safe(problematic_plugin)
            
    except SandboxInitializationError as e:
        print(f"❌ Sandbox initialization failed: {e}")
        
    except ResourceLimitExceededError as e:
        print(f"📊 Resource limit exceeded: {e}")
        print("Consider increasing resource limits or optimizing plugin")
        
    except SecurityViolationError as e:
        print(f"🔒 Security violation detected: {e}")
        print("Plugin attempted unauthorized operation")
        
    except PluginExecutionError as e:
        print(f"⚡ Plugin execution error: {e}")
        print("Check plugin code for bugs")
        
    except SandboxException as e:
        print(f"🏰 General sandbox error: {e}")
        
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        
    finally:
        # Always check telemetry for debugging
        if 'sandbox' in locals():
            telemetry = sandbox.get_telemetry()
            print(f"Debug info - Sandbox ID: {telemetry.sandbox_id}")
```

### Recovery Strategies

```python
async def recovery_strategy_example():
    """Example of implementing recovery strategies"""
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Adjust limits based on previous failures
            adjusted_limits = PluginLimitsV2(
                max_memory_mb=128 + (retry_count * 64),  # Increase memory each retry
                max_execution_time_seconds=30 + (retry_count * 15)  # Increase time
            )
            
            sandbox = EnhancedPluginSandbox(adjusted_limits, permissions, config)
            
            async with sandbox:
                result = await sandbox.execute_plugin_safe(my_plugin)
                print(f"✅ Success on attempt {retry_count + 1}")
                return result
                
        except ResourceLimitExceededError as e:
            retry_count += 1
            print(f"🔄 Retry {retry_count}/{max_retries} - Resource limit exceeded")
            
            if retry_count >= max_retries:
                print("❌ Max retries reached, plugin may be fundamentally incompatible")
                raise
                
        except SecurityViolationError:
            # Don't retry security violations
            print("🔒 Security violation - not retrying")
            raise
```

---

## ⚡ Performance Optimization

### Resource-Efficient Configuration

```python
# For high-throughput scenarios
high_throughput_config = IsolationConfig(
    level=IsolationLevel.MINIMAL,
    enable_real_time_monitoring=False,      # Disable for performance
    telemetry_enabled=False,                # Reduce overhead
    resource_check_interval_seconds=10.0    # Less frequent checks
)

# For batch processing
batch_processing_config = IsolationConfig(
    level=IsolationLevel.STANDARD,
    enable_real_time_monitoring=True,
    resource_check_interval_seconds=2.0,    # Moderate frequency
    max_sandbox_lifetime_minutes=120        # Longer lifetime for big jobs
)

# For interactive/development use
development_config = IsolationConfig(
    level=IsolationLevel.STRICT,
    enable_real_time_monitoring=True,
    telemetry_enabled=True,
    resource_check_interval_seconds=0.5,    # Frequent monitoring
    auto_recovery_enabled=True               # Auto-recovery for debugging
)
```

### Sandbox Pooling

```python
class SandboxPool:
    """Simple sandbox pool for high-throughput scenarios"""
    
    def __init__(self, pool_size: int = 5):
        self.pool_size = pool_size
        self.available_sandboxes = []
        self.in_use_sandboxes = set()
        
    async def initialize_pool(self):
        """Initialize sandbox pool"""
        for _ in range(self.pool_size):
            sandbox = EnhancedPluginSandbox(limits, permissions, config)
            await sandbox.__aenter__()
            self.available_sandboxes.append(sandbox)
    
    async def get_sandbox(self) -> EnhancedPluginSandbox:
        """Get sandbox from pool"""
        if not self.available_sandboxes:
            # Create new sandbox if pool is empty
            sandbox = EnhancedPluginSandbox(limits, permissions, config)
            await sandbox.__aenter__()
            return sandbox
        
        sandbox = self.available_sandboxes.pop()
        self.in_use_sandboxes.add(sandbox)
        return sandbox
    
    async def return_sandbox(self, sandbox: EnhancedPluginSandbox):
        """Return sandbox to pool"""
        if sandbox in self.in_use_sandboxes:
            self.in_use_sandboxes.remove(sandbox)
            # Reset sandbox state if needed
            self.available_sandboxes.append(sandbox)

# Usage example
pool = SandboxPool(pool_size=10)
await pool.initialize_pool()

sandbox = await pool.get_sandbox()
try:
    result = await sandbox.execute_plugin_safe(my_plugin)
finally:
    await pool.return_sandbox(sandbox)
```

---

## 🎯 Best Practices

### 1. Configuration Management

```python
# Use environment-specific configurations
def get_sandbox_config(environment: str) -> IsolationConfig:
    """Get configuration based on environment"""
    
    if environment == "development":
        return IsolationConfig(
            level=IsolationLevel.STRICT,
            enable_real_time_monitoring=True,
            telemetry_enabled=True,
            auto_recovery_enabled=True
        )
    
    elif environment == "testing":
        return IsolationConfig(
            level=IsolationLevel.STANDARD,
            enable_real_time_monitoring=True,
            telemetry_enabled=True
        )
    
    elif environment == "production":
        return IsolationConfig(
            level=IsolationLevel.MAXIMUM,
            enable_real_time_monitoring=True,
            violation_threshold=1,
            quarantine_on_violation=True,
            auto_recovery_enabled=False  # Manual intervention required
        )
    
    else:
        raise ValueError(f"Unknown environment: {environment}")
```

### 2. Logging Integration

```python
import logging

# Configure logging for sandbox operations
logging.basicConfig(level=logging.INFO)
sandbox_logger = logging.getLogger("enhanced_sandbox")

async def logged_plugin_execution(plugin_func, plugin_name: str):
    """Execute plugin with comprehensive logging"""
    
    sandbox_logger.info(f"Starting execution of plugin: {plugin_name}")
    
    try:
        sandbox = EnhancedPluginSandbox(limits, permissions, config)
        
        async with sandbox:
            start_time = datetime.now()
            result = await sandbox.execute_plugin_safe(plugin_func)
            end_time = datetime.now()
            
            telemetry = sandbox.get_telemetry()
            violations = sandbox.get_violations()
            
            # Log execution metrics
            sandbox_logger.info(f"Plugin '{plugin_name}' completed successfully")
            sandbox_logger.info(f"Execution time: {end_time - start_time}")
            sandbox_logger.info(f"Peak memory: {telemetry.peak_memory_mb:.2f}MB")
            
            if violations:
                sandbox_logger.warning(f"Plugin '{plugin_name}' had {len(violations)} violations")
                for violation in violations:
                    sandbox_logger.warning(f"Violation: {violation.type.value} - {violation.message}")
            
            return result
            
    except Exception as e:
        sandbox_logger.error(f"Plugin '{plugin_name}' execution failed: {e}")
        raise
```

### 3. Testing Integration

```python
import pytest

class TestPluginSandbox:
    """Test suite for plugin sandbox functionality"""
    
    @pytest.fixture
    def sandbox_config(self):
        """Test sandbox configuration"""
        return IsolationConfig(
            level=IsolationLevel.STANDARD,
            enable_real_time_monitoring=True,
            max_sandbox_lifetime_minutes=5  # Short lifetime for tests
        )
    
    @pytest.fixture
    def test_limits(self):
        """Test resource limits"""
        return PluginLimitsV2(
            max_memory_mb=64,
            max_execution_time_seconds=10
        )
    
    @pytest.mark.asyncio
    async def test_plugin_execution(self, test_limits, sandbox_config):
        """Test successful plugin execution"""
        
        def test_plugin(env):
            return {"status": "success", "data": "test"}
        
        permissions = PluginPermissionsV2()
        sandbox = EnhancedPluginSandbox(test_limits, permissions, sandbox_config)
        
        async with sandbox:
            result = await sandbox.execute_plugin_safe(test_plugin)
            assert result["status"] == "success"
            
            telemetry = sandbox.get_telemetry()
            assert telemetry.peak_memory_mb > 0
    
    @pytest.mark.asyncio 
    async def test_resource_violation(self, test_limits, sandbox_config):
        """Test resource limit violation handling"""
        
        def memory_intensive_plugin(env):
            # Use more memory than allowed
            large_data = ["x" * 1024] * 1024 * 100  # ~100MB
            return {"data_size": len(large_data)}
        
        permissions = PluginPermissionsV2()
        sandbox = EnhancedPluginSandbox(test_limits, permissions, sandbox_config)
        
        with pytest.raises(ResourceLimitExceededError):
            async with sandbox:
                await sandbox.execute_plugin_safe(memory_intensive_plugin)
```

---

## 🔄 Common Patterns

### Pattern 1: Plugin Factory

```python
class PluginExecutor:
    """Reusable plugin executor with consistent configuration"""
    
    def __init__(self, environment: str = "production"):
        self.config = get_sandbox_config(environment)
        self.default_limits = PluginLimitsV2(
            max_memory_mb=128,
            max_execution_time_seconds=30
        )
        self.default_permissions = PluginPermissionsV2(
            security_level=SecurityLevel.HIGH
        )
    
    async def execute_plugin(self, plugin_func, custom_limits=None, custom_permissions=None):
        """Execute plugin with default or custom configuration"""
        
        limits = custom_limits or self.default_limits
        permissions = custom_permissions or self.default_permissions
        
        sandbox = EnhancedPluginSandbox(limits, permissions, self.config)
        
        async with sandbox:
            return await sandbox.execute_plugin_safe(plugin_func)

# Usage
executor = PluginExecutor("production")
result = await executor.execute_plugin(my_plugin)
```

### Pattern 2: Plugin Pipeline

```python
async def plugin_pipeline(*plugins):
    """Execute multiple plugins in sequence with shared data"""
    
    pipeline_data = {"results": []}
    
    for i, plugin in enumerate(plugins):
        sandbox = EnhancedPluginSandbox(limits, permissions, config)
        
        async with sandbox:
            def pipeline_plugin(env):
                # Plugin has access to pipeline data
                return plugin(env, pipeline_data)
            
            result = await sandbox.execute_plugin_safe(pipeline_plugin)
            pipeline_data["results"].append({
                "step": i,
                "plugin": plugin.__name__,
                "result": result
            })
    
    return pipeline_data

# Usage
def step1(env, pipeline_data):
    return {"step1": "processed data"}

def step2(env, pipeline_data):
    previous = pipeline_data["results"][-1]["result"]
    return {"step2": f"enhanced {previous}"}

result = await plugin_pipeline(step1, step2)
```

### Pattern 3: Plugin Registry

```python
class PluginRegistry:
    """Registry for managing and executing named plugins"""
    
    def __init__(self):
        self.plugins = {}
        self.configurations = {}
    
    def register_plugin(self, name: str, plugin_func, config: IsolationConfig):
        """Register a plugin with specific configuration"""
        self.plugins[name] = plugin_func
        self.configurations[name] = config
    
    async def execute_registered_plugin(self, name: str, *args, **kwargs):
        """Execute a registered plugin"""
        
        if name not in self.plugins:
            raise ValueError(f"Plugin '{name}' not registered")
        
        plugin_func = self.plugins[name]
        config = self.configurations[name]
        
        sandbox = EnhancedPluginSandbox(limits, permissions, config)
        
        async with sandbox:
            return await sandbox.execute_plugin_safe(plugin_func, *args, **kwargs)

# Usage
registry = PluginRegistry()

registry.register_plugin("data_processor", data_processor_plugin, standard_config)
registry.register_plugin("security_scanner", security_plugin, strict_config)

result = await registry.execute_registered_plugin("data_processor", input_data)
```

---

## 📚 Additional Resources

- **[API Reference](api-reference.md)** - Complete API documentation
- **[Configuration Reference](configuration-reference.md)** - All configuration options
- **[Security Guide](security-guide.md)** - Security best practices
- **[Testing Guide](testing-guide.md)** - Testing strategies and examples
- **[Monitoring Guide](monitoring-guide.md)** - Telemetry and observability
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

---

**Next Steps**: Review the [Configuration Reference](configuration-reference.md) for detailed configuration options.
