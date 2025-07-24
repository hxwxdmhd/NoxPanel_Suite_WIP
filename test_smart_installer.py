#!/usr/bin/env python3
"""
NoxSuite Smart Installer Test Suite
Basic validation and testing for the smart installer
"""

import sys
import os
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing module imports...")
    
    try:
        from noxsuite_smart_installer_complete import (
            SmartLogger, InstallationAuditor, PlatformDetector, 
            SmartDependencyManager, ConfigurationWizard, SmartNoxSuiteInstaller,
            OSType, InstallMode, SystemInfo, InstallConfig
        )
        print("✅ Core installer modules imported successfully")
        
        from noxsuite_installer_utils import (
            ProgressTracker, FileBackupManager, DockerManager,
            NetworkValidator, SystemResourceMonitor, ConfigurationValidator,
            UpdateChecker
        )
        print("✅ Utility modules imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_logger():
    """Test the SmartLogger functionality"""
    print("🧪 Testing SmartLogger...")
    
    try:
        from noxsuite_smart_installer_complete import SmartLogger
        
        # Create temporary log file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            log_file = f.name
        
        logger = SmartLogger(log_file)
        
        # Test basic logging
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.step_start("test_step", "Testing step functionality")
        logger.step_complete("test_step", {"result": "success"})
        
        # Test UTF-8 support
        logger.info("Testing UTF-8: 🧠 NoxSuite 🚀 Test")
        
        # Verify log file exists and has content
        log_path = Path(log_file)
        if log_path.exists() and log_path.stat().st_size > 0:
            print("✅ SmartLogger working correctly")
            
            # Clean up
            log_path.unlink()
            return True
        else:
            print("❌ Log file not created or empty")
            return False
            
    except Exception as e:
        print(f"❌ SmartLogger test failed: {e}")
        return False

def test_platform_detector():
    """Test the PlatformDetector functionality"""
    print("🧪 Testing PlatformDetector...")
    
    try:
        from noxsuite_smart_installer_complete import PlatformDetector, SmartLogger
        
        # Create mock logger
        logger = SmartLogger()
        detector = PlatformDetector(logger)
        
        # Test system detection
        system_info = detector.detect_system()
        
        # Validate system info
        if (system_info.os_type and 
            system_info.architecture and 
            system_info.python_version and 
            system_info.cpu_cores > 0 and
            system_info.available_memory > 0):
            
            print(f"✅ System detected: {system_info.os_type.value} {system_info.architecture}")
            print(f"   Python: {system_info.python_version}, {system_info.cpu_cores} cores, {system_info.available_memory}GB RAM")
            return True
        else:
            print("❌ Invalid system information detected")
            return False
            
    except Exception as e:
        print(f"❌ PlatformDetector test failed: {e}")
        return False

def test_configuration_wizard():
    """Test the ConfigurationWizard (mock user input)"""
    print("🧪 Testing ConfigurationWizard...")
    
    try:
        from noxsuite_smart_installer_complete import (
            ConfigurationWizard, SmartLogger, PlatformDetector, 
            InstallationAuditor, InstallMode
        )
        
        logger = SmartLogger()
        detector = PlatformDetector(logger)
        system_info = detector.detect_system()
        auditor = InstallationAuditor(Path("test.log"))
        
        wizard = ConfigurationWizard(system_info, logger, auditor)
        
        # Test fast mode configuration (no user input required)
        config = wizard.run_wizard(InstallMode.FAST)
        
        if (config and 
            config.install_directory and 
            config.modules and 
            len(config.modules) > 0):
            
            print(f"✅ Fast mode config created: {len(config.modules)} modules")
            print(f"   Directory: {config.install_directory}")
            return True
        else:
            print("❌ Invalid configuration generated")
            return False
            
    except Exception as e:
        print(f"❌ ConfigurationWizard test failed: {e}")
        return False

def test_atomic_operations():
    """Test atomic operations functionality"""
    print("🧪 Testing AtomicOperation...")
    
    try:
        from noxsuite_smart_installer_complete import AtomicOperation
        
        # Test successful operation
        test_data = {"value": 0}
        
        def increment_func():
            test_data["value"] += 1
            return test_data["value"]
        
        def decrement_func(data):
            test_data["value"] -= 1
        
        def validate_func(data):
            return data > 0
        
        operation = AtomicOperation(
            name="test_increment",
            execute_func=increment_func,
            rollback_func=decrement_func,
            validate_func=validate_func
        )
        
        # Execute operation
        success = operation.execute()
        
        if success and test_data["value"] == 1:
            print("✅ AtomicOperation executed successfully")
            return True
        else:
            print("❌ AtomicOperation failed")
            return False
            
    except Exception as e:
        print(f"❌ AtomicOperation test failed: {e}")
        return False

def test_directory_scaffold():
    """Test directory scaffold functionality"""
    print("🧪 Testing DirectoryScaffold...")
    
    try:
        from noxsuite_smart_installer_complete import DirectoryScaffold, SmartLogger
        
        logger = SmartLogger()
        
        # Create temporary test directory
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir) / "test_install"
            scaffold = DirectoryScaffold(base_path, logger)
            
            # Test directory structure
            structure = {
                "config": {},
                "data": {
                    "logs": {},
                    "backups": {}
                },
                "scripts": {}
            }
            
            # Test dry run first
            success_dry = scaffold.create_structure(structure, dry_run=True)
            
            # Test actual creation
            success_real = scaffold.create_structure(structure, dry_run=False)
            
            # Verify directories were created
            expected_dirs = [
                base_path / "config",
                base_path / "data" / "logs", 
                base_path / "data" / "backups",
                base_path / "scripts"
            ]
            
            all_exist = all(d.exists() and d.is_dir() for d in expected_dirs)
            
            if success_dry and success_real and all_exist:
                print("✅ DirectoryScaffold working correctly")
                return True
            else:
                print("❌ DirectoryScaffold failed")
                return False
                
    except Exception as e:
        print(f"❌ DirectoryScaffold test failed: {e}")
        return False

