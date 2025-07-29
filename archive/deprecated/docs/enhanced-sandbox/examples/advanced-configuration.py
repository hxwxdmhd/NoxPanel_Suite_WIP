#!/usr/bin/env python3
"""
Advanced Configuration Examples for Enhanced Plugin Sandbox Isolation

This file demonstrates advanced configuration patterns, custom security policies,
performance optimization, and specialized use cases.
"""

import asyncio
import json
import logging
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import sandbox components
try:
    from plugin_sandbox_isolation_enhanced import (
        EnhancedPluginSandbox,
        IsolationConfig,
        IsolationLevel,
        SecurityEnforcer,
        ResourceMonitor,
        SandboxEnvironment
    )
    from plugin_framework_v2 import (
        PluginLimitsV2,
        PluginPermissionsV2,
        SecurityLevel,
        PluginMetadata
    )
    SANDBOX_AVAILABLE = True
except ImportError:
    print("⚠️ Enhanced sandbox components not available")
    SANDBOX_AVAILABLE = False


# Configure logging for examples
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CustomSecurityPolicy:
    """Example custom security policy implementation"""
    
    def __init__(self, allowed_modules: List[str], restricted_paths: List[str]):
        self.allowed_modules = set(allowed_modules)
        self.restricted_paths = set(restricted_paths)
    
    def check_import(self, module_name: str) -> bool:
        """Check if module import is allowed"""
        return module_name in self.allowed_modules or module_name.split('.')[0] in self.allowed_modules
    
    def check_file_access(self, file_path: str) -> bool:
        """Check if file access is allowed"""
        path = Path(file_path).resolve()
        for restricted in self.restricted_paths:
            try:
                path.relative_to(Path(restricted).resolve())
                return False  # Path is within restricted directory
            except ValueError:
                continue  # Path is not within this restricted directory
        return True


async def example_1_custom_security_policy():
    """Example 1: Custom security policies and module restrictions"""
    
    print("🔒 Example 1: Custom Security Policies")
    print("=" * 50)
    
    if not SANDBOX_AVAILABLE:
        print("❌ Sandbox components not available")
        return
    
    # Create custom security policy
    security_policy = CustomSecurityPolicy(
        allowed_modules=['json', 'datetime', 'math', 're'],
        restricted_paths=['/etc', '/sys', str(Path.home())]
    )
    
    # High-security configuration
    config = IsolationConfig(
        level=IsolationLevel.STRICT,
        enable_real_time_monitoring=True,
        violation_threshold=1,  # Very strict
        auto_recovery_enabled=True,
        security_hardening_enabled=True,
        environment_isolation_enabled=True
    )
    
    limits = PluginLimitsV2(
        max_memory_mb=64,
        max_execution_time_seconds=10,
        max_cpu_percent=50.0,
        max_file_operations=10,
        max_network_connections=0  # No network access
    )
    
    permissions = PluginPermissionsV2(
        security_level=SecurityLevel.MAXIMUM,
        can_access_filesystem=True,
        can_access_network=False,
        can_modify_environment=False,
        allowed_file_patterns=['*.txt', '*.json'],
        restricted_paths=['/etc', '/sys', '/proc']
    )
    
    sandbox = EnhancedPluginSandbox(limits, permissions, config)
    
    try:
        async with sandbox:
            def secure_plugin(environment, data: Dict[str, Any]):
                """Plugin that demonstrates security-aware operations"""
                
                # Allowed operations
                import json
                import math
                from datetime import datetime
                
                # Process data securely
                processed_data = {
                    "input_keys": list(data.keys()),
                    "processing_time": str(datetime.now()),
                    "math_operation": math.sqrt(sum([v for v in data.values() if isinstance(v, (int, float))])),
                    "security_level": "HIGH"
                }
                
                # JSON serialization (allowed)
                json_output = json.dumps(processed_data, indent=2)
                
                return {
                    "status": "success",
                    "security_compliant": True,
                    "output": processed_data,
                    "serialized_size": len(json_output)
                }
            
            # Test with sample data
            test_data = {
                "value1": 10,
                "value2": 20,
                "name": "test_dataset",
                "score": 85.5
            }
            
            result = await sandbox.execute_plugin_safe(secure_plugin, test_data)
            
            print(f"✅ Secure execution completed")
            print(f"🔒 Security compliant: {result['security_compliant']}")
            print(f"📊 Math result: {result['output']['math_operation']:.2f}")
            
            # Check violations
            violations = sandbox.get_violations()
            if violations:
                print(f"🚨 {len(violations)} security violations detected")
            else:
                print("✅ No security violations")
    
    except Exception as e:
        print(f"❌ Security error: {e}")


