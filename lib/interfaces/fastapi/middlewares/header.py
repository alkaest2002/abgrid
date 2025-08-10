"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from fastapi import Request, status
from fastapi.responses import JSONResponse


class HeaderSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to limit HTTP header sizes and prevent header-based attacks.

    This middleware inspects all incoming request headers and rejects requests
    where any individual header value exceeds the configured size limit. This
    helps prevent header-based denial of service attacks and memory exhaustion.

    Args:
        app: The ASGI application instance
        max_header_size: Maximum allowed size for any individual header value
                        in bytes (default: 8KB)

    Raises:
        JSONResponse: Returns 413 status for headers exceeding the size limit

    Note:
        This middleware checks individual header values, not the total size
        of all headers combined. Each header value must be within the limit.
    """

    def __init__(self, app: ASGIApp, max_header_size: int = 8 * 1024) -> None:
        """
        Initialize the middleware with header size limit configuration.

        Args:
            app: The ASGI application instance
            max_header_size: Maximum allowed size for any individual header value
                           in bytes (default: 8KB)
        """
        super().__init__(app)
        self.max_header_size = max_header_size

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """
        Process incoming request and enforce header size limits.

        Iterates through all request headers and validates that each header value
        does not exceed the configured size limit. If any header is too large,
        returns an error response immediately.

        Args:
            request: The incoming HTTP request with headers to validate
            call_next: The next middleware or route handler in the chain

        Returns:
            Response: Either an error response for oversized headers or the result
                     from the next handler in the chain

        Raises:
            JSONResponse: 413 status if any header value exceeds the size limit.
                         The error message includes the name of the offending header.
        """
        for header_value in request.headers.values():
            if len(header_value) > self.max_header_size:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "header_is_too_large"}
                )

        return await call_next(request)

