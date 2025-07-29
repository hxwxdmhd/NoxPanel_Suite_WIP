from NoxPanel.noxcore.utils.logging_config import get_logger
logger = get_logger(__name__)

#!/usr/bin/env python3
"""
NoxPanel Code Analysis and Improvement Script
Runs comprehensive code analysis and generates reports
"""

import sys
import argparse
from pathlib import Path
import logging

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


def main():
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
        default=['*/test_*', '*/tests/*', '*/__pycache__/*', '*/archive/*', '*/deprecated/*', '*/node_modules/*', '*/security/quarantine/*', '*/backup_*/*'],
        help='Patterns to exclude'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--only-active',
        action='store_true',
        help='Only analyze active files (exclude more patterns)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging({
        'level': 'DEBUG' if args.verbose else 'INFO',
        'handlers': {
            'console': {
                'enabled': True,
                'level': 'DEBUG' if args.verbose else 'INFO'
            }
        }
    })
    
    logger = get_logger('noxpanel.analysis')
    
    # Additional exclusions for active files only
    if args.only_active:
        args.exclude.extend([
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
    
    try:
        logger.info(f"Starting code analysis of {args.directory}")
        logger.info(f"Exclusion patterns: {args.exclude}")
        
        # Run analysis
        analyzer = CodeAnalyzer()
        directory = Path(args.directory)
        
        if not directory.exists():
            logger.error(f"Directory does not exist: {directory}")
            sys.exit(1)
        
        issues = analyzer.analyze_directory(directory, args.exclude)
        
        # Generate report
        report = analyzer.generate_report(args.format)
        
        # Output report
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Report written to {output_path}")
        else:
            logger.info(report)
        
        # Summary
        summary = analyzer.get_summary()
        logger.info(f"Analysis completed: {summary['total_issues']} issues found in {summary['files_analyzed']} files")
        
        # Exit with appropriate code
        if summary['total_issues'] > 0:
            critical_issues = sum(1 for issue in issues if issue.severity.value == 'critical')
            high_issues = sum(1 for issue in issues if issue.severity.value == 'high')
            
            if critical_issues > 0:
                logger.error(f"Found {critical_issues} critical issues")
                sys.exit(2)
            elif high_issues > 0:
                logger.warning(f"Found {high_issues} high severity issues")
                sys.exit(1)
        
        logger.info("Code analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        handle_error(e, {'directory': args.directory, 'format': args.format})
        sys.exit(1)


if __name__ == '__main__':
    main()