async def example_2_performance_optimization():
    """Example 2: Performance optimization configurations"""
    
    print("\n⚡ Example 2: Performance Optimization")
    print("=" * 50)
    
    if not SANDBOX_AVAILABLE:
        print("❌ Sandbox components not available")
        return
    
    # Performance-optimized configuration
    config = IsolationConfig(
        level=IsolationLevel.STANDARD,
        enable_real_time_monitoring=False,  # Reduce monitoring overhead
        resource_check_interval_seconds=5.0,  # Less frequent checks
        cleanup_timeout_seconds=30.0,
        performance_mode_enabled=True,  # Hypothetical performance mode
        memory_optimization_enabled=True
    )
    
    # High-performance limits
    limits = PluginLimitsV2(
        max_memory_mb=512,  # Higher memory limit
        max_execution_time_seconds=60,  # Longer execution time
        max_cpu_percent=80.0,  # Higher CPU usage allowed
        max_file_operations=1000,
        max_disk_space_mb=100
    )
    
    permissions = PluginPermissionsV2(
        security_level=SecurityLevel.MEDIUM,  # Balanced security
        can_access_filesystem=True,
        can_access_network=False
    )
    
    sandbox = EnhancedPluginSandbox(limits, permissions, config)
    
    try:
        async with sandbox:
            def high_performance_plugin(environment, dataset_size: int = 10000):
                """Plugin optimized for high-performance data processing"""
                
                import time
                from datetime import datetime
                
                start_time = time.time()
                
                # Generate large dataset
                dataset = []
                for i in range(dataset_size):
                    record = {
                        "id": i,
                        "value": i * 2.5,
                        "category": f"cat_{i % 10}",
                        "timestamp": datetime.now().isoformat(),
                        "metadata": f"record_{i}_metadata" * 10  # Some text data
                    }
                    dataset.append(record)
                
                # Perform intensive processing
                # Group by category
                categories = {}
                for record in dataset:
                    cat = record["category"]
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append(record)
                
                # Calculate statistics per category
                stats = {}
                for cat, records in categories.items():
                    values = [r["value"] for r in records]
                    stats[cat] = {
                        "count": len(records),
                        "sum": sum(values),
                        "avg": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values)
                    }
                
                processing_time = time.time() - start_time
                
                return {
                    "status": "success",
                    "dataset_size": dataset_size,
                    "categories_processed": len(categories),
                    "processing_time_seconds": processing_time,
                    "records_per_second": dataset_size / processing_time,
                    "category_stats": stats,
                    "performance_optimized": True
                }
            
            # Execute high-performance plugin
            result = await sandbox.execute_plugin_safe(high_performance_plugin, 25000)
            
            print(f"✅ High-performance execution completed")
            print(f"📊 Processed {result['dataset_size']} records")
            print(f"⏱️ Processing time: {result['processing_time_seconds']:.3f}s")
            print(f"⚡ Records/second: {result['records_per_second']:.0f}")
            print(f"📂 Categories: {result['categories_processed']}")
            
            # Performance telemetry
            telemetry = sandbox.get_telemetry()
            print(f"📈 Peak memory: {telemetry.peak_memory_mb:.2f}MB")
            print(f"🔥 Peak CPU: {telemetry.peak_cpu_percent:.1f}%")
    
    except Exception as e:
        print(f"❌ Performance error: {e}")


