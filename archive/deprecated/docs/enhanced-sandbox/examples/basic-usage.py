#!/usr/bin/env python3
"""
Basic Usage Examples for Enhanced Plugin Sandbox Isolation

This file demonstrates basic usage patterns for the Enhanced Plugin Sandbox
Isolation system. Each example is self-contained and can be run independently.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List

# Import sandbox components
try:
    from plugin_sandbox_isolation_enhanced import (
        EnhancedPluginSandbox,
        IsolationConfig,
        IsolationLevel
    )
    from plugin_framework_v2 import (
        PluginLimitsV2,
        PluginPermissionsV2,
        SecurityLevel
    )
    SANDBOX_AVAILABLE = True
except ImportError:
    print("⚠️ Enhanced sandbox components not available")
    print("Make sure plugin_sandbox_isolation_enhanced.py is in your path")
    SANDBOX_AVAILABLE = False


async def example_1_basic_usage():
    """Example 1: Basic sandbox usage with minimal configuration"""
    
    print("🏰 Example 1: Basic Sandbox Usage")
    print("=" * 50)
    
    if not SANDBOX_AVAILABLE:
        print("❌ Sandbox components not available")
        return
    
    # Simple configuration
    config = IsolationConfig(level=IsolationLevel.STANDARD)
    limits = PluginLimitsV2(max_memory_mb=64, max_execution_time_seconds=10)
    permissions = PluginPermissionsV2()
    
    # Create sandbox
    sandbox = EnhancedPluginSandbox(limits, permissions, config)
    
    try:
        async with sandbox:
            # Simple plugin function
            def hello_world_plugin(environment):
                """Simple plugin that returns a greeting"""
                return {
                    "message": "Hello from the sandbox!",
                    "environment": environment,
                    "timestamp": str(datetime.now())
                }
            
            # Execute plugin
            result = await sandbox.execute_plugin_safe(hello_world_plugin)
            
            print(f"✅ Plugin executed successfully")
            print(f"📄 Result: {result}")
            
            # Get telemetry
            telemetry = sandbox.get_telemetry()
            print(f"📊 Peak memory usage: {telemetry.peak_memory_mb:.2f}MB")
            
    except Exception as e:
        print(f"❌ Error: {e}")


async def example_2_plugin_with_parameters():
    """Example 2: Plugin with input parameters"""
    
    print("\n🔧 Example 2: Plugin with Parameters")
    print("=" * 50)
    
    if not SANDBOX_AVAILABLE:
        print("❌ Sandbox components not available")
        return
    
    # Configure sandbox
    config = IsolationConfig(level=IsolationLevel.STANDARD)
    limits = PluginLimitsV2(max_memory_mb=128, max_execution_time_seconds=20)
    permissions = PluginPermissionsV2()
    
    sandbox = EnhancedPluginSandbox(limits, permissions, config)
    
    try:
        async with sandbox:
            def calculator_plugin(environment, numbers: List[float], operation: str = "sum"):
                """Plugin that performs calculations on a list of numbers"""
                
                if operation == "sum":
                    result = sum(numbers)
                elif operation == "average":
                    result = sum(numbers) / len(numbers) if numbers else 0
                elif operation == "max":
                    result = max(numbers) if numbers else 0
                elif operation == "min":
                    result = min(numbers) if numbers else 0
                else:
                    result = None
                
                return {
                    "operation": operation,
                    "input": numbers,
                    "result": result,
                    "count": len(numbers),
                    "calculated_at": str(datetime.now())
                }
            
            # Test different operations
            test_numbers = [1.5, 2.7, 3.2, 4.1, 5.9]
            
            for operation in ["sum", "average", "max", "min"]:
                result = await sandbox.execute_plugin_safe(
                    calculator_plugin, 
                    test_numbers, 
                    operation=operation
                )
                print(f"📊 {operation.upper()}: {result['result']:.2f}")
    
    except Exception as e:
        print(f"❌ Error: {e}")


async def example_3_data_processing():
    """Example 3: Data processing plugin"""
    
    print("\n📊 Example 3: Data Processing")
    print("=" * 50)
    
    if not SANDBOX_AVAILABLE:
        print("❌ Sandbox components not available")
        return
    
    # Higher limits for data processing
    config = IsolationConfig(level=IsolationLevel.STANDARD)
    limits = PluginLimitsV2(
        max_memory_mb=256,
        max_execution_time_seconds=30,
        max_cpu_percent=70.0
    )
    permissions = PluginPermissionsV2()
    
    sandbox = EnhancedPluginSandbox(limits, permissions, config)
    
    try:
        async with sandbox:
            def data_processor_plugin(environment, data: List[Dict[str, Any]], filter_key: str):
                """Plugin that processes and filters data"""
                
                # Filter data based on key
                filtered_data = [item for item in data if filter_key in item]
                
                # Calculate statistics
                total_items = len(data)
                filtered_items = len(filtered_data)
                filter_ratio = (filtered_items / total_items) * 100 if total_items > 0 else 0
                
                # Process each filtered item
                processed_data = []
                for item in filtered_data:
                    processed_item = {
                        **item,
                        "processed_at": str(datetime.now()),
                        "has_filter_key": True
                    }
                    processed_data.append(processed_item)
                
                return {
                    "total_input_items": total_items,
                    "filtered_items": filtered_items,
                    "filter_ratio_percent": round(filter_ratio, 2),
                    "processed_data": processed_data,
                    "processing_completed": True
                }
            
            # Sample data
            sample_data = [
                {"id": 1, "name": "Alice", "category": "A", "score": 85},
                {"id": 2, "name": "Bob", "score": 92},
                {"id": 3, "name": "Charlie", "category": "B", "score": 78},
                {"id": 4, "name": "Diana", "category": "A", "score": 96},
                {"id": 5, "name": "Eve", "score": 88}
            ]
            
            # Process data
            result = await sandbox.execute_plugin_safe(
                data_processor_plugin,
                sample_data,
                filter_key="category"
            )
            
            print(f"📄 Processed {result['total_input_items']} items")
            print(f"🔍 Found {result['filtered_items']} items with 'category' key")
            print(f"📊 Filter ratio: {result['filter_ratio_percent']}%")
            
            # Show telemetry
            telemetry = sandbox.get_telemetry()
            print(f"📈 Peak memory: {telemetry.peak_memory_mb:.2f}MB")
            
    except Exception as e:
        print(f"❌ Error: {e}")


async def example_4_error_handling():
    """Example 4: Error handling and violation detection"""
    
    print("\n⚠️ Example 4: Error Handling")
    print("=" * 50)
    
    if not SANDBOX_AVAILABLE:
        print("❌ Sandbox components not available")
        return
    
    # Strict configuration with low limits to trigger violations
    config = IsolationConfig(
        level=IsolationLevel.STRICT,
        violation_threshold=2,
        auto_recovery_enabled=True
    )
    limits = PluginLimitsV2(
        max_memory_mb=32,  # Very low limit
        max_execution_time_seconds=5  # Short timeout
    )
    permissions = PluginPermissionsV2(security_level=SecurityLevel.HIGH)
    
    sandbox = EnhancedPluginSandbox(limits, permissions, config)
    
    try:
        async with sandbox:
            def problematic_plugin(environment, should_exceed_memory: bool = False):
                """Plugin that may exceed resource limits"""
                
                if should_exceed_memory:
                    # Try to allocate lots of memory
                    large_data = []
                    for i in range(100000):  # This might exceed 32MB limit
                        large_data.append(f"Data item {i} with lots of text " * 100)
                    
                    return {
                        "status": "success",
                        "data_items": len(large_data),
                        "memory_intensive": True
                    }
                else:
                    # Normal operation
                    return {
                        "status": "success",
                        "message": "Normal execution completed",
                        "memory_intensive": False
                    }
            
            # Test 1: Normal execution (should succeed)
            print("🧪 Test 1: Normal execution")
            result1 = await sandbox.execute_plugin_safe(problematic_plugin, False)
            print(f"✅ Normal execution: {result1['status']}")
            
            # Test 2: Memory-intensive execution (might violate limits)
            print("\n🧪 Test 2: Memory-intensive execution")
            try:
                result2 = await sandbox.execute_plugin_safe(problematic_plugin, True)
                print(f"✅ Memory-intensive execution: {result2['status']}")
            except Exception as e:
                print(f"⚠️ Expected violation: {e}")
            
            # Check for violations
            violations = sandbox.get_violations()
            if violations:
                print(f"\n🚨 Detected {len(violations)} violations:")
                for i, violation in enumerate(violations, 1):
                    print(f"  {i}. {violation.type.value}: {violation.message}")
            else:
                print("\n✅ No violations detected")
            
            # Show telemetry
            telemetry = sandbox.get_telemetry()
            print(f"\n📊 Telemetry Summary:")
            print(f"  Peak Memory: {telemetry.peak_memory_mb:.2f}MB")
            print(f"  Peak CPU: {telemetry.peak_cpu_percent:.1f}%")
            
    except Exception as e:
        print(f"❌ Sandbox error: {e}")


async def example_5_monitoring_and_telemetry():
    """Example 5: Monitoring and telemetry collection"""
    
    print("\n📈 Example 5: Monitoring and Telemetry")
    print("=" * 50)
    
    if not SANDBOX_AVAILABLE:
        print("❌ Sandbox components not available")
        return
    
    # Configuration with detailed monitoring
    config = IsolationConfig(
        level=IsolationLevel.STANDARD,
        enable_real_time_monitoring=True,
        telemetry_enabled=True,
        resource_check_interval_seconds=0.5  # Frequent monitoring
    )
    limits = PluginLimitsV2(max_memory_mb=128, max_execution_time_seconds=15)
    permissions = PluginPermissionsV2()
    
    sandbox = EnhancedPluginSandbox(limits, permissions, config)
    
    try:
        async with sandbox:
            def monitored_plugin(environment, work_duration: float = 2.0):
                """Plugin that demonstrates monitoring capabilities"""
                
                print(f"🔄 Starting work for {work_duration} seconds...")
                
                # Simulate different types of work
                data = []
                start_time = time.time()
                
                while time.time() - start_time < work_duration:
                    # Memory allocation
                    batch = [f"Item {i}" * 10 for i in range(100)]
                    data.extend(batch)
                    
                    # CPU work
                    _ = sum(range(1000))
                    
                    # Small delay
                    time.sleep(0.1)
                
                return {
                    "status": "completed",
                    "work_duration": work_duration,
                    "data_items_created": len(data),
                    "actual_duration": time.time() - start_time
                }
            
            # Execute monitored plugin
            result = await sandbox.execute_plugin_safe(monitored_plugin, 3.0)
            print(f"✅ Plugin completed: {result['status']}")
            print(f"📊 Created {result['data_items_created']} data items")
            
            # Detailed telemetry analysis
            telemetry = sandbox.get_telemetry()
            
            print(f"\n📈 Detailed Telemetry:")
            print(f"  Sandbox ID: {telemetry.sandbox_id}")
            print(f"  Execution Time: {telemetry.end_time - telemetry.start_time}")
            print(f"  Peak Memory: {telemetry.peak_memory_mb:.2f}MB")
            print(f"  Peak CPU: {telemetry.peak_cpu_percent:.1f}%")
            print(f"  File Operations: {telemetry.file_operations_count}")
            print(f"  Network Operations: {telemetry.network_operations_count}")
            print(f"  Resource Samples: {len(telemetry.resource_samples)}")
            print(f"  Cleanup Successful: {telemetry.cleanup_successful}")
            
            # Show resource samples (if available)
            if hasattr(telemetry, 'resource_samples') and telemetry.resource_samples:
                print(f"\n📊 Resource Sample History:")
                for i, sample in enumerate(telemetry.resource_samples[:3]):  # Show first 3 samples
                    print(f"  Sample {i+1}: Memory={sample.get('memory_mb', 0):.1f}MB, "
                          f"CPU={sample.get('cpu_percent', 0):.1f}%")
                
                if len(telemetry.resource_samples) > 3:
                    print(f"  ... and {len(telemetry.resource_samples) - 3} more samples")
    
    except Exception as e:
        print(f"❌ Error: {e}")


async def example_6_configuration_comparison():
    """Example 6: Comparing different isolation levels"""
    
    print("\n⚙️ Example 6: Isolation Level Comparison")
    print("=" * 50)
    
    if not SANDBOX_AVAILABLE:
        print("❌ Sandbox components not available")
        return
    
    # Test plugin that performs standard operations
    def benchmark_plugin(environment, iterations: int = 1000):
        """Plugin for benchmarking different isolation levels"""
        
        data = []
        for i in range(iterations):
            item = {
                "id": i,
                "value": f"data_{i}",
                "timestamp": str(datetime.now())
            }
            data.append(item)
        
        # Some processing
        processed = [item for item in data if item["id"] % 2 == 0]
        
        return {
            "status": "success",
            "iterations": iterations,
            "total_items": len(data),
            "processed_items": len(processed),
            "efficiency": len(processed) / len(data) * 100
        }
    
    # Test different isolation levels
    isolation_levels = [
        (IsolationLevel.MINIMAL, "Minimal"),
        (IsolationLevel.STANDARD, "Standard"),
        (IsolationLevel.STRICT, "Strict")
    ]
    
    results = []
    
    for level, level_name in isolation_levels:
        print(f"\n🧪 Testing {level_name} isolation level...")
        
        config = IsolationConfig(
            level=level,
            enable_real_time_monitoring=True,
            resource_check_interval_seconds=1.0
        )
        limits = PluginLimitsV2(max_memory_mb=128, max_execution_time_seconds=10)
        permissions = PluginPermissionsV2()
        
        sandbox = EnhancedPluginSandbox(limits, permissions, config)
        
        try:
            start_time = time.time()
            
            async with sandbox:
                result = await sandbox.execute_plugin_safe(benchmark_plugin, 2000)
                
            end_time = time.time()
            execution_time = end_time - start_time
            
            telemetry = sandbox.get_telemetry()
            
            results.append({
                "level": level_name,
                "execution_time": execution_time,
                "peak_memory": telemetry.peak_memory_mb,
                "violations": len(sandbox.get_violations()),
                "processed_items": result["processed_items"]
            })
            
            print(f"  ✅ Execution time: {execution_time:.3f}s")
            print(f"  📊 Peak memory: {telemetry.peak_memory_mb:.2f}MB")
            print(f"  ⚠️ Violations: {len(sandbox.get_violations())}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Summary comparison
    if results:
        print(f"\n📊 Performance Comparison Summary:")
        print(f"{'Level':<10} {'Time (s)':<10} {'Memory (MB)':<12} {'Violations':<10}")
        print("-" * 50)
        
        for result in results:
            print(f"{result['level']:<10} {result['execution_time']:<10.3f} "
                  f"{result['peak_memory']:<12.2f} {result['violations']:<10}")


async def main():
    """Run all examples"""
    
    print("🚀 Enhanced Plugin Sandbox - Basic Usage Examples")
    print("=" * 60)
    
    examples = [
        example_1_basic_usage,
        example_2_plugin_with_parameters,
        example_3_data_processing,
        example_4_error_handling,
        example_5_monitoring_and_telemetry,
        example_6_configuration_comparison
    ]
    
    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"❌ Example failed: {e}")
        
        print("\n" + "─" * 60)
    
    print("✅ All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
