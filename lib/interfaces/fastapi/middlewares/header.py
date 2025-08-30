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
    """Middleware to limit HTTP header sizes, ensure JSON content for POST requests, and validate JWT tokens.

    Attributes:
            max_header_size: Maximum allowed size for HTTP headers.
            exempt_paths: Set of paths that are exempt from JWT authentication.
    """

    MAX_HEADER_SIZE: ClassVar[int] = 8 * 1024 # 8KB
    EXEMPT_PATHS: ClassVar[set[str]] = {"/", "/health"} # Routes that don't require JWT authentication

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the middleware with header size limit configuration.

        Args:
            app: The ASGI application instance.

        Returns:
            None.
        """
        super().__init__(app)
        self.jwt_handler = AnonymousJWT()

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process incoming request and enforce header validations and JWT authentication.

        Args:
            request: The incoming HTTP request with headers to validate.
            call_next: The next middleware or route handler in the chain.

        Returns:
            Response: Either an error response for validation failures or the result
                     from the next handler in the chain.

        Raises:
            HTTPException: 401 Unauthorized.
            HTTPException: 413 Request Entity Too Large.
            HTTPException: 415 Unsupported Media Type.
        """
        # Check header sizes
        for header_value in request.headers.values():
            if len(header_value) > self.MAX_HEADER_SIZE:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "header_is_too_large"}
                )

        # Skip JWT check for exempt paths and OPTIONS requests
        if request.url.path not in self.EXEMPT_PATHS and request.method != "OPTIONS":

            # Extract JWT token
            auth_header = request.headers.get("authorization")
            if not auth_header or not auth_header.lower().startswith("bearer "):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "missing_jwt_token"}
                )

            # Remove "Bearer " prefix from JWT token
            token = auth_header[7:]

            # Verify JWT token
            if not self.jwt_handler.verify_token_boolean(token):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "invalid_jwt_token"}
                )

        # Ensure JSON content type for POST requests
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
