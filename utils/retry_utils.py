"""
Retry utilities for handling transient errors.
This module provides decorators and utility functions for retry logic.
"""

import time
import functools
import logging
from typing import Callable, Any, Optional, List, Union, Type

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def retry_on_exception(
    max_retries: int = 5,
    initial_delay: float = 5.0,
    backoff_factor: float = 3.0,
    exception_types: Union[Type[Exception], List[Type[Exception]]] = Exception,
    retry_on_message_patterns: List[str] = None
) -> Callable:
    """
    Decorator that retries a function when specified exceptions occur.
    
    Args:
        max_retries: Maximum number of retry attempts.
        initial_delay: Initial delay between retries in seconds.
        backoff_factor: Factor by which the delay increases with each retry.
        exception_types: Exception type(s) that should trigger a retry.
        retry_on_message_patterns: List of strings that, if found in the exception message,
                                  will trigger a retry. If None, all exceptions of the specified
                                  types will trigger a retry.
    
    Returns:
        Decorated function with retry logic.
    """
    if retry_on_message_patterns is None:
        # Default patterns for rate limiting errors
        retry_on_message_patterns = [
            "rate limit", 
            "too many requests", 
            "ratelimiterror", 
            "timeout", 
            "connection error",
            "service unavailable",
            "internal server error"
        ]
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        logger.info(f"Retry attempt {attempt}/{max_retries} for {func.__name__}")
                    
                    return func(*args, **kwargs)
                
                except exception_types as e:
                    last_exception = e
                    error_message = str(e).lower()
                    
                    # Check if this exception should trigger a retry
                    should_retry = False
                    if retry_on_message_patterns:
                        should_retry = any(pattern.lower() in error_message for pattern in retry_on_message_patterns)
                    else:
                        should_retry = True
                    
                    # If we shouldn't retry or we're out of retries, raise the exception
                    if not should_retry or attempt >= max_retries:
                        logger.error(f"Error in {func.__name__}: {error_message}")
                        raise
                    
                    # Calculate wait time with exponential backoff
                    wait_time = initial_delay * (backoff_factor ** attempt)
                    logger.warning(f"Error: {error_message}. Waiting {wait_time:.2f} seconds before retry...")
                    time.sleep(wait_time)
            
            # This should never be reached due to the raise in the except block
            if last_exception:
                raise last_exception
            
        return wrapper
    
    return decorator
