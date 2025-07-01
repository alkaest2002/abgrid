import time
import hashlib
import threading
from collections import OrderedDict
from functools import wraps


class RateLimitException(Exception):
    """Raised when rate limit is exceeded."""
    pass


class SimpleRateLimiter:
    """
    Simple JWT-based rate limiter using sliding window approach.
    Focuses on simplicity while preventing memory leaks.
    """
    
    def __init__(
        self, 
        limit: int, 
        window_seconds: int,
        max_cache_size: int = 10000
    ):
        self.limit = limit
        self.window_seconds = window_seconds
        self.max_cache_size = max_cache_size
        
        # Cache stores: key -> (window_start_time, request_count)
        self._cache = OrderedDict()
        self._lock = threading.RLock()

    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if not request:
                raise RateLimitException("Request object required for rate limiting")
            
            key = self._get_cache_key(request)
            self._check_rate_limit(key)
            
            return await func(*args, **kwargs)
        return wrapper

    def _get_cache_key(self, request) -> str:
        """Extract JWT token and create cache key."""
        auth_header = request.headers.get("Authorization", "")
        
        if not auth_header.startswith("Bearer "):
            raise RateLimitException("JWT token required")
        
        token = auth_header[7:]  # Remove "Bearer "
        if not token:
            raise RateLimitException("JWT token required")
        
        # Use SHA-256 hash for privacy and collision prevention
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return f"rate_limit:{token_hash}:{request.url.path}"

    def _check_rate_limit(self, key: str):
        """Check and update rate limit for given key."""
        current_time = time.time()
        
        with self._lock:
            # Auto-cleanup: remove entries older than 2x window to prevent memory leaks
            self._cleanup_expired(current_time)
            
            if key in self._cache:
                window_start, count = self._cache[key]
                
                # If we're still in the same time window
                if (current_time - window_start) < self.window_seconds:
                    if count >= self.limit:
                        raise RateLimitException("Rate limit exceeded")
                    
                    # Update count and move to end (LRU)
                    self._cache[key] = (window_start, count + 1)
                    self._cache.move_to_end(key)
                else:
                    # New time window - reset
                    self._cache[key] = (current_time, 1)
                    self._cache.move_to_end(key)
            else:
                # First request for this key
                # Evict oldest if at capacity
                if len(self._cache) >= self.max_cache_size:
                    self._cache.popitem(last=False)
                
                self._cache[key] = (current_time, 1)

    def _cleanup_expired(self, current_time: float):
        """Remove entries older than 2x window_seconds to prevent memory leaks."""
        cutoff_time = current_time - (2 * self.window_seconds)
        expired_keys = [
            k for k, (window_start, _) in self._cache.items() 
            if window_start < cutoff_time
        ]
        
        for key in expired_keys:
            del self._cache[key]