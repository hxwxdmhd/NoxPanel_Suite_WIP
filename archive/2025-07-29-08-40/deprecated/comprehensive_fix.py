#!/usr/bin/env python3
"""
Comprehensive NoxPanel/Heimnetz Codebase Fix Script
Performs systematic fixes across the entire codebase
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from NoxPanel.noxcore.utils.logging_config import setup_logging, get_logger
from NoxPanel.noxcore.utils.datetime_utils import utc_now
from NoxPanel.noxcore.utils.error_handling import handle_error

class ComprehensiveFixer:
    """Comprehensive codebase fixer."""
    
    def __init__(self, project_root: Path):
        """Initialize fixer.
        
        Args:
            project_root: Project root directory
        """
        self.project_root = project_root
        self.logger = get_logger('comprehensive_fixer')
        self.fixes_applied = []
        
    def fix_syntax_errors(self) -> int:
        """Fix all syntax errors in the codebase.
        
        Returns:
            Number of syntax errors fixed
        """
        self.logger.info("Starting syntax error fixes...")
        fixes_count = 0
        
        # Common syntax error patterns
        syntax_fixes = [
            # Missing parentheses in print statements
            (r'print\s+([^()]*[^)])\s*$', r'print(\1)'),
            # Missing commas in function calls
            (r'(\w+)\s+(\w+)\s*\)', r'\1, \2)'),
        ]
        
        # Find Python files with syntax errors
        for py_file in self.project_root.rglob('*.py'):
            if self._should_skip_file(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Try to compile to check for syntax errors
                try:
                    compile(content, str(py_file), 'exec')
                except SyntaxError as e:
                    self.logger.info(f"Fixing syntax error in {py_file}: {e}")
                    
                    # Apply common fixes
                    fixed_content = self._apply_syntax_fixes(content, py_file)
                    
                    if fixed_content != content:
                        with open(py_file, 'w', encoding='utf-8') as f:
                            f.write(fixed_content)
                        fixes_count += 1
                        self.fixes_applied.append(f"Fixed syntax error in {py_file}")
                        
            except Exception as e:
                self.logger.warning(f"Could not process {py_file}: {e}")
        
        self.logger.info(f"Fixed {fixes_count} syntax errors")
        return fixes_count
    
    def fix_deprecated_usage(self) -> int:
        """Fix deprecated usage patterns.
        
        Returns:
            Number of deprecated usages fixed
        """
        self.logger.info("Starting deprecated usage fixes...")
        fixes_count = 0
        
        deprecated_fixes = {
            'datetime.now(timezone.utc)': 'datetime.now(timezone.utc)',
            'datetime.fromtimestamp(': 'datetime.fromtimestamp(',
            'utc_now().timestamp()': 'utc_now().timestamp()',
        }
        
        for py_file in self.project_root.rglob('*.py'):
            if self._should_skip_file(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                for deprecated, replacement in deprecated_fixes.items():
                    if deprecated in content:
                        content = content.replace(deprecated, replacement)
                        
                if content != original_content:
                    # Ensure proper imports are added
                    if 'datetime.now(timezone.utc)' in content:
                        if 'from datetime import datetime, timezone' not in content:
                            content = self._add_datetime_imports(content)
                    
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    fixes_count += 1
                    self.fixes_applied.append(f"Fixed deprecated usage in {py_file}")
                    
            except Exception as e:
                self.logger.warning(f"Could not process {py_file}: {e}")
        
        self.logger.info(f"Fixed {fixes_count} deprecated usages")
        return fixes_count
    
    def fix_type_annotations(self) -> int:
        """Add missing type annotations.
        
        Returns:
            Number of type annotations added
        """
        self.logger.info("Starting type annotation fixes...")
        fixes_count = 0
        
        # This would require more sophisticated AST parsing
        # For now, we'll focus on common patterns
        common_type_fixes = [
            # Function parameters
            ('def __init__(self)', 'def __init__(self: "MyClass")'),
            ('def get_connection(self)', 'def get_connection(self) -> Any'),
        ]
        
        # This is a placeholder - real type annotation fixing requires AST manipulation
        self.logger.info(f"Type annotation fixing is complex - skipping for now")
        return fixes_count
    
    def fix_logging_statements(self) -> int:
        """Convert print statements to proper logging.
        
        Returns:
            Number of logging statements fixed
        """
        self.logger.info("Starting logging statement fixes...")
        fixes_count = 0
        
        for py_file in self.project_root.rglob('*.py'):
            if self._should_skip_file(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                modified = False
                new_lines = []
                needs_logger_import = False
                
                for line in lines:
                    if line.strip().startswith('print('):
                        # Convert print to logger
                        print_content = line.strip()[6:-1]  # Remove print( and )
                        new_line = line.replace(line.strip(), f'logger.info({print_content})')
                        new_lines.append(new_line)
                        modified = True
                        needs_logger_import = True
                    else:
                        new_lines.append(line)
                
                if modified:
                    # Add logger import if needed
                    if needs_logger_import:
                        new_lines = self._add_logger_import(new_lines)
                    
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.writelines(new_lines)
                    fixes_count += 1
                    self.fixes_applied.append(f"Fixed logging in {py_file}")
                    
            except Exception as e:
                self.logger.warning(f"Could not process {py_file}: {e}")
        
        self.logger.info(f"Fixed {fixes_count} logging statements")
        return fixes_count
    
    def clean_unused_imports(self) -> int:
        """Remove unused imports.
        
        Returns:
            Number of files with imports cleaned
        """
        self.logger.info("Starting unused import cleanup...")
        fixes_count = 0
        
        # Use autoflake to remove unused imports
        try:
            for py_file in self.project_root.rglob('*.py'):
                if self._should_skip_file(py_file):
                    continue
                
                # Run autoflake on the file
                result = subprocess.run([
                    'python', '-m', 'autoflake', 
                    '--remove-all-unused-imports',
                    '--remove-unused-variables',
                    '--in-place',
                    str(py_file)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    fixes_count += 1
                    
        except Exception as e:
            self.logger.warning(f"Could not run autoflake: {e}")
        
        self.logger.info(f"Cleaned imports in {fixes_count} files")
        return fixes_count
    
    def format_code(self) -> int:
        """Format code using black and isort.
        
        Returns:
            Number of files formatted
        """
        self.logger.info("Starting code formatting...")
        fixes_count = 0
        
        # Format with black
        try:
            result = subprocess.run([
                'python', '-m', 'black', 
                '--line-length', '88',
                str(self.project_root)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("Black formatting completed")
                
        except Exception as e:
            self.logger.warning(f"Could not run black: {e}")
        
        # Sort imports with isort
        try:
            result = subprocess.run([
                'python', '-m', 'isort',
                str(self.project_root)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("Import sorting completed")
                
        except Exception as e:
            self.logger.warning(f"Could not run isort: {e}")
        
        return fixes_count
    
    def archive_deprecated_files(self) -> int:
        """Archive deprecated and obsolete files.
        
        Returns:
            Number of files archived
        """
        self.logger.info("Starting file archival...")
        archived_count = 0
        
        # Create archive directory
        archive_dir = self.project_root / 'archive' / utc_now().strftime('%Y-%m-%d')
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Files to archive (empty files, old status files, etc.)
        patterns_to_archive = [
            '*.md',  # Many status markdown files
            '*_COMPLETE.md',
            '*_STATUS.md',
            '*_REPORT.md',
            'AUDIT_*.md',
            'WEEK*_*.md',
        ]
        
        for pattern in patterns_to_archive:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file() and file_path.stat().st_size == 0:
                    # Archive empty files
                    archive_path = archive_dir / file_path.name
                    shutil.move(str(file_path), str(archive_path))
                    archived_count += 1
                    self.fixes_applied.append(f"Archived empty file {file_path.name}")
        
        # Create README in archive
        readme_path = archive_dir / 'README.md'
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(f"# Archived Files - {utc_now().strftime('%Y-%m-%d')}\n\n")
            f.write("Files archived during comprehensive codebase cleanup:\n\n")
            for fix in self.fixes_applied:
                if 'Archived' in fix:
                    f.write(f"- {fix}\n")
        
        self.logger.info(f"Archived {archived_count} files")
        return archived_count
    
    def fix_all(self) -> Dict[str, int]:
        """Apply all fixes.
        
        Returns:
            Dictionary of fix counts
        """
        self.logger.info("Starting comprehensive fixes...")
        
        results = {
            'syntax_errors': self.fix_syntax_errors(),
            'deprecated_usage': self.fix_deprecated_usage(),
            'type_annotations': self.fix_type_annotations(),
            'logging_statements': self.fix_logging_statements(),
            'unused_imports': self.clean_unused_imports(),
            'code_formatting': self.format_code(),
            'archived_files': self.archive_deprecated_files(),
        }
        
        total_fixes = sum(results.values())
        self.logger.info(f"Applied {total_fixes} total fixes")
        
        return results
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped.
        
        Args:
            file_path: File path to check
            
        Returns:
            True if file should be skipped
        """
        skip_patterns = [
            '__pycache__',
            '.git',
            'node_modules',
            'archive',
            'deprecated',
            'backup_',
            '.pyc',
            'test_',
            'tests/',
        ]
        
        file_str = str(file_path)
        return any(pattern in file_str for pattern in skip_patterns)
    
    def _apply_syntax_fixes(self, content: str, file_path: Path) -> str:
        """Apply syntax fixes to content.
        
        Args:
            content: File content
            file_path: File path
            
        Returns:
            Fixed content
        """
        # Check for specific known syntax errors
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Fix missing closing parentheses in logger.info
            if 'logger.info(json.dumps(' in line and not line.rstrip().endswith('))'):
                line = line.rstrip() + '))'
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _add_datetime_imports(self, content: str) -> str:
        """Add datetime imports to content.
        
        Args:
            content: File content
            
        Returns:
            Content with imports added
        """
        lines = content.split('\n')
        
        # Find where to insert import
        import_index = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_index = i + 1
            elif line.strip() == '':
                continue
            else:
                break
        
        # Insert import
        import_line = 'from datetime import datetime, timezone'
        if import_line not in content:
            lines.insert(import_index, import_line)
        
        return '\n'.join(lines)
    
    def _add_logger_import(self, lines: List[str]) -> List[str]:
        """Add logger import to lines.
        
        Args:
            lines: File lines
            
        Returns:
            Lines with logger import added
        """
        # Find where to insert import
        import_index = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_index = i + 1
            elif line.strip() == '':
                continue
            else:
                break
        
        # Insert imports
        logger_imports = [
            'from NoxPanel.noxcore.utils.logging_config import get_logger\n',
            'logger = get_logger(__name__)\n',
            '\n'
        ]
        
        for i, import_line in enumerate(logger_imports):
            lines.insert(import_index + i, import_line)
        
        return lines


def main():
    """Main function."""
    # Setup logging
    setup_logging({
        'level': 'INFO',
        'handlers': {
            'console': {'enabled': True, 'level': 'INFO'},
            'file': {'enabled': True, 'level': 'DEBUG', 'file': 'comprehensive_fix.log'}
        }
    })
    
    logger = get_logger('comprehensive_fix')
    logger.info("Starting comprehensive codebase fix")
    
    try:
        fixer = ComprehensiveFixer(project_root)
        results = fixer.fix_all()
        
        # Generate report
        report = {
            'timestamp': utc_now().isoformat(),
            'results': results,
            'fixes_applied': fixer.fixes_applied,
            'total_fixes': sum(results.values())
        }
        
        # Save report
        with open('comprehensive_fix_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Comprehensive fix completed: {report['total_fixes']} total fixes")
        
    except Exception as e:
        logger.error(f"Comprehensive fix failed: {e}")
        handle_error(e, {'script': 'comprehensive_fix'})
        sys.exit(1)


if __name__ == '__main__':
    main()
