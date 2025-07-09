"""
Logging configuration for the AI Core System.

This module provides structured JSON logging with configurable levels
and specialized logging functions for different types of events.
"""

import logging
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional
import structlog
from structlog.stdlib import LoggerFactory

from .config import get_settings


def setup_logging() -> None:
    """Setup structured logging configuration."""
    settings = get_settings()
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.log_format == "json" else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def log_request(
    logger: structlog.stdlib.BoundLogger,
    method: str,
    url: str,
    status_code: int,
    processing_time: float,
    client_ip: str,
    user_agent: str,
    api_key: str,
    **kwargs: Any
) -> None:
    """Log HTTP request details."""
    logger.info(
        "HTTP request",
        method=method,
        url=url,
        status_code=status_code,
        processing_time=processing_time,
        client_ip=client_ip,
        user_agent=user_agent,
        api_key=api_key,
        **kwargs
    )


def log_security_event(
    logger: structlog.stdlib.BoundLogger,
    event_type: str,
    client_ip: str,
    user_agent: str,
    details: Dict[str, Any],
    **kwargs: Any
) -> None:
    """Log security-related events."""
    logger.warning(
        "Security event",
        event_type=event_type,
        client_ip=client_ip,
        user_agent=user_agent,
        details=details,
        timestamp=datetime.utcnow().isoformat(),
        **kwargs
    )


def log_model_operation(
    logger: structlog.stdlib.BoundLogger,
    operation: str,
    model_name: str,
    processing_time: float,
    success: bool,
    error: Optional[str] = None,
    memory_usage: Optional[float] = None,
    **kwargs: Any
) -> None:
    """Log model operations (load, unload, inference)."""
    log_data = {
        "operation": operation,
        "model_name": model_name,
        "processing_time": processing_time,
        "success": success,
        "timestamp": datetime.utcnow().isoformat(),
        **kwargs
    }
    
    if error:
        log_data["error"] = error
    
    if memory_usage:
        log_data["memory_usage"] = memory_usage
    
    if success:
        logger.info("Model operation", **log_data)
    else:
        logger.error("Model operation failed", **log_data)


def log_performance_metrics(
    logger: structlog.stdlib.BoundLogger,
    metric_name: str,
    value: float,
    unit: str,
    tags: Optional[Dict[str, str]] = None,
    **kwargs: Any
) -> None:
    """Log performance metrics."""
    log_data = {
        "metric_name": metric_name,
        "value": value,
        "unit": unit,
        "timestamp": datetime.utcnow().isoformat(),
        **kwargs
    }
    
    if tags:
        log_data["tags"] = tags
    
    logger.info("Performance metric", **log_data)


def log_system_event(
    logger: structlog.stdlib.BoundLogger,
    event_type: str,
    message: str,
    severity: str = "info",
    **kwargs: Any
) -> None:
    """Log system events (startup, shutdown, health checks)."""
    log_data = {
        "event_type": event_type,
        "message": message,
        "severity": severity,
        "timestamp": datetime.utcnow().isoformat(),
        **kwargs
    }
    
    if severity.lower() == "error":
        logger.error("System event", **log_data)
    elif severity.lower() == "warning":
        logger.warning("System event", **log_data)
    else:
        logger.info("System event", **log_data)


# Initialize logging on module import
setup_logging() 