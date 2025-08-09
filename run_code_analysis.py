#!/usr/bin/env python3
"""NoxPanel Code Analysis and Improvement Script."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from NoxPanel.noxcore.utils.code_analysis import analyze_codebase
from NoxPanel.noxcore.utils.error_handling import handle_error
from NoxPanel.noxcore.utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main() -> None:
    """Main entry point for code analysis."""
    parser = argparse.ArgumentParser(description="NoxPanel Code Analysis Tool")
    parser.add_argument(
        "directory",
        nargs="?",
        default=str(project_root),
        help="Directory to analyze (default: current project)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Report format (default: text)",
    )
    parser.add_argument(
        "--output",
        help="Output file for report (default: stdout)",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Additional patterns to exclude",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--only-active",
        action="store_true",
        help="Only analyze active files (exclude archived/deprecated)",
    )

    args = parser.parse_args()

    setup_logging(
        {
            "version": 1,
            "level": "DEBUG" if args.verbose else "INFO",
            "handlers": {
                "console": {
                    "type": "console",
                    "level": "DEBUG" if args.verbose else "INFO",
                    "format": "enhanced",
                }
            },
            "loggers": {
                "noxpanel": {
                    "level": "DEBUG" if args.verbose else "INFO",
                    "handlers": ["console"],
                }
            },
        }
    )

    logger.info(f"Starting code analysis of {args.directory}")

    exclude_patterns = [
        "*/test_*",
        "*/tests/*",
        "*/__pycache__/*",
        "*/archive/*",
        "*/deprecated/*",
        "*/node_modules/*",
        "*/security/quarantine/*",
        "*/backup_*/*",
    ]

    if args.only_active:
        exclude_patterns.extend(
            [
                "*/backup_*/*",
                "*/examples/*",
                "*/samples/*",
                "*/archive/*",
                "*/deprecated/*",
                "*/legacy/*",
                "*/old/*",
                "*/temp/*",
                "*/tmp/*",
            ]
        )

    exclude_patterns.extend(args.exclude)
    logger.info(f"Exclusion patterns: {exclude_patterns}")

    try:
        issues, report = analyze_codebase(
            args.directory,
            exclude_patterns=exclude_patterns,
            report_format=args.format,
        )

        if args.format == "json":
            results = {
                "timestamp": datetime.utcnow().isoformat(),
                "directory": str(args.directory),
                "issues_count": len(issues),
                "issues": [issue.to_dict() for issue in issues],
                "report": report,
            }
        else:
            results = report

        if args.output:
            output_path = Path(args.output)
            if args.format == "json":
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2)
                logger.info(f"JSON report written to {output_path}")
            else:
                output_path.write_text(str(results), encoding="utf-8")
                logger.info(f"Report written to {output_path}")
        else:
            if args.format == "json":
                print(json.dumps(results, indent=2))
            else:
                print(results)

        logger.info(
            f"Analysis completed: {len(issues)} issues found in {args.directory}"
        )

    except Exception as exc:  # noqa: BLE001
        logger.error(f"Code analysis failed: {exc}")
        handle_error(exc)
        sys.exit(1)

    except (OSError, ValueError) as exc:
        logger.error(f"Code analysis failed due to an expected error: {exc}")
        handle_error(exc)
        sys.exit(1)
    except Exception as exc:
        # Catch-all for unexpected exceptions to ensure graceful shutdown and logging.
        logger.error(f"An unexpected error occurred during code analysis: {exc}")
        handle_error(exc)
        sys.exit(1)
if __name__ == "__main__":
    main()
