"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response
from starlette.types import ASGIApp

from fastapi import Request, status
from fastapi.responses import JSONResponse
from lib.interfaces.fastapi.settings import Settings


settings: Settings = Settings.load()


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """ASGI middleware to enforce request body size limits and prevent memory exhaustion attacks.

    This middleware provides protection against oversized request bodies by implementing:
    - Pre-validation using Content-Length header when available
    - Streaming validation for chunked transfers or requests without Content-Length
    - Dual-mode operation for compressed vs decompressed body validation
    - Configurable size limits based on compression state

    The middleware can operate in two modes:
    - "compressed": Validates compressed request body size (prevents large uploads)
    - "decompressed": Validates decompressed request body size (prevents compression bombs)

    Attributes:
        max_body_size (int): Maximum allowed request body size in bytes
        limit_type (str): Type of limit enforcement ("compressed" or "decompressed")
    """

    def __init__(
        self,
        app: ASGIApp,
        limit_type: str = "decompressed",
        max_body_size: int | None = None
    ) -> None:
        """Initialize the body size limit middleware.

        Sets up the middleware with the specified maximum body size limit and limit type.
        The limit type determines whether to check compressed or decompressed body sizes,
        allowing for defense-in-depth against different attack vectors.

        Args:
            app (ASGIApp): The ASGI application instance to wrap.
            limit_type (str): Type of body size limit to enforce. Must be either
                "compressed" or "decompressed". Defaults to "decompressed".
            max_body_size (int | None): Maximum allowed request body size in bytes.
                If None, loads from settings based on limit_type. Must be positive.

        Returns:
            None.

        Raises:
            ValueError: If limit_type is not "compressed" or "decompressed".

        Notes:
            Default limits are loaded from settings:
            - compressed: Typically 50MB to prevent large file uploads
            - decompressed: Typically 200MB to prevent compression bomb attacks
        """
        super().__init__(app)

        # Set limit type
        self.limit_type = limit_type

        # Set default sizes based on limit type
        if max_body_size is None:
            if limit_type == "compressed":
                self.max_body_size = settings.max_compressed_body_size
            else:
                self.max_body_size = settings.max_decompressed_body_size
        else:
            self.max_body_size = max_body_size

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process incoming HTTP requests and enforce body size limits.

        This method implements a two-phase approach to body size validation:

        1. **Header-based validation**: If Content-Length header is present, validates
           the declared size immediately without reading the body.

        2. **Streaming validation**: For requests without Content-Length or using
           chunked encoding, wraps the request to monitor size during body consumption.

        The validation behavior depends on the limit_type:
        - "compressed": Checks raw request body size (before decompression)
        - "decompressed": Checks processed body size (after decompression)

        Args:
            request (Request): The incoming FastAPI/Starlette request object containing
                HTTP method, headers, and body stream.
            call_next (Callable[[Request], Awaitable[Response]]): The next middleware
                or route handler in the ASGI chain.

        Returns:
            Response: One of the following:
                - JSONResponse with 413 status if body exceeds size limit
                - JSONResponse with 400 status if Content-Length header is malformed
                - Response from the next handler if body size is acceptable

        Notes:
            For compressed limit type, validation occurs before decompression.
            For decompressed limit type, validation occurs after decompression.
            This allows for comprehensive protection against different attack vectors.
        """
        # Skip body size checks for methods that typically don't have bodies
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return await call_next(request)

        # Phase 1: Pre-validation using Content-Length header
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                declared_size = int(content_length)
                # For compressed mode, check the declared compressed size
                if self.limit_type == "compressed" and declared_size > self.max_body_size:
                    return self._size_exceeded_response()
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "invalid_content_length_header"}
                )

        # Phase 2: Streaming validation for chunked/unknown size requests
        # For compressed mode, always wrap to monitor raw body size
        # For decompressed mode, only wrap if no reliable content-length
        should_wrap = (
            self.limit_type == "compressed" or
            not content_length or
            request.headers.get("transfer-encoding") == "chunked"
        )

        if should_wrap:
            try:
                request = await self._wrap_request_body(request)
            except ValueError:
                return self._size_exceeded_response()

        return await call_next(request)

    def _size_exceeded_response(self) -> JSONResponse:
        """Generate appropriate error response for size limit violations.

        Creates a standardized error response when body size limits are exceeded,
        with error messages that indicate the specific type of limit that was violated.

        Returns:
            JSONResponse: HTTP 413 response with appropriate error message.

        Notes:
            Error messages differentiate between compressed and decompressed limits
            to help with debugging and provide clear feedback about the violation type.
        """
        if self.limit_type == "compressed":
            detail = "compressed_request_body_too_large"
        else:
            detail = "decompressed_request_body_too_large"

        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": detail}
        )

    async def _wrap_request_body(self, request: Request) -> Request:
        """Create a size-monitored wrapper around the request's body stream.

        This method creates a new request object with an intercepted receive callable
        that monitors the cumulative size of body chunks as they are consumed by
        the application. The monitoring behavior depends on the limit_type setting.

        Args:
            request (Request): The original request object to wrap.

        Returns:
            Request: A new Request object with size-monitored receive callable.

        Raises:
            ValueError: When the accumulated body size exceeds the configured limit
                during stream processing.

        Notes:
            Creates a SizeLimitedBody wrapper around the original receive callable.
            The wrapper type and behavior depends on the configured limit_type.
        """
        class SizeLimitedBody:
            """ASGI receive callable wrapper that enforces cumulative body size limits.

            This class implements the ASGI receive protocol while adding transparent
            size monitoring for HTTP request bodies. The monitoring behavior is
            configurable based on whether compressed or decompressed limits are enforced.

            Attributes:
                original_receive: The original ASGI receive callable from the request
                max_size: Maximum allowed cumulative body size in bytes
                current_size: Running total of body bytes processed so far
                limit_type: Type of limit being enforced ("compressed" or "decompressed")
            """

            def __init__(
                self,
                original_receive: Callable[[], Awaitable[MutableMapping[str, Any]]],
                max_size: int,
                limit_type: str
            ) -> None:
                """Initialize the size-limited body wrapper.

                Args:
                    original_receive: The original ASGI receive callable.
                    max_size: Maximum allowed cumulative body size in bytes.
                    limit_type: Type of limit enforcement ("compressed" or "decompressed").

                Returns:
                    None.
                """
                self.original_receive = original_receive
                self.max_size = max_size
                self.current_size = 0
                self.limit_type = limit_type

            async def __call__(self) -> MutableMapping[str, Any]:
                """Process ASGI messages with size monitoring for request bodies.

                Implements the ASGI receive protocol by forwarding calls to the original
                receive callable while intercepting and monitoring HTTP request body
                messages for size enforcement.

                Returns:
                    MutableMapping[str, Any]: The original ASGI message unchanged.

                Raises:
                    ValueError: When the cumulative body size exceeds max_size.

                Notes:
                    For compressed limit type, monitors raw body chunks.
                    For decompressed limit type, would need integration with
                    decompression middleware to monitor actual decompressed size.
                """
                message = await self.original_receive()

                if message["type"] == "http.request":
                    body = message.get("body", b"")
                    self.current_size += len(body)

                    if self.current_size > self.max_size:
                        if self.limit_type == "compressed":
                            error_message = "compressed_request_body_too_large"
                        else:
                            error_message = "decompressed_request_body_too_large"
                        raise ValueError(error_message)

                return message

        # Create new request with size-limited body
        limited_receive = SizeLimitedBody(
            request.receive,
            self.max_body_size,
            self.limit_type
        )

        # Create new request object with limited receive
        return StarletteRequest(
            scope=request.scope,
            receive=limited_receive
        )
