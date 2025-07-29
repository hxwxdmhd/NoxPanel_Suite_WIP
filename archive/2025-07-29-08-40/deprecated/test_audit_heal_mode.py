#!/usr/bin/env python3
"""
Test script to verify the audit-heal mode functionality
This creates a test environment and simulates various failure scenarios
"""

import os
import sys
import tempfile
import shutil
import json
from pathlib import Path
import subprocess
import time

def create_test_installation(test_dir: Path, scenario: str = "healthy"):
    """Create a test NoxSuite installation with various issues"""
    print(f"📁 Creating test installation: {scenario}")
    
    # Create basic directory structure
    dirs = [
        "config",
        "config/ai",
        "scripts", 
        "docker",
        "data",
        "data/logs"
    ]
    
    for dir_path in dirs:
        (test_dir / dir_path).mkdir(parents=True, exist_ok=True)
    
    if scenario == "healthy":
        # Create valid configuration files
        create_healthy_config(test_dir)
    elif scenario == "missing_configs":
        # Create directory structure but missing config files
        pass  # Just directories, no config files
    elif scenario == "corrupted_configs":
        # Create corrupted configuration files
        create_corrupted_config(test_dir)
    elif scenario == "encoding_issues":
        # Create config files with encoding issues
        create_encoding_issues(test_dir)
    elif scenario == "permission_issues":
        # Create files with wrong permissions (Unix only)
        create_healthy_config(test_dir)
        if os.name != 'nt':  # Not Windows
            # Make script non-executable
            script_file = test_dir / "scripts" / "start-noxsuite.sh"
            script_file.write_text("#!/bin/bash\necho 'Starting NoxSuite'")
            script_file.chmod(0o644)  # Remove execute permission
    elif scenario == "windows_issues":
        # Create Windows-specific issues
        create_healthy_config(test_dir)
        # Create files without BOM on Windows
        config_file = test_dir / "config" / "noxsuite.json"
        with open(config_file, 'w', encoding='utf-8') as f:  # No BOM
            json.dump({"version": "1.0", "platform": "windows"}, f)

