#!/usr/bin/env python3
"""
RLVR Guardian - Compliance Validation System
Simplified version for CI/CD pipeline compatibility
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict


def validate_compliance() -> Dict[str, Any]:
    """Run basic compliance validation."""

    # Basic file structure checks
    project_root = Path(__file__).parent
    required_files = [
        "requirements.txt",
        "install.py",
        "start_noxpanel.py",
        "validate_installation.py",
    ]

    missing_files = []
    for file_path in required_files:
        if not (project_root / file_path).exists():
            missing_files.append(file_path)

    # Check for Python syntax in core files
    syntax_errors = []
    python_files = [
        "install.py",
        "start_noxpanel.py",
        "validate_installation.py",
        "run_code_analysis.py",
    ]

    for py_file in python_files:
        file_path = project_root / py_file
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    compile(f.read(), str(file_path), "exec")
            except SyntaxError as e:
                syntax_errors.append(f"{py_file}: {e}")

    # Calculate compliance score
    total_checks = len(required_files) + len(python_files)
    failed_checks = len(missing_files) + len(syntax_errors)
    compliance_score = max(0, (total_checks - failed_checks) / total_checks * 100)

    return {
        "compliance_score": compliance_score,
        "status": "PASS" if compliance_score >= 90 else "FAIL",
        "missing_files": missing_files,
        "syntax_errors": syntax_errors,
        "total_checks": total_checks,
        "failed_checks": failed_checks,
        "timestamp": Path(__file__).stat().st_mtime,
    }


def main():
    """Main entry point for RLVR Guardian."""
    parser = argparse.ArgumentParser(description="RLVR Guardian Compliance Validator")
    parser.add_argument(
        "--validate", action="store_true", help="Run compliance validation"
    )
    parser.add_argument(
        "--output", default="rlvr_results.json", help="Output file for results"
    )

    args = parser.parse_args()

    if args.validate:
        print("🔍 Running RLVR compliance validation...")
        results = validate_compliance()

        # Save results
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)

        # Print summary
        print(f"📊 Compliance Score: {results['compliance_score']:.1f}%")
        print(f"🎯 Status: {results['status']}")

        if results["missing_files"]:
            print(f"❌ Missing files: {', '.join(results['missing_files'])}")

        if results["syntax_errors"]:
            print(f"🐛 Syntax errors: {len(results['syntax_errors'])}")
            for error in results["syntax_errors"]:
                print(f"   - {error}")

        if results["status"] == "PASS":
            print("✅ RLVR validation passed!")
            return 0
        else:
            print("❌ RLVR validation failed!")
            return 1

    else:
        print("RLVR Guardian - use --validate to run compliance checks")
        return 0


if __name__ == "__main__":
    sys.exit(main())
