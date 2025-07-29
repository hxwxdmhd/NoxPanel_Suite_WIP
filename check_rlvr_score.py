#!/usr/bin/env python3
"""
RLVR Score Checker - Compliance Score Validation
Checks RLVR compliance score and fails if below threshold
"""

import argparse
import json
import sys
from pathlib import Path


def check_rlvr_score(
    threshold: float = 90.0, results_file: str = "rlvr_results.json"
) -> int:
    """Check RLVR compliance score against threshold.

    Args:
        threshold: Minimum acceptable compliance score
        results_file: Path to RLVR results file

    Returns:
        0 if score meets threshold, 1 otherwise
    """

    results_path = Path(results_file)

    if not results_path.exists():
        print(f"❌ RLVR results file not found: {results_file}")
        print("💡 Run 'python rlvr_guardian.py --validate' first")
        return 1

    try:
        with open(results_path, "r") as f:
            results = json.load(f)
    except (json.JSONDecodeError, KeyError) as e:
        print(f"❌ Invalid RLVR results file: {e}")
        return 1

    score = results.get("compliance_score", 0)
    status = results.get("status", "UNKNOWN")

    print(f"📊 RLVR Compliance Score: {score:.1f}%")
    print(f"🎯 Required Threshold: {threshold}%")
    print(f"📈 Status: {status}")

    if score >= threshold:
        print(f"✅ Score meets threshold ({score:.1f}% >= {threshold}%)")
        return 0
    else:
        print(f"❌ Score below threshold ({score:.1f}% < {threshold}%)")

        # Show details of failures
        missing_files = results.get("missing_files", [])
        syntax_errors = results.get("syntax_errors", [])

        if missing_files:
            print(f"\n📁 Missing files ({len(missing_files)}):")
            for file in missing_files:
                print(f"   - {file}")

        if syntax_errors:
            print(f"\n🐛 Syntax errors ({len(syntax_errors)}):")
            for error in syntax_errors:
                print(f"   - {error}")

        print("\n💡 Fix the above issues to improve compliance score")
        return 1


def main():
    """Main entry point for RLVR score checker."""
    parser = argparse.ArgumentParser(description="RLVR Score Checker")
    parser.add_argument(
        "--fail-under",
        type=float,
        default=90.0,
        help="Fail if score is under this threshold (default: 90.0)",
    )
    parser.add_argument(
        "--results-file",
        default="rlvr_results.json",
        help="RLVR results file to check (default: rlvr_results.json)",
    )

    args = parser.parse_args()

    return check_rlvr_score(args.fail_under, args.results_file)


if __name__ == "__main__":
    sys.exit(main())