def create_healthy_config(test_dir: Path):
    """Create a healthy configuration"""
    # Main config
    config = {
        "version": "1.0",
        "installation": {
            "directory": str(test_dir),
            "platform": "linux",
            "installed_modules": ["noxpanel", "noxguard"],
            "features": {
                "ai_enabled": True,
                "voice_enabled": False,
                "mobile_enabled": True,
                "dev_mode": False
            }
        },
        "system": {
            "os_type": "linux",
            "architecture": "x86_64",
            "python_version": "3.12.0"
        }
    }
    
    with open(test_dir / "config" / "noxsuite.json", 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    
    # Environment files
    env_vars = {
        "NOXSUITE_VERSION": "1.0.0",
        "NOXSUITE_PLATFORM": "linux",
        "NOXSUITE_INSTALL_PATH": str(test_dir)
    }
    
    with open(test_dir / "config" / ".env", 'w', encoding='utf-8') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    with open(test_dir / "config" / ".env.linux", 'w', encoding='utf-8') as f:
        f.write("DOCKER_BUILDKIT=1\n")
    
    # Database config
    db_config = {
        "default": "sqlite",
        "sqlite": {"path": "data/noxsuite.db", "timeout": 30}
    }
    
    with open(test_dir / "config" / "database.json", 'w', encoding='utf-8') as f:
        json.dump(db_config, f, indent=2)
    
    # Network config
    network_config = {
        "ports": {"web": 3000, "api": 8000},
        "docker": {"network": "noxsuite_network"}
    }
    
    with open(test_dir / "config" / "network.json", 'w', encoding='utf-8') as f:
        json.dump(network_config, f, indent=2)
    
    # Logging config
    logging_config = {
        "version": 1,
        "formatters": {"detailed": {"format": "%(asctime)s [%(levelname)s] %(message)s"}},
        "handlers": {"file": {"class": "logging.FileHandler", "filename": "data/logs/noxsuite.log"}},
        "root": {"level": "INFO", "handlers": ["file"]}
    }
    
    with open(test_dir / "config" / "logging.json", 'w', encoding='utf-8') as f:
        json.dump(logging_config, f, indent=2)
    
    # AI config
    ai_config = {
        "enabled": True,
        "models": [{"name": "mistral:7b-instruct", "enabled": True}]
    }
    
    with open(test_dir / "config" / "ai" / "models.json", 'w', encoding='utf-8') as f:
        json.dump(ai_config, f, indent=2)
    
    # Docker compose
    compose_config = {
        "version": "3.8",
        "services": {
            "noxpanel": {"image": "noxsuite/noxpanel:latest", "ports": ["3000:3000"]}
        }
    }
    
    with open(test_dir / "docker" / "docker-compose.noxsuite.yml", 'w', encoding='utf-8') as f:
        json.dump(compose_config, f, indent=2)  # Using JSON for simplicity
    
    with open(test_dir / "docker" / "docker-compose.development.yml", 'w', encoding='utf-8') as f:
        json.dump({"version": "3.8", "services": {}}, f, indent=2)
    
    with open(test_dir / "docker" / "docker-compose.production.yml", 'w', encoding='utf-8') as f:
        json.dump({"version": "3.8", "services": {}}, f, indent=2)
    
    # Scripts
    if os.name == 'nt':  # Windows
        start_script = test_dir / "scripts" / "start-noxsuite.bat"
        start_script.write_text("@echo off\necho Starting NoxSuite\n", encoding='utf-8')
        
        stop_script = test_dir / "scripts" / "stop-noxsuite.bat"
        stop_script.write_text("@echo off\necho Stopping NoxSuite\n", encoding='utf-8')
    else:  # Unix
        start_script = test_dir / "scripts" / "start-noxsuite.sh"
        start_script.write_text("#!/bin/bash\necho 'Starting NoxSuite'\n", encoding='utf-8')
        start_script.chmod(0o755)
        
        stop_script = test_dir / "scripts" / "stop-noxsuite.sh"
        stop_script.write_text("#!/bin/bash\necho 'Stopping NoxSuite'\n", encoding='utf-8')
        stop_script.chmod(0o755)

def create_corrupted_config(test_dir: Path):
    """Create corrupted configuration files"""
    # Invalid JSON
    with open(test_dir / "config" / "noxsuite.json", 'w', encoding='utf-8') as f:
        f.write("{ invalid json content")
    
    # Missing required fields
    with open(test_dir / "config" / "database.json", 'w', encoding='utf-8') as f:
        json.dump({"incomplete": "config"}, f)

def create_encoding_issues(test_dir: Path):
    """Create files with encoding issues"""
    create_healthy_config(test_dir)
    
    # Create file with wrong encoding on Windows
    if os.name == 'nt':
        config_file = test_dir / "config" / "noxsuite.json"
        # Write without BOM
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump({"version": "1.0", "encoding": "issue"}, f)

def run_audit_test(test_dir: Path, scenario: str) -> dict:
    """Run audit test on a test installation"""
    print(f"\n🔍 Testing audit-heal mode on scenario: {scenario}")
    
    # Run the installer in audit-heal mode
    try:
        # Copy installer files to test directory for easier testing
        current_dir = Path(__file__).parent
        installer_file = current_dir / "noxsuite_smart_installer_complete.py"
        
        if not installer_file.exists():
            print(f"❌ Installer file not found: {installer_file}")
            return {"success": False, "error": "installer_not_found"}
        
        # Change to test directory and run audit
        original_cwd = os.getcwd()
        os.chdir(test_dir)
        
        # Since we can't easily mock user input, we'll test the detection logic
        # by importing and testing individual components
        sys.path.insert(0, str(current_dir))
        
        try:
            from noxsuite_smart_installer_complete import (
                SmartNoxSuiteInstaller, 
                OSType, 
                SystemInfo,
                InstallConfig,
                InstallMode
            )
            
            # Create installer instance
            installer = SmartNoxSuiteInstaller()
            
            # Test installation detection
            installations = installer._detect_existing_installations()
            
            if str(test_dir) not in installations:
                return {"success": False, "error": "installation_not_detected"}
            
            # Test config loading
            config = installer._load_existing_config(test_dir)
            
            if scenario == "healthy" and not config:
                return {"success": False, "error": "failed_to_load_healthy_config"}
            
            # Set up minimal config for testing
            if not config:
                config = InstallConfig(
                    install_directory=test_dir,
                    modules=["noxpanel", "noxguard"],
                    mode=InstallMode.AUDIT_HEAL
                )
            
            installer.config = config
            
            # Test validation
            from noxsuite_smart_installer_complete import InstallationValidator
            validator = InstallationValidator(config, installer.system_info, installer.logger)
            result = validator.validate_complete_installation()
            
            # Test healing if issues found
            healing_result = None
            if not result.all_passed:
                healing_result = validator.attempt_auto_healing(result.failures)
            
            return {
                "success": True,
                "installations_detected": len(installations),
                "config_loaded": config is not None,
                "total_checks": result.total_checks,
                "passed_checks": result.passed_checks,
                "failed_checks": len(result.failures),
                "issues_found": [f.check_name for f in result.failures],
                "healing_attempted": healing_result is not None,
                "healed_count": healing_result.healed_count if healing_result else 0
            }
            
        finally:
            os.chdir(original_cwd)
            if str(current_dir) in sys.path:
                sys.path.remove(str(current_dir))
            
    except Exception as e:
        return {"success": False, "error": str(e), "traceback": str(e)}

def main():
    """Main test function"""
    print("🧪 NoxSuite Audit-Heal Mode Test Suite")
    print("=" * 60)
    
    # Test scenarios
    scenarios = [
        "healthy",
        "missing_configs", 
        "corrupted_configs",
        "encoding_issues",
        "permission_issues"
    ]
    
    # Add Windows-specific scenario if on Windows
    if os.name == 'nt':
        scenarios.append("windows_issues")
    
    results = {}
    
    for scenario in scenarios:
        print(f"\n📋 Testing scenario: {scenario}")
        print("-" * 40)
        
        # Create temporary test directory
        with tempfile.TemporaryDirectory(prefix=f"noxsuite_audit_test_{scenario}_") as temp_dir:
            test_dir = Path(temp_dir)
            
            # Create test installation
            create_test_installation(test_dir, scenario)
            
            # Run audit test
            result = run_audit_test(test_dir, scenario)
            results[scenario] = result
            
            # Display results
            if result["success"]:
                print(f"✅ Test passed")
                print(f"   Installations detected: {result['installations_detected']}")
                print(f"   Config loaded: {result['config_loaded']}")
                print(f"   Validation checks: {result['passed_checks']}/{result['total_checks']} passed")
                
                if result["failed_checks"] > 0:
                    print(f"   Issues found: {', '.join(result['issues_found'])}")
                    print(f"   Issues healed: {result['healed_count']}")
                else:
                    print(f"   No issues found (healthy installation)")
            else:
                print(f"❌ Test failed: {result.get('error', 'unknown error')}")
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 60)
    
    passed_tests = sum(1 for r in results.values() if r["success"])
    total_tests = len(results)
    
    print(f"Passed: {passed_tests}/{total_tests}")
    print(f"Failed: {total_tests - passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Audit-heal mode is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        
        # Show failed tests
        failed_tests = [scenario for scenario, result in results.items() if not result["success"]]
        print(f"Failed scenarios: {', '.join(failed_tests)}")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
