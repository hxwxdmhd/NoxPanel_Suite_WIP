"""
Unified Error Handling Utilities for NoxPanel
Provides standardized error handling, logging, and exception management
"""

import logging
import traceback
import sys
from datetime import datetime, timezone
from functools import wraps
from typing import Optional, Dict, Any, Callable, Type, Union, List
from enum import Enum
import json


class ErrorSeverity(Enum):
    """Error severity levels for consistent classification."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ErrorCategory(Enum):
    """Error categories for better organization."""
    SYSTEM = "system"
    DATABASE = "database"
    NETWORK = "network"
    AUTH = "authentication"
    VALIDATION = "validation"
    PLUGIN = "plugin"
    CONFIG = "configuration"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USER = "user"


class NoxPanelError(Exception):
    """Base exception class for NoxPanel with enhanced metadata."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        """Initialize NoxPanel error with comprehensive metadata.
        
        Args:
            message: Error message
            category: Error category
            severity: Error severity level
            details: Additional error details
            context: Context information when error occurred
            original_exception: Original exception if this is a wrapper
        """
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.details = details or {}
        self.context = context or {}
        self.original_exception = original_exception
        self.timestamp = datetime.now(timezone.utc)
        self.error_id = self._generate_error_id()
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID for tracking."""
        import uuid
        return f"NOX-{self.category.value.upper()}-{str(uuid.uuid4())[:8]}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            'error_id': self.error_id,
            'message': self.message,
            'category': self.category.value,
            'severity': self.severity.value,
            'details': self.details,
            'context': self.context,
            'timestamp': self.timestamp.isoformat(),
            'original_exception': str(self.original_exception) if self.original_exception else None,
            'traceback': traceback.format_exc() if self.original_exception else None
        }
    
    def __str__(self) -> str:
        """String representation of error."""
        return f"[{self.error_id}] {self.category.value.upper()}: {self.message}"


class DatabaseError(NoxPanelError):
    """Database-specific error."""
    
    def __init__(self, message: str, **kwargs) -> None:
        kwargs.setdefault('category', ErrorCategory.DATABASE)
        kwargs.setdefault('severity', ErrorSeverity.HIGH)
        super().__init__(message, **kwargs)


class NetworkError(NoxPanelError):
    """Network-specific error."""
    
    def __init__(self, message: str, **kwargs) -> None:
        kwargs.setdefault('category', ErrorCategory.NETWORK)
        kwargs.setdefault('severity', ErrorSeverity.MEDIUM)
        super().__init__(message, **kwargs)


class AuthenticationError(NoxPanelError):
    """Authentication-specific error."""
    
    def __init__(self, message: str, **kwargs) -> None:
        kwargs.setdefault('category', ErrorCategory.AUTH)
        kwargs.setdefault('severity', ErrorSeverity.HIGH)
        super().__init__(message, **kwargs)


class ValidationError(NoxPanelError):
    """Validation-specific error."""
    
    def __init__(self, message: str, **kwargs) -> None:
        kwargs.setdefault('category', ErrorCategory.VALIDATION)
        kwargs.setdefault('severity', ErrorSeverity.MEDIUM)
        super().__init__(message, **kwargs)


class PluginError(NoxPanelError):
    """Plugin-specific error."""
    
    def __init__(self, message: str, **kwargs) -> None:
        kwargs.setdefault('category', ErrorCategory.PLUGIN)
        kwargs.setdefault('severity', ErrorSeverity.MEDIUM)
        super().__init__(message, **kwargs)


class ConfigurationError(NoxPanelError):
    """Configuration-specific error."""
    
    def __init__(self, message: str, **kwargs) -> None:
        kwargs.setdefault('category', ErrorCategory.CONFIG)
        kwargs.setdefault('severity', ErrorSeverity.HIGH)
        super().__init__(message, **kwargs)


class ErrorHandler:
    """Centralized error handling with logging and reporting capabilities."""
    
    def __init__(self, logger_name: str = __name__) -> None:
        """Initialize error handler.
        
        Args:
            logger_name: Name for the logger
        """
        self.logger = logging.getLogger(logger_name)
# Security: Audit logging for security events
def log_security_event(event_type: str, details: dict, request_ip: str = None):
    """Log security-related events for audit trails."""
    security_event = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'details': details,
        'request_ip': request_ip,
        'severity': 'security'
    }
    logger.warning(f"SECURITY_EVENT: {json.dumps(security_event)}")

def log_access_attempt(endpoint: str, user_id: str = None, success: bool = True):
    """Log access attempts for security monitoring."""
    log_security_event('access_attempt', {
        'endpoint': endpoint,
        'user_id': user_id,
        'success': success
    })

