"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
import asyncio
from collections.abc import Awaitable, Callable
from typing import ClassVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from fastapi import Request, status
from fastapi.responses import JSONResponse, Response
from lib.interfaces.fastapi.settings import Settings


settings: Settings = Settings.load()

class RequestMiddleware(BaseHTTPMiddleware):
    """Middleware to protect against request-based attacks and resource exhaustion.

    Attributes:
        request_timeout: Timeout duration for incoming requests.
        semaphore: Semaphore to limit concurrent API requests.
    """

    REQUEST_TIMEOUT: ClassVar[int] = 60  # 60 seconds timeout for all requests
    SEMAPHORE: ClassVar[asyncio.Semaphore] = asyncio.Semaphore(settings.max_concurrent_requests) # from .env

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the middleware with validation and protection settings.

        Sets up the middleware with timeout and concurrency controls based on
        application settings. The semaphore limit is loaded from settings to
        control maximum concurrent API requests.

        Args:
            app (ASGIApp): The ASGI application instance to wrap with protection.

        Returns:
            None.
        """
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process incoming requests with appropriate protection measures.

        Routes requests to different protection handlers based on the URL path:
        - API routes (/api/*): Apply both timeout and concurrency limiting
        - Other routes: Apply timeout protection only

        Args:
            request (Request): The incoming HTTP request object.
            call_next (Callable): The next middleware or route handler in the chain.

        Returns:
            Response: HTTP response from the protected request processing.

        Raises:
            The method handles exceptions internally and returns appropriate
            HTTP error responses rather than propagating exceptions.
        """
        if request.url.path.startswith("/api"):
            return await self._handle_api_request(request, call_next)
        return await self._execute_with_timeout(request, call_next)

    async def _handle_api_request(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Handle API requests with concurrency limiting protection.

        Checks if the concurrent request limit has been reached and either
        processes the request or returns a 429 Too Many Requests response.
        Uses a semaphore to control concurrent access to API endpoints.

        Args:
            request (Request): The API request to process.
            call_next (Callable): The next handler in the processing chain.

        Returns:
            Response: Either the processed request response or a 429 error response
                - 200-5xx: Normal response from successful request processing.
                - 429: Too many concurrent requests error with JSON detail.

        Notes:
            The semaphore.locked() check provides immediate rejection without
            waiting, preventing request queuing when at capacity.
        """
        if self.SEMAPHORE.locked():
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "too_many_concurrent_requests"}
            )

        async with self.SEMAPHORE:
            return await self._execute_with_timeout(request, call_next)

    async def _execute_with_timeout(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Execute request processing with timeout protection.

        Wraps the request processing in an asyncio timeout to prevent
        long-running requests from consuming resources indefinitely.

        Args:
            request (Request): The request to process with timeout protection.
            call_next (Callable): The next handler in the processing chain.

        Returns:
            Response: Either the processed request response or a timeout error
                - 200-5xx: Normal response from successful request processing.
                - 408: Request timeout error with JSON detail.

        Raises:
            TimeoutError: Caught internally and converted to 408 HTTP response.

        Notes:
            The timeout value is configured in self.request_timeout (60 seconds).
            This prevents both malicious and accidental resource exhaustion from
            long-running requests.
        """
        try:
            return await asyncio.wait_for(
                call_next(request),
                timeout=self.REQUEST_TIMEOUT
            )
        except TimeoutError:
            return JSONResponse(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                content={"detail": "request_timeout"}
            )
