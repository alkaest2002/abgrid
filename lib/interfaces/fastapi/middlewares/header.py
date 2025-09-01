"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from collections.abc import Awaitable, Callable
from typing import ClassVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from fastapi import Request, status
from fastapi.responses import JSONResponse
from lib.interfaces.fastapi.security.jwt import AnonymousJWT


class HeaderMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT token validation, POST request content-type enforcement, and compression validation.

    Attributes:
        exempt_paths: Set of paths that are exempt from JWT authentication.
        jwt_handler: Shared JWT handler instance for token validation.
    """

    EXEMPT_PATHS: ClassVar[set[str]] = {"/", "/health"}
    JWT_HANDLER: ClassVar[AnonymousJWT] = AnonymousJWT()

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the middleware for JWT, content-type, and compression validation.

        Args:
            app: The ASGI application instance.

        Returns:
            None.
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process incoming request with JWT validation, POST content-type enforcement, and compression validation.

        Processing order:
        1. Extract and validate JWT token for protected paths
        2. Ensure JSON content type for POST requests
        3. Enforce gzip compression if any compression is present

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler in the chain.

        Returns:
            Response: Either an error response for validation failures or the result
                     from the next handler in the chain.
        """
        # Step 1: JWT token extraction and validation
        if request.url.path not in self.EXEMPT_PATHS and request.method != "OPTIONS":

            # Extract JWT token
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.lower().startswith("bearer "):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "missing_jwt_token"}
                )

            # Remove "Bearer " prefix from JWT token
            token = auth_header[7:].strip()

            # Verify JWT token using shared class instance
            if not self.JWT_HANDLER.verify_token(token):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "invalid_or_expired_jwt_token"}
                )

        # Step 2: Ensure JSON content type for POST requests
        if request.method == "POST":
            # Check for Content-Type header
            content_type = request.headers.get("content-type", "")

            # Extract main content type (ignore charset and other parameters)
            main_content_type = content_type.split(";")[0].strip().lower()

            # Check if the request body is JSON
            if main_content_type != "application/json":
                return JSONResponse(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    content={"detail": "post_requests_must_be_json"}
                )

        # Step 3: Enforce gzip compression if any compression is present
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            # Check for Content-Encoding header
            content_encoding = request.headers.get("content-encoding", "").lower()

            # Check if the request body is gzip compressed
            if content_encoding and content_encoding != "gzip":
                return JSONResponse(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    content={"detail": "only_gzip_compression_supported"}
                )

        return await call_next(request)
