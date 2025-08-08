"""
Centralized Logging Configuration for NoxPanel
Provides structured logging setup with multiple handlers and formatters
"""

import logging
import logging.handlers
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import json


class NoxPanelFormatter(logging.Formatter):
    """Custom formatter for NoxPanel with enhanced metadata."""
    
    def __init__(self, include_context: bool = True):
        """Initialize formatter.
        
        Args:
            include_context: Whether to include context information
        """
        self.include_context = include_context
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with enhanced information.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log message
        """
        # Create timestamp
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc)
        
        # Base message
        base_msg = f"{timestamp.isoformat()} | {record.levelname:8} | {record.name:20} | {record.getMessage()}"
        
        # Add context if available and requested
        if self.include_context and hasattr(record, 'context'):
            context_str = json.dumps(record.context, default=str, separators=(',', ':'))
            base_msg += f" | Context: {context_str}"
        
        # Add exception info if present
        if record.exc_info:
            base_msg += f"\n{self.formatException(record.exc_info)}"
        
        return base_msg


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON formatted log message
        """
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName,
            'process': record.process
        }
        
        # Add context if available
        if hasattr(record, 'context'):
            log_data['context'] = record.context
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info)
            }
        
        return json.dumps(log_data, default=str, separators=(',', ':'))