logger = logging.getLogger(logger_name)
        self.error_count = 0
        self.recent_errors: List[Dict[str, Any]] = []
        self.max_recent_errors = 100
    
    def handle_error(
        self,
        error: Union[Exception, NoxPanelError],
        context: Optional[Dict[str, Any]] = None,
        log_level: int = logging.ERROR
    ) -> str:
        """Handle error with logging and tracking.
        
        Args:
            error: Exception or NoxPanelError to handle
            context: Additional context information
            log_level: Logging level for the error
            
        Returns:
            Error ID for tracking
        """
        self.error_count += 1
        
        # Convert to NoxPanelError if needed
        if not isinstance(error, NoxPanelError):
            nox_error = NoxPanelError(
                message=str(error),
                context=context,
                original_exception=error
            )
        else:
            nox_error = error
            if context:
                nox_error.context.update(context)
        
        # Log the error
        error_dict = nox_error.to_dict()
        
        if nox_error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"CRITICAL ERROR: {nox_error}")
        elif nox_error.severity == ErrorSeverity.HIGH:
            self.logger.error(f"HIGH SEVERITY: {nox_error}")
        elif nox_error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"MEDIUM SEVERITY: {nox_error}")
        else:
            self.logger.info(f"LOW SEVERITY: {nox_error}")
        
        # Add to recent errors
        self.recent_errors.append(error_dict)
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors = self.recent_errors[-self.max_recent_errors:]
        
        return nox_error.error_id
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors.
        
        Returns:
            Dictionary containing error statistics
        """
        categories = {}
        severities = {}
        
        for error in self.recent_errors:
            category = error['category']
            severity = error['severity']
            
            categories[category] = categories.get(category, 0) + 1
            severities[severity] = severities.get(severity, 0) + 1
        
        return {
            'total_errors': self.error_count,
            'recent_errors': len(self.recent_errors),
            'categories': categories,
            'severities': severities,
            'last_error': self.recent_errors[-1] if self.recent_errors else None
        }
    
    def clear_recent_errors(self) -> None:
        """Clear recent errors list."""
        self.recent_errors.clear()
        self.logger.info("Recent errors cleared")


def error_handler(
    category: ErrorCategory = ErrorCategory.SYSTEM,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    reraise: bool = True,
    log_level: int = logging.ERROR
):
    """Decorator for automatic error handling.
    
    Args:
        category: Error category
        severity: Error severity
        reraise: Whether to reraise the exception
        log_level: Logging level
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> None:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = ErrorHandler(func.__module__)
                context = {
                    'function': func.__name__,
                    'args': str(args)[:200],  # Limit to avoid huge logs
                    'kwargs': str(kwargs)[:200]
                }
                
                if isinstance(e, NoxPanelError):
                    error_id = handler.handle_error(e, context, log_level)
                else:
                    nox_error = NoxPanelError(
                        message=str(e),
                        category=category,
                        severity=severity,
                        context=context,
                        original_exception=e
                    )
                    error_id = handler.handle_error(nox_error, context, log_level)
                
                if reraise:
                    raise
                
                return None
        return wrapper
    return decorator


def safe_execute(
    func: Callable,
    *args,
    default_return: Any = None,
    context: Optional[Dict[str, Any]] = None,
    log_errors: bool = True,
    **kwargs
) -> Any:
    """Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Function arguments
        default_return: Default return value on error
        context: Additional context for error logging
        log_errors: Whether to log errors
        **kwargs: Function keyword arguments
        
    Returns:
        Function result or default_return on error
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            handler = ErrorHandler()
            error_context = {
                'function': func.__name__ if hasattr(func, '__name__') else str(func),
                'args': str(args)[:200],
                'kwargs': str(kwargs)[:200]
            }
            if context:
                error_context.update(context)
            
            handler.handle_error(e, error_context)
        
        return default_return


def validate_input(
    value: Any,
    validators: List[Callable[[Any], bool]],
    error_message: str = "Validation failed",
    context: Optional[Dict[str, Any]] = None
) -> Any:
    """Validate input with custom validators.
    
    Args:
        value: Value to validate
        validators: List of validation functions
        error_message: Error message on validation failure
        context: Additional context
        
    Returns:
        Validated value
        
    Raises:
        ValidationError: If validation fails
    """
    for validator in validators:
        try:
            if not validator(value):
                raise ValidationError(
                    error_message,
                    details={'value': str(value)[:100], 'validator': validator.__name__},
                    context=context
                )
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(
                f"Validation error: {str(e)}",
                details={'value': str(value)[:100], 'validator': validator.__name__},
                context=context,
                original_exception=e
            )
    
    return value


# Global error handler instance
global_error_handler = ErrorHandler(__name__)


# Convenience functions
def handle_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> str:
    """Handle error using global handler."""
    return global_error_handler.handle_error(error, context)


def get_error_summary() -> Dict[str, Any]:
    """Get error summary from global handler."""
    return global_error_handler.get_error_summary()


# Export main utilities
__all__ = [
    'ErrorSeverity',
    'ErrorCategory', 
    'NoxPanelError',
    'DatabaseError',
    'NetworkError',
    'AuthenticationError',
    'ValidationError',
    'PluginError',
    'ConfigurationError',
    'ErrorHandler',
    'error_handler',
    'safe_execute',
    'validate_input',
    'handle_error',
    'get_error_summary'
]
