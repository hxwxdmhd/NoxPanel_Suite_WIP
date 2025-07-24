# 📖 API Reference - Enhanced Plugin Sandbox Isolation

**Version**: 2.5  
**Module**: `plugin_sandbox_isolation_enhanced`  

This document provides complete API documentation for all classes, methods, and functions in the Enhanced Plugin Sandbox Isolation system.

## 📋 Table of Contents

- [Core Classes](#core-classes)
- [Configuration Classes](#configuration-classes)  
- [Monitoring Classes](#monitoring-classes)
- [Recovery Classes](#recovery-classes)
- [Utility Classes](#utility-classes)
- [Enumerations](#enumerations)
- [Data Classes](#data-classes)
- [Exceptions](#exceptions)

---

## 🏗️ Core Classes

### `EnhancedPluginSandbox`

The main sandbox class providing advanced isolation and monitoring capabilities.

#### **Constructor**

```python
EnhancedPluginSandbox(
    limits: PluginLimitsV2,
    permissions: PluginPermissionsV2,
    config: IsolationConfig,
    sandbox_id: Optional[str] = None
)
```

**Parameters:**
- `limits` (`PluginLimitsV2`): Resource limits for the sandbox
- `permissions` (`PluginPermissionsV2`): Permission settings
- `config` (`IsolationConfig`): Isolation configuration
- `sandbox_id` (`Optional[str]`): Unique sandbox identifier (auto-generated if None)

#### **Methods**

##### `async def __aenter__(self) -> 'EnhancedPluginSandbox'`
Async context manager entry. Initializes sandbox environment.

**Returns:** Self instance for context management

**Raises:**
- `SandboxInitializationError`: If sandbox setup fails
- `ResourceError`: If required resources unavailable

##### `async def __aexit__(self, exc_type, exc_val, exc_tb) -> None`
Async context manager exit. Cleans up sandbox environment.

**Parameters:**
- `exc_type`: Exception type if error occurred
- `exc_val`: Exception value if error occurred  
- `exc_tb`: Exception traceback if error occurred

##### `async def execute_plugin_safe(self, plugin_function: Callable, *args, **kwargs) -> Any`
Execute a plugin function safely within the sandbox.

**Parameters:**
- `plugin_function` (`Callable`): The plugin function to execute
- `*args`: Positional arguments for the plugin function
- `**kwargs`: Keyword arguments for the plugin function

**Returns:** Plugin function result

**Raises:**
- `PluginExecutionError`: If plugin execution fails
- `SecurityViolationError`: If security violation detected
- `ResourceLimitExceededError`: If resource limits exceeded

##### `def get_telemetry(self) -> SandboxTelemetry`
Get comprehensive sandbox telemetry data.

**Returns:** `SandboxTelemetry` object with monitoring data

##### `def get_violations(self) -> List[SandboxViolation]`
Get list of detected violations.

**Returns:** List of `SandboxViolation` objects

##### `async def cleanup_sandbox(self) -> bool`
Manually trigger sandbox cleanup.

**Returns:** `True` if cleanup successful, `False` otherwise

---

### `EnhancedPluginFramework`

Enhanced plugin framework with integrated sandbox isolation.

#### **Constructor**

```python
EnhancedPluginFramework(
    plugin_dir: str,
    config: Optional[IsolationConfig] = None
)
```

**Parameters:**
- `plugin_dir` (`str`): Directory containing plugins
- `config` (`Optional[IsolationConfig]`): Default isolation configuration

#### **Methods**

##### `async def load_plugin_enhanced(self, plugin_id: str, config: Optional[IsolationConfig] = None) -> Dict[str, Any]`
Load and execute plugin with enhanced isolation.

**Parameters:**
- `plugin_id` (`str`): Plugin identifier
- `config` (`Optional[IsolationConfig]`): Custom isolation config (uses default if None)

**Returns:** Dictionary containing plugin result and execution metadata

##### `def get_framework_telemetry(self) -> Dict[str, Any]`
Get framework-level telemetry and statistics.

**Returns:** Dictionary with framework metrics

---

## ⚙️ Configuration Classes

### `IsolationConfig`

Configuration class for sandbox isolation settings.

#### **Attributes**

```python
@dataclass
class IsolationConfig:
    level: IsolationLevel = IsolationLevel.STANDARD
    enable_process_isolation: bool = True
    enable_network_isolation: bool = True
    enable_filesystem_isolation: bool = True
    enable_real_time_monitoring: bool = True
    auto_recovery_enabled: bool = True
    violation_threshold: int = 3
    quarantine_on_violation: bool = True
    telemetry_enabled: bool = True
    watchdog_timeout_seconds: int = 30
    resource_check_interval_seconds: float = 1.0
    max_sandbox_lifetime_minutes: int = 60
```

**Attribute Descriptions:**
- `level`: Base isolation level (MINIMAL, STANDARD, STRICT, MAXIMUM)
- `enable_process_isolation`: Enable process-level isolation
- `enable_network_isolation`: Enable network access control
- `enable_filesystem_isolation`: Enable filesystem monitoring
- `enable_real_time_monitoring`: Enable real-time resource monitoring
- `auto_recovery_enabled`: Enable automatic recovery from violations
- `violation_threshold`: Number of violations before escalated response
- `quarantine_on_violation`: Quarantine plugins after threshold violations
- `telemetry_enabled`: Enable telemetry data collection
- `watchdog_timeout_seconds`: Timeout for watchdog operations
- `resource_check_interval_seconds`: Interval between resource checks
- `max_sandbox_lifetime_minutes`: Maximum sandbox lifetime

---

## 📊 Monitoring Classes

### `EnhancedResourceMonitor`

Real-time resource monitoring and enforcement.

#### **Constructor**

```python
EnhancedResourceMonitor(
    limits: PluginLimitsV2,
    config: IsolationConfig
)
```

#### **Methods**

##### `def start_monitoring(self, process_id: Optional[int] = None) -> None`
Start resource monitoring for specified process.

**Parameters:**
- `process_id` (`Optional[int]`): Process ID to monitor (current process if None)

##### `def stop_monitoring(self) -> None`
Stop resource monitoring and cleanup.

##### `def get_current_stats(self) -> Dict[str, Any]`
Get current resource usage statistics.

**Returns:** Dictionary with current CPU, memory, and I/O usage

##### `def check_violations(self) -> List[SandboxViolation]`
Check for resource limit violations.

**Returns:** List of current violations

---

### `FilesystemWatchdog`

Filesystem monitoring and access control.

#### **Constructor**

```python
FilesystemWatchdog(
    sandbox_directory: str,
    config: IsolationConfig
)
```

#### **Methods**

##### `def start_watching(self) -> bool`
Start filesystem monitoring.

**Returns:** `True` if monitoring started successfully

##### `def stop_watching(self) -> None`
Stop filesystem monitoring.

##### `def get_file_operations(self) -> List[Dict[str, Any]]`
Get list of monitored file operations.

**Returns:** List of file operation records

---

### `NetworkIsolationManager`

Network isolation and monitoring.

#### **Constructor**

```python
NetworkIsolationManager(config: IsolationConfig)
```

#### **Methods**

##### `def enable_isolation(self) -> bool`
Enable network isolation.

**Returns:** `True` if isolation enabled successfully

##### `def disable_isolation(self) -> None`
Disable network isolation.

##### `def get_network_activity(self) -> List[Dict[str, Any]]`
Get network activity log.

**Returns:** List of network operation records

---

## 🔧 Recovery Classes

### `SandboxRecoveryManager`

Automatic recovery and rollback management.

#### **Constructor**

```python
SandboxRecoveryManager(config: Optional[IsolationConfig] = None)
```

#### **Methods**

##### `async def auto_recovery_violation(self, violation: SandboxViolation) -> bool`
Attempt automatic recovery from violation.

**Parameters:**
- `violation` (`SandboxViolation`): The violation to recover from

**Returns:** `True` if recovery successful

##### `def quarantine_plugin(self, plugin_id: str, reason: str) -> None`
Quarantine a problematic plugin.

**Parameters:**
- `plugin_id` (`str`): Plugin identifier
- `reason` (`str`): Reason for quarantine

##### `def get_recovery_history(self) -> List[Dict[str, Any]]`
Get history of recovery actions.

**Returns:** List of recovery action records

---

## 🔢 Enumerations

### `IsolationLevel`

Enumeration of available isolation levels.

```python
class IsolationLevel(Enum):
    MINIMAL = "minimal"      # Basic sandboxing, minimal overhead
    STANDARD = "standard"    # Balanced isolation and performance
    STRICT = "strict"        # Enhanced security, higher overhead
    MAXIMUM = "maximum"      # Maximum security, highest overhead
```

### `SandboxViolationType`

Types of sandbox violations.

```python
class SandboxViolationType(Enum):
    RESOURCE_EXCEEDED = "resource_exceeded"
    FILESYSTEM_VIOLATION = "filesystem_violation" 
    NETWORK_VIOLATION = "network_violation"
    EXECUTION_TIMEOUT = "execution_timeout"
    PERMISSION_DENIED = "permission_denied"
    SECURITY_BREACH = "security_breach"
```

---

## 📊 Data Classes

### `SandboxTelemetry`

Comprehensive telemetry data container.

```python
@dataclass
class SandboxTelemetry:
    sandbox_id: str
    plugin_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    peak_memory_mb: float = 0.0
    peak_cpu_percent: float = 0.0
    file_operations_count: int = 0
    network_operations_count: int = 0
    violations: List[SandboxViolation] = field(default_factory=list)
    resource_samples: List[Dict[str, Any]] = field(default_factory=list)
    process_hierarchy: List[Dict[str, Any]] = field(default_factory=list)
    exit_code: Optional[int] = None
    exit_reason: str = ""
    cleanup_successful: bool = False
```

### `SandboxViolation`

Violation record data container.

```python
@dataclass
class SandboxViolation:
    type: SandboxViolationType
    message: str
    timestamp: datetime
    severity: str = "warning"
    details: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    auto_recovery_attempted: bool = False
```

---

## ⚠️ Exceptions

### `SandboxException`

Base exception for sandbox-related errors.

```python
class SandboxException(Exception):
    """Base exception for sandbox operations"""
    pass
```

### `SandboxInitializationError`

Exception raised when sandbox initialization fails.

```python
class SandboxInitializationError(SandboxException):
    """Raised when sandbox fails to initialize"""
    pass
```

### `PluginExecutionError`

Exception raised when plugin execution fails.

```python
class PluginExecutionError(SandboxException):
    """Raised when plugin execution encounters an error"""
    pass
```

### `SecurityViolationError`

Exception raised when security violation is detected.

```python
class SecurityViolationError(SandboxException):
    """Raised when security violation is detected"""
    pass
```

### `ResourceLimitExceededError`

Exception raised when resource limits are exceeded.

```python
class ResourceLimitExceededError(SandboxException):
    """Raised when resource limits are exceeded"""
    pass
```

---

## 🧪 Example Usage Patterns

### **Basic Sandbox Usage**

```python
async def basic_example():
    config = IsolationConfig(level=IsolationLevel.STANDARD)
    limits = PluginLimitsV2(max_memory_mb=128)
    permissions = PluginPermissionsV2()
    
    sandbox = EnhancedPluginSandbox(limits, permissions, config)
    
    async with sandbox:
        result = await sandbox.execute_plugin_safe(my_plugin_function)
        telemetry = sandbox.get_telemetry()
```

### **Advanced Monitoring Configuration**

```python
async def monitoring_example():
    config = IsolationConfig(
        level=IsolationLevel.STRICT,
        enable_real_time_monitoring=True,
        resource_check_interval_seconds=0.5,
        violation_threshold=2
    )
    
    sandbox = EnhancedPluginSandbox(limits, permissions, config)
    
    async with sandbox:
        result = await sandbox.execute_plugin_safe(my_plugin)
        violations = sandbox.get_violations()
        
        if violations:
            print(f"Detected {len(violations)} violations")
```

### **Recovery Management**

```python
async def recovery_example():
    recovery_manager = SandboxRecoveryManager()
    
    # Handle violations
    for violation in violations:
        success = await recovery_manager.auto_recovery_violation(violation)
        if not success:
            recovery_manager.quarantine_plugin(plugin_id, "Auto-recovery failed")
```

---

## 📚 Type Hints Reference

All classes and methods include comprehensive type hints for development tooling support:

```python
from typing import Optional, List, Dict, Any, Callable, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
```

---

**Next**: Continue with the [Developer Guide](developer-guide.md) for implementation examples.