class LoggingConfig:
    """Centralized logging configuration manager."""
    
    DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DEFAULT_LEVEL = logging.INFO
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize logging configuration.
        
        Args:
            config: Logging configuration dictionary
        """
        self.config = config or self._get_default_config()
        self.handlers: List[logging.Handler] = []
        self.loggers: Dict[str, logging.Logger] = {}
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default logging configuration.
        
        Returns:
            Default configuration dictionary
        """
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'level': 'INFO',
            'format': 'enhanced',
            'handlers': {
                'console': {
                    'enabled': True,
                    'level': 'INFO',
                    'format': 'enhanced'
                },
                'file': {
                    'enabled': True,
                    'level': 'DEBUG',
                    'format': 'enhanced',
                    'filename': 'logs/noxpanel.log',
                    'max_size': '10MB',
                    'backup_count': 5
                },
                'error_file': {
                    'enabled': True,
                    'level': 'ERROR',
                    'format': 'json',
                    'filename': 'logs/noxpanel_errors.log',
                    'max_size': '10MB',
                    'backup_count': 10
                },
                'audit': {
                    'enabled': True,
                    'level': 'INFO',
                    'format': 'json',
                    'filename': 'logs/noxpanel_audit.log',
                    'max_size': '50MB',
                    'backup_count': 20
                }
            },
            'loggers': {
                'noxpanel': {
                    'level': 'DEBUG',
                    'handlers': ['console', 'file', 'error_file']
                },
                'noxpanel.audit': {
                    'level': 'INFO',
                    'handlers': ['audit'],
                    'propagate': False
                },
                'noxpanel.security': {
                    'level': 'WARNING',
                    'handlers': ['console', 'file', 'error_file', 'audit']
                },
                'noxpanel.performance': {
                    'level': 'INFO',
                    'handlers': ['file']
                }
            }
        }
    
    def setup_logging(self) -> None:
        """Setup logging configuration."""
        try:
            # Create logs directory
            log_dir = Path('logs')
            log_dir.mkdir(exist_ok=True)
            
            # Clear existing handlers
            self._clear_handlers()
            
            # Setup handlers
            self._setup_handlers()
            
            # Setup loggers
            self._setup_loggers()
            
            # Set root logger level
            root_logger = logging.getLogger()
            root_logger.setLevel(self._get_log_level(self.config.get('level', 'INFO')))
            
            # Log successful setup
            logger = logging.getLogger('noxpanel.logging')
            logger.info("Logging configuration setup completed successfully")
            
        except Exception as e:
            # Fallback to basic configuration
            logging.basicConfig(
                level=logging.INFO,
                format=self.DEFAULT_FORMAT,
                handlers=[logging.StreamHandler(sys.stdout)]
            )
            logging.error(f"Failed to setup logging configuration, using fallback: {e}")
    
    def _clear_handlers(self) -> None:
        """Clear existing handlers."""
        # Clear root logger handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            handler.close()
        
        # Clear our managed handlers
        for handler in self.handlers:
            handler.close()
        self.handlers.clear()
    
    def _setup_handlers(self) -> None:
        """Setup logging handlers based on configuration."""
        handlers_config = self.config.get('handlers', {})
        
        for handler_name, handler_config in handlers_config.items():
            if not handler_config.get('enabled', True):
                continue
            
            try:
                handler = self._create_handler(handler_name, handler_config)
                if handler:
                    self.handlers.append(handler)
            except Exception as e:
                logging.error(f"Failed to create handler '{handler_name}': {e}")
    
    def _create_handler(self, name: str, config: Dict[str, Any]) -> Optional[logging.Handler]:
        """Create a logging handler based on configuration.
        
        Args:
            name: Handler name
            config: Handler configuration
            
        Returns:
            Configured logging handler or None
        """
        handler_type = config.get('type', name)
        level = self._get_log_level(config.get('level', 'INFO'))
        format_type = config.get('format', 'enhanced')
        
        # Create handler based on type
        if handler_type == 'console' or name == 'console':
            handler = logging.StreamHandler(sys.stdout)
        elif handler_type == 'file' or 'file' in name:
            filename = config.get('filename', f'logs/{name}.log')
            max_size = self._parse_size(config.get('max_size', '10MB'))
            backup_count = config.get('backup_count', 5)
            
            # Ensure directory exists
            Path(filename).parent.mkdir(parents=True, exist_ok=True)
            
            handler = logging.handlers.RotatingFileHandler(
                filename=filename,
                maxBytes=max_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
        else:
            logging.warning(f"Unknown handler type: {handler_type}")
            return None
        
        # Set level and formatter
        handler.setLevel(level)
        handler.setFormatter(self._get_formatter(format_type))
        
        return handler
    
    def _setup_loggers(self) -> None:
        """Setup loggers based on configuration."""
        loggers_config = self.config.get('loggers', {})
        
        for logger_name, logger_config in loggers_config.items():
            logger = logging.getLogger(logger_name)
            
            # Set level
            level = self._get_log_level(logger_config.get('level', 'INFO'))
            logger.setLevel(level)
            
            # Set propagate
            logger.propagate = logger_config.get('propagate', True)
            
            # Add handlers
            handler_names = logger_config.get('handlers', [])
            for handler_name in handler_names:
                handler = self._find_handler(handler_name)
                if handler and handler not in logger.handlers:
                    logger.addHandler(handler)
            
            self.loggers[logger_name] = logger
    
    def _find_handler(self, name: str) -> Optional[logging.Handler]:
        """Find handler by name.
        
        Args:
            name: Handler name
            
        Returns:
            Handler or None if not found
        """
        handlers_config = self.config.get('handlers', {})
        
        for i, handler in enumerate(self.handlers):
            handler_names = list(handlers_config.keys())
            if i < len(handler_names) and handler_names[i] == name:
                return handler
        
        return None
    
    def _get_formatter(self, format_type: str) -> logging.Formatter:
        """Get formatter based on type.
        
        Args:
            format_type: Formatter type
            
        Returns:
            Configured formatter
        """
        if format_type == 'json':
            return JSONFormatter()
        elif format_type == 'enhanced':
            return NoxPanelFormatter(include_context=True)
        else:
            return logging.Formatter(self.DEFAULT_FORMAT)
    
    def _get_log_level(self, level_str: str) -> int:
        """Convert string level to logging level constant.
        
        Args:
            level_str: String representation of log level
            
        Returns:
            Logging level constant
        """
        return getattr(logging, level_str.upper(), logging.INFO)
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string to bytes.
        
        Args:
            size_str: Size string (e.g., '10MB', '1GB')
            
        Returns:
            Size in bytes
        """
        size_str = size_str.upper()
        
        if size_str.endswith('KB'):
            return int(float(size_str[:-2]) * 1024)
        elif size_str.endswith('MB'):
            return int(float(size_str[:-2]) * 1024 * 1024)
        elif size_str.endswith('GB'):
            return int(float(size_str[:-2]) * 1024 * 1024 * 1024)
        else:
            return int(size_str)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get or create logger with proper configuration.
        
        Args:
            name: Logger name
            
        Returns:
            Configured logger
        """
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(name)
        
        # Apply default configuration if not explicitly configured
        if not any(name.startswith(configured_name) for configured_name in self.loggers.keys()):
            logger.setLevel(self.DEFAULT_LEVEL)
            
            # Add console handler if no handlers present
            if not logger.handlers and not logger.parent.handlers:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(self.DEFAULT_LEVEL)
                console_handler.setFormatter(NoxPanelFormatter())
                logger.addHandler(console_handler)
        
        self.loggers[name] = logger
        return logger
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update logging configuration.
        
        Args:
            new_config: New configuration to apply
        """
        self.config.update(new_config)
        self.setup_logging()
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get logging statistics.
        
        Returns:
            Dictionary containing logging statistics
        """
        return {
            'handlers_count': len(self.handlers),
            'loggers_count': len(self.loggers),
            'log_files': [
                str(Path(handler.baseFilename))
                for handler in self.handlers
                if hasattr(handler, 'baseFilename')
            ],
            'root_level': logging.getLogger().level,
            'config_version': self.config.get('version', 1)
        }


# Global logging configuration instance
logging_config = LoggingConfig()


def setup_logging(config: Optional[Dict[str, Any]] = None) -> None:
    """Setup logging with optional configuration.
    
    Args:
        config: Optional logging configuration
    """
    if config:
        logging_config.update_config(config)
    else:
        logging_config.setup_logging()


def get_logger(name: str) -> logging.Logger:
    """Get configured logger.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger
    """
    return logging_config.get_logger(name)


def add_context_to_logger(logger: logging.Logger, context: Dict[str, Any]) -> None:
    """Add context information to all log records from a logger.
    
    Args:
        logger: Logger to modify
        context: Context dictionary to add
    """
    class ContextFilter(logging.Filter):
        def filter(self, record):
            record.context = context
            return True
    
    logger.addFilter(ContextFilter())


# Export main utilities
__all__ = [
    'NoxPanelFormatter',
    'JSONFormatter',
    'LoggingConfig',
    'setup_logging',
    'get_logger',
    'add_context_to_logger',
    'logging_config'
]
