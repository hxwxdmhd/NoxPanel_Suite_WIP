#!/usr/bin/env python3
"""
NoxPanel Code Analysis and Improvement Script
Runs comprehensive code analysis and generates reports
"""

from NoxPanel.noxcore.utils.logging_config import get_logger
logger = get_logger(__name__)

import sys
import argparse
from pathlib import Path
import logging
import json
from typing import Dict, List, Optional, Any, Union

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from NoxPanel.noxcore.utils.code_analysis import CodeAnalyzer, analyze_codebase
    from NoxPanel.noxcore.utils.logging_config import setup_logging, get_logger
    from NoxPanel.noxcore.utils.datetime_utils import utc_now
    from NoxPanel.noxcore.utils.error_handling import handle_error
except ImportError as e:
    logger.info(f"Import error: {e}")
    logger.info("Please ensure the NoxPanel package is properly installed")
    sys.exit(1)


def main() -> None:
    """Main entry point for code analysis."""
    parser = argparse.ArgumentParser(description='NoxPanel Code Analysis Tool')
    parser.add_argument(
        'directory', 
        nargs='?', 
        default=str(project_root),
        help='Directory to analyze (default: current project)'
    )
    parser.add_argument(
        '--format', 
        choices=['text', 'json', 'markdown'],
        default='text',
        help='Report format (default: text)'
    )
    parser.add_argument(
        '--output', 
        help='Output file for report (default: stdout)'
    )
    parser.add_argument(
        '--exclude',
        nargs='*',
        default=[],
        help='Additional patterns to exclude'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--only-active',
        action='store_true',
        help='Only analyze active files (exclude archived/deprecated)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(
        level=logging.DEBUG if args.verbose else logging.INFO,
        enable_file_logging=True
    )
    
    logger = get_logger('noxpanel.analysis')
    logger.info(f"Starting code analysis of {args.directory}")
    
    # Default exclusion patterns
    exclude_patterns = [
        '*/test_*',
        '*/tests/*',
        '*/__pycache__/*',
        '*/archive/*',
        '*/deprecated/*',
        '*/node_modules/*',
        '*/security/quarantine/*',
        '*/backup_*/*'
    ]
    
    # Additional exclusions for active files only
    if args.only_active:
        exclude_patterns.extend([
            '*/backup_*/*',
            '*/examples/*',
            '*/samples/*',
            '*/archive/*',
            '*/deprecated/*',
            '*/legacy/*',
            '*/old/*',
            '*/temp/*',
            '*/tmp/*'
        ])
    
    # Add user-specified exclusions
    exclude_patterns.extend(args.exclude)
    
    logger.info(f"Exclusion patterns: {exclude_patterns}")
    
    try:
        # Run analysis
        results = analyze_codebase(
            args.directory,
            exclude_patterns=exclude_patterns,
            output_format=args.format
        )
        
        # Output results
        if args.output:
            output_path = Path(args.output)
            if args.format == 'json':
                with open(output_path, 'w') as f:
                    json.dump(results, f, indent=2)
                logger.info(f"Report written to {output_path}")
            else:
                output_path.write_text(str(results), encoding='utf-8')
                logger.info(f"Report written to {output_path}")
        else:
            print(results)
        
        # Check for critical issues
        summary = results if isinstance(results, dict) else {}
        critical_issues = summary.get('summary', {}).get('severities', {}).get('critical', 0)
        
        logger.info(f"Analysis completed: {summary.get('summary', {}).get('total_issues', 0)} issues found in {summary.get('summary', {}).get('files_analyzed', 0)} files")
        
        if critical_issues > 0:
            logger.error(f"Found {critical_issues} critical issues")
            sys.exit(2)
        else:
            logger.info("No critical issues found")
            sys.exit(0)
            
    except Exception as e:
        handle_error(e, "Code analysis failed", logger)
        sys.exit(1)


if __name__ == '__main__':
    main()