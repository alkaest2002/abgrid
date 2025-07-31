"""
Author: Pierpaolo Calanna

Date Created: Jul 1, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import asyncio
import time
import hashlib
from collections import OrderedDict
from functools import wraps
from typing import Tuple, Callable, Any, Awaitable

class RateLimitException(Exception):
    """
    Exception raised when the rate limit is exceeded.

    Attributes:
        message: The error message describing the rate limit violation.
    """
    def __init__(self, message: str = "Rate limit exceeded") -> None:
        """Initialize a RateLimitException with a default error message."""
        self.message = message
        super().__init__(message)

class SimpleRateLimiter:
    """
    JWT-based rate limiter using a sliding window approach with LRU cache.

    This rate limiter extracts JWT tokens from Authorization headers and
    applies rate limiting per token per endpoint using asyncio for FastAPI compatibility.
    
    Args:
        limit: Maximum number of requests allowed per window.
        window_seconds: Time window duration in seconds.
        max_cache_size: Maximum number of entries to keep in cache.
    
    Raises:
        ValueError: If any parameter is <= 0.
    """
    
    def __init__(
        self, 
        limit: int, 
        window_seconds: int,
        max_cache_size: int = 10000
    ) -> None:
        """
        Initialize the rate limiter with asyncio lock for FastAPI compatibility.

        Args:
            limit: Maximum requests allowed per window.
            window_seconds: Duration of rate limit window in seconds.
            max_cache_size: Maximum cache entries to prevent memory leaks.
        """
        if limit <= 0 or window_seconds <= 0 or max_cache_size <= 0:
            raise ValueError("rate_limiter_all_parameters_must_be_positive_integers")
        
        # Create a unique identifier for this limiter instance
        self.limiter_id = f"{limit}req_{window_seconds}s"
            
        # Store values
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_cache_size = max_cache_size
        
        # Cache stores: key -> (window_start_time, request_count)
        self._cache: OrderedDict[str, Tuple[float, int]] = OrderedDict()
        # Use asyncio.Lock for FastAPI async compatibility
        self._lock: asyncio.Lock = asyncio.Lock()

    def __call__(self, func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        """
        Decorator that applies rate limiting to an async function.

        The decorated function must accept a 'request' parameter that contains 
        the HTTP request object with headers.
        
        Args:
            func: Async function to be rate limited.
            
        Returns:
            Wrapped async function with rate limiting applied.

        Raises:
            RateLimitException: When rate limit is exceeded or JWT token is missing.
        """
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not (request := kwargs.get("request")):
                raise RateLimitException("request_object_required_for_rate_limiting")
            key: str = self._get_cache_key(request)
            # Await the async rate limit check
            await self._check_rate_limit(key)
            
            return await func(*args, **kwargs)
        return wrapper

    def _get_cache_key(self, request: Any) -> str:
        """
        Extract JWT token from request and create a unique cache key.

        Args:
            request: HTTP request object with headers and url attributes.
            
        Returns:
            Unique cache key string in format "rate_limit:{token_hash}:{path}".

        Raises:
            RateLimitException: If Authorization header is missing, malformed,
                                or doesn't contain a Bearer token.
        """
        try:
            auth_header = request.headers.get("Authorization", "")
        except (AttributeError, TypeError):
            raise RateLimitException("required_jwt_token")
        
        if not auth_header.startswith("Bearer "):
            raise RateLimitException("required_jwt_token")
            
        if not (token := auth_header[7:].strip()):
            raise RateLimitException("required_jwt_token")
        
        # SECURITY: Validate token size
        if len(token) > 2048:
            raise RateLimitException("jwt_token_too_large")
        
        # SECURITY: Basic format validation
        if token.count('.') != 2:
            raise RateLimitException("invalid_jwt_format")
        
        # Token is safe to hash
        token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
        
        try:
            path = getattr(getattr(request, 'url', None), 'path', '')
        except (AttributeError, TypeError):
            path = ''
            
        return f"rate_limit:{self.limiter_id}:{token_hash}:{path}"
        

    async def _check_rate_limit(self, key: str) -> None:
        """
        Asynchronously check if request exceeds rate limit and update counters.

        Implements the sliding window algorithm with asyncio lock for thread safety
        in FastAPI's async environment.
        
        Args:
            key: Unique cache key for the request.
            
        Raises:
            RateLimitException: When the rate limit is exceeded.
        """
        # Get current time
        current_time: float = time.time()
        
        # Async lock operation - non-blocking for FastAPI
        async with self._lock:
            
            # User identified by key is found in cache
            if key in self._cache:
                # Get time and count of found user key
                window_start, count = self._cache[key]
                
                # If we're still in the same time window
                if (current_time - window_start) < self.window_seconds:
                    # If user hits limit
                    if count >= self.limit:
                        raise RateLimitException("requests_exceeded_rate_limit")
                    
                    # Increment request count for current window
                    self._cache[key] = (window_start, count + 1)
                else:
                    # New time window - reset counter
                    self._cache[key] = (current_time, 1)
                
                # Move user to end for LRU cache behavior
                self._cache.move_to_end(key)
            else:
                # If cache hits maximum capacity
                if len(self._cache) >= self.max_cache_size:
                    # Evict oldest entry (LRU eviction)
                    self._cache.popitem(last=False)
                
                # First request for user identified by this key
                self._cache[key] = (current_time, 1)
