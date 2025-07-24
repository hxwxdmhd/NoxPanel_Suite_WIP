# ⚙️ Configuration Reference - Enhanced Plugin Sandbox Isolation

**Version**: 2.5  
**Target Audience**: System administrators, DevOps engineers, security architects  

This document provides comprehensive reference for all configuration options in the Enhanced Plugin Sandbox Isolation system.

## 📋 Table of Contents

1. [IsolationConfig Reference](#isolationconfig-reference)
2. [PluginLimitsV2 Reference](#pluginlimitsv2-reference)
3. [PluginPermissionsV2 Reference](#pluginpermissionsv2-reference)
4. [Environment Variables](#environment-variables)
5. [Configuration Profiles](#configuration-profiles)
6. [Security Levels](#security-levels)
7. [Performance Tuning](#performance-tuning)

---

## 🏰 IsolationConfig Reference

The `IsolationConfig` class controls all aspects of sandbox isolation and monitoring.

### **Complete Parameter Reference**

```python
@dataclass
class IsolationConfig:
    # Core isolation settings
    level: IsolationLevel = IsolationLevel.STANDARD
    enable_process_isolation: bool = True
    enable_network_isolation: bool = True
    enable_filesystem_isolation: bool = True
    
    # Monitoring configuration
    enable_real_time_monitoring: bool = True
    telemetry_enabled: bool = True
    resource_check_interval_seconds: float = 1.0
    
    # Violation handling
    auto_recovery_enabled: bool = True
    violation_threshold: int = 3
    quarantine_on_violation: bool = True
    
    # Timeouts and limits
    watchdog_timeout_seconds: int = 30
    max_sandbox_lifetime_minutes: int = 60
```

### **Parameter Descriptions**

#### **Core Isolation Settings**

##### `level: IsolationLevel`
- **Default**: `IsolationLevel.STANDARD`
- **Values**: `MINIMAL`, `STANDARD`, `STRICT`, `MAXIMUM`
- **Description**: Base isolation level that affects all other settings
- **Impact**: Higher levels increase security but reduce performance

```python
# Example configurations for different levels
minimal = IsolationConfig(level=IsolationLevel.MINIMAL)    # ~1% overhead
standard = IsolationConfig(level=IsolationLevel.STANDARD)  # ~3% overhead  
strict = IsolationConfig(level=IsolationLevel.STRICT)      # ~7% overhead
maximum = IsolationConfig(level=IsolationLevel.MAXIMUM)    # ~15% overhead
```

##### `enable_process_isolation: bool`
- **Default**: `True`
- **Description**: Enable process-level isolation for plugins
- **Security Impact**: HIGH - Prevents plugin interference with host process
- **Performance Impact**: LOW (~1% overhead)

##### `enable_network_isolation: bool`  
- **Default**: `True`
- **Description**: Control and monitor network access from plugins
- **Security Impact**: HIGH - Prevents unauthorized network access
- **Performance Impact**: MEDIUM (~3% overhead)

##### `enable_filesystem_isolation: bool`
- **Default**: `True` 
- **Description**: Monitor and control filesystem access
- **Security Impact**: HIGH - Prevents unauthorized file access
- **Performance Impact**: MEDIUM (~5% overhead, requires `watchdog` library)

#### **Monitoring Configuration**

##### `enable_real_time_monitoring: bool`
- **Default**: `True`
- **Description**: Enable real-time resource usage monitoring
- **Benefits**: Violation detection, performance analysis, debugging
- **Performance Impact**: MEDIUM (~2-4% overhead)

```python
# Monitoring disabled for maximum performance
performance_config = IsolationConfig(
    enable_real_time_monitoring=False,
    telemetry_enabled=False
)

# Full monitoring for development
debug_config = IsolationConfig(
    enable_real_time_monitoring=True,
    telemetry_enabled=True,
    resource_check_interval_seconds=0.1  # Very frequent
)
```

##### `telemetry_enabled: bool`
- **Default**: `True`
- **Description**: Enable comprehensive telemetry data collection
- **Benefits**: Performance analysis, audit trails, debugging
- **Storage**: Telemetry data stored in memory during execution

##### `resource_check_interval_seconds: float`
- **Default**: `1.0`
- **Range**: `0.1` - `60.0` seconds
- **Description**: Interval between resource usage checks
- **Performance Trade-off**:
  - **Faster** (0.1-0.5s): Higher accuracy, more overhead
  - **Standard** (1.0-2.0s): Balanced accuracy and performance  
  - **Slower** (5.0-60.0s): Lower accuracy, minimal overhead

```python
# Real-time monitoring for critical applications
realtime_config = IsolationConfig(
    resource_check_interval_seconds=0.1,  # Check every 100ms
    violation_threshold=1  # Zero tolerance
)

# Background monitoring for batch processing
batch_config = IsolationConfig(
    resource_check_interval_seconds=5.0,  # Check every 5 seconds
    violation_threshold=5  # More tolerant
)
```

#### **Violation Handling**

##### `auto_recovery_enabled: bool`
- **Default**: `True`
- **Description**: Enable automatic recovery from violations
- **Recovery Actions**:
  - Garbage collection for memory violations
  - Process throttling for CPU violations
  - Temporary suspension for I/O violations

##### `violation_threshold: int`
- **Default**: `3`
- **Range**: `1` - `10`
- **Description**: Number of violations before escalated response
- **Escalation Actions**: Quarantine, termination, notification

```python
# Zero-tolerance configuration for production
zero_tolerance = IsolationConfig(
    violation_threshold=1,
    quarantine_on_violation=True,
    auto_recovery_enabled=False  # Manual intervention required
)

# Development-friendly configuration
development = IsolationConfig(
    violation_threshold=5,
    quarantine_on_violation=False,
    auto_recovery_enabled=True  # Auto-fix common issues
)
```

##### `quarantine_on_violation: bool`
- **Default**: `True`
- **Description**: Quarantine plugins after threshold violations
- **Quarantine Effects**: Plugin blocked from execution until manual review
- **Review Process**: Manual analysis of violations and plugin code

#### **Timeouts and Limits**

##### `watchdog_timeout_seconds: int`
- **Default**: `30`
- **Range**: `5` - `300` seconds  
- **Description**: Timeout for watchdog operations
- **Use Case**: Filesystem monitoring setup, network isolation setup

##### `max_sandbox_lifetime_minutes: int`
- **Default**: `60`
- **Range**: `1` - `1440` minutes (24 hours)
- **Description**: Maximum lifetime for a sandbox instance
- **Purpose**: Prevent resource leaks, force cleanup, security rotation

```python
# Short-lived sandboxes for web requests
web_config = IsolationConfig(
    max_sandbox_lifetime_minutes=5,  # 5 minutes max
    resource_check_interval_seconds=0.5
)

# Long-running sandboxes for data processing
batch_config = IsolationConfig(
    max_sandbox_lifetime_minutes=240,  # 4 hours max
    resource_check_interval_seconds=10.0
)
```

---

## 📊 PluginLimitsV2 Reference

Controls resource usage limits for plugin execution.

### **Complete Parameter Reference**

```python
@dataclass
class PluginLimitsV2:
    # Memory limits
    max_memory_mb: float = 128.0
    memory_warning_threshold_mb: float = 96.0  # 75% of max
    
    # Execution limits
    max_execution_time_seconds: int = 30
    execution_warning_threshold_seconds: int = 25  # 80% of max
    
    # CPU limits
    max_cpu_percent: float = 50.0
    cpu_warning_threshold_percent: float = 40.0  # 80% of max
    
    # I/O limits
    max_file_operations: int = 1000
    max_file_size_mb: float = 50.0
    max_network_requests: int = 10
    max_disk_usage_mb: float = 100.0
    
    # Advanced limits
    max_subprocess_count: int = 0  # 0 = no subprocesses allowed
    max_thread_count: int = 4
    max_open_files: int = 50
```

### **Sizing Guidelines**

#### **Memory Configuration**

```python
# Lightweight plugins (text processing, simple calculations)
lightweight_limits = PluginLimitsV2(
    max_memory_mb=32.0,
    memory_warning_threshold_mb=24.0
)

# Standard plugins (data processing, API calls)
standard_limits = PluginLimitsV2(
    max_memory_mb=128.0,
    memory_warning_threshold_mb=96.0
)

# Data-intensive plugins (file processing, analytics)
intensive_limits = PluginLimitsV2(
    max_memory_mb=512.0,
    memory_warning_threshold_mb=384.0
)

# Enterprise plugins (large dataset processing)
enterprise_limits = PluginLimitsV2(
    max_memory_mb=2048.0,
    memory_warning_threshold_mb=1536.0
)
```

#### **Execution Time Configuration**

```python
# Quick operations (validation, formatting)
quick_limits = PluginLimitsV2(
    max_execution_time_seconds=5,
    execution_warning_threshold_seconds=4
)

# Standard operations (API calls, file processing)  
standard_limits = PluginLimitsV2(
    max_execution_time_seconds=30,
    execution_warning_threshold_seconds=25
)

# Long-running operations (data analysis, reports)
longrunning_limits = PluginLimitsV2(
    max_execution_time_seconds=300,  # 5 minutes
    execution_warning_threshold_seconds=240
)

# Batch processing (scheduled tasks, bulk operations)
batch_limits = PluginLimitsV2(
    max_execution_time_seconds=3600,  # 1 hour
    execution_warning_threshold_seconds=3300
)
```

---

## 🔒 PluginPermissionsV2 Reference

Controls what operations plugins are allowed to perform.

### **Complete Parameter Reference**

```python
@dataclass
class PluginPermissionsV2:
    # File system permissions
    allow_file_access: bool = True
    allowed_directories: List[str] = field(default_factory=lambda: ["/tmp", "/var/tmp"])
    blocked_directories: List[str] = field(default_factory=lambda: ["/etc", "/usr", "/var"])
    allow_file_creation: bool = True
    allow_file_deletion: bool = False
    max_file_size_mb: float = 10.0
    
    # Network permissions
    allow_network_access: bool = False
    allowed_hosts: List[str] = field(default_factory=list)
    blocked_hosts: List[str] = field(default_factory=list)
    allowed_ports: List[int] = field(default_factory=lambda: [80, 443])
    
    # Module permissions  
    allowed_modules: List[str] = field(default_factory=list)  # Empty = all allowed
    blocked_modules: List[str] = field(default_factory=lambda: ["os", "subprocess"])
    
    # System permissions
    allow_subprocess_execution: bool = False
    allow_thread_creation: bool = True
    allow_environment_variables: bool = True
    
    # Security settings
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    require_code_signing: bool = False
    sandbox_user: Optional[str] = None
```

### **Security Profiles**

#### **Minimal Security (Development)**

```python
minimal_permissions = PluginPermissionsV2(
    allow_file_access=True,
    allow_network_access=True,
    allow_subprocess_execution=True,
    allowed_modules=[],  # All modules allowed
    blocked_modules=[],  # Nothing blocked
    security_level=SecurityLevel.LOW
)
```

#### **Standard Security (Production)**

```python
standard_permissions = PluginPermissionsV2(
    allow_file_access=True,
    allowed_directories=["/tmp", "/var/tmp", "/app/data"],
    blocked_directories=["/etc", "/usr", "/var", "/home"],
    allow_file_deletion=False,
    
    allow_network_access=False,  # No network by default
    
    blocked_modules=["os", "subprocess", "sys", "importlib"],
    
    allow_subprocess_execution=False,
    security_level=SecurityLevel.MEDIUM
)
```

#### **Maximum Security (Sensitive Operations)**

```python
maximum_permissions = PluginPermissionsV2(
    allow_file_access=True,
    allowed_directories=["/tmp/sandbox"],  # Very restricted
    blocked_directories=["*"],  # Block everything else
    allow_file_creation=True,
    allow_file_deletion=False,
    max_file_size_mb=1.0,  # Very small files only
    
    allow_network_access=False,  # No network access
    
    allowed_modules=["json", "datetime", "math", "random"],  # Only safe modules
    blocked_modules=["*"],  # Block everything else
    
    allow_subprocess_execution=False,
    allow_thread_creation=False,  # Single-threaded only
    
    security_level=SecurityLevel.MAXIMUM,
    require_code_signing=True,
    sandbox_user="sandbox_user"  # Run as restricted user
)
```

---

## 🌍 Environment Variables

Configure sandbox behavior through environment variables:

### **Core Configuration**

```bash
# Default isolation level
SANDBOX_ISOLATION_LEVEL=STANDARD  # MINIMAL|STANDARD|STRICT|MAXIMUM

# Enable/disable monitoring  
SANDBOX_MONITORING_ENABLED=true
SANDBOX_TELEMETRY_ENABLED=true

# Resource check frequency
SANDBOX_RESOURCE_CHECK_INTERVAL=1.0

# Violation handling
SANDBOX_VIOLATION_THRESHOLD=3
SANDBOX_AUTO_RECOVERY=true
SANDBOX_QUARANTINE_ENABLED=true
```

### **Performance Tuning**

```bash
# Memory configuration
SANDBOX_DEFAULT_MEMORY_MB=128
SANDBOX_MAX_MEMORY_MB=1024

# Execution limits
SANDBOX_DEFAULT_TIMEOUT_SECONDS=30
SANDBOX_MAX_TIMEOUT_SECONDS=300

# Monitoring optimization
SANDBOX_MONITORING_THREADS=2
SANDBOX_TELEMETRY_BUFFER_SIZE=1000
```

### **Security Configuration**

```bash
# Security settings
SANDBOX_SECURITY_LEVEL=MEDIUM  # LOW|MEDIUM|HIGH|MAXIMUM
SANDBOX_REQUIRE_CODE_SIGNING=false
SANDBOX_SANDBOX_USER=sandbox

# Directory restrictions
SANDBOX_ALLOWED_DIRS=/tmp,/var/tmp
SANDBOX_BLOCKED_DIRS=/etc,/usr,/var

# Module restrictions
SANDBOX_BLOCKED_MODULES=os,subprocess,sys
```

### **Development Configuration**

```bash
# Debug settings
SANDBOX_DEBUG_MODE=false
SANDBOX_LOG_LEVEL=INFO  # DEBUG|INFO|WARNING|ERROR

# Testing configuration
SANDBOX_TEST_MODE=false
SANDBOX_MOCK_VIOLATIONS=false
```

---

## 📋 Configuration Profiles

Pre-defined configuration profiles for common use cases:

### **Profile: Web Application Plugins**

```python
def get_web_app_config() -> Tuple[IsolationConfig, PluginLimitsV2, PluginPermissionsV2]:
    """Configuration optimized for web application plugins"""
    
    config = IsolationConfig(
        level=IsolationLevel.STANDARD,
        enable_real_time_monitoring=True,
        resource_check_interval_seconds=0.5,  # Responsive monitoring
        violation_threshold=2,  # Quick response to violations
        max_sandbox_lifetime_minutes=10  # Short-lived for web requests
    )
    
    limits = PluginLimitsV2(
        max_memory_mb=64.0,  # Moderate memory for web plugins
        max_execution_time_seconds=15,  # Quick execution for web responsiveness
        max_cpu_percent=30.0,  # Don't impact web server performance
        max_file_operations=100,  # Limited file operations
        max_network_requests=5  # Allow some external API calls
    )
    
    permissions = PluginPermissionsV2(
        allow_file_access=True,
        allowed_directories=["/tmp/web_plugins"],
        allow_network_access=True,
        allowed_hosts=["api.example.com", "cdn.example.com"],
        allowed_ports=[80, 443],
        blocked_modules=["os", "subprocess"],
        security_level=SecurityLevel.MEDIUM
    )
    
    return config, limits, permissions
```

### **Profile: Data Processing Batch Jobs**

```python
def get_batch_processing_config() -> Tuple[IsolationConfig, PluginLimitsV2, PluginPermissionsV2]:
    """Configuration optimized for batch data processing"""
    
    config = IsolationConfig(
        level=IsolationLevel.STANDARD,
        enable_real_time_monitoring=True,
        resource_check_interval_seconds=5.0,  # Less frequent for batch jobs
        violation_threshold=5,  # More tolerant for long-running jobs
        max_sandbox_lifetime_minutes=240  # 4 hours for batch processing
    )
    
    limits = PluginLimitsV2(
        max_memory_mb=1024.0,  # High memory for data processing
        max_execution_time_seconds=3600,  # 1 hour execution time
        max_cpu_percent=80.0,  # Can use most CPU for batch jobs
        max_file_operations=10000,  # Many file operations expected
        max_disk_usage_mb=500.0,  # Temporary storage for processing
        max_network_requests=0  # No network access for security
    )
    
    permissions = PluginPermissionsV2(
        allow_file_access=True,
        allowed_directories=["/data/processing", "/tmp/batch"],
        allow_file_creation=True,
        allow_file_deletion=True,  # Cleanup temporary files
        allow_network_access=False,  # Isolated processing
        blocked_modules=["os", "subprocess"],
        security_level=SecurityLevel.HIGH
    )
    
    return config, limits, permissions
```

### **Profile: Development and Testing**

```python
def get_development_config() -> Tuple[IsolationConfig, PluginLimitsV2, PluginPermissionsV2]:
    """Configuration optimized for development and testing"""
    
    config = IsolationConfig(
        level=IsolationLevel.STRICT,  # Strict monitoring for development
        enable_real_time_monitoring=True,
        telemetry_enabled=True,
        resource_check_interval_seconds=0.5,
        auto_recovery_enabled=True,  # Auto-fix for development convenience
        violation_threshold=3,
        max_sandbox_lifetime_minutes=30  # Medium lifetime for development
    )
    
    limits = PluginLimitsV2(
        max_memory_mb=256.0,  # Generous memory for development
        max_execution_time_seconds=60,  # Longer execution for debugging
        max_cpu_percent=70.0,  # Can use CPU for intensive development tasks
        max_file_operations=5000,
        max_network_requests=20  # Allow external API testing
    )
    
    permissions = PluginPermissionsV2(
        allow_file_access=True,
        allowed_directories=["/tmp/dev", "/app/test_data", "/var/log/dev"],
        allow_network_access=True,
        allowed_hosts=["*"],  # Allow all hosts for testing
        blocked_modules=["os"],  # Block only dangerous modules
        allow_thread_creation=True,
        security_level=SecurityLevel.MEDIUM
    )
    
    return config, limits, permissions
```

### **Profile: High-Security Enterprise**

```python
def get_enterprise_security_config() -> Tuple[IsolationConfig, PluginLimitsV2, PluginPermissionsV2]:
    """Configuration optimized for high-security enterprise environments"""
    
    config = IsolationConfig(
        level=IsolationLevel.MAXIMUM,  # Maximum security
        enable_real_time_monitoring=True,
        enable_process_isolation=True,
        enable_network_isolation=True,
        enable_filesystem_isolation=True,
        resource_check_interval_seconds=0.5,  # Frequent monitoring
        auto_recovery_enabled=False,  # Manual intervention required
        violation_threshold=1,  # Zero tolerance
        quarantine_on_violation=True,
        max_sandbox_lifetime_minutes=60
    )
    
    limits = PluginLimitsV2(
        max_memory_mb=128.0,  # Conservative memory limits
        max_execution_time_seconds=30,  # Conservative execution time
        max_cpu_percent=25.0,  # Conservative CPU usage
        max_file_operations=100,  # Very limited file operations
        max_file_size_mb=1.0,  # Small file sizes only
        max_network_requests=0,  # No network access
        max_subprocess_count=0,  # No subprocesses
        max_thread_count=1,  # Single-threaded only
        max_open_files=10  # Very limited file handles
    )
    
    permissions = PluginPermissionsV2(
        allow_file_access=True,
        allowed_directories=["/tmp/enterprise_sandbox"],  # Single restricted directory
        blocked_directories=["*"],  # Block everything else
        allow_file_creation=True,
        allow_file_deletion=False,  # No deletion allowed
        max_file_size_mb=1.0,  # Small files only
        
        allow_network_access=False,  # No network access
        
        allowed_modules=["json", "datetime", "math"],  # Only essential modules
        blocked_modules=["*"],  # Block everything else
        
        allow_subprocess_execution=False,
        allow_thread_creation=False,
        allow_environment_variables=False,  # No environment access
        
        security_level=SecurityLevel.MAXIMUM,
        require_code_signing=True,
        sandbox_user="enterprise_sandbox"
    )
    
    return config, limits, permissions
```

---

## ⚡ Performance Tuning

### **Monitoring Overhead by Configuration**

| Configuration | CPU Overhead | Memory Overhead | I/O Overhead |
|--------------|--------------|-----------------|--------------|
| **Minimal** | ~1% | ~5MB | ~2% |
| **Standard** | ~3% | ~10MB | ~5% |
| **Strict** | ~7% | ~20MB | ~10% |
| **Maximum** | ~15% | ~50MB | ~20% |

### **Performance Optimization Guidelines**

#### **High-Throughput Scenarios**

```python
# Optimize for maximum throughput
high_throughput_config = IsolationConfig(
    level=IsolationLevel.MINIMAL,
    enable_real_time_monitoring=False,  # Disable for performance
    telemetry_enabled=False,  # Reduce memory usage
    resource_check_interval_seconds=10.0  # Infrequent checks
)
```

#### **Low-Latency Scenarios**

```python
# Optimize for minimum latency
low_latency_config = IsolationConfig(
    level=IsolationLevel.STANDARD,
    enable_real_time_monitoring=True,  # Enable for safety
    resource_check_interval_seconds=2.0,  # Balanced monitoring
    max_sandbox_lifetime_minutes=5  # Quick cleanup
)
```

#### **Resource-Constrained Environments**

```python
# Optimize for limited resources
constrained_config = IsolationConfig(
    level=IsolationLevel.MINIMAL,
    enable_real_time_monitoring=False,
    telemetry_enabled=False,
    resource_check_interval_seconds=30.0,  # Very infrequent
    max_sandbox_lifetime_minutes=120  # Longer lifetime to reduce overhead
)

constrained_limits = PluginLimitsV2(
    max_memory_mb=32.0,  # Very conservative
    max_execution_time_seconds=10,
    max_cpu_percent=20.0,
    max_file_operations=50
)
```

---

## 📚 Usage Examples

### **Loading Configuration from File**

```python
import yaml
from pathlib import Path

def load_config_from_file(config_file: str) -> IsolationConfig:
    """Load isolation configuration from YAML file"""
    
    config_path = Path(config_file)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    
    with open(config_path) as f:
        config_data = yaml.safe_load(f)
    
    return IsolationConfig(**config_data.get('isolation', {}))

# Example YAML configuration file
yaml_config = """
isolation:
  level: STANDARD
  enable_real_time_monitoring: true
  resource_check_interval_seconds: 1.0
  violation_threshold: 3
  max_sandbox_lifetime_minutes: 60

limits:
  max_memory_mb: 128.0
  max_execution_time_seconds: 30
  max_cpu_percent: 50.0

permissions:
  allow_file_access: true
  allow_network_access: false
  security_level: MEDIUM
"""
```

### **Dynamic Configuration Based on Plugin Type**

```python
def get_plugin_config(plugin_type: str) -> Tuple[IsolationConfig, PluginLimitsV2, PluginPermissionsV2]:
    """Get configuration based on plugin type"""
    
    if plugin_type == "web_api":
        return get_web_app_config()
    elif plugin_type == "data_processing":
        return get_batch_processing_config()
    elif plugin_type == "security_scan":
        return get_enterprise_security_config()
    elif plugin_type == "development":
        return get_development_config()
    else:
        # Default configuration
        return (
            IsolationConfig(),
            PluginLimitsV2(),
            PluginPermissionsV2()
        )
```

---

**Next**: Continue with the [Security Guide](security-guide.md) for security best practices and guidelines.
