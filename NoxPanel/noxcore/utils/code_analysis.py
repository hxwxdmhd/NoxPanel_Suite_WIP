"""
Code Analysis and Validation Utilities for NoxPanel
Provides static analysis, code quality checks, and deprecation detection
"""

import ast
import logging
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class IssueType(Enum):
    """Types of code issues that can be detected."""

    DEPRECATED = "deprecated"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    TYPE_HINT = "type_hint"
    IMPORT = "import"
    ERROR_HANDLING = "error_handling"
    LOGGING = "logging"
    COMPATIBILITY = "compatibility"


class IssueSeverity(Enum):
    """Severity levels for code issues."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class CodeIssue:
    """Represents a code issue found during analysis."""

    file_path: str
    line_number: int
    column: int
    issue_type: IssueType
    severity: IssueSeverity
    title: str
    description: str
    suggestion: str = ""
    code_snippet: str = ""
    rule_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert issue to dictionary."""
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "issue_type": self.issue_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "suggestion": self.suggestion,
            "code_snippet": self.code_snippet,
            "rule_id": self.rule_id,
        }


class CodeAnalyzer:
    """Static code analyzer for detecting issues and patterns."""

    # Deprecated patterns to detect
    DEPRECATED_PATTERNS = {
        "datetime.now(timezone.utc)": {
            "replacement": "datetime.now(timezone.utc)",
            "reason": "datetime.now(timezone.utc) is deprecated in Python 3.12+",
            "severity": IssueSeverity.HIGH,
        },
        "datetime.utcfromtimestamp": {
            "replacement": "datetime.fromtimestamp(ts, tz=timezone.utc)",
            "reason": "datetime.fromtimestamp() is deprecated in Python 3.12+",
            "severity": IssueSeverity.HIGH,
        },
        "collections.Mapping": {
            "replacement": "collections.abc.Mapping",
            "reason": "collections.Mapping moved to collections.abc",
            "severity": IssueSeverity.MEDIUM,
        },
        "collections.MutableMapping": {
            "replacement": "collections.abc.MutableMapping",
            "reason": "collections.MutableMapping moved to collections.abc",
            "severity": IssueSeverity.MEDIUM,
        },
        "imp.": {
            "replacement": "importlib",
            "reason": "imp module is deprecated, use importlib",
            "severity": IssueSeverity.HIGH,
        },
        "distutils": {
            "replacement": "setuptools or packaging",
            "reason": "distutils is deprecated and removed in Python 3.12",
            "severity": IssueSeverity.CRITICAL,
        },
    }

    # Security patterns to detect
    SECURITY_PATTERNS = {
        "eval(": {
            "reason": "eval() can execute arbitrary code",
            "severity": IssueSeverity.CRITICAL,
        },
        "exec(": {
            "reason": "exec() can execute arbitrary code",
            "severity": IssueSeverity.CRITICAL,
        },
        "subprocess.call": {
            "reason": "Use subprocess.run() instead for better security",
            "severity": IssueSeverity.MEDIUM,
        },
        "shell=True": {
            "reason": "shell=True can be vulnerable to injection attacks",
            "severity": IssueSeverity.HIGH,
        },
        "pickle.load": {
            "reason": "pickle.load can execute arbitrary code from untrusted data",
            "severity": IssueSeverity.HIGH,
        },
        "yaml.load": {
            "reason": "Use yaml.safe_load() instead to prevent code execution",
            "severity": IssueSeverity.HIGH,
        },
    }

    def __init__(self):
        """Initialize code analyzer."""
        self.issues: List[CodeIssue] = []
        self.file_count = 0
        self.line_count = 0

    def analyze_file(self, file_path: Path) -> List[CodeIssue]:
        """Analyze a single Python file.

        Args:
            file_path: Path to Python file

        Returns:
            List of issues found in the file
        """
        issues = []

        try:
            if not file_path.exists() or file_path.suffix != ".py":
                return issues

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.splitlines()

            self.file_count += 1
            self.line_count += len(lines)

            # Analyze with AST
            try:
                tree = ast.parse(content, filename=str(file_path))
                issues.extend(self._analyze_ast(tree, str(file_path), lines))
            except SyntaxError as e:
                issues.append(
                    CodeIssue(
                        file_path=str(file_path),
                        line_number=e.lineno or 1,
                        column=e.offset or 0,
                        issue_type=IssueType.COMPATIBILITY,
                        severity=IssueSeverity.CRITICAL,
                        title="Syntax Error",
                        description=f"Syntax error: {e.msg}",
                        rule_id="syntax-error",
                    )
                )

            # Analyze line by line for patterns
            issues.extend(self._analyze_patterns(str(file_path), lines))

            # Analyze imports
            issues.extend(self._analyze_imports(str(file_path), lines))

            # Analyze logging usage
            issues.extend(self._analyze_logging(str(file_path), lines))

        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            issues.append(
                CodeIssue(
                    file_path=str(file_path),
                    line_number=1,
                    column=0,
                    issue_type=IssueType.ERROR_HANDLING,
                    severity=IssueSeverity.MEDIUM,
                    title="Analysis Error",
                    description=f"Could not analyze file: {e}",
                    rule_id="analysis-error",
                )
            )

        return issues

    def _analyze_ast(
        self, tree: ast.AST, file_path: str, lines: List[str]
    ) -> List[CodeIssue]:
        """Analyze using AST.

        Args:
            tree: AST tree
            file_path: File path
            lines: File lines

        Returns:
            List of issues found
        """
        issues = []

        class Visitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node):
                # Check for missing type hints
                if not node.returns and not node.name.startswith("_"):
                    issues.append(
                        CodeIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            column=node.col_offset,
                            issue_type=IssueType.TYPE_HINT,
                            severity=IssueSeverity.LOW,
                            title="Missing Return Type Hint",
                            description=f"Function '{node.name}' is missing return type annotation",
                            suggestion="Add return type annotation: def func() -> ReturnType:",
                            rule_id="missing-return-type",
                        )
                    )

                # Check for missing parameter type hints
                for arg in node.args.args:
                    if not arg.annotation and not arg.arg.startswith("_"):
                        issues.append(
                            CodeIssue(
                                file_path=file_path,
                                line_number=node.lineno,
                                column=node.col_offset,
                                issue_type=IssueType.TYPE_HINT,
                                severity=IssueSeverity.LOW,
                                title="Missing Parameter Type Hint",
                                description=f"Parameter '{arg.arg}' in function '{node.name}' is missing type annotation",
                                suggestion="Add parameter type annotation: def func(param: ParamType):",
                                rule_id="missing-param-type",
                            )
                        )

                self.generic_visit(node)

            def visit_Try(self, node):
                # Check for bare except clauses
                for handler in node.handlers:
                    if not handler.type:
                        issues.append(
                            CodeIssue(
                                file_path=file_path,
                                line_number=handler.lineno,
                                column=handler.col_offset,
                                issue_type=IssueType.ERROR_HANDLING,
                                severity=IssueSeverity.MEDIUM,
                                title="Bare Except Clause",
                                description="Using bare 'except Exception:' clause can hide errors",
                                suggestion="Use specific exception types: except SpecificError:",
                                rule_id="bare-except",
                            )
                        )

                self.generic_visit(node)

            def visit_Call(self, node):
                # Check for print statements
                if isinstance(node.func, ast.Name) and node.func.id == "print":
                    issues.append(
                        CodeIssue(
                            file_path=file_path,
                            line_number=node.lineno,
                            column=node.col_offset,
                            issue_type=IssueType.LOGGING,
                            severity=IssueSeverity.LOW,
                            title="Print Statement",
                            description="Using print() instead of proper logging",
                            suggestion="Use logger.info(), logger.debug(), etc. instead",
                            rule_id="print-statement",
                        )
                    )

                self.generic_visit(node)

        visitor = Visitor()
        visitor.visit(tree)

        return issues

    def _analyze_patterns(self, file_path: str, lines: List[str]) -> List[CodeIssue]:
        """Analyze for deprecated and security patterns.

        Args:
            file_path: File path
            lines: File lines

        Returns:
            List of issues found
        """
        issues = []

        # Skip analysis if this is the code_analysis.py file itself
        if "code_analysis.py" in file_path:
            return issues

        for line_num, line in enumerate(lines, 1):
            stripped_line = line.strip()

            # Skip comments, docstrings, and dictionary definitions
            if (
                stripped_line.startswith("#")
                or stripped_line.startswith('"""')
                or stripped_line.startswith("'''")
                or "': {" in stripped_line
                or "'reason':" in stripped_line
                or "'replacement':" in stripped_line
            ):
                continue

            # Check deprecated patterns
            for pattern, info in self.DEPRECATED_PATTERNS.items():
                if pattern in line and not self._is_in_string_literal(line, pattern):
                    issues.append(
                        CodeIssue(
                            file_path=file_path,
                            line_number=line_num,
                            column=line.find(pattern),
                            issue_type=IssueType.DEPRECATED,
                            severity=info["severity"],
                            title="Deprecated Code",
                            description=info["reason"],
                            suggestion=f"Replace with: {info['replacement']}",
                            code_snippet=line.strip(),
                            rule_id=f"deprecated-{pattern.replace('.', '-').replace('(', '').replace(')', '')}",
                        )
                    )

            # Check security patterns
            for pattern, info in self.SECURITY_PATTERNS.items():
                if pattern in line and not self._is_in_string_literal(line, pattern):
                    issues.append(
                        CodeIssue(
                            file_path=file_path,
                            line_number=line_num,
                            column=line.find(pattern),
                            issue_type=IssueType.SECURITY,
                            severity=info["severity"],
                            title="Security Issue",
                            description=info["reason"],
                            code_snippet=line.strip(),
                            rule_id=f"security-{pattern.replace('.', '-').replace('(', '').replace(')', '').replace('=', '')}",
                        )
                    )

        return issues

    def _analyze_imports(self, file_path: str, lines: List[str]) -> List[CodeIssue]:
        """Analyze import statements.

        Args:
            file_path: File path
            lines: File lines

        Returns:
            List of issues found
        """
        issues = []

        import_lines = []
        from_import_lines = []

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("import "):
                import_lines.append((line_num, stripped))
            elif stripped.startswith("from "):
                from_import_lines.append((line_num, stripped))

        # Check for unused imports (basic check)
        # This is a simplified check - full unused import detection requires more analysis

        # Check import organization
        if import_lines and from_import_lines:
            # Check if regular imports come after from imports
            last_import_line = import_lines[-1][0] if import_lines else 0
            first_from_line = (
                from_import_lines[0][0] if from_import_lines else float("inf")
            )

            if last_import_line > first_from_line:
                issues.append(
                    CodeIssue(
                        file_path=file_path,
                        line_number=last_import_line,
                        column=0,
                        issue_type=IssueType.STYLE,
                        severity=IssueSeverity.LOW,
                        title="Import Order",
                        description="Regular imports should come before 'from' imports",
                        suggestion="Organize imports: stdlib, third-party, local imports",
                        rule_id="import-order",
                    )
                )

        return issues

    def _analyze_logging(self, file_path: str, lines: List[str]) -> List[CodeIssue]:
        """Analyze logging usage.

        Args:
            file_path: File path
            lines: File lines

        Returns:
            List of issues found
        """
        issues = []

        has_logging_import = False

        for line_num, line in enumerate(lines, 1):
            line.strip()

            # Check for logging imports
            if "import logging" in line or "from logging" in line:
                has_logging_import = True

            # Check for logger creation
            if "getLogger" in line:
                pass

            # Check for f-string in logging
            if re.search(r'logger\.\w+\(f["\']', line):
                issues.append(
                    CodeIssue(
                        file_path=file_path,
                        line_number=line_num,
                        column=0,
                        issue_type=IssueType.PERFORMANCE,
                        severity=IssueSeverity.LOW,
                        title="F-string in Logging",
                        description="F-strings are evaluated even when logging level is disabled",
                        suggestion="Use lazy formatting: logger.info('Message %s', value)",
                        rule_id="logging-fstring",
                    )
                )

        # Check if file has any logging usage but missing imports
        uses_logging = any("logger." in line for line in lines)
        if uses_logging and not has_logging_import:
            issues.append(
                CodeIssue(
                    file_path=file_path,
                    line_number=1,
                    column=0,
                    issue_type=IssueType.LOGGING,
                    severity=IssueSeverity.MEDIUM,
                    title="Missing Logging Import",
                    description="File uses logging but doesn't import logging module",
                    suggestion="Add: import logging",
                    rule_id="missing-logging-import",
                )
            )

        return issues

    def analyze_directory(
        self, directory: Path, exclude_patterns: Optional[List[str]] = None
    ) -> List[CodeIssue]:
        """Analyze all Python files in a directory.

        Args:
            directory: Directory to analyze
            exclude_patterns: Patterns to exclude (glob style)

        Returns:
            List of all issues found
        """
        if exclude_patterns is None:
            exclude_patterns = [
                "*/test_*",
                "*/tests/*",
                "*/__pycache__/*",
                "*/archive/*",
                "*/deprecated/*",
                "*/node_modules/*",
                "*/security/quarantine/*",
                "*/backup_*/*",
                "*/old/*",
                "*/tmp/*",
                "*/temp/*",
            ]

        all_issues = []

        for py_file in directory.rglob("*.py"):
            # Check if file should be excluded
            skip_file = False
            file_str = str(py_file)

            for pattern in exclude_patterns:
                # Convert glob pattern to simple string matching
                pattern_str = (
                    pattern.replace("*/", "").replace("/*", "").replace("*", "")
                )
                if pattern_str in file_str:
                    skip_file = True
                    break

            if skip_file:
                continue

            issues = self.analyze_file(py_file)
            all_issues.extend(issues)

        self.issues = all_issues
        return all_issues

    def get_summary(self) -> Dict[str, Any]:
        """Get analysis summary.

        Returns:
            Summary dictionary
        """
        issue_counts = {}
        severity_counts = {}

        for issue in self.issues:
            issue_type = issue.issue_type.value
            severity = issue.severity.value

            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            "total_issues": len(self.issues),
            "files_analyzed": self.file_count,
            "lines_analyzed": self.line_count,
            "issue_types": issue_counts,
            "severities": severity_counts,
            "top_issues": [
                issue.to_dict()
                for issue in sorted(
                    self.issues, key=lambda x: (x.severity.value, x.issue_type.value)
                )[:10]
            ],
        }

    def generate_report(self, format_type: str = "text") -> str:
        """Generate analysis report.

        Args:
            format_type: Report format ('text', 'json', 'markdown')

        Returns:
            Formatted report string
        """
        summary = self.get_summary()

        if format_type == "json":
            import json

            return json.dumps(
                {
                    "summary": summary,
                    "issues": [issue.to_dict() for issue in self.issues],
                },
                indent=2,
            )

        elif format_type == "markdown":
            lines = [
                "# Code Analysis Report",
                "",
                f"**Files Analyzed:** {summary['files_analyzed']}",
                f"**Lines Analyzed:** {summary['lines_analyzed']}",
                f"**Total Issues:** {summary['total_issues']}",
                "",
                "## Issue Summary",
                "",
            ]

            for issue_type, count in summary["issue_types"].items():
                lines.append(f"- **{issue_type.title()}:** {count}")

            lines.extend(["", "## Severity Breakdown", ""])

            for severity, count in summary["severities"].items():
                lines.append(f"- **{severity.title()}:** {count}")

            if summary["top_issues"]:
                lines.extend(["", "## Top Issues", ""])
                for issue in summary["top_issues"]:
                    lines.append(f"### {issue['file_path']}:{issue['line_number']}")
                    lines.append(f"**{issue['title']}** ({issue['severity']})")
                    lines.append(f"{issue['description']}")
                    if issue["suggestion"]:
                        lines.append(f"*Suggestion: {issue['suggestion']}*")
                    lines.append("")

            return "\n".join(lines)

        else:  # text format
            lines = [
                "=" * 60,
                "CODE ANALYSIS REPORT",
                "=" * 60,
                f"Files Analyzed: {summary['files_analyzed']}",
                f"Lines Analyzed: {summary['lines_analyzed']}",
                f"Total Issues: {summary['total_issues']}",
                "",
            ]

            if summary["issue_types"]:
                lines.append("Issue Types:")
                for issue_type, count in summary["issue_types"].items():
                    lines.append(f"  {issue_type}: {count}")
                lines.append("")

            if summary["severities"]:
                lines.append("Severities:")
                for severity, count in summary["severities"].items():
                    lines.append(f"  {severity}: {count}")
                lines.append("")

            if self.issues:
                lines.append("Issues Found:")
                lines.append("-" * 40)

                for issue in self.issues[:20]:  # Show first 20 issues
                    lines.extend(
                        [
                            f"File: {issue.file_path}:{issue.line_number}",
                            f"Type: {issue.issue_type.value} ({issue.severity.value})",
                            f"Title: {issue.title}",
                            f"Description: {issue.description}",
                        ]
                    )
                    if issue.suggestion:
                        lines.append(f"Suggestion: {issue.suggestion}")
                    if issue.code_snippet:
                        lines.append(f"Code: {issue.code_snippet}")
                    lines.append("")

                if len(self.issues) > 20:
                    lines.append(f"... and {len(self.issues) - 20} more issues")

            return "\n".join(lines)

    def _is_in_string_literal(self, line: str, pattern: str) -> bool:
        """Check if pattern is inside a string literal.

        Args:
            line: Line to check
            pattern: Pattern to find

        Returns:
            True if pattern is in string literal
        """
        # Simple check for common string literal cases
        pattern_pos = line.find(pattern)
        if pattern_pos == -1:
            return False

        # Check if it's inside quotes
        before_pattern = line[:pattern_pos]
        single_quotes = before_pattern.count("'") - before_pattern.count("\\'")
        double_quotes = before_pattern.count('"') - before_pattern.count('\\"')

        # If odd number of quotes before pattern, it's likely inside a string
        return (single_quotes % 2 == 1) or (double_quotes % 2 == 1)


# Convenience function for quick analysis
def analyze_codebase(
    directory: Union[str, Path],
    exclude_patterns: Optional[List[str]] = None,
    report_format: str = "text",
) -> Tuple[List[CodeIssue], str]:
    """Analyze codebase and return issues and report.

    Args:
        directory: Directory to analyze
        exclude_patterns: Patterns to exclude
        report_format: Report format

    Returns:
        Tuple of (issues list, report string)
    """
    analyzer = CodeAnalyzer()
    issues = analyzer.analyze_directory(Path(directory), exclude_patterns)
    report = analyzer.generate_report(report_format)

    return issues, report


# Export main utilities
__all__ = [
    "IssueType",
    "IssueSeverity",
    "CodeIssue",
    "CodeAnalyzer",
    "analyze_codebase",
]
