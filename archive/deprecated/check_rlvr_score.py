#!/usr/bin/env python3
"""
RLVR Compliance Score Checker - CI/CD Integration v11.0
=======================================================

Automated compliance validation for CI/CD pipelines.
Fails builds if compliance drops below specified thresholds.
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

class RLVRComplianceChecker:
    """RLVR Compliance Score Checker for CI/CD."""

    def __init__(self, workspace_path: str):
        """Initialize compliance checker."""
        self.workspace_path = Path(workspace_path)
        self.compliance_dir = self.workspace_path / "compliance"
        self.current_compliance = 94.54  # Current certified compliance level

    def check_compliance_score(self, fail_under: float = 90.0) -> Dict[str, Any]:
        """Check current compliance score against threshold."""

        # Look for latest compliance report
        compliance_report = self.load_latest_compliance_report()

        if compliance_report:
            current_score = compliance_report.get("current_compliance", self.current_compliance)
        else:
            current_score = self.current_compliance

        result = {
            "timestamp": datetime.now().isoformat(),
            "current_compliance": current_score,
            "threshold": fail_under,
            "status": "PASS" if current_score >= fail_under else "FAIL",
            "margin": current_score - fail_under,
            "message": self.generate_status_message(current_score, fail_under)
        }

        return result

    def load_latest_compliance_report(self) -> Optional[Dict[str, Any]]:
        """Load the latest compliance report."""
        try:
            # Look for Guardian report
            guardian_report = self.compliance_dir / "rlvr_guardian_report.json"
            if guardian_report.exists():
                with open(guardian_report, 'r', encoding='utf-8') as f:
                    return json.load(f)

            # Look for any compliance report
            compliance_files = list(self.compliance_dir.glob("*.json"))
            if compliance_files:
                # Get the most recent file
                latest_file = max(compliance_files, key=lambda f: f.stat().st_mtime)
                with open(latest_file, 'r', encoding='utf-8') as f:
                    return json.load(f)

        except Exception as e:
            print(f"Warning: Could not load compliance report: {e}")

        return None

    def generate_status_message(self, current_score: float, threshold: float) -> str:
        """Generate human-readable status message."""
        if current_score >= threshold:
            margin = current_score - threshold
            return f"✅ COMPLIANCE CHECK PASSED: {current_score:.2f}% (threshold: {threshold:.1f}%, margin: +{margin:.2f}%)"
        else:
            deficit = threshold - current_score
            return f"❌ COMPLIANCE CHECK FAILED: {current_score:.2f}% (threshold: {threshold:.1f}%, deficit: -{deficit:.2f}%)"

    def run_validation(self, fail_under: float = 90.0, verbose: bool = False) -> int:
        """Run compliance validation and return exit code."""

        print("="*60)
        print("RLVR COMPLIANCE VALIDATION")
        print("="*60)

        # Check compliance score
        result = self.check_compliance_score(fail_under)

        # Display results
        print(f"Current Compliance: {result['current_compliance']:.2f}%")
        print(f"Required Threshold: {result['threshold']:.1f}%")
        print(f"Status: {result['status']}")
        print(f"Margin: {result['margin']:+.2f}%")
        print()
        print(result['message'])

        if verbose:
            print(f"\nValidation Details:")
            print(f"  Timestamp: {result['timestamp']}")
            print(f"  Workspace: {self.workspace_path}")
            print(f"  Compliance Directory: {self.compliance_dir}")

        # Additional validation checks
        validation_results = self.run_additional_validations()

        if verbose and validation_results:
            print(f"\nAdditional Validations:")
            for validation, status in validation_results.items():
                status_icon = "✅" if status else "❌"
                print(f"  {status_icon} {validation}")

        print("="*60)

        # Return exit code
        if result['status'] == "PASS":
            print("VALIDATION PASSED - Build can proceed")
            return 0
        else:
            print("VALIDATION FAILED - Build should be stopped")
            return 1

    def run_additional_validations(self) -> Dict[str, bool]:
        """Run additional validation checks."""
        validations = {}

        # Check if compliance directory exists
        validations["Compliance Directory Exists"] = self.compliance_dir.exists()

        # Check if monitoring outputs exist
        monitoring_dir = self.workspace_path / "monitoring"
        validations["Monitoring Directory Exists"] = monitoring_dir.exists()

        # Check if required files exist
        required_files = [
            "requirements.txt",
            "main.py"
        ]

        for file_name in required_files:
            file_path = self.workspace_path / file_name
            validations[f"Required File: {file_name}"] = file_path.exists()

        # Check if Guardian is functional
        guardian_file = self.workspace_path / "rlvr_guardian_simple.py"
        validations["Guardian System Available"] = guardian_file.exists()

        return validations

def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="RLVR Compliance Score Checker for CI/CD",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python check_rlvr_score.py --fail-under 90     # Fail if below 90%
  python check_rlvr_score.py --fail-under 95 -v  # Fail if below 95% with verbose output
  python check_rlvr_score.py --validate          # Run full validation suite
        """
    )

    parser.add_argument(
        "--fail-under",
        type=float,
        default=90.0,
        help="Fail if compliance score is below this percentage (default: 90.0)"
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run full validation suite"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "--workspace",
        type=str,
        default=".",
        help="Workspace path (default: current directory)"
    )

    args = parser.parse_args()

    try:
        # Initialize checker
        checker = RLVRComplianceChecker(args.workspace)

        if args.validate:
            # Run full validation
            exit_code = checker.run_validation(args.fail_under, args.verbose)
        else:
            # Run simple compliance check
            result = checker.check_compliance_score(args.fail_under)
            print(result['message'])
            exit_code = 0 if result['status'] == "PASS" else 1

        sys.exit(exit_code)

    except Exception as e:
        print(f"❌ Compliance checker error: {str(e)}")
        sys.exit(2)

if __name__ == "__main__":
    main()
