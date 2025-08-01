"""
NoxPanel Core Utilities Package
Provides common utilities for configuration, datetime handling, error management,
logging configuration, and code analysis.
"""

from .code_analysis import (
    CodeAnalyzer,
    CodeIssue,
    IssueSeverity,
    IssueType,
    analyze_codebase,
)
from .config import NoxConfig
from .datetime_utils import DateTimeUtils, format_iso, parse_iso, time_ago, utc_now
from .error_handling import (
    AuthenticationError,
    ConfigurationError,
    DatabaseError,
    ErrorCategory,
    ErrorHandler,
    ErrorSeverity,
    NetworkError,
    NoxPanelError,
    PluginError,
    ValidationError,
    error_handler,
    get_error_summary,
    handle_error,
    safe_execute,
    validate_input,
)
from .logging_config import (
    JSONFormatter,
    LoggingConfig,
    NoxPanelFormatter,
    add_context_to_logger,
    get_logger,
    logging_config,
    setup_logging,
)

__all__ = [
    # Configuration
    "NoxConfig",
    # DateTime utilities
    "DateTimeUtils",
    "utc_now",
    "format_iso",
    "parse_iso",
    "time_ago",
    # Error handling
    "ErrorSeverity",
    "ErrorCategory",
    "NoxPanelError",
    "DatabaseError",
    "NetworkError",
    "AuthenticationError",
    "ValidationError",
    "PluginError",
    "ConfigurationError",
    "ErrorHandler",
    "error_handler",
    "safe_execute",
    "validate_input",
    "handle_error",
    "get_error_summary",
    # Logging
    "NoxPanelFormatter",
    "JSONFormatter",
    "LoggingConfig",
    "setup_logging",
    "get_logger",
    "add_context_to_logger",
    "logging_config",
    # Code analysis
    "IssueType",
    "IssueSeverity",
    "CodeIssue",
    "CodeAnalyzer",
    "analyze_codebase",
]
