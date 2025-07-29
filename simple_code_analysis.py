#!/usr/bin/env python3
"""
Simple Code Analysis Fallback
Basic code analysis that works even when complex analysis fails
"""

import sys
import json
import ast
from pathlib import Path
import argparse

def analyze_python_file(file_path):
    """Analyze a single Python file for basic issues."""
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for syntax errors
        try:
            ast.parse(content)
        except SyntaxError as e:
            issues.append({
                'type': 'syntax_error',
                'severity': 'critical',
                'message': f'Syntax error: {e}',
                'file': str(file_path),
                'line': e.lineno if hasattr(e, 'lineno') else 0
            })
        
        # Check for basic security issues
        content_lower = content.lower()
        if 'password=' in content_lower and '"' in content:
            if any(f'password="{p}"' in content_lower for p in ['password', '123', 'admin']):
                issues.append({
                    'type': 'hardcoded_password',
                    'severity': 'high',
                    'message': 'Potential hardcoded password',
                    'file': str(file_path),
                    'line': 0
                })
                
    except Exception as e:
        issues.append({
            'type': 'analysis_error',
            'severity': 'low',
            'message': f'Could not analyze: {e}',
            'file': str(file_path),
            'line': 0
        })
    
    return issues

def main():
    parser = argparse.ArgumentParser(description='Simple Code Analysis')
    parser.add_argument('--only-active', action='store_true')
    parser.add_argument('--format', default='json')
    parser.add_argument('--output', default='analysis-results.json')
    
    args = parser.parse_args()
    
    # Find Python files
    exclude_patterns = [
        'archive', 'deprecated', 'backup_', '__pycache__', 
        '.git', 'node_modules', 'tests'
    ]
    
    python_files = []
    for py_file in Path('.').rglob('*.py'):
        # Skip excluded paths
        if any(pattern in str(py_file) for pattern in exclude_patterns):
            continue
        python_files.append(py_file)
    
    # Analyze files
    all_issues = []
    for py_file in python_files:
        issues = analyze_python_file(py_file)
        all_issues.extend(issues)
    
    # Count by severity
    severities = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    for issue in all_issues:
        severity = issue.get('severity', 'low')
        severities[severity] = severities.get(severity, 0) + 1
    
    # Create report
    report = {
        'summary': {
            'total_issues': len(all_issues),
            'files_analyzed': len(python_files),
            'severities': severities
        },
        'issues': all_issues
    }
    
    # Output results
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Analysis complete: {len(all_issues)} issues found in {len(python_files)} files")
    print(f"Critical: {severities['critical']}, High: {severities['high']}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())