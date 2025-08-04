"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import asyncio
from typing import Callable
from fastapi import Request, status
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
    - Separate concurrent limits for different endpoint types
    - Selective application of limits based on URL path patterns
    
    The middleware can be configured to apply different protection levels to different
    routes, allowing fine-grained control over resource protection.
    
    Args:
        app: The ASGI application instance
        request_timeout: Maximum time in seconds a request can take before timing out
                        (default: 60 seconds)
        max_concurrent_requests_for_group: Maximum concurrent requests for /api/group endpoints
        max_concurrent_requests_for_report: Maximum concurrent requests for /api/report endpoints
                               
    Raises:
        JSONResponse: Returns 429 status when concurrent request limit is exceeded
        JSONResponse: Returns 408 status when request timeout is exceeded
        
    Note:
        - Request timeout applies to ALL requests regardless of route
        - Concurrent request limits apply separately to /api/group and /api/report routes
        - Route matching uses prefix matching (startswith)
    """
    
    def __init__(
        self, 
        app, 
        request_timeout: int = 60,  # seconds
        max_concurrent_requests_for_group: int = settings.max_concurrent_requests_for_group,
        max_concurrent_requests_for_report: int = settings.max_concurrent_requests_for_report,
    ) -> None:
        """
        Initialize the middleware with request protection configuration.
        
        Args:
            app: The ASGI application instance
            request_timeout: Maximum time in seconds a request can take before timing out
                           (default: 60 seconds)
            max_concurrent_requests_for_group: Maximum concurrent requests for /api/group endpoints
            max_concurrent_requests_for_report: Maximum concurrent requests for /api/report endpoints
        """
        super().__init__(app)
        self.request_timeout = request_timeout
        self.max_concurrent_requests_for_group = max_concurrent_requests_for_group
        self.max_concurrent_requests_for_report = max_concurrent_requests_for_report
        
        # Track active requests separately for each endpoint type
        self.active_group_requests: int = 0
        self.active_report_requests: int = 0
        self._lock: asyncio.Lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        """
        Process incoming request with timeout and concurrent request protection.
        
        This method implements a two-tier protection system:
        1. Concurrent request limiting - Applied separately to /api/group and /api/report routes
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
            The active request counters are properly managed with async locks to ensure
            thread safety in concurrent environments. Requests are always decremented
            from the counter in the finally block to prevent counter drift.
        """
        # Get url path
        request_path: str = request.url.path
        
        # Determine endpoint type and check concurrent limits
        is_group_request = request_path.startswith("/api/group")
        is_report_request = request_path.startswith("/api/report")
        
        # Apply concurrent request limit based on endpoint type
        if is_group_request:
            async with self._lock:
                if self.active_group_requests >= self.max_concurrent_requests_for_group:
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={"detail": "too_many_concurrent_group_requests"}
                    )
                self.active_group_requests += 1
                
        elif is_report_request:
            async with self._lock:
                if self.active_report_requests >= self.max_concurrent_requests_for_report:
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={"detail": "too_many_concurrent_report_requests"}
                    )
                self.active_report_requests += 1

        try:
            # Create timeout for the request (applies to all requests)
            response: Response = await asyncio.wait_for(
                call_next(request),
                timeout=self.request_timeout
            )
                
            return response
            
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                content={"detail": "request_timeout"}
            )
        finally:
            # Decrement the appropriate counter
            if is_group_request:
                async with self._lock:
                    self.active_group_requests -= 1
            elif is_report_request:
                async with self._lock:
                    self.active_report_requests -= 1
