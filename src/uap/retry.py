"""Retry logic with exponential backoff"""

import asyncio
import random
from typing import Any, Callable, Optional, Type, Union
from functools import wraps

from .exceptions import UAPException
from .logging_config import get_logger

logger = get_logger(__name__)


class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: tuple = (Exception,)
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay for the given attempt"""
    delay = config.base_delay * (config.exponential_base ** attempt)
    delay = min(delay, config.max_delay)
    
    if config.jitter:
        # Add random jitter to prevent thundering herd
        delay *= (0.5 + random.random() * 0.5)
    
    return delay


async def retry_async(
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> Any:
    """Retry an async function with exponential backoff"""
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)
        except config.retryable_exceptions as e:
            last_exception = e
            
            if attempt == config.max_attempts - 1:
                # Last attempt, re-raise the exception
                logger.error(
                    "Retry exhausted",
                    function=func.__name__,
                    attempts=config.max_attempts,
                    error=str(e),
                    exc_info=True
                )
                raise e
            
            delay = calculate_delay(attempt, config)
            logger.warning(
                "Retry attempt failed, retrying",
                function=func.__name__,
                attempt=attempt + 1,
                max_attempts=config.max_attempts,
                delay=delay,
                error=str(e)
            )
            
            await asyncio.sleep(delay)
    
    # This should never be reached, but just in case
    if last_exception:
        raise last_exception


def retry_sync(
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> Any:
    """Retry a sync function with exponential backoff"""
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            return func(*args, **kwargs)
        except config.retryable_exceptions as e:
            last_exception = e
            
            if attempt == config.max_attempts - 1:
                # Last attempt, re-raise the exception
                logger.error(
                    "Retry exhausted",
                    function=func.__name__,
                    attempts=config.max_attempts,
                    error=str(e),
                    exc_info=True
                )
                raise e
            
            delay = calculate_delay(attempt, config)
            logger.warning(
                "Retry attempt failed, retrying",
                function=func.__name__,
                attempt=attempt + 1,
                max_attempts=config.max_attempts,
                delay=delay,
                error=str(e)
            )
            
            import time
            time.sleep(delay)
    
    # This should never be reached, but just in case
    if last_exception:
        raise last_exception


def retry(
    config: Optional[RetryConfig] = None,
    retryable_exceptions: Optional[tuple] = None
):
    """Decorator for retrying functions"""
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                retry_config = config or RetryConfig()
                if retryable_exceptions:
                    retry_config.retryable_exceptions = retryable_exceptions
                return await retry_async(func, *args, config=retry_config, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                retry_config = config or RetryConfig()
                if retryable_exceptions:
                    retry_config.retryable_exceptions = retryable_exceptions
                return retry_sync(func, *args, config=retry_config, **kwargs)
            return sync_wrapper
    return decorator
