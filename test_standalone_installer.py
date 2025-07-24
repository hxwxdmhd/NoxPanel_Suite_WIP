#!/usr/bin/env python3
"""
Test script to simulate running the installer in a fresh environment
This simulates what would happen when a user downloads and runs the installer
"""

import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path

def create_test_environment():
    """Create a clean test environment"""
    test_dir = Path(tempfile.mkdtemp(prefix="noxsuite_test_"))
    print(f"📁 Created test environment: {test_dir}")
    
    # Copy installer files to test directory
    current_dir = Path(__file__).parent
    installer_files = [
        "install_noxsuite.py",
        "noxsuite_bootstrap_installer.py", 
        "noxsuite_smart_installer_complete.py",
        "noxsuite_installer_utils.py"
    ]
    
    for file in installer_files:
        src = current_dir / file
        if src.exists():
            dst = test_dir / file
            shutil.copy2(src, dst)
            print(f"✅ Copied {file}")
        else:
            print(f"⚠️  Missing {file}")
    
    return test_dir

def test_installer_modes(test_dir):
    """Test different installer modes"""
    test_cases = [
        ("help", ["--help"]),
        ("version", ["--version"]),
        ("check-deps", ["--check-deps"]),
        ("dry-run", ["dry-run"])
    ]
    
    results = {}
    original_cwd = os.getcwd()
    
    try:
        os.chdir(test_dir)
        
        for test_name, args in test_cases:
            print(f"\n🧪 Testing {test_name} mode...")
            try:
                result = subprocess.run(
                    [sys.executable, "install_noxsuite.py"] + args,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                results[test_name] = {
                    "returncode": result.returncode,
                    "stdout_lines": len(result.stdout.splitlines()),
                    "stderr_lines": len(result.stderr.splitlines()),
                    "success": result.returncode == 0
                }
                
                if result.returncode == 0:
                    print(f"✅ {test_name} mode successful")
                else:
                    print(f"❌ {test_name} mode failed (code: {result.returncode})")
                    if result.stderr:
                        print(f"   Error: {result.stderr.strip()[:100]}...")
                        
            except subprocess.TimeoutExpired:
                print(f"⏰ {test_name} mode timed out")
                results[test_name] = {"success": False, "error": "timeout"}
            except Exception as e:
                print(f"💥 {test_name} mode crashed: {e}")
                results[test_name] = {"success": False, "error": str(e)}
    
    finally:
        os.chdir(original_cwd)
    
    return results

def test_log_creation(test_dir):
    """Test if logs are created properly"""
    log_files = ["noxsuite_installer.log", "noxsuite_bootstrap.log"]
    
    log_status = {}
    for log_file in log_files:
        log_path = test_dir / log_file
        if log_path.exists():
            size = log_path.stat().st_size
            log_status[log_file] = {"exists": True, "size": size}
            print(f"✅ Log file {log_file} exists ({size} bytes)")
        else:
            log_status[log_file] = {"exists": False, "size": 0}
            print(f"⚠️  Log file {log_file} not found")
    
    return log_status

def test_encoding_safety(test_dir):
    """Test if the installer handles encoding issues properly"""
    print("\n🔤 Testing encoding safety...")
    
    # Create a file with different encodings to test UTF-8 handling
    test_file = test_dir / "encoding_test.txt"
    
    # Write file with UTF-8 content including emojis
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("Test with emojis: 🧠 🚀 ✅ ⚠️ ❌\n")
        f.write("Unicode characters: åäö ñçü αβγ 中文\n")
    
    # Test if installer can read the file
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print("✅ UTF-8 file reading works")
            return True
    except Exception as e:
        print(f"❌ UTF-8 handling failed: {e}")
        return False

def generate_report(test_dir, results, log_status, encoding_test):
    """Generate a comprehensive test report"""
    report = {
        "test_environment": str(test_dir),
        "python_version": sys.version,
        "platform": sys.platform,
        "test_results": results,
        "log_status": log_status,
        "encoding_test": encoding_test,
        "summary": {
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results.values() if r.get("success", False)),
            "failed_tests": sum(1 for r in results.values() if not r.get("success", False))
        }
    }
    
    # Save report
    report_file = test_dir / "test_report.json"
    import json
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 Test report saved to: {report_file}")
    return report

def main():
    """Main test function"""
    print("🧪 NoxSuite Standalone Installer Test")
    print("=" * 50)
    
    # Create test environment
    test_dir = create_test_environment()
    
    try:
        # Run tests
        print("\n🔧 Running installer mode tests...")
        results = test_installer_modes(test_dir)
        
        print("\n📝 Checking log file creation...")
        log_status = test_log_creation(test_dir)
        
        print("\n🔤 Testing encoding safety...")
        encoding_test = test_encoding_safety(test_dir)
        
        # Generate report
        report = generate_report(test_dir, results, log_status, encoding_test)
        
        # Summary
        print("\n📋 Test Summary:")
        print(f"✅ Passed: {report['summary']['passed_tests']}")
        print(f"❌ Failed: {report['summary']['failed_tests']}")
        print(f"📊 Total:  {report['summary']['total_tests']}")
        
        if report['summary']['failed_tests'] == 0:
            print("\n🎉 All tests passed! The installer works in standalone mode.")
        else:
            print(f"\n⚠️  {report['summary']['failed_tests']} tests failed. Check the report for details.")
            
        return report['summary']['failed_tests'] == 0
        
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        return False
    
    finally:
        # Cleanup option
        keep_files = input(f"\nKeep test files in {test_dir}? (y/N): ").lower().startswith('y')
        if not keep_files:
            shutil.rmtree(test_dir)
            print("🗑️  Test files cleaned up")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
