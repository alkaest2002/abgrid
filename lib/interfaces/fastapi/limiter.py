"""
Filename: limiter.py

Description: Simple rate limiter system.

Author: Pierpaolo Calanna

Date Created: Jul 1, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import time
import hashlib
import threading
from collections import OrderedDict
from functools import wraps
from typing import Tuple, Callable, Any, Awaitable, List

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
    applies rate limiting per token per endpoint.
    
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
        Initialize the rate limiter.

        Args:
            limit: Maximum requests allowed per window (must be > 0).
            window_seconds: Duration of rate limit window in seconds (must be > 0).
            max_cache_size: Maximum cache entries to prevent memory leaks (must be > 0).
        """
        # Create a unique identifier for this limiter instance
        self.limiter_id = f"{limit}req_{window_seconds}s"
            
        # Store values
        self.limit: int = limit
        self.window_seconds: int = window_seconds
        self.max_cache_size: int = max_cache_size
        
        # Cache stores: key -> (window_start_time, request_count)
        self._cache: OrderedDict[str, Tuple[float, int]] = OrderedDict()
        self._lock: threading.RLock = threading.RLock()

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
            # Request object is needed
            if not (request := kwargs.get("request")):
                raise RateLimitException("fastapi_request_object_required_for_rate_limiting")
            
            # Rate limit happens here
            key: str = self._get_cache_key(request)
            self._check_rate_limit(key)
            
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
        # Get Authorization header
        auth_header: str = getattr(request.headers, 'get', lambda k, d: '')("Authorization", "")
        
        # JWT token validation and extraction
        if not auth_header or not auth_header.startswith("Bearer ") or not (token := auth_header[7:].strip()):
            raise RateLimitException("fastapi_required_jwt_token")
        
        # Use SHA-256 to hash token for privacy and collision prevention
        token_hash: str = hashlib.sha256(token.encode('utf-8')).hexdigest()
        
        # Get request path, fallback to empty string if not available
        path: str = getattr(getattr(request, 'url', None), 'path', '') or ''
        
        return f"rate_limit:{self.limiter_id}:{token_hash}:{path}"
        

    def _check_rate_limit(self, key: str) -> None:
        """
        Check if request exceeds rate limit and update counters.

        Implements the sliding window algorithm.
        
        Args:
            key: Unique cache key for the request.
            
        Raises:
            RateLimitException: When the rate limit is exceeded.
        """
        # Get time
        current_time: float = time.time()
        
        # Thread safe operation
        with self._lock:
            # Auto-cleanup: remove entries older than 2x window to prevent memory leaks
            self._cleanup_expired(current_time)
            
            # User identified by key is found in cache
            if key in self._cache:
                # Get time and count of found user key
                window_start, count = self._cache[key]
                
                # If we're still in the same time window
                if (current_time - window_start) < self.window_seconds:
                    
                    # If user hits limit
                    if count >= self.limit:
                        raise RateLimitException("fastapi_requests_exceeded_rate_limit")
                    
                    # Update count
                    self._cache[key] = (window_start, count + 1)
                else:
                    # New time window + reset counter
                    self._cache[key] = (current_time, 1)
                
                # Move user to end (LRU)
                self._cache.move_to_end(key)
            else:
                # If cache hits maximum capacity
                if len(self._cache) >= self.max_cache_size:
                    
                    # Evict oldest entry (LRU eviction)
                    self._cache.popitem(last=False)
                
                # First request for user identified by this key
                self._cache[key] = (current_time, 1)

    def _cleanup_expired(self, current_time: float) -> None:
        """
        Remove cache entries older than 2x window_seconds to prevent memory leaks.

        Args:
            current_time: Current timestamp for comparison.
        """
        # Define cutoff time
        cutoff_time: float = current_time - (2 * self.window_seconds)
        
        # Get expired keys
        expired_keys: List[str] = [
            k for k, (window_start, _) in self._cache.items() 
            if window_start < cutoff_time
        ]
        
        # Delete expired keys
        for key in expired_keys:
            del self._cache[key]
