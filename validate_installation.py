#!/usr/bin/env python3
"""
NoxSuite Installation Validation Script
Validates that all core components are functional and secure
"""

import sys
import os
import subprocess
from pathlib import Path

def validate_syntax():
    """Validate Python syntax for all active files"""
    print("🔍 Validating Python syntax...")
    
    project_root = Path(__file__).parent
    python_files = list(project_root.rglob("*.py"))
    active_files = [f for f in python_files if "archive" not in str(f)]
    
    errors = []
    for py_file in active_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                compile(f.read(), py_file, 'exec')
        except SyntaxError as e:
            errors.append(f"{py_file}: {e}")
        except Exception as e:
            errors.append(f"{py_file}: {e}")
    
    if errors:
        print(f"❌ Syntax errors found in {len(errors)} files:")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print(f"✅ All {len(active_files)} Python files have valid syntax")
        return True

def validate_imports():
    """Validate that core modules can be imported"""
    print("\n🔍 Validating core imports...")
    
    test_imports = [
        ("NoxPanel.noxcore.database", "NoxDatabase"),
        ("NoxPanel.noxcore.repositories", "_hash_password"),
        ("AI.NoxPanel.test_server_optimized", "app"),
    ]
    
    sys.path.insert(0, str(Path(__file__).parent))
    
    errors = []
    for module, symbol in test_imports:
        try:
            imported_module = __import__(module, fromlist=[symbol])
            getattr(imported_module, symbol)
            print(f"  ✅ {module}.{symbol}")
        except ImportError as e:
            errors.append(f"{module}: Import error - {e}")
        except AttributeError as e:
            errors.append(f"{module}.{symbol}: Symbol not found - {e}")
        except Exception as e:
            errors.append(f"{module}: Unexpected error - {e}")
    
    if errors:
        print(f"❌ Import errors found:")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print(f"✅ All core modules import successfully")
        return True

def validate_security():
    """Check for common security issues"""
    print("\n🔍 Validating security...")
    
    project_root = Path(__file__).parent
    issues = []
    
    # Check for hardcoded secrets
    for py_file in project_root.rglob("*.py"):
        if "archive" in str(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for potential security issues
            if 'password="' in content.lower() and 'test' not in py_file.name.lower():
                if not any(safe in content for safe in ['test', 'example', 'placeholder']):
                    issues.append(f"{py_file}: Potential hardcoded password")
            
            if 'secret_key = ' in content and 'test' not in py_file.name.lower():
                if 'secrets.token' not in content:
                    issues.append(f"{py_file}: Hardcoded secret key")
                    
        except Exception:
            continue
    
    if issues:
        print(f"❌ Security issues found:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("✅ No obvious security issues detected")
        return True

def validate_installer():
    """Test the installer in dry-run mode"""
    print("\n🔍 Validating installer...")
    
    try:
        result = subprocess.run(
            [sys.executable, "install.py", "dry-run"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✅ Installer dry-run completed successfully")
            return True
        else:
            print(f"❌ Installer failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Installer timed out")
        return False
    except Exception as e:
        print(f"❌ Installer test failed: {e}")
        return False

def validate_webapp():
    """Test that the web application can start"""
    print("\n🔍 Validating web application...")
    
    try:
        # Import and test Flask app
        sys.path.insert(0, str(Path(__file__).parent))
        from AI.NoxPanel.test_server_optimized import app
        
        # Check if app has routes
        routes = list(app.url_map.iter_rules())
        if len(routes) > 1:  # More than just static route
            print(f"✅ Flask app has {len(routes)} routes")
            return True
        else:
            print(f"❌ Flask app has insufficient routes")
            return False
            
    except Exception as e:
        print(f"❌ Web application test failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("🧠 NoxSuite Installation Validation")
    print("=" * 50)
    
    tests = [
        ("Syntax Validation", validate_syntax),
        ("Import Validation", validate_imports),
        ("Security Check", validate_security),
        ("Installer Test", validate_installer),
        ("Web App Test", validate_webapp),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print("-" * 50)
    print(f"TOTAL: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All validation tests passed! NoxSuite is ready.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} validation tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())