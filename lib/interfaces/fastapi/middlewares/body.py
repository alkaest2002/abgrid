"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any, ClassVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response
from starlette.types import ASGIApp

from fastapi import Request, status
from fastapi.responses import JSONResponse


class BodyMiddleware(BaseHTTPMiddleware):
    """ASGI middleware to enforce request body size limits and prevent memory exhaustion attacks.

    Attributes:
        max_body_size: Maximum allowed request body size in bytes.
        leniency_percentage: Percentage of leniency for Content-Length validation.
    """

    MAX_BODY_SIZE: ClassVar[int] = 524288  # Max size 512KB
    LENIENCY_PERCENTAGE: ClassVar[float] = 0.10  # 10% leniency

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the body size limit middleware.

        Args:
            app (ASGIApp): The ASGI application instance to wrap.

        Returns:
            None.
        """
        super().__init__(app)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process incoming HTTP requests and enforce body size limits.

        This method implements a three-phase approach to body size validation:
        1. Early exit if Content-Length exceeds maximum size (with leniency)
        2. Content-Length validation - verify actual body is within acceptable range
        3. Stream validation for requests without Content-Length header

        Body checking is skipped if the request body is gzip compressed.

        Args:
            request (Request): The incoming FastAPI/Starlette request object.
            call_next (Callable[[Request], Awaitable[Response]]): The next middleware
                or route handler in the ASGI chain.

        Returns:
            Response: JSONResponse with 413 status if body exceeds size limit,
                JSONResponse with 400 status if Content-Length header is malformed,
                or Response from the next handler if body size is acceptable.
        """
        # Skip body size checks for methods that typically don't have bodies
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return await call_next(request)

        # Skip body size checks if the body is gzip compressed
        if self._is_body_gzip_compressed(request):
            return await call_next(request)

        # Phase 1: Check Content-Length header and exit early if too large (with leniency)
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                # Get declared size from Content-Length header
                declared_size = int(content_length)
                # Apply leniency to the maximum size check
                max_allowed_with_leniency = self.MAX_BODY_SIZE + int(self.MAX_BODY_SIZE * self.LENIENCY_PERCENTAGE)
                # If declared size exceeds the maximum allowed size (with leniency)
                if declared_size > max_allowed_with_leniency:
                    return self._size_exceeded_response()
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "invalid_content_length_header"}
                )

        # Phase 2 & 3: Wrap request body for validation
        try:
            request = await self._wrap_request_body(request, content_length)
        except ValueError:
            return self._size_exceeded_response()

        return await call_next(request)

    ##################################################################################################################
    #   PRIVATE METHODS
    ##################################################################################################################

    def _is_body_gzip_compressed(self, request: Request) -> bool:
        """Check if the request body is gzip compressed based on Content-Encoding header.

        Args:
            request (Request): The incoming FastAPI/Starlette request object.

        Returns:
            bool: True if the body is gzip compressed, False otherwise.
        """
        content_encoding = request.headers.get("content-encoding", "").lower()
        return content_encoding == "gzip"

    def _size_exceeded_response(self) -> JSONResponse:
        """Generate error response for size limit violations.

        Returns:
            JSONResponse: HTTP 413 response with error message.
        """
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": "request_body_too_large"}
        )

    async def _wrap_request_body(self, request: Request, content_length: str | None) -> Request:
        """Create a size-monitored wrapper around the request's body stream.

        Args:
            request (Request): The original request object to wrap.
            content_length (str | None): The Content-Length header value if present.

        Returns:
            Request: A new Request object with size-monitored receive callable.

        Raises:
            ValueError: When the body size validation fails.
        """
        declared_size = None
        if content_length:
            try:
                declared_size = int(content_length)
            except ValueError:
                # This should not happen as we already validated it, but just in case
                declared_size = None

        class SizeLimitedBody:
            """ASGI receive callable wrapper that enforces body size limits with leniency."""

            def __init__(
                self,
                original_receive: Callable[[], Awaitable[MutableMapping[str, Any]]],
                max_size: int,
                expected_size: int | None,
                leniency_percentage: float
            ) -> None:
                self.original_receive = original_receive
                self.max_size = max_size
                self.expected_size = expected_size
                self.leniency_percentage = leniency_percentage
                self.current_size = 0

            async def __call__(self) -> MutableMapping[str, Any]:
                """Process ASGI messages with size monitoring and lenient content-length validation.

                Returns:
                    MutableMapping[str, Any]: The original ASGI message unchanged.

                Raises:
                    ValueError: When the body size validation fails.
                """
                message = await self.original_receive()

                if message["type"] == "http.request":
                    body = message.get("body", b"")

                    self.current_size += len(body)

                    # If Content-Length is set, validate with leniency
                    if self.expected_size is not None:
                        # Calculate the maximum allowed size with leniency
                        # Use the larger of: max_size or expected_size + leniency
                        leniency_buffer = int(self.max_size * self.leniency_percentage)
                        max_allowed = max(
                            self.max_size + leniency_buffer,
                            self.expected_size + leniency_buffer
                        )

                        if self.current_size > max_allowed:
                            error_message = "request_body_too_large"
                            raise ValueError(error_message)
                    else:
                        # No Content-Length header - enforce max size limit with leniency
                        max_allowed_with_leniency = self.max_size + int(self.max_size * self.leniency_percentage)
                        if self.current_size > max_allowed_with_leniency:
                            error_message = "request_body_too_large"
                            raise ValueError(error_message)

                return message

        # Create new request with size-limited body
        limited_receive = SizeLimitedBody(
            request.receive,
            self.MAX_BODY_SIZE,
            declared_size,
            self.LENIENCY_PERCENTAGE
        )

        # Create new request object with limited receive
        return StarletteRequest(
            scope=request.scope,
            receive=limited_receive
        )
