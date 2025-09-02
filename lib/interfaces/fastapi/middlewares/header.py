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
from lib.interfaces.fastapi.security.jwt import SimpleJWT


class HeaderMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT token validation, POST request content-type enforcement, and compression validation.

    Attributes:
        exempt_paths: Set of paths that are exempt from JWT authentication.
        jwt_handler: Shared JWT handler instance for token validation.
    """

    EXEMPT_PATHS: ClassVar[set[str]] = {"/", "/health"}
    JWT_HANDLER: ClassVar[SimpleJWT] = SimpleJWT()

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the middleware for JWT, content-type, and compression validation.

        Args:
            app: The ASGI application instance.

        Returns:
            None.
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process incoming request with JWT validation first, then method-specific validation.

        Processing order:
        1. JWT token validation (with route and OPTIONS exemptions)
        2. Method-specific validation (content-type, compression, etc.)

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler in the chain.

        Returns:
            Response: Either an error response for validation failures or the result
                     from the next handler in the chain.
        """
        # STEP 1: JWT Token Validation (with exemptions)
        jwt_error = await self._validate_jwt_token(request)
        if jwt_error:
            return jwt_error

        # STEP 2: Method-specific validation
        method_error = await self._handle_method_validation(request)
        if method_error:
            return method_error

        return await call_next(request)

    ##################################################################################################################
    #   PRIVATE METHODS
    ##################################################################################################################

    async def _validate_jwt_token(self, request: Request) -> Response | None:
        """Validate JWT token with route and OPTIONS method exemptions.

        Args:
            request: The incoming HTTP request.

        Returns:
            Response or None: Error response if validation fails, None otherwise.
        """
        # Exempt paths and OPTIONS method from JWT validation
        if request.url.path in self.EXEMPT_PATHS or request.method == "OPTIONS":
            return None

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

        return None

    async def _handle_method_validation(self, request: Request) -> Response | None:
        """Handle method-specific validation.

        Args:
            request: The incoming HTTP request.

        Returns:
            Response or None: Error response if validation fails, None otherwise.
        """
        # Map HTTP methods to their validation handlers
        method_handlers = {
            "GET": self._validate_default,
            "HEAD": self._validate_default,
            "OPTIONS": self._validate_default,
            "POST": self._validate_post_request,
        }

        # Select the appropriate handler for the request method
        handler = method_handlers.get(request.method, self._handle_not_allowed_request)

        return await handler(request)

    async def _handle_not_allowed_request(self, request: Request) -> JSONResponse: # noqa: ARG002
        """Validate any other HTTP method.

        Args:
            request: The incoming HTTP request.

        Returns:
            JSONResponse: Always a 405 Method Not Allowed response.
        """
        # Return a 405 Method Not Allowed response
        return JSONResponse(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                content={"detail": "method_not_allowed"}
            )

    async def _validate_default(self, request: Request) -> Response | None:  # noqa: ARG002
        """Validate that the request has no body data.

        Args:
            request: The incoming HTTP request.

        Returns:
            None: No checks. Just return None.
        """
        return None

    async def _validate_post_request(self, request: Request) -> Response | None:
        """Validate POST request.

        Args:
            request: The incoming HTTP request.

        Returns:
            Response or None: Error response if validation fails, None otherwise.
        """
        # Validate JSON content type
        json_error = self._validate_json_content_type(request)
        if json_error:
            return json_error

        # Validate compression
        return self._validate_compression_encoding(request)

    def _validate_json_content_type(self, request: Request) -> Response | None:
        """Validate that the request has JSON content type.

        Args:
            request: The incoming HTTP request.

        Returns:
            Response or None: Error response if validation fails, None otherwise.
        """
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

        return None

    def _validate_compression_encoding(self, request: Request) -> Response | None:
        """Validate compression encoding (only gzip allowed).

        Args:
            request: The incoming HTTP request.

        Returns:
            Response or None: Error response if validation fails, None otherwise.
        """
        # Check for Content-Encoding header
        content_encoding = request.headers.get("content-encoding", "").lower()

        # Check if the request body is gzip compressed
        if content_encoding and content_encoding != "gzip":
            return JSONResponse(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                content={"detail": "only_gzip_compression_supported"}
            )

        return None
