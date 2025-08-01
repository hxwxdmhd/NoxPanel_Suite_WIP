#!/usr/bin/env python3
"""
Code Quality Improvement Tool for NoxPanel
Automatically fixes code style issues, unused imports, and formatting
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, cwd=cwd
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def fix_imports_and_formatting():
    """Fix imports and basic formatting issues"""
    print("🔧 Fixing imports and formatting...")
    
    # Run isort to fix imports
    print("  - Running isort...")
    code, out, err = run_command("isort NoxPanel/ --profile black")
    if code == 0:
        print("    ✓ isort completed successfully")
    else:
        print(f"    ⚠ isort had issues: {err}")
    
    # Run black to fix formatting
    print("  - Running black...")
    code, out, err = run_command("black NoxPanel/ --line-length 88")
    if code == 0:
        print("    ✓ black completed successfully")
    else:
        print(f"    ⚠ black had issues: {err}")

def remove_unused_imports():
    """Remove unused imports from files"""
    print("🗑️  Removing unused imports...")
    
    # Install autoflake if not available
    code, _, _ = run_command("which autoflake")
    if code != 0:
        print("  - Installing autoflake...")
        run_command("pip install autoflake")
    
    # Remove unused imports
    code, out, err = run_command(
        "autoflake --remove-all-unused-imports --remove-unused-variables --in-place --recursive NoxPanel/"
    )
    if code == 0:
        print("    ✓ autoflake completed successfully")
    else:
        print(f"    ⚠ autoflake had issues: {err}")

def fix_whitespace_issues():
    """Fix whitespace issues manually"""
    print("📄 Fixing whitespace issues...")
    
    for py_file in Path("NoxPanel").rglob("*.py"):
        try:
            with open(py_file, 'r') as f:
                lines = f.readlines()
            
            # Fix whitespace issues
            fixed_lines = []
            for line in lines:
                # Remove trailing whitespace from blank lines
                if line.strip() == "":
                    fixed_lines.append("\n")
                else:
                    fixed_lines.append(line.rstrip() + "\n")
            
            # Ensure file ends with newline
            if fixed_lines and not fixed_lines[-1].endswith('\n'):
                fixed_lines[-1] += '\n'
            
            with open(py_file, 'w') as f:
                f.writelines(fixed_lines)
            
        except Exception as e:
            print(f"    ⚠ Error fixing {py_file}: {e}")
    
    print("    ✓ Whitespace issues fixed")

def create_code_quality_config():
    """Create code quality configuration files"""
    print("⚙️  Creating code quality configurations...")
    
    # Create .flake8 config
    flake8_config = """[flake8]
max-line-length = 88
extend-ignore = E203, W503, E501
exclude = 
    .git,
    __pycache__,
    archive,
    deprecated,
    backup_*,
    .venv,
    venv,
    build,
    dist,
max-complexity = 10
"""
    
    with open('.flake8', 'w') as f:
        f.write(flake8_config)
    
    # Create pyproject.toml additions for black and isort
    pyproject_addition = """
# Black configuration
[tool.black]
line-length = 88
target-version = ['py310', 'py311', 'py312']
include = '\\.pyi?$'
extend-exclude = '''
/(
  # directories
  \\.eggs
  | \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | build
  | dist
  | archive
  | deprecated
  | backup_.*
)/
'''