async def example_3_plugin_chaining():
    """Example 3: Plugin chaining and pipeline execution"""
    
    print("\n🔗 Example 3: Plugin Chaining and Pipelines")
    print("=" * 50)
    
    if not SANDBOX_AVAILABLE:
        print("❌ Sandbox components not available")
        return
    
    # Pipeline configuration - balanced for chaining
    config = IsolationConfig(
        level=IsolationLevel.STANDARD,
        enable_real_time_monitoring=True,
        state_persistence_enabled=True,  # Enable state sharing between plugins
        pipeline_mode_enabled=True
    )
    
    limits = PluginLimitsV2(
        max_memory_mb=256,
        max_execution_time_seconds=30
    )
    
    permissions = PluginPermissionsV2(security_level=SecurityLevel.MEDIUM)
    
    # Define pipeline plugins
    def data_loader_plugin(environment, source_config: Dict[str, Any]):
        """Stage 1: Load and validate data"""
        
        # Simulate data loading
        raw_data = []
        for i in range(source_config.get("record_count", 100)):
            record = {
                "id": i,
                "raw_value": i * 3.14,
                "status": "raw",
                "source": source_config.get("source_name", "default")
            }
            raw_data.append(record)
        
        return {
            "stage": "data_loader",
            "status": "success",
            "data": raw_data,
            "record_count": len(raw_data),
            "next_stage": "data_processor"
        }
    
    def data_processor_plugin(environment, input_data: List[Dict[str, Any]]):
        """Stage 2: Process and transform data"""
        
        processed_data = []
        for record in input_data:
            processed_record = {
                **record,
                "processed_value": record["raw_value"] * 2,
                "category": "high" if record["raw_value"] > 150 else "low",
                "status": "processed"
            }
            processed_data.append(processed_record)
        
        return {
            "stage": "data_processor",
            "status": "success",
            "data": processed_data,
            "record_count": len(processed_data),
            "next_stage": "data_analyzer"
        }
    
    def data_analyzer_plugin(environment, input_data: List[Dict[str, Any]]):
        """Stage 3: Analyze and summarize data"""
        
        # Analyze data
        high_category_count = sum(1 for record in input_data if record["category"] == "high")
        low_category_count = sum(1 for record in input_data if record["category"] == "low")
        
        total_processed_value = sum(record["processed_value"] for record in input_data)
        average_processed_value = total_processed_value / len(input_data)
        
        analysis_result = {
            "stage": "data_analyzer",
            "status": "success",
            "total_records": len(input_data),
            "high_category_count": high_category_count,
            "low_category_count": low_category_count,
            "total_processed_value": total_processed_value,
            "average_processed_value": average_processed_value,
            "analysis_complete": True
        }
        
        return analysis_result
    
    # Execute plugin pipeline
    sandbox = EnhancedPluginSandbox(limits, permissions, config)
    
    try:
        async with sandbox:
            print("🔗 Executing plugin pipeline...")
            
            # Stage 1: Data Loading
            print("  📥 Stage 1: Loading data...")
            stage1_result = await sandbox.execute_plugin_safe(
                data_loader_plugin,
                {"record_count": 200, "source_name": "test_dataset"}
            )
            print(f"    ✅ Loaded {stage1_result['record_count']} records")
            
            # Stage 2: Data Processing
            print("  ⚙️ Stage 2: Processing data...")
            stage2_result = await sandbox.execute_plugin_safe(
                data_processor_plugin,
                stage1_result["data"]
            )
            print(f"    ✅ Processed {stage2_result['record_count']} records")
            
            # Stage 3: Data Analysis
            print("  📊 Stage 3: Analyzing data...")
            stage3_result = await sandbox.execute_plugin_safe(
                data_analyzer_plugin,
                stage2_result["data"]
            )
            print(f"    ✅ Analysis complete")
            
            # Pipeline summary
            print(f"\n📋 Pipeline Summary:")
            print(f"  Total Records: {stage3_result['total_records']}")
            print(f"  High Category: {stage3_result['high_category_count']}")
            print(f"  Low Category: {stage3_result['low_category_count']}")
            print(f"  Average Value: {stage3_result['average_processed_value']:.2f}")
            
            # Pipeline telemetry
            telemetry = sandbox.get_telemetry()
            print(f"  Peak Memory: {telemetry.peak_memory_mb:.2f}MB")
            print(f"  Total Time: {telemetry.end_time - telemetry.start_time:.3f}s")
    
    except Exception as e:
        print(f"❌ Pipeline error: {e}")


