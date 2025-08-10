"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from fastapi import Request, status
from fastapi.responses import JSONResponse, Response
from lib.interfaces.fastapi.settings import Settings


settings: Settings = Settings.load()

# Alternative implementation with a single combined context manager
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
        app: ASGIApp,
        request_timeout: int = 60,
        max_concurrent_requests_for_group: int = settings.max_concurrent_requests_for_group,
        max_concurrent_requests_for_report: int = settings.max_concurrent_requests_for_report,
    ) -> None:
        """Initialize the middleware."""
        super().__init__(app)
        self.request_timeout = request_timeout

        self.semaphores = {
            "/api/group": asyncio.Semaphore(max_concurrent_requests_for_group),
            "/api/report": asyncio.Semaphore(max_concurrent_requests_for_report),
        }

        self.error_messages = {
            "/api/group": "too_many_concurrent_group_requests",
            "/api/report": "too_many_concurrent_report_requests",
        }

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request with protection."""
        async with self._protected_request(request, call_next) as response:
            return response

    @asynccontextmanager
    async def _protected_request(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> AsyncIterator[Response]:
        """Combined context manager for all request protection.

        This context manager handles both rate limiting and timeout protection
        in a single, clean interface.
        """
        path = request.url.path
        semaphore = None
        error_detail = None

        # Find applicable semaphore
        for prefix, sem in self.semaphores.items():
            if path.startswith(prefix):
                semaphore = sem
                error_detail = self.error_messages[prefix]
                break

        if semaphore:
            # Check if we can acquire the semaphore
            if semaphore._value == 0:  # noqa: SLF001
                yield JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": error_detail}
                )
                return

            # Acquire semaphore and process request
            async with semaphore:
                try:
                    response = await asyncio.wait_for(
                        call_next(request),
                        timeout=self.request_timeout
                    )
                    yield response
                except TimeoutError:
                    yield JSONResponse(
                        status_code=status.HTTP_408_REQUEST_TIMEOUT,
                        content={"detail": "request_timeout"}
                    )
        else:
            # No rate limiting, just timeout protection
            try:
                response = await asyncio.wait_for(
                    call_next(request),
                    timeout=self.request_timeout
                )
                yield response
            except TimeoutError:
                yield JSONResponse(
                    status_code=status.HTTP_408_REQUEST_TIMEOUT,
                    content={"detail": "request_timeout"}
                )
