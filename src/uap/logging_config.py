"""Centralized logging configuration for UAP"""

import logging
import sys
from typing import Any, Dict, Optional

import structlog


def configure_logging(
    level: str = "INFO",
    format_type: str = "json",
    include_timestamps: bool = True
) -> None:
    """Configure structured logging for UAP"""
    
    # Configure standard library logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        stream=sys.stdout
    )
    
    # Configure structlog processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
    ]
    
    if include_timestamps:
        processors.append(structlog.processors.TimeStamper(fmt="iso"))
    
    processors.extend([
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ])
    
    if format_type == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger for a module"""
    return structlog.get_logger(name)


# Global logger instances for different components
core_logger = get_logger("uap.core")
aml_logger = get_logger("uap.aml")
reflection_logger = get_logger("uap.reflection")
storage_logger = get_logger("uap.storage")
transport_logger = get_logger("uap.transport")
bridge_logger = get_logger("uap.bridge")
