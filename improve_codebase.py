from datetime import datetime, timezone
from NoxPanel.noxcore.utils.logging_config import get_logger
logger = get_logger(__name__)

#!/usr/bin/env python3
"""
NoxPanel Codebase Improvement Script
Automatically applies fixes for common issues and improvements
"""

import sys
import re
import argparse
from pathlib import Path
import logging
import shutil
from typing import List, Dict, Any, Tuple
import ast

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from NoxPanel.noxcore.utils.code_analysis import CodeAnalyzer, IssueType, IssueSeverity
    from NoxPanel.noxcore.utils.logging_config import setup_logging, get_logger
    from NoxPanel.noxcore.utils.datetime_utils import utc_now
    from NoxPanel.noxcore.utils.error_handling import handle_error, safe_execute
except ImportError as e:
    logger.info(f"Import error: {e}")
    logger.info("Please ensure the NoxPanel package is properly installed")
    sys.exit(1)


class CodeImprover:
    """Automated code improvement tool."""
    
    def __init__((self, dry_run: bool = False, backup: bool = True) -> None:
        """Initialize code improver.
        
        Args:
            dry_run: If True, don't make actual changes
            backup: If True, create backups before changes
        """
        self.dry_run = dry_run
        self.backup = backup
        self.changes_made = 0
        self.files_processed = 0
        self.logger = get_logger('noxpanel.improver')
        
    def improve_file(self, file_path: Path) -> bool:
        """Improve a single Python file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            True if changes were made
        """
        if not file_path.exists() or file_path.suffix != '.py':
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            improved_content = original_content
            changes_made = False
            
            # Apply various improvements
            improved_content, changed = self._fix_datetime_deprecations(improved_content)
            changes_made = changes_made or changed
            
            improved_content, changed = self._fix_print_statements(improved_content)
            changes_made = changes_made or changed
            
            improved_content, changed = self._fix_bare_except(improved_content)
            changes_made = changes_made or changed
            
            improved_content, changed = self._add_type_imports(improved_content)
            changes_made = changes_made or changed
            
            improved_content, changed = self._improve_docstrings(improved_content)
            changes_made = changes_made or changed
            
            improved_content, changed = self._fix_imports(improved_content)
            changes_made = changes_made or changed
            
            # Only write if changes were made
            if changes_made and improved_content != original_content:
                if not self.dry_run:
                    # Create backup if requested
                    if self.backup:
                        backup_path = file_path.with_suffix('.py.backup')
                        shutil.copy2(file_path, backup_path)
                        self.logger.debug(f"Created backup: {backup_path}")
                    
                    # Write improved content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(improved_content)
                
                self.changes_made += 1
                self.logger.info(f"Improved file: {file_path}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error improving file {file_path}: {e}")
            return False
    
    def _fix_datetime_deprecations(self, content: str) -> Tuple[str, bool]:
        """Fix deprecated datetime usage.
        
        Args:
            content: File content
            
        Returns:
            Tuple of (improved_content, changes_made)
        """
        changes_made = False
        
        # Fix datetime.now(timezone.utc) 
        if 'datetime.now(timezone.utc)' in content:
            # Add timezone import if not present
            if 'from datetime import' in content and 'timezone' not in content:
                content = re.sub(
                    r'(from datetime import[^\\n]+)',
                    r'\1, timezone',
                    content
                )
            elif 'import datetime' in content and 'from datetime import' not in content:
                content = re.sub(
                    r'(import datetime)',
                    r'\1\nfrom datetime import timezone',
                    content
                )
            
            # Replace usage
            content = content.replace('datetime.now(timezone.utc)', 'datetime.now(timezone.utc)')
            changes_made = True
        
        # Fix datetime.utcfromtimestamp
        if 'datetime.utcfromtimestamp' in content:
            content = re.sub(
                r'datetime\.utcfromtimestamp\(([^)]+)\)',
                r'datetime.fromtimestamp(\1, tz=timezone.utc)',
                content
            )
            changes_made = True
        
        return content, changes_made
    
    def _fix_print_statements(self, content: str) -> Tuple[str, bool]:
        """Convert print statements to logging where appropriate.
        
        Args:
            content: File content
            
        Returns:
            Tuple of (improved_content, changes_made)
        """
        changes_made = False
        lines = content.splitlines()
        
        # Check if logging is already imported
        has_logging = any('import logging' in line or 'from logging' in line for line in lines)
        has_logger = any('logger = ' in line and 'logging.getLogger' in line for line in lines)
        
        improved_lines = []
        
        for i, line in enumerate(lines):
            # Simple print statement detection
            if re.match(r'\s*print\s*\(', line) and not line.strip().startswith('#'):
                # Don't convert prints in tests or debug code
                if any(pattern in str(line.lower()) for pattern in ['test', 'debug', 'tmp', 'temp']):
                    improved_lines.append(line)
                    continue
                
                # Extract the print content
                match = re.search(r'print\s*\(([^)]+)\)', line)
                if match:
                    print_content = match.group(1)
                    indent = re.match(r'(\s*)', line).group(1)
                    
                    # Simple heuristic for log level
                    if any(word in print_content.lower() for word in ['error', 'fail', 'exception']):
                        log_level = 'error'
                    elif any(word in print_content.lower() for word in ['warn', 'warning']):
                        log_level = 'warning'
                    elif any(word in print_content.lower() for word in ['debug', 'trace']):
                        log_level = 'debug'
                    else:
                        log_level = 'info'
                    
                    # Replace with logger call
                    new_line = f"{indent}logger.{log_level}({print_content})"
                    improved_lines.append(new_line)
                    changes_made = True
                    
                    # Add logging setup if not present
                    if changes_made and not has_logging:
                        # Find a good place to add logging import
                        if i == 0 or (i < len(lines) - 1):
                            improved_lines.insert(-1, "import logging")
                            has_logging = True
                    
                    if changes_made and not has_logger:
                        # Add logger creation
                        improved_lines.insert(-1, f"logger = logging.getLogger(__name__)")
                        has_logger = True
                    
                    continue
            
            improved_lines.append(line)
        
        if changes_made:
            content = '\n'.join(improved_lines)
        
        return content, changes_made
    
    def _fix_bare_except(self, content: str) -> Tuple[str, bool]:
        """Fix bare except clauses.
        
        Args:
            content: File content
            
        Returns:
            Tuple of (improved_content, changes_made)
        """
        changes_made = False
        
        # Replace bare except with Exception
        if re.search(r'except\s*:', content):
            content = re.sub(r'except\s*:', 'except Exception:', content)
            changes_made = True
        
        return content, changes_made
    
    def _add_type_imports(self, content: str) -> Tuple[str, bool]:
        """Add typing imports where needed.
        
        Args:
            content: File content
            
        Returns:
            Tuple of (improved_content, changes_made)
        """
        changes_made = False
        
        # Check if typing imports are needed but missing
        needs_typing = any(pattern in content for pattern in [
            'List[', 'Dict[', 'Optional[', 'Union[', 'Tuple[', 'Callable['
        ])
        
        has_typing = 'from typing import' in content or 'import typing' in content
        
        if needs_typing and not has_typing:
            # Find where imports are
            lines = content.splitlines()
            import_line_idx = -1
            
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    import_line_idx = i
            
            if import_line_idx >= 0:
                # Add typing import after other imports
                typing_imports = []
                if 'List[' in content:
                    typing_imports.append('List')
                if 'Dict[' in content:
                    typing_imports.append('Dict')
                if 'Optional[' in content:
                    typing_imports.append('Optional')
                if 'Union[' in content:
                    typing_imports.append('Union')
                if 'Tuple[' in content:
                    typing_imports.append('Tuple')
                if 'Callable[' in content:
                    typing_imports.append('Callable')
                if 'Any' in content and 'Any' not in typing_imports:
                    typing_imports.append('Any')
                
                if typing_imports:
                    import_line = f"from typing import {', '.join(typing_imports)}"
                    lines.insert(import_line_idx + 1, import_line)
                    content = '\n'.join(lines)
                    changes_made = True
        
        return content, changes_made
    
    def _improve_docstrings(self, content: str) -> Tuple[str, bool]:
        """Improve docstring formatting.
        
        Args:
            content: File content
            
        Returns:
            Tuple of (improved_content, changes_made)
        """
        changes_made = False
        
        # This is a simple improvement - in practice, you'd want more sophisticated docstring analysis
        # For now, just ensure module-level docstrings use triple quotes
        lines = content.splitlines()
        
        if lines and lines[0].startswith('#') and '#!/' not in lines[0]:
            # Convert header comment to docstring
            header_lines = []
            i = 0
            while i < len(lines) and (lines[i].startswith('#') or lines[i].strip() == ''):
                if lines[i].startswith('#'):
                    header_lines.append(lines[i][1:].strip())
                i += 1
            
            if header_lines:
                # Create docstring
                docstring = '"""\n' + '\n'.join(header_lines) + '\n"""'
                new_lines = [docstring, ''] + lines[i:]
                content = '\n'.join(new_lines)
                changes_made = True
        
        return content, changes_made
    
    def _fix_imports(self, content: str) -> Tuple[str, bool]:
        """Fix import organization.
        
        Args:
            content: File content
            
        Returns:
            Tuple of (improved_content, changes_made)
        """
        # This is a simplified import fixer
        # For production use, consider using tools like isort
        changes_made = False
        
        lines = content.splitlines()
        import_lines = []
        from_import_lines = []
        other_lines = []
        
        in_import_section = True
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('import ') and in_import_section:
                import_lines.append(line)
            elif stripped.startswith('from ') and in_import_section:
                from_import_lines.append(line)
            else:
                if stripped and not stripped.startswith('#') and in_import_section:
                    in_import_section = False
                other_lines.append(line)
        
        # Check if reorganization is needed
        if import_lines and from_import_lines:
            original_order = []
            for line in lines:
                if line in import_lines or line in from_import_lines:
                    original_order.append(line)
            
            # Sort imports
            import_lines.sort()
            from_import_lines.sort()
            
            new_order = import_lines + from_import_lines
            
            if original_order != new_order:
                # Rebuild content with sorted imports
                result_lines = []
                import_section_done = False
                
                for line in lines:
                    if line in import_lines or line in from_import_lines:
                        if not import_section_done:
                            result_lines.extend(new_order)
                            if new_order:
                                result_lines.append('')  # Add blank line after imports
                            import_section_done = True
                    else:
                        result_lines.append(line)
                
                content = '\n'.join(result_lines)
                changes_made = True
        
        return content, changes_made
    
    def improve_directory(self, directory: Path, exclude_patterns: List[str] = None) -> Dict[str, Any]:
        """Improve all Python files in a directory.
        
        Args:
            directory: Directory to improve
            exclude_patterns: Patterns to exclude
            
        Returns:
            Summary of improvements made
        """
        if exclude_patterns is None:
            exclude_patterns = ['*/test_*', '*/tests/*', '*/__pycache__/*', '*/archive/*', '*/deprecated/*']
        
        files_changed = []
        
        for py_file in directory.rglob('*.py'):
            # Check if file should be excluded
            skip_file = False
            for pattern in exclude_patterns:
                if py_file.match(pattern):
                    skip_file = True
                    break
            
            if skip_file:
                continue
            
            self.files_processed += 1
            
            if self.improve_file(py_file):
                files_changed.append(str(py_file))
        
        return {
            'files_processed': self.files_processed,
            'files_changed': len(files_changed),
            'changes_made': self.changes_made,
            'changed_files': files_changed
        }


def main() -> bool:
    """Main entry point for code improvement."""
    parser = argparse.ArgumentParser(description='NoxPanel Code Improvement Tool')
    parser.add_argument(
        'directory',
        nargs='?',
        default=str(project_root),
        help='Directory to improve (default: current project)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without making changes'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Don\'t create backup files'
    )
    parser.add_argument(
        '--exclude',
        nargs='*',
        default=['*/test_*', '*/tests/*', '*/__pycache__/*', '*/archive/*', '*/deprecated/*'],
        help='Patterns to exclude'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'  
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging({
        'level': 'DEBUG' if args.verbose else 'INFO',
        'handlers': {
            'console': {
                'enabled': True,
                'level': 'DEBUG' if args.verbose else 'INFO'
            }
        }
    })
    
    logger = get_logger('noxpanel.improver')
    
    try:
        logger.info(f"Starting code improvement of {args.directory}")
        if args.dry_run:
            logger.info("DRY RUN MODE: No changes will be made")
        
        # Run improvements
        improver = CodeImprover(dry_run=args.dry_run, backup=not args.no_backup)
        directory = Path(args.directory)
        
        if not directory.exists():
            logger.error(f"Directory does not exist: {directory}")
            sys.exit(1)
        
        summary = improver.improve_directory(directory, args.exclude)
        
        # Output summary
        logger.info(f"Improvement completed:")
        logger.info(f"  Files processed: {summary['files_processed']}")
        logger.info(f"  Files changed: {summary['files_changed']}")
        logger.info(f"  Total changes: {summary['changes_made']}")
        
        if args.verbose and summary['changed_files']:
            logger.info("Changed files:")
            for file_path in summary['changed_files']:
                logger.info(f"  - {file_path}")
        
        if summary['changes_made'] > 0:
            logger.info("Code improvement completed successfully")
        else:
            logger.info("No improvements needed")
        
    except Exception as e:
        logger.error(f"Improvement failed: {e}")
        handle_error(e, {'directory': args.directory, 'dry_run': args.dry_run})
        sys.exit(1)


if __name__ == '__main__':
    main()
