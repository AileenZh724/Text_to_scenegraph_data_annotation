"""Logging configuration for Text2SG.

Provides structured logging with Rich console output and file logging.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback

from .settings import LoggingSettings, get_settings


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Add extra context to log record
        if hasattr(record, 'extra_data'):
            record.msg = f"{record.msg} | {record.extra_data}"
        
        return super().format(record)


class Text2SGLogger:
    """Custom logger class with enhanced functionality."""
    
    def __init__(self, name: str, settings: Optional[LoggingSettings] = None):
        self.name = name
        self.settings = settings or get_settings().logging
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with handlers and formatters."""
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Set logger level
        self.logger.setLevel(getattr(logging, self.settings.level))
        
        # Add console handler if enabled
        if self.settings.console_enabled:
            self._add_console_handler()
        
        # Add file handler if path is specified
        if self.settings.file_path:
            self._add_file_handler()
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def _add_console_handler(self):
        """Add console handler with Rich formatting."""
        if self.settings.rich_enabled:
            console = Console(stderr=True)
            handler = RichHandler(
                console=console,
                show_time=True,
                show_path=True,
                rich_tracebacks=self.settings.rich_traceback,
                markup=True
            )
        else:
            handler = logging.StreamHandler(sys.stderr)
            formatter = StructuredFormatter(self.settings.format)
            handler.setFormatter(formatter)
        
        handler.setLevel(getattr(logging, self.settings.console_level))
        self.logger.addHandler(handler)
    
    def _add_file_handler(self):
        """Add rotating file handler."""
        log_file = Path(self.settings.file_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=self.settings.max_file_size,
            backupCount=self.settings.backup_count,
            encoding='utf-8'
        )
        
        formatter = StructuredFormatter(self.settings.format)
        handler.setFormatter(formatter)
        handler.setLevel(getattr(logging, self.settings.level))
        
        self.logger.addHandler(handler)
    
    def debug(self, msg: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log debug message with optional extra data."""
        self._log(logging.DEBUG, msg, extra_data)
    
    def info(self, msg: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log info message with optional extra data."""
        self._log(logging.INFO, msg, extra_data)
    
    def warning(self, msg: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log warning message with optional extra data."""
        self._log(logging.WARNING, msg, extra_data)
    
    def error(self, msg: str, extra_data: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log error message with optional extra data and exception info."""
        self._log(logging.ERROR, msg, extra_data, exc_info=exc_info)
    
    def critical(self, msg: str, extra_data: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log critical message with optional extra data and exception info."""
        self._log(logging.CRITICAL, msg, extra_data, exc_info=exc_info)
    
    def exception(self, msg: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log exception with traceback."""
        self._log(logging.ERROR, msg, extra_data, exc_info=True)
    
    def _log(self, level: int, msg: str, extra_data: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Internal logging method."""
        extra = {'extra_data': extra_data} if extra_data else {}
        self.logger.log(level, msg, extra=extra, exc_info=exc_info)
    
    def log_function_call(self, func_name: str, args: Optional[Dict[str, Any]] = None, 
                         result: Optional[Any] = None, duration: Optional[float] = None):
        """Log function call with parameters and results."""
        extra_data = {
            'function': func_name,
            'args': args or {},
            'result_type': type(result).__name__ if result is not None else None,
            'duration_ms': round(duration * 1000, 2) if duration else None
        }
        self.info(f"Function call: {func_name}", extra_data)
    
    def log_api_request(self, provider: str, endpoint: str, status_code: Optional[int] = None,
                       duration: Optional[float] = None, error: Optional[str] = None):
        """Log API request details."""
        extra_data = {
            'provider': provider,
            'endpoint': endpoint,
            'status_code': status_code,
            'duration_ms': round(duration * 1000, 2) if duration else None,
            'error': error
        }
        
        if error:
            self.error(f"API request failed: {provider} {endpoint}", extra_data)
        else:
            self.info(f"API request: {provider} {endpoint}", extra_data)
    
    def log_processing_stats(self, operation: str, processed: int, total: int, 
                           duration: Optional[float] = None, errors: int = 0):
        """Log processing statistics."""
        success_rate = ((processed - errors) / processed * 100) if processed > 0 else 0
        
        extra_data = {
            'operation': operation,
            'processed': processed,
            'total': total,
            'errors': errors,
            'success_rate': round(success_rate, 1),
            'duration_s': round(duration, 2) if duration else None
        }
        
        self.info(f"Processing completed: {operation}", extra_data)


# Global logger registry
_loggers: Dict[str, Text2SGLogger] = {}


def setup_logging(settings: Optional[LoggingSettings] = None) -> None:
    """Setup global logging configuration."""
    settings = settings or get_settings().logging
    
    # Install rich traceback if enabled
    if settings.rich_enabled and settings.rich_traceback:
        install_rich_traceback(show_locals=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.level))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Add a basic handler to prevent logging errors
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(settings.format)
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)


def get_logger(name: str, settings: Optional[LoggingSettings] = None) -> Text2SGLogger:
    """Get or create a logger instance."""
    if name not in _loggers:
        _loggers[name] = Text2SGLogger(name, settings)
    return _loggers[name]


def configure_logger(name: str, settings: LoggingSettings) -> Text2SGLogger:
    """Configure a specific logger with custom settings."""
    logger = Text2SGLogger(name, settings)
    _loggers[name] = logger
    return logger


def get_module_logger(module_name: str) -> Text2SGLogger:
    """Get logger for a specific module."""
    return get_logger(f"text2sg.{module_name}")


# Convenience functions for common loggers
def get_api_logger() -> Text2SGLogger:
    """Get logger for API operations."""
    return get_module_logger("api")


def get_processing_logger() -> Text2SGLogger:
    """Get logger for data processing operations."""
    return get_module_logger("processing")


def get_cli_logger() -> Text2SGLogger:
    """Get logger for CLI operations."""
    return get_module_logger("cli")


def get_service_logger(service_name: str) -> Text2SGLogger:
    """Get logger for a specific service."""
    return get_module_logger(f"services.{service_name}")