async def example_4_dynamic_configuration():
    """Example 4: Dynamic configuration and adaptive limits"""
    
    print("\n🎛️ Example 4: Dynamic Configuration")
    print("=" * 50)
    
    if not SANDBOX_AVAILABLE:
        print("❌ Sandbox components not available")
        return
    
    class AdaptiveConfigurationManager:
        """Manages dynamic configuration based on plugin requirements"""
        
        def __init__(self):
            self.execution_history = []
        
        def get_config_for_plugin(self, plugin_metadata: PluginMetadata) -> tuple:
            """Generate configuration based on plugin characteristics"""
            
            # Analyze plugin requirements
            is_memory_intensive = any(keyword in plugin_metadata.description.lower() 
                                    for keyword in ["memory", "large", "dataset", "processing"])
            is_cpu_intensive = any(keyword in plugin_metadata.description.lower() 
                                 for keyword in ["compute", "calculation", "cpu", "intensive"])
            is_io_intensive = any(keyword in plugin_metadata.description.lower() 
                                for keyword in ["file", "network", "io", "download"])
            
            # Base configuration
            base_memory = 128
            base_time = 20
            base_cpu = 60.0
            
            # Adjust based on requirements
            if is_memory_intensive:
                base_memory *= 2
                base_time *= 1.5
            
            if is_cpu_intensive:
                base_cpu *= 1.3
                base_time *= 2
            
            if is_io_intensive:
                base_time *= 2
            
            # Create adaptive configuration
            config = IsolationConfig(
                level=IsolationLevel.STANDARD,
                enable_real_time_monitoring=True,
                adaptive_limits_enabled=True,
                resource_check_interval_seconds=1.0 if is_memory_intensive else 2.0
            )
            
            limits = PluginLimitsV2(
                max_memory_mb=int(base_memory),
                max_execution_time_seconds=int(base_time),
                max_cpu_percent=min(base_cpu, 90.0),
                max_file_operations=1000 if is_io_intensive else 100
            )
            
            permissions = PluginPermissionsV2(
                security_level=SecurityLevel.MEDIUM,
                can_access_filesystem=is_io_intensive
            )
            
            return config, limits, permissions
    
    # Create adaptive manager
    config_manager = AdaptiveConfigurationManager()
    
    # Test plugins with different characteristics
    test_plugins = [
        {
            "metadata": PluginMetadata(
                name="lightweight_plugin",
                version="1.0.0",
                description="Simple calculation plugin with minimal resource requirements"
            ),
            "plugin": lambda env: {"result": sum(range(100)), "type": "lightweight"}
        },
        {
            "metadata": PluginMetadata(
                name="memory_intensive_plugin",
                version="1.0.0", 
                description="Large dataset processing plugin requiring significant memory"
            ),
            "plugin": lambda env: {
                "result": len([i * j for i in range(1000) for j in range(100)]),
                "type": "memory_intensive"
            }
        },
        {
            "metadata": PluginMetadata(
                name="cpu_intensive_plugin",
                version="1.0.0",
                description="CPU-intensive calculation plugin with complex compute operations"
            ),
            "plugin": lambda env: {
                "result": sum([i ** 2 for i in range(10000)]),
                "type": "cpu_intensive"
            }
        }
    ]
    
    # Execute plugins with adaptive configuration
    for plugin_info in test_plugins:
        metadata = plugin_info["metadata"]
        plugin_func = plugin_info["plugin"]
        
        print(f"\n🔧 Testing {metadata.name}...")
        
        # Get adaptive configuration
        config, limits, permissions = config_manager.get_config_for_plugin(metadata)
        
        print(f"  📊 Memory limit: {limits.max_memory_mb}MB")
        print(f"  ⏱️ Time limit: {limits.max_execution_time_seconds}s")
        print(f"  🔥 CPU limit: {limits.max_cpu_percent:.1f}%")
        
        # Execute with adaptive configuration
        sandbox = EnhancedPluginSandbox(limits, permissions, config)
        
        try:
            async with sandbox:
                result = await sandbox.execute_plugin_safe(plugin_func)
                
                telemetry = sandbox.get_telemetry()
                
                print(f"  ✅ Executed successfully")
                print(f"  📈 Peak memory: {telemetry.peak_memory_mb:.2f}MB")
                print(f"  ⏱️ Execution time: {telemetry.end_time - telemetry.start_time:.3f}s")
                print(f"  🔥 Peak CPU: {telemetry.peak_cpu_percent:.1f}%")
        
        except Exception as e:
            print(f"  ❌ Execution failed: {e}")


