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
    """Middleware to limit HTTP header sizes and ensure JSON content for POST requests.

    This middleware inspects all incoming request headers and:
    1. Rejects requests where any individual header value exceeds the size limit
    2. Ensures POST requests have Content-Type: application/json

    Args:
        app: The ASGI application instance
        max_header_size: Maximum allowed size for any individual header value
                        in bytes (default: 8KB).

    Raises:
        - JSONResponse: Returns 413 status for headers exceeding the size limit.
        - JSONResponse: Returns 415 status for POST requests without JSON content type.

    Notes:
        This middleware checks individual header values, not the total size
        of all headers combined. Each header value must be within the limit.
    """

    def __init__(self, app: ASGIApp, max_header_size: int = 8 * 1024) -> None:
        """Initialize the middleware with header size limit configuration.

        Args:
            app: The ASGI application instance.
            max_header_size: Maximum allowed size for any individual header value
                           in bytes (default: 8KB).

        Return:
            None.
        """
        super().__init__(app)
        self.max_header_size = max_header_size

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process incoming request and enforce header validations.

        Validates header sizes and ensures POST requests have JSON content type.

        Args:
            request: The incoming HTTP request with headers to validate.
            call_next: The next middleware or route handler in the chain.

        Returns:
            Response: Either an error response for validation failures or the result
                     from the next handler in the chain.

        Raises:
            - JSONResponse: 413 status if any header value exceeds the size limit.
            - JSONResponse: 415 status if POST request doesn't have JSON content type.
        """
        # Check header sizes
        for header_value in request.headers.values():
            if len(header_value) > self.max_header_size:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "header_is_too_large"}
                )

        # Check JSON content type for POST requests
        if request.method == "POST":
            content_type = request.headers.get("content-type", "")
            # Extract main content type (ignore charset and other parameters)
            main_content_type = content_type.split(";")[0].strip().lower()

            if main_content_type != "application/json":
                return JSONResponse(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    content={"detail": "post_requests_must_be_json"}
                )

        return await call_next(request)
