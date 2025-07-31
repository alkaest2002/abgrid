"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import asyncio
import time
from typing import Callable, List, Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from lib.interfaces.fastapi.settings import Settings

settings = Settings.load()


class RequestProtectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to protect against request-based attacks and resource exhaustion.
    
    This middleware provides comprehensive request protection through:
    - Request timeout enforcement to prevent slow HTTP attacks
    - Concurrent request limiting for specific routes to prevent resource exhaustion
    - Selective application of limits based on URL path patterns
    
    The middleware can be configured to apply different protection levels to different
    routes, allowing fine-grained control over resource protection.
    
    Args:
        app: The ASGI application instance
        request_timeout: Maximum time in seconds a request can take before timing out
                        (default: 60 seconds)
        max_concurrent_requests: Maximum number of concurrent requests allowed for
                               specified routes (default: from settings)
        concurrent_limit_routes: List of URL path prefixes that should have concurrent
                               request limits applied (default: ["/api/report"])
                               
    Raises:
        JSONResponse: Returns 429 status when concurrent request limit is exceeded
        JSONResponse: Returns 408 status when request timeout is exceeded
        
    Note:
        - Request timeout applies to ALL requests regardless of route
        - Concurrent request limits only apply to specified routes
        - Route matching uses prefix matching (startswith)
    """
    
    def __init__(
        self, 
        app, 
        request_timeout: int = 60,  # seconds
        max_concurrent_requests: int = settings.max_concurrent_requests,
        concurrent_limit_routes: Optional[List[str]] = None  # Routes to apply concurrent limits
    ) -> None:
        """
        Initialize the middleware with request protection configuration.
        
        Args:
            app: The ASGI application instance
            request_timeout: Maximum time in seconds a request can take before timing out
                           (default: 60 seconds)
            max_concurrent_requests: Maximum number of concurrent requests allowed for
                                   specified routes (default: from settings)
            concurrent_limit_routes: List of URL path prefixes that should have concurrent
                                   request limits applied. If None, defaults to ["/api/report"]
        """
        super().__init__(app)
        self.request_timeout = request_timeout
        self.max_concurrent_requests = max_concurrent_requests
        
        # Default to /api/report if no routes specified
        self.concurrent_limit_routes = concurrent_limit_routes or ["/api/report"]
        
        # Track active requests only for specified routes
        self.active_requests: int = 0
        self._lock: asyncio.Lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        """
        Process incoming request with timeout and concurrent request protection.
        
        This method implements a two-tier protection system:
        1. Concurrent request limiting - Applied only to specified routes
        2. Request timeout - Applied to all requests
        
        The concurrent request limit is checked first for applicable routes. If the
        limit is not exceeded, the request proceeds with timeout protection.
        
        Args:
            request: The incoming HTTP request to process
            call_next: The next middleware or route handler in the chain
            
        Returns:
            Response: Either an error response for protection violations or the result
                     from the next handler in the chain
                     
        Raises:
            JSONResponse: 429 status when concurrent request limit is exceeded for
                         protected routes
            JSONResponse: 408 status when request processing exceeds the timeout limit
            
        Note:
            The active request counter is properly managed with async locks to ensure
            thread safety in concurrent environments. Requests are always decremented
            from the counter in the finally block to prevent counter drift.
        """
        # Get url path
        request_path: str = request.url.path
        
        # Check if current request path should have concurrent limits applied
        should_limit_concurrency: bool = any(
            request_path.startswith(route) for route in self.concurrent_limit_routes
        )
        
        # Apply concurrent request limit only to specified routes
        if should_limit_concurrency:
            async with self._lock:
                if self.active_requests >= self.max_concurrent_requests:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "too_many_concurrent_requests"}
                    )
                self.active_requests += 1

        try:
            # Create timeout for the request (applies to all requests)
            response: Response = await asyncio.wait_for(
                call_next(request),
                timeout=self.request_timeout
            )
                
            return response
            
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=408,
                content={"detail": "request_timeout"}
            )
        finally:
            # Only decrement counter if we incremented it for this route
            if should_limit_concurrency:
                async with self._lock:
                    self.active_requests -= 1