async def example_5_environment_customization():
    """Example 5: Custom environment setup and isolation"""
    
    print("\n🌍 Example 5: Environment Customization")
    print("=" * 50)
    
    if not SANDBOX_AVAILABLE:
        print("❌ Sandbox components not available")
        return
    
    # Create custom environment configuration
    config = IsolationConfig(
        level=IsolationLevel.STANDARD,
        environment_isolation_enabled=True,
        custom_environment_variables={
            "PLUGIN_MODE": "SANDBOX",
            "MAX_ITERATIONS": "10000",
            "DEBUG_LEVEL": "INFO",
            "CUSTOM_PATH": "/tmp/plugin_workspace"
        },
        temp_directory_enabled=True,
        working_directory_isolation=True
    )
    
    limits = PluginLimitsV2(max_memory_mb=128, max_execution_time_seconds=15)
    permissions = PluginPermissionsV2(
        security_level=SecurityLevel.MEDIUM,
        can_access_filesystem=True,
        can_modify_environment=False  # Prevent environment tampering
    )
    
    sandbox = EnhancedPluginSandbox(limits, permissions, config)
    
    try:
        async with sandbox:
            def environment_aware_plugin(environment):
                """Plugin that demonstrates environment customization"""
                
                import os
                import tempfile
                from pathlib import Path
                
                # Access custom environment variables
                plugin_mode = os.environ.get("PLUGIN_MODE", "UNKNOWN")
                max_iterations = int(os.environ.get("MAX_ITERATIONS", "1000"))
                debug_level = os.environ.get("DEBUG_LEVEL", "WARNING")
                
                # Check working directory isolation
                current_dir = Path.cwd()
                temp_dir = Path(tempfile.gettempdir())
                
                # Perform environment-aware operations
                environment_info = {
                    "plugin_mode": plugin_mode,
                    "max_iterations": max_iterations,
                    "debug_level": debug_level,
                    "current_directory": str(current_dir),
                    "temp_directory": str(temp_dir),
                    "environment_isolated": current_dir != Path.home(),
                    "custom_vars_present": all(var in os.environ for var in 
                                             ["PLUGIN_MODE", "MAX_ITERATIONS", "DEBUG_LEVEL"])
                }
                
                # Create temporary file in isolated environment
                try:
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tmp') as f:
                        f.write("Plugin execution log\n")
                        f.write(f"Mode: {plugin_mode}\n")
                        f.write(f"Iterations: {max_iterations}\n")
                        temp_file_path = f.name
                    
                    # Verify file was created
                    file_exists = Path(temp_file_path).exists()
                    
                    # Clean up
                    if file_exists:
                        Path(temp_file_path).unlink()
                    
                    environment_info["temp_file_test"] = "success"
                
                except Exception as e:
                    environment_info["temp_file_test"] = f"failed: {e}"
                
                return {
                    "status": "success",
                    "environment_info": environment_info,
                    "isolation_verified": environment_info["environment_isolated"],
                    "custom_configuration_active": True
                }
            
            # Execute environment-aware plugin
            result = await sandbox.execute_plugin_safe(environment_aware_plugin)
            
            env_info = result["environment_info"]
            
            print(f"✅ Environment customization test completed")
            print(f"🔧 Plugin mode: {env_info['plugin_mode']}")
            print(f"🔢 Max iterations: {env_info['max_iterations']}")
            print(f"📝 Debug level: {env_info['debug_level']}")
            print(f"🏠 Working directory: {env_info['current_directory']}")
            print(f"🔒 Environment isolated: {env_info['environment_isolated']}")
            print(f"✅ Custom vars present: {env_info['custom_vars_present']}")
            print(f"📄 Temp file test: {env_info['temp_file_test']}")
    
    except Exception as e:
        print(f"❌ Environment error: {e}")


