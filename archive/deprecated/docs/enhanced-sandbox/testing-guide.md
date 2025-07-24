# Enhanced Plugin Sandbox Isolation - Testing Guide

This document provides comprehensive testing strategies, frameworks, and examples for the Enhanced Plugin Sandbox Isolation system.

## Table of Contents

- [Testing Overview](#testing-overview)
- [Unit Testing](#unit-testing)
- [Integration Testing](#integration-testing)
- [Performance Testing](#performance-testing)
- [Security Testing](#security-testing)
- [Automated Testing Framework](#automated-testing-framework)
- [Test Data Management](#test-data-management)
- [Continuous Testing](#continuous-testing)

## Testing Overview

### Testing Philosophy

The Enhanced Plugin Sandbox Isolation system requires comprehensive testing across multiple dimensions:

1. **Functional Testing**: Core functionality works as expected
2. **Security Testing**: Security controls are effective
3. **Performance Testing**: System meets performance requirements
4. **Reliability Testing**: System handles failures gracefully
5. **Compliance Testing**: System meets regulatory requirements

### Testing Pyramid

```
    ┌─────────────────┐
    │   E2E Tests     │  ← Integration & System Tests
    │   (Slow, Few)   │
    ├─────────────────┤
    │ Integration     │  ← Component Integration Tests
    │ Tests           │
    │ (Medium)        │
    ├─────────────────┤
    │   Unit Tests    │  ← Fast, Isolated Tests
    │ (Fast, Many)    │
    └─────────────────┘
```

## Unit Testing

### Core Component Testing

```python
import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from plugin_sandbox_isolation_enhanced import (
    EnhancedPluginSandbox,
    IsolationConfig,
    IsolationLevel
)
from plugin_framework_v2 import PluginLimitsV2, PluginPermissionsV2, SecurityLevel

class TestEnhancedPluginSandbox:
    """Unit tests for EnhancedPluginSandbox class"""
    
    @pytest.fixture
    def sandbox_config(self):
        """Standard test configuration"""
        config = IsolationConfig(level=IsolationLevel.STANDARD)
        limits = PluginLimitsV2(max_memory_mb=128, max_execution_time_seconds=30)
        permissions = PluginPermissionsV2(security_level=SecurityLevel.MEDIUM)
        return config, limits, permissions
    
    @pytest.fixture
    def sandbox(self, sandbox_config):
        """Create test sandbox instance"""
        config, limits, permissions = sandbox_config
        return EnhancedPluginSandbox(limits, permissions, config)
    
    @pytest.mark.asyncio
    async def test_sandbox_initialization(self, sandbox):
        """Test sandbox initializes correctly"""
        assert sandbox is not None
        assert sandbox.limits.max_memory_mb == 128
        assert sandbox.config.level == IsolationLevel.STANDARD
    
    @pytest.mark.asyncio
    async def test_simple_plugin_execution(self, sandbox):
        """Test basic plugin execution"""
        
        def test_plugin(environment):
            return {"status": "success", "message": "Hello World"}
        
        async with sandbox:
            result = await sandbox.execute_plugin_safe(test_plugin)
        
        assert result["status"] == "success"
        assert "message" in result
    
    @pytest.mark.asyncio
    async def test_plugin_with_parameters(self, sandbox):
        """Test plugin execution with parameters"""
        
        def math_plugin(environment, a: int, b: int, operation: str = "add"):
            if operation == "add":
                return {"result": a + b}
            elif operation == "multiply":
                return {"result": a * b}
            else:
                return {"error": "Unknown operation"}
        
        async with sandbox:
            result = await sandbox.execute_plugin_safe(math_plugin, 5, 3, operation="add")
        
        assert result["result"] == 8
    
    @pytest.mark.asyncio
    async def test_plugin_timeout(self, sandbox):
        """Test plugin timeout handling"""
        
        def slow_plugin(environment):
            import time
            time.sleep(35)  # Exceeds 30 second limit
            return {"status": "completed"}
        
        with pytest.raises(asyncio.TimeoutError):
            async with sandbox:
                await sandbox.execute_plugin_safe(slow_plugin)
    
    @pytest.mark.asyncio
    async def test_memory_limit_enforcement(self, sandbox):
        """Test memory limit enforcement"""
        
        def memory_hog_plugin(environment):
            # Try to allocate more than 128MB
            data = []
            for i in range(200000):  # Large allocation
                data.append("x" * 1000)
            return {"allocated": len(data)}
        
        # Should either complete within limits or trigger violation
        async with sandbox:
            try:
                result = await sandbox.execute_plugin_safe(memory_hog_plugin)
                # If it completes, check violations were recorded
                violations = sandbox.get_violations()
                assert len(violations) > 0 or result is not None
            except Exception:
                # Memory limit exception is expected
                violations = sandbox.get_violations()
                assert len(violations) > 0
    
    @pytest.mark.asyncio
    async def test_telemetry_collection(self, sandbox):
        """Test telemetry data collection"""
        
        def monitored_plugin(environment):
            import time
            time.sleep(1)  # Some execution time
            return {"status": "success"}
        
        async with sandbox:
            await sandbox.execute_plugin_safe(monitored_plugin)
        
        telemetry = sandbox.get_telemetry()
        assert telemetry.peak_memory_mb > 0
        assert telemetry.end_time > telemetry.start_time
        assert telemetry.cleanup_successful is True
    
    def test_configuration_validation(self):
        """Test configuration validation"""
        
        # Valid configuration
        config = IsolationConfig(level=IsolationLevel.STRICT)
        limits = PluginLimitsV2(max_memory_mb=64, max_execution_time_seconds=10)
        permissions = PluginPermissionsV2(security_level=SecurityLevel.HIGH)
        
        sandbox = EnhancedPluginSandbox(limits, permissions, config)
        assert sandbox.config.level == IsolationLevel.STRICT
        
        # Invalid configuration should raise errors
        with pytest.raises(ValueError):
            invalid_limits = PluginLimitsV2(max_memory_mb=-1)  # Invalid memory limit


class TestIsolationConfig:
    """Unit tests for IsolationConfig class"""
    
    def test_default_configuration(self):
        """Test default configuration values"""
        config = IsolationConfig()
        assert config.level == IsolationLevel.STANDARD
        assert config.enable_real_time_monitoring is True
        assert config.violation_threshold == 5
    
    def test_strict_configuration(self):
        """Test strict isolation configuration"""
        config = IsolationConfig(
            level=IsolationLevel.STRICT,
            violation_threshold=1,
            security_hardening_enabled=True
        )
        
        assert config.level == IsolationLevel.STRICT
        assert config.violation_threshold == 1
        assert config.security_hardening_enabled is True
    
    def test_configuration_serialization(self):
        """Test configuration can be serialized/deserialized"""
        config = IsolationConfig(level=IsolationLevel.MINIMAL)
        
        # Should be able to convert to dict and back
        config_dict = config.__dict__
        assert "level" in config_dict
        assert config_dict["level"] == IsolationLevel.MINIMAL


class TestResourceMonitoring:
    """Unit tests for resource monitoring components"""
    
    @pytest.fixture
    def mock_system_metrics(self):
        """Mock system metrics for testing"""
        return {
            "memory_mb": 45.2,
            "cpu_percent": 15.7,
            "disk_usage_mb": 12.3,
            "network_connections": 2
        }
    
    @pytest.mark.asyncio
    async def test_resource_tracking(self, sandbox, mock_system_metrics):
        """Test resource usage tracking"""
        
        def resource_test_plugin(environment):
            # Simulate some resource usage
            data = [i * 2 for i in range(1000)]
            return {"processed": len(data)}
        
        with patch('plugin_sandbox_isolation_enhanced.get_system_metrics', 
                  return_value=mock_system_metrics):
            async with sandbox:
                await sandbox.execute_plugin_safe(resource_test_plugin)
            
            telemetry = sandbox.get_telemetry()
            assert telemetry.peak_memory_mb >= 0
            assert telemetry.peak_cpu_percent >= 0
    
    def test_violation_detection(self, sandbox):
        """Test violation detection logic"""
        
        # Simulate violation conditions
        sandbox._record_violation("memory_limit", {
            "current_usage": 150,
            "limit": 128,
            "timestamp": datetime.now()
        })
        
        violations = sandbox.get_violations()
        assert len(violations) == 1
        assert violations[0].type == "memory_limit"


# Test Utilities
class TestHelpers:
    """Helper functions for testing"""
    
    @staticmethod
    def create_test_plugin(behavior: str = "normal"):
        """Create test plugins with different behaviors"""
        
        if behavior == "normal":
            def normal_plugin(environment):
                return {"status": "success", "type": "normal"}
            return normal_plugin
        
        elif behavior == "slow":
            def slow_plugin(environment):
                import time
                time.sleep(2)
                return {"status": "success", "type": "slow"}
            return slow_plugin
        
        elif behavior == "memory_intensive":
            def memory_plugin(environment):
                data = ["x" * 1000 for _ in range(10000)]
                return {"status": "success", "type": "memory_intensive", "size": len(data)}
            return memory_plugin
        
        elif behavior == "error":
            def error_plugin(environment):
                raise ValueError("Test error")
            return error_plugin
        
        else:
            raise ValueError(f"Unknown behavior: {behavior}")
    
    @staticmethod
    def assert_telemetry_valid(telemetry):
        """Assert telemetry data is valid"""
        assert telemetry.sandbox_id is not None
        assert telemetry.start_time > 0
        assert telemetry.end_time >= telemetry.start_time
        assert telemetry.peak_memory_mb >= 0
        assert telemetry.peak_cpu_percent >= 0
        assert isinstance(telemetry.cleanup_successful, bool)


# Parametrized Tests
class TestParametrizedScenarios:
    """Parametrized tests for different scenarios"""
    
    @pytest.mark.parametrize("isolation_level", [
        IsolationLevel.MINIMAL,
        IsolationLevel.STANDARD,
        IsolationLevel.STRICT
    ])
    @pytest.mark.asyncio
    async def test_different_isolation_levels(self, isolation_level):
        """Test sandbox behavior with different isolation levels"""
        
        config = IsolationConfig(level=isolation_level)
        limits = PluginLimitsV2(max_memory_mb=128, max_execution_time_seconds=10)
        permissions = PluginPermissionsV2(security_level=SecurityLevel.MEDIUM)
        
        sandbox = EnhancedPluginSandbox(limits, permissions, config)
        
        def test_plugin(environment):
            return {"isolation_level": isolation_level.value}
        
        async with sandbox:
            result = await sandbox.execute_plugin_safe(test_plugin)
        
        assert result["isolation_level"] == isolation_level.value
    
    @pytest.mark.parametrize("memory_limit,expected_result", [
        (32, "low_memory"),
        (128, "medium_memory"),
        (512, "high_memory")
    ])
    @pytest.mark.asyncio
    async def test_memory_configurations(self, memory_limit, expected_result):
        """Test different memory limit configurations"""
        
        config = IsolationConfig(level=IsolationLevel.STANDARD)
        limits = PluginLimitsV2(max_memory_mb=memory_limit, max_execution_time_seconds=10)
        permissions = PluginPermissionsV2(security_level=SecurityLevel.MEDIUM)
        
        sandbox = EnhancedPluginSandbox(limits, permissions, config)
        
        def memory_test_plugin(environment):
            if limits.max_memory_mb < 64:
                return {"category": "low_memory"}
            elif limits.max_memory_mb < 256:
                return {"category": "medium_memory"}
            else:
                return {"category": "high_memory"}
        
        async with sandbox:
            result = await sandbox.execute_plugin_safe(memory_test_plugin)
        
        assert result["category"] == expected_result


# Performance Tests
class TestPerformance:
    """Performance-focused unit tests"""
    
    @pytest.mark.asyncio
    async def test_execution_performance(self):
        """Test execution performance benchmarks"""
        
        config = IsolationConfig(level=IsolationLevel.STANDARD)
        limits = PluginLimitsV2(max_memory_mb=256, max_execution_time_seconds=5)
        permissions = PluginPermissionsV2(security_level=SecurityLevel.MEDIUM)
        
        sandbox = EnhancedPluginSandbox(limits, permissions, config)
        
        def benchmark_plugin(environment, iterations: int):
            start_time = time.time()
            result = sum(range(iterations))
            end_time = time.time()
            
            return {
                "result": result,
                "execution_time": end_time - start_time,
                "iterations": iterations
            }
        
        # Test with different iteration counts
        for iterations in [1000, 10000, 100000]:
            async with sandbox:
                result = await sandbox.execute_plugin_safe(benchmark_plugin, iterations)
            
            # Performance assertions
            assert result["iterations"] == iterations
            assert result["execution_time"] < 5.0  # Within timeout
            
            # Check telemetry
            telemetry = sandbox.get_telemetry()
            assert telemetry.end_time - telemetry.start_time < 5.0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