def test_utilities():
    """Test utility modules"""
    print("🧪 Testing utility modules...")
    
    try:
        from noxsuite_installer_utils import (
            ProgressTracker, NetworkValidator, ConfigurationValidator
        )
        from noxsuite_smart_installer_complete import SmartLogger
        
        logger = SmartLogger()
        
        # Test ProgressTracker
        tracker = ProgressTracker(5, logger)
        start_time = tracker.start_step("test_step")
        tracker.complete_step(start_time)
        
        # Test NetworkValidator
        validator = NetworkValidator(logger)
        # Test with localhost (should always work)
        results = validator.check_connectivity(["http://localhost"], timeout=1)
        
        # Test ConfigurationValidator
        config_validator = ConfigurationValidator(logger)
        
        # Create test JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test": "value"}, f)
            test_json_file = f.name
        
        validation = config_validator.validate_json_config(Path(test_json_file))
        
        # Clean up
        Path(test_json_file).unlink()
        
        if validation.get("valid", False):
            print("✅ Utility modules working correctly")
            return True
        else:
            print("❌ Utility module validation failed")
            return False
            
    except Exception as e:
        print(f"❌ Utility modules test failed: {e}")
        return False

def test_full_installer_dry_run():
    """Test full installer in dry-run mode"""
    print("🧪 Testing full installer (dry-run mode)...")
    
    try:
        from noxsuite_smart_installer_complete import SmartNoxSuiteInstaller, InstallMode
        
        installer = SmartNoxSuiteInstaller()
        
        # Run in dry-run mode (should not make any changes)
        success = installer.run_installation(InstallMode.DRY_RUN)
        
        if success:
            print("✅ Full installer dry-run completed successfully")
            return True
        else:
            print("❌ Full installer dry-run failed")
            return False
            
    except Exception as e:
        print(f"❌ Full installer test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and return results"""
    tests = [
        ("Import Tests", test_imports),
        ("SmartLogger", test_logger),
        ("PlatformDetector", test_platform_detector),
        ("ConfigurationWizard", test_configuration_wizard),
        ("AtomicOperation", test_atomic_operations),
        ("DirectoryScaffold", test_directory_scaffold),
        ("Utility Modules", test_utilities),
        ("Full Installer (Dry Run)", test_full_installer_dry_run)
    ]
    
    print("🚀 Running NoxSuite Smart Installer Test Suite")
    print("=" * 60)
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:<8} {test_name}")
        
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} tests, {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! The installer is ready to use.")
        return True
    else:
        print(f"⚠️  {failed} test(s) failed. Please review the output above.")
        return False

def main():
    """Main test runner"""
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Tests cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test runner crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
