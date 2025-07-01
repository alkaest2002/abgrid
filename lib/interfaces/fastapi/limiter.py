import time
from collections import OrderedDict
from dataclasses import dataclass
from functools import wraps
from typing import Any, Type
import threading

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
    
    def size(self):
        return len(self._cache)
    
    def items(self):
        with self._lock:
            return list(self._cache.items())


class DefaultLimiter:
    def __init__(
            self,
            limit,
            seconds: int,
            max_memory_entries: int = 10000,
            cleanup_interval: int = 300,
            exception: Type[Exception] | None = None,
            exception_status: int = 429,  # This field is unused with RateLimitException
            exception_message: Any = "",
    ):
        self._limit = limit
        self._seconds = seconds
        self._local_session = LRUCache(max_memory_entries, cleanup_interval)
        self._exception_cls = exception or RateLimitException  # Default to RateLimitException
        self._exception_message = exception_message

    def raise_exception(self):
        """An exception is raised when the rate limit reaches the limit.

        If there is an exception class passed by the user, the exception passed by the user is generated.
        If the exception class passed by the user does not exist, a RateLimitException is thrown.
        """
        raise self._exception_cls(self._exception_message)

    def get_memory_stats(self):
        """Get current memory usage statistics.
        
        Returns:
            dict: Dictionary containing memory usage statistics
        """
        return {
            "entries_count": self._local_session.size(),
            "max_entries": self._local_session.max_size
        }

    def cleanup_expired_entries(self):
        """Clean up expired entries from memory to prevent memory leaks.
        
        This method is now mostly handled automatically by the LRU cache,
        but can still be called manually if needed.
        """
        self._local_session._cleanup_expired(self._seconds)


class RateLimiter(DefaultLimiter):
    def __init__(
        self,
        limit: int,
        seconds: int,
        max_memory_entries: int = 10000,
        cleanup_interval: int = 300,
        exception: Type[Exception] | None = None,
        exception_status: int = 429,  # This field is unused with RateLimitException
        exception_message: Any = "Rate Limit Exceed",
    ):
        self.exception_message = exception_message
        super().__init__(limit, seconds, max_memory_entries, cleanup_interval, exception, exception_status, self.exception_message)

    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request", None)
            key = self.__get_key(request, LimitTypeKey.RateLimit)
            await self.__check_in_memory(key)
            return await func(*args, **kwargs)

        return wrapper
    
    async def is_rate_limited(self, request) -> bool:
        """Check if a request is currently rate limited without raising exceptions.
        
        Args:
            request: FastAPI.Request Object
            
        Returns:
            bool: True if rate limited, False otherwise
        """
        key = self.__get_key(request, LimitTypeKey.RateLimit)
        current_time = time.time()
        existing_data = self._local_session.get(key, (0, 0))
        last_request_time, request_count = existing_data

        return (current_time - last_request_time) < self._seconds and request_count >= self._limit


    @staticmethod
    def __get_key(request, key_name: str):
        """Creates and returns a RateLimit Key.
        
        Create a key and count the limit according to the Client IP Address and API URL Path.

        Args:
            request: FastAPI.Request Object
            key_name: Key prefix name

        Returns:
            str: The generated key
        """
        if request:
            return f"{key_name}:{request.client.host}:{request.url.path}"
        return ""

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