# isort configuration
[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
skip_glob = ["archive/*", "deprecated/*", "backup_*/*"]
"""
    
    # Check if pyproject.toml exists and add our config
    if os.path.exists('pyproject.toml'):
        with open('pyproject.toml', 'r') as f:
            content = f.read()
        
        # Only add if not already present
        if '[tool.black]' not in content:
            with open('pyproject.toml', 'a') as f:
                f.write(pyproject_addition)
    
    print("    ✓ Configuration files created")

def run_security_scan():
    """Run security scan with bandit"""
    print("🔒 Running security scan...")
    
    code, out, err = run_command(
        "bandit -r NoxPanel/ -f json -o security_scan_results.json"
    )
    
    # Also run a simple text output
    code, out, err = run_command(
        "bandit -r NoxPanel/ --exclude=*/tests/* -ll"
    )
    
    if code == 0:
        print("    ✓ Security scan completed - no issues found")
    else:
        print(f"    ⚠ Security scan found issues:\n{out}")
    
    return code

def run_type_checking():
    """Run type checking with mypy"""
    print("🔍 Running type checking...")
    
    code, out, err = run_command(
        "mypy NoxPanel/noxcore/ --ignore-missing-imports --no-strict-optional"
    )
    
    if code == 0:
        print("    ✓ Type checking passed")
    else:
        print(f"    ⚠ Type checking found issues:\n{out}")
    
    return code

def get_quality_metrics():
    """Get code quality metrics"""
    print("📊 Generating quality metrics...")
    
    # Count lines of code
    code, out, err = run_command(
        "find NoxPanel/ -name '*.py' -exec wc -l {} + | tail -1"
    )
    total_lines = out.strip().split()[-2] if out.strip() else "unknown"
    
    # Run flake8 to count issues
    code, out, err = run_command(
        "flake8 NoxPanel/noxcore/ --count --statistics"
    )
    
    flake8_issues = out.strip().split('\n')[-1] if out.strip() else "0"
    
    # Count test files
    code, out, err = run_command(
        "find NoxPanel/tests/ -name 'test_*.py' | wc -l"
    )
    test_files = out.strip() if out.strip() else "0"
    
    print(f"    📈 Total lines of code: {total_lines}")
    print(f"    📈 Test files: {test_files}")
    print(f"    📈 Flake8 issues remaining: {flake8_issues}")
    
    return {
        'total_lines': total_lines,
        'test_files': test_files,
        'flake8_issues': flake8_issues
    }

def create_quality_report(metrics):
    """Create a comprehensive quality report"""
    print("📋 Creating quality report...")
    
    report = f"""# NoxPanel Code Quality Report
Generated: {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()}

## Metrics
- **Total Lines of Code**: {metrics['total_lines']}
- **Test Files**: {metrics['test_files']}
- **Flake8 Issues**: {metrics['flake8_issues']}

## Tools Applied
- ✅ **Black**: Code formatting standardized
- ✅ **isort**: Import organization standardized  
- ✅ **autoflake**: Unused imports removed
- ✅ **Bandit**: Security scanning completed
- ✅ **mypy**: Type checking performed
- ✅ **flake8**: Style checking performed

## Quality Improvements Made
1. Fixed import organization and removed unused imports
2. Standardized code formatting with Black
3. Removed trailing whitespace and fixed blank lines
4. Applied consistent 88-character line length
5. Created code quality configuration files
6. Performed security and type checking

## Configuration Files Created
- `.flake8`: Flake8 linting configuration
- `pyproject.toml`: Black and isort configuration

## Recommendations
1. Run `black NoxPanel/` before committing changes
2. Run `flake8 NoxPanel/` to check for style issues
3. Run `bandit -r NoxPanel/` for security scanning
4. Use `isort NoxPanel/` to organize imports
5. Consider adding type hints where missing
"""
    
    with open('CODE_QUALITY_REPORT.md', 'w') as f:
        f.write(report)
    
    print("    ✓ Quality report saved to CODE_QUALITY_REPORT.md")

def main():
    """Main function to run all quality improvements"""
    print("🚀 Starting NoxPanel Code Quality Improvement")
    print("=" * 50)
    
    # Change to project directory
    os.chdir(Path(__file__).parent)
    
    try:
        # Step 1: Create configurations
        create_code_quality_config()
        
        # Step 2: Fix imports and basic issues
        remove_unused_imports()
        
        # Step 3: Fix imports and formatting
        fix_imports_and_formatting()
        
        # Step 4: Fix whitespace issues
        fix_whitespace_issues()
        
        # Step 5: Run security scan
        security_result = run_security_scan()
        
        # Step 6: Run type checking
        type_result = run_type_checking()
        
        # Step 7: Get final metrics
        metrics = get_quality_metrics()
        
        # Step 8: Create report
        create_quality_report(metrics)
        
        print("\n" + "=" * 50)
        print("✅ Code quality improvement completed!")
        print(f"📊 Final flake8 issues: {metrics['flake8_issues']}")
        
        if security_result == 0 and type_result == 0:
            print("🎉 All quality checks passed!")
        else:
            print("⚠️  Some quality checks found issues (see above)")
        
        print("📋 Check CODE_QUALITY_REPORT.md for detailed report")
        
    except Exception as e:
        print(f"❌ Error during quality improvement: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()