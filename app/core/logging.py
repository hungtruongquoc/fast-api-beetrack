"""
Structured logging configuration using structlog

This module provides centralized logging configuration for the FastAPI application.
It supports both development (human-readable) and production (JSON) output formats.

Features:
    - JSON formatting for production environments
    - Human-readable formatting for development
    - Request ID injection for tracing
    - Consistent log structure across the application
    - Environment-based configuration

Usage:
    from app.core.logging import configure_logging, get_logger
    
    # Configure logging on application startup
    configure_logging()
    
    # Get a logger in any module
    logger = get_logger(__name__)
    logger.info("Application started", component="main")
"""

import logging
import sys
from typing import Any, Dict

import structlog
from structlog.types import Processor

from app.core.config import settings


def add_log_level(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add log level to the event dictionary
    
    Args:
        logger: The logger instance (unused)
        method_name: The logging method name (info, error, etc.)
        event_dict: The event dictionary to modify
        
    Returns:
        Modified event dictionary with log level
    """
    event_dict["level"] = method_name.upper()
    return event_dict


def add_timestamp(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add timestamp to the event dictionary
    
    Args:
        logger: The logger instance (unused)
        method_name: The logging method name (unused)
        event_dict: The event dictionary to modify
        
    Returns:
        Modified event dictionary with timestamp
    """
    import datetime
    event_dict["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"
    return event_dict


def configure_logging() -> None:
    """
    Configure structured logging for the application
    
    Sets up structlog with appropriate processors and formatters based on
    the environment. Uses JSON formatting for production and human-readable
    formatting for development.
    """
    # Determine if we're in development mode
    is_dev = settings.ENVIRONMENT == 'development'
    
    # Convert log level string to logging constant
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Common processors for all environments
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        add_timestamp,
    ]
    
    if is_dev:
        # Development: human-readable output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    else:
        # Production: JSON output
        processors = shared_processors + [
            structlog.processors.JSONRenderer()
        ]
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.WriteLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    # Set log levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance
    
    Args:
        name: Logger name, typically __name__ of the calling module
        
    Returns:
        Configured structlog BoundLogger instance
        
    Example:
        logger = get_logger(__name__)
        logger.info("User created", user_id=123, email="user@example.com")
    """
    return structlog.get_logger(name)


def bind_request_context(request_id: str, method: str, path: str) -> None:
    """
    Bind request context to the current structlog context
    
    This function should be called by middleware to add request-specific
    context that will be included in all subsequent log messages.
    
    Args:
        request_id: Unique identifier for the request
        method: HTTP method (GET, POST, etc.)
        path: Request path
        
    Example:
        bind_request_context("req_123", "GET", "/api/v1/items")
    """
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=method,
        path=path,
    )


def clear_request_context() -> None:
    """
    Clear request context from structlog
    
    Should be called at the end of request processing to ensure
    context doesn't leak between requests.
    """
    structlog.contextvars.clear_contextvars()