"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import asyncio
import hashlib
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any


class RateLimitError(Exception):
    """
    Exception raised when the rate limit is exceeded.

    Attributes:
        message: The error message describing the rate limit violation.
    """
    def __init__(self, message: str = "Rate limit exceeded") -> None:
        """Initialize a RateLimitError with a default error message."""
        self.message = message
        super().__init__(message)

class SimpleRateLimiter:
    """
    JWT-based rate limiter using a sliding window approach with LRU cache.

    This rate limiter extracts JWT tokens from Authorization headers and
    applies rate limiting per token per endpoint using asyncio for FastAPI compatibility.
    OPTIONS requests (CORS preflight) bypass rate limiting entirely.

    Args:
        limit: Maximum number of requests allowed per window.
        window_seconds: Time window duration in seconds.
        max_cache_size: Maximum number of entries to keep in cache.
        skip_options: Whether to skip rate limiting for OPTIONS requests (default: True).

    Raises:
        ValueError: If any numeric parameter is <= 0.
    """

    def __init__(
        self,
        limit: int = 1,
        window_seconds: int = 15,
        max_cache_size: int = 10000,
        skip_options: bool = True
    ) -> None:
        """
        Initialize the rate limiter with asyncio lock for FastAPI compatibility.

        Args:
            limit: Maximum requests allowed per window (default 1).
            window_seconds: Duration of rate limit window in seconds (default 15).
            max_cache_size: Maximum cache entries to prevent memory leaks (default 10000).
            skip_options: Skip rate limiting for OPTIONS requests (CORS preflight).
        """
        if limit <= 0 or window_seconds <= 0 or max_cache_size <= 0:
            error_message = "rate_limiter_all_parameters_must_be_positive_integers"
            raise ValueError(error_message)

        # Create a unique identifier for this limiter instance
        self.limiter_id = f"{limit}req_{window_seconds}s"

        # Store values
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_cache_size = max_cache_size
        self.skip_options = skip_options

        self._cache: OrderedDict[str, tuple[float, int]] = OrderedDict()
        # Use asyncio.Lock for FastAPI async compatibility
        self._lock: asyncio.Lock = asyncio.Lock()

    def __call__(self, func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        """
        Decorator that applies rate limiting to an async function.

        The decorated function must accept a 'request' parameter that contains
        the HTTP request object with headers. OPTIONS requests bypass rate limiting
        if skip_options is True.

        Args:
            func: Async function to be rate limited.

        Returns:
            Wrapped async function with rate limiting applied.

        Raises:
            RateLimitError: When rate limit is exceeded or JWT token is missing.
        """
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not (request := kwargs.get("request")):
                error_message = "request_object_required_for_rate_limiting"
                raise RateLimitError(error_message)

            # Skip rate limiting for OPTIONS requests (CORS preflight)
            if self.skip_options and getattr(request, "method", None) == "OPTIONS":
                return await func(*args, **kwargs)

            # Get cache key from JWT token
            key: str = self._get_cache_key(request)

            # Check rate limit
            await self._check_rate_limit(key)

            return await func(*args, **kwargs)
        return wrapper

    def _get_cache_key(self, request: Any) -> str:
        """
        Extract JWT token from request and create a unique cache key.

        Args:
            request: HTTP request object with headers and url attributes.

        Returns:
            Unique cache key string in format "rate_limit:{limiter_id}:{token_hash}:{path}".

        Raises:
            RateLimitError: If Authorization header is missing, malformed,
                                or doesn't contain a Bearer token.
        """
        # Set token max size
        # Extract JWT token
        token: str | None = self._extract_jwt_token(request)

        if not token:
            error_message = "required_jwt_token"
            raise RateLimitError(error_message)

        # Validate token size
        token_max_size = 2048
        if len(token) > token_max_size:
            error_message = "jwt_token_too_large"
            raise RateLimitError(error_message)

        # Validate basic JWT format (header.payload.signature)
        token_parts_count = 2
        if token.count(".") != token_parts_count:
            error_message = "invalid_jwt_format"
            raise RateLimitError(error_message)

        # Hash the token for security
        token_hash: str = hashlib.sha256(token.encode("utf-8")).hexdigest()

        # Get request path
        path: str = getattr(getattr(request, "url", None), "path", "")

        return f"rate_limit:{self.limiter_id}:{token_hash}:{path}"

    def _extract_jwt_token(self, request: Any) -> str | None:
        """
        Safely extract JWT token from Authorization header.

        Args:
            request: HTTP request object with headers.

        Returns:
            JWT token string if found and valid, None otherwise.
        """
        try:
            auth_header: str = request.headers.get("Authorization", "")
        except (AttributeError, TypeError):
            return None

        if not auth_header.startswith("Bearer "):
            return None

        token: str = auth_header[7:].strip()
        return token if token else None

    async def _check_rate_limit(self, key: str) -> None:
        """
        Asynchronously check if request exceeds rate limit and update counters.

        Implements the sliding window algorithm with asyncio lock for thread safety
        in FastAPI's async environment.

        Args:
            key: Unique cache key for the request.

        Raises:
            RateLimitError: When the rate limit is exceeded.
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
                        error_message = "requests_exceeded_rate_limit"
                        raise RateLimitError(error_message)

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
