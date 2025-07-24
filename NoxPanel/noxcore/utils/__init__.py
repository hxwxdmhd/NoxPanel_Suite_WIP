"""
NoxPanel Core Utilities Package
Provides common utilities for configuration, datetime handling, error management, 
logging configuration, and code analysis.
"""

from .config import NoxConfig
from .datetime_utils import DateTimeUtils, utc_now, format_iso, parse_iso, time_ago
from .error_handling import (
    ErrorSeverity, ErrorCategory, NoxPanelError, DatabaseError, NetworkError,
    AuthenticationError, ValidationError, PluginError, ConfigurationError,
    ErrorHandler, error_handler, safe_execute, validate_input, handle_error, get_error_summary
)
from .logging_config import (
    NoxPanelFormatter, JSONFormatter, LoggingConfig, setup_logging, get_logger,
    add_context_to_logger, logging_config
)
from .code_analysis import (
    IssueType, IssueSeverity, CodeIssue, CodeAnalyzer, analyze_codebase
)

__all__ = [
    # Configuration
    'NoxConfig',
    
    # DateTime utilities  
    'DateTimeUtils', 'utc_now', 'format_iso', 'parse_iso', 'time_ago',
    
    # Error handling
    'ErrorSeverity', 'ErrorCategory', 'NoxPanelError', 'DatabaseError', 'NetworkError',
    'AuthenticationError', 'ValidationError', 'PluginError', 'ConfigurationError',
    'ErrorHandler', 'error_handler', 'safe_execute', 'validate_input', 'handle_error', 
    'get_error_summary',
    
    # Logging
    'NoxPanelFormatter', 'JSONFormatter', 'LoggingConfig', 'setup_logging', 'get_logger',
    'add_context_to_logger', 'logging_config',
    
    # Code analysis
    'IssueType', 'IssueSeverity', 'CodeIssue', 'CodeAnalyzer', 'analyze_codebase'
]
