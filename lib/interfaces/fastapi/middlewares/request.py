"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import asyncio
from collections.abc import Awaitable
from typing import Callable, Optional
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse, Response
from lib.interfaces.fastapi.settings import Settings
settings: Settings = Settings.load()


class RequestProtectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to protect against request-based attacks and resource exhaustion.
    
    This middleware provides comprehensive request protection through:
    - Request timeout enforcement to prevent slow HTTP attacks
    - Concurrent request limiting for specific routes to prevent resource exhaustion
    - Separate concurrent limits for different endpoint types
    
    The middleware uses asyncio.Semaphore for thread-safe concurrent request limiting,
    ensuring robust protection against resource exhaustion attacks.
    
    Args:
        app: The ASGI application instance
        request_timeout: Maximum time in seconds a request can take before timing out
                        (default: 60 seconds)
        max_concurrent_requests_for_group: Maximum concurrent requests for /api/group endpoint
        max_concurrent_requests_for_report: Maximum concurrent requests for /api/report endpoint
                               
    Raises:
        JSONResponse: Returns 429 status when concurrent request limit is exceeded
        JSONResponse: Returns 408 status when request timeout is exceeded
        
    Note:
        - Request timeout applies to ALL requests regardless of route
        - Concurrent request limits apply separately to /api/group and /api/report routes
        - Route matching uses prefix matching (startswith)
        - Semaphores automatically handle the acquire/release pattern in a thread-safe manner
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
        
        # Use semaphores for thread-safe concurrent request limiting
        # Semaphores automatically handle counting and are exception-safe
        self.report_semaphore = asyncio.Semaphore(max_concurrent_requests_for_report)
        print(max_concurrent_requests_for_group, max_concurrent_requests_for_report)
        self.group_semaphore = asyncio.Semaphore(max_concurrent_requests_for_group)
        self.report_semaphore = asyncio.Semaphore(max_concurrent_requests_for_report)
        
        # Store limits for reference
        self.max_concurrent_requests_for_group = max_concurrent_requests_for_group
        self.max_concurrent_requests_for_report = max_concurrent_requests_for_report

    async def dispatch(
        self, 
        request: Request, 
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process incoming request with timeout and concurrent request protection.
        
        This method implements a two-tier protection system:
        1. Concurrent request limiting - Applied separately to /api/group and /api/report routes
        2. Request timeout - Applied to all requests
        
        The concurrent request limit is checked first for applicable routes. If the
        limit is not exceeded, the request proceeds with timeout protection.
        
        Semaphores are used to ensure thread-safe concurrent request limiting with
        automatic acquire/release patterns that are exception-safe.
        
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
        """
        # Get url path
        request_path: str = request.url.path
        
        # Determine which semaphore and error message to use based on the endpoint
        semaphore: Optional[asyncio.Semaphore] = None
        error_detail: Optional[str] = None
        
        if request_path.startswith("/api/group"):
            semaphore = self.group_semaphore
            error_detail = "too_many_concurrent_group_requests"
        elif request_path.startswith("/api/report"):
            semaphore = self.report_semaphore
            error_detail = "too_many_concurrent_report_requests"
        
        # Handle rate-limited endpoints
        if semaphore is not None:
            # Check if semaphore is available without blocking
            if semaphore._value <= 0:
                # Semaphore is at capacity, reject the request immediately
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": error_detail}
                )
            
            # Acquire the semaphore and process the request
            async with semaphore:
                return await self._process_request_with_timeout(request, call_next)
        else:
            # No rate limiting for other endpoints, just apply timeout
            return await self._process_request_with_timeout(request, call_next)

    async def _process_request_with_timeout(
        self, 
        request: Request, 
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process a request with timeout protection.
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler in the chain
            
        Returns:
            Response: The response from the handler or a timeout error
            
        Raises:
            JSONResponse: 408 status when request processing exceeds the timeout limit
        """
        try:
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

