import time
from collections import OrderedDict
from dataclasses import dataclass
from functools import wraps
from typing import Any
import threading
import hashlib

class RateLimitException(Exception):
    """
    This is a custom Exception that occurs when the API RateLimit is reached.
    Occurs when a set limit is reached
    """

    def __init__(self, message: str = None):
        super(RateLimitException, self).__init__(message)


@dataclass
class LimitTypeKey:
    RateLimit = 'default'


class LRUCache:
    """LRU Cache with size limit and automatic cleanup."""
    
    def __init__(self, max_size: int = 10000, cleanup_interval: int = 300):
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval
        self._cache = OrderedDict()
        self._lock = threading.RLock()
        self._last_cleanup = time.time()
    
    def get(self, key: str, default=None):
        with self._lock:
            if key in self._cache:
                # Move to end (most recently used)
                self._cache.move_to_end(key)
                return self._cache[key]
            return default
    
    def set(self, key: str, value):
        with self._lock:
            # Auto cleanup if needed
            self._auto_cleanup()
            
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                # Evict oldest if at capacity
                if len(self._cache) >= self.max_size:
                    self._cache.popitem(last=False)  # Remove oldest
            
            self._cache[key] = value
    
    def delete(self, key: str):
        with self._lock:
            self._cache.pop(key, None)
    
    def _auto_cleanup(self):
        """Automatically cleanup expired entries."""
        current_time = time.time()
        if (current_time - self._last_cleanup) > self.cleanup_interval:
            self._cleanup_expired()
            self._last_cleanup = current_time
    
    def _cleanup_expired(self, expiry_seconds: int = 3600):
        """Remove entries older than expiry_seconds."""
        current_time = time.time()
        expired_keys = []
        
        for key, (timestamp, _) in self._cache.items():
            if (current_time - timestamp) > expiry_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]


class RateLimiter:
    def __init__(
        self,
        limit: int,
        seconds: int,
        max_memory_entries: int = 10000,
        cleanup_interval: int = 300,
        exception_message: Any = "Rate Limit Exceed",
    ):
        self._limit = limit
        self._seconds = seconds
        self._local_session = LRUCache(max_memory_entries, cleanup_interval)
        self._exception_cls = RateLimitException
        self._exception_message = exception_message

    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request", None)
            key = self.__get_key(request, LimitTypeKey.RateLimit)
            await self.__check_in_memory(key)
            return await func(*args, **kwargs)

        return wrapper
    
    def raise_exception(self):
        """An exception is raised when the rate limit reaches the limit."""
        raise self._exception_cls(self._exception_message)

    
    def __get_key(self, request, key_name: str):
        """Creates and returns a RateLimit Key based on JWT token.
        
        Requires a JWT token in the Authorization header. Raises RateLimitException if not found.
        Uses full SHA-256 hash to prevent collisions.

        Args:
            request: FastAPI.Request Object
            key_name: Key prefix name

        Returns:
            str: The generated key

        Raises:
            RateLimitException: If JWT token is not found in request
        """
        if not request:
            raise RateLimitException("Request object is required")
        
        # Extract JWT token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise RateLimitException("JWT token is required for rate limiting")
        
        jwt_token = auth_header.split(" ", 1)[1]
        if not jwt_token:
            raise RateLimitException("JWT token is required for rate limiting")
        
        # Use full SHA-256 hash to prevent collisions
        token_hash = hashlib.sha256(jwt_token.encode()).hexdigest()
        return f"{key_name}:jwt:{token_hash}:{request.url.path}"

    async def __check_in_memory(self, key: str):
        """This is a check function used when memory is used as rate limit storage.
        
        Use a dictionary in memory to check usage based on key.

        Args:
            key: RateLimit Key
        """
        current_time = time.time()
        existing_data = self._local_session.get(key, (0, 0))
        last_request_time, request_count = existing_data

        if (current_time - last_request_time) < self._seconds and request_count >= self._limit:
            self.raise_exception()
        else:
            new_count = 1 if request_count >= self._limit else request_count + 1
            self._local_session.set(key, (current_time, new_count))