async def example_6_configuration_profiles():
    """Example 6: Configuration profiles for different use cases"""
    
    print("\n📋 Example 6: Configuration Profiles")
    print("=" * 50)
    
    if not SANDBOX_AVAILABLE:
        print("❌ Sandbox components not available")
        return
    
    # Define configuration profiles
    profiles = {
        "development": {
            "config": IsolationConfig(
                level=IsolationLevel.MINIMAL,
                enable_real_time_monitoring=True,
                violation_threshold=10,
                auto_recovery_enabled=True,
                development_mode_enabled=True
            ),
            "limits": PluginLimitsV2(
                max_memory_mb=256,
                max_execution_time_seconds=60,
                max_cpu_percent=80.0
            ),
            "permissions": PluginPermissionsV2(
                security_level=SecurityLevel.LOW,
                can_access_filesystem=True,
                can_access_network=True
            )
        },
        
        "testing": {
            "config": IsolationConfig(
                level=IsolationLevel.STANDARD,
                enable_real_time_monitoring=True,
                violation_threshold=5,
                auto_recovery_enabled=True,
                testing_mode_enabled=True
            ),
            "limits": PluginLimitsV2(
                max_memory_mb=128,
                max_execution_time_seconds=30,
                max_cpu_percent=60.0
            ),
            "permissions": PluginPermissionsV2(
                security_level=SecurityLevel.MEDIUM,
                can_access_filesystem=True,
                can_access_network=False
            )
        },
        
        "production": {
            "config": IsolationConfig(
                level=IsolationLevel.STRICT,
                enable_real_time_monitoring=True,
                violation_threshold=2,
                auto_recovery_enabled=True,
                security_hardening_enabled=True,
                production_mode_enabled=True
            ),
            "limits": PluginLimitsV2(
                max_memory_mb=64,
                max_execution_time_seconds=15,
                max_cpu_percent=40.0,
                max_network_connections=0
            ),
            "permissions": PluginPermissionsV2(
                security_level=SecurityLevel.MAXIMUM,
                can_access_filesystem=False,
                can_access_network=False,
                can_modify_environment=False
            )
        }
    }
    
    # Test plugin for all profiles
    def profile_test_plugin(environment, profile_name: str):
        """Plugin to test different configuration profiles"""
        
        import time
        import os
        
        start_time = time.time()
        
        # Test basic operations
        basic_computation = sum(range(1000))
        
        # Test environment access
        env_vars_count = len(os.environ)
        
        # Test filesystem awareness (without actual access)
        current_dir = os.getcwd()
        
        execution_time = time.time() - start_time
        
        return {
            "status": "success",
            "profile": profile_name,
            "basic_computation": basic_computation,
            "environment_variables_count": env_vars_count,
            "current_directory": current_dir,
            "execution_time": execution_time,
            "profile_test_complete": True
        }
    
    # Test each profile
    for profile_name, profile_config in profiles.items():
        print(f"\n🧪 Testing {profile_name.upper()} profile...")
        
        sandbox = EnhancedPluginSandbox(
            profile_config["limits"],
            profile_config["permissions"], 
            profile_config["config"]
        )
        
        try:
            async with sandbox:
                result = await sandbox.execute_plugin_safe(profile_test_plugin, profile_name)
                
                telemetry = sandbox.get_telemetry()
                violations = sandbox.get_violations()
                
                print(f"  ✅ Profile test completed")
                print(f"  ⏱️ Execution time: {result['execution_time']:.4f}s")
                print(f"  📊 Peak memory: {telemetry.peak_memory_mb:.2f}MB")
                print(f"  🔥 Peak CPU: {telemetry.peak_cpu_percent:.1f}%")
                print(f"  ⚠️ Violations: {len(violations)}")
                print(f"  🌍 Env vars: {result['environment_variables_count']}")
        
        except Exception as e:
            print(f"  ❌ Profile test failed: {e}")
    
    print(f"\n📋 Profile Comparison Summary:")
    print(f"  Development: High limits, low security, development-friendly")
    print(f"  Testing: Balanced limits, medium security, testing-optimized")
    print(f"  Production: Low limits, maximum security, production-hardened")


async def main():
    """Run all advanced configuration examples"""
    
    print("🚀 Enhanced Plugin Sandbox - Advanced Configuration Examples")
    print("=" * 70)
    
    examples = [
        example_1_custom_security_policy,
        example_2_performance_optimization,
        example_3_plugin_chaining,
        example_4_dynamic_configuration,
        example_5_environment_customization,
        example_6_configuration_profiles
    ]
    
    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"❌ Example failed: {e}")
        
        print("\n" + "─" * 70)
    
    print("✅ All advanced configuration examples completed!")
    
    # Summary
    print(f"\n📊 Advanced Configuration Summary:")
    print(f"✅ Custom security policies and module restrictions")
    print(f"✅ Performance optimization techniques")
    print(f"✅ Plugin chaining and pipeline execution")
    print(f"✅ Dynamic configuration and adaptive limits")
    print(f"✅ Environment customization and isolation")
    print(f"✅ Configuration profiles for different use cases")


if __name__ == "__main__":
    asyncio.run(main())
