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


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """ASGI middleware to enforce request body size limits and prevent memory exhaustion attacks.

    This middleware provides protection against oversized request bodies by implementing two-tier validation:
    1. Pre-validation using Content-Length header when available
    2. Streaming validation for chunked transfers or requests without Content-Length

    Attributes:
        max_body_size (int): Maximum allowed request body size in bytes

    Notes:
        This middleware should be added early in the middleware stack to prevent
        processing of oversized requests before they consume significant resources.
    """

    def __init__(self, app: ASGIApp, max_body_size: int = 500 * 1024) -> None:
        """Initialize the body size limit middleware.

        Sets up the middleware with the specified maximum body size limit.
        The default limit is set to 500KB to provide reasonable protection
        while accommodating typical API request sizes.

        Args:
            app: The ASGI application instance to wrap
            max_body_size (int, optional): Maximum allowed request body size in bytes.
                Defaults to 102,400 bytes (500KB). Must be a positive integer.

        Returns:
            None.
        """
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process incoming HTTP requests and enforce body size limits.

        This method implements a two-phase approach to body size validation:

        1. **Header-based validation**: If Content-Length header is present, validates
           the declared size immediately without reading the body.

        2. **Streaming validation**: For requests without Content-Length or using
           chunked encoding, wraps the request to monitor size during body consumption.

        The method prioritizes efficiency by rejecting oversized requests as early
        as possible in the request lifecycle.

        Args:
            request (Request): The incoming FastAPI/Starlette request object containing
                HTTP method, headers, and body stream.
            call_next (Callable[[Request], Awaitable[Response]]): The next middleware
                or route handler in the ASGI chain.

        Returns:
            Response: One of the following:
                - JSONResponse with 413 status if body exceeds size limit.
                - JSONResponse with 400 status if Content-Length header is malformed.
                - Response from the next handler if body size is acceptable.

        Raises:
            No exceptions are raised directly. All error conditions are converted
            to appropriate HTTP error responses.

        """
        # Phase 1: Pre-validation using Content-Length header
        content_length = request.headers.get("Content-Length")
        if content_length:
            try:
                body_size = int(content_length)
                if body_size > self.max_body_size:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={"detail": "request_body_too_large"}
                    )
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "invalid_content_length_header"}
                )

        # Phase 2: Streaming validation for chunked/unknown size requests
        if not content_length or request.headers.get("Transfer-Encoding") == "chunked":
            try:
                request = await self._wrap_request_body(request)
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "request_body_too_large"}
                )

        return await call_next(request)

    async def _wrap_request_body(self, request: Request) -> Request:
        """Create a size-monitored wrapper around the request's body stream.

        This method creates a new request object with an intercepted receive callable
        that monitors the cumulative size of body chunks as they are consumed by
        the application. This approach is necessary for requests where the total
        body size cannot be determined upfront (chunked encoding, missing Content-Length).

        The wrapper implements transparent size monitoring without affecting the
        normal request processing flow, only intervening when size limits are exceeded.

        Args:
            request (Request): The original request object to wrap. Must be a valid
                FastAPI/Starlette Request instance with an active receive callable.

        Returns:
            Request: A new Request object with identical scope but wrapped receive
                callable that enforces size limits. The returned request behaves
                identically to the original except for size enforcement.

        Raises:
            ValueError: When the accumulated body size exceeds the configured limit
                during stream processing. This exception is caught by the dispatch
                method and converted to an HTTP 413 response.

        Notes:
            - Creates a SizeLimitedBody wrapper around the original receive callable
            - Preserves all original request metadata (headers, method, path, etc.)
            - Monitors only 'http.request' message types for body content
            - Maintains running total of body bytes across all chunks

        """

        class SizeLimitedBody:
            """
            ASGI receive callable wrapper that enforces cumulative body size limits.

            This class implements the ASGI receive protocol while adding transparent
            size monitoring for HTTP request bodies. It intercepts ASGI messages
            and tracks the cumulative size of body chunks, raising an exception
            when the configured limit is exceeded.

            The wrapper is designed to be transparent to the application - it passes
            through all non-body messages unchanged and only monitors body content
            without modifying it.

            Attributes:
                original_receive: The original ASGI receive callable from the request
                max_size: Maximum allowed cumulative body size in bytes
                current_size: Running total of body bytes processed so far

            ASGI Protocol Compliance:
                - Properly handles all ASGI message types
                - Maintains message structure and content integrity
                - Only monitors 'http.request' messages with body content
                - Preserves message ordering and timing
            """

            def __init__(self, original_receive: Callable[[], Awaitable[MutableMapping[str, Any]]], max_size: int) -> None:
                """
                Initialize the size-limited body wrapper.

                Sets up the wrapper with the original receive callable and size limit.
                Initializes the size counter to zero for tracking cumulative body size.

                Args:
                    original_receive: The original ASGI receive callable that returns
                        ASGI messages. Must be a valid async callable that returns
                        MutableMapping[str, Any] representing ASGI messages.
                    max_size: Maximum allowed cumulative body size in bytes. Must be
                        a positive integer representing the size limit.

                Returns:
                    None.
                """
                self.original_receive = original_receive
                self.max_size = max_size
                self.current_size = 0

            async def __call__(self) -> MutableMapping[str, Any]:
                """
                Process ASGI messages with size monitoring for request bodies.

                This method implements the ASGI receive protocol by forwarding calls
                to the original receive callable while intercepting and monitoring
                HTTP request body messages for size enforcement.

                Message Processing Logic:
                1. Retrieve the next ASGI message from the original receive callable
                2. If message type is 'http.request', extract and measure body content
                3. Update cumulative size counter with body length
                4. Check if cumulative size exceeds the configured limit
                5. Raise exception if limit exceeded, otherwise return message unchanged

                Returns:
                    MutableMapping[str, Any]: The original ASGI message unchanged.
                        Message structure and content are preserved exactly as received
                        from the original receive callable.

                Raises:
                    ValueError: When the cumulative body size exceeds max_size.
                        Raised with message "Request body too large" to indicate
                        the specific reason for rejection.

                ASGI Message Types Handled:
                    - 'http.request': Monitored for body size, may trigger size check
                    - All other types: Passed through unchanged without processing

                Body Size Calculation:
                    - Extracts 'body' field from 'http.request' messages
                    - Handles missing 'body' field gracefully (treats as empty)
                    - Accumulates size across multiple chunks for streaming bodies
                    - Counts actual byte length, not character count
                """
                message = await self.original_receive()

                if message["type"] == "http.request":
                    body = message.get("body", b"")
                    self.current_size += len(body)

                    if self.current_size > self.max_size:
                        error_message = "request_body_too_large"
                        raise ValueError(error_message)

                return message

        # Create new request with size-limited body
        limited_receive = SizeLimitedBody(request.receive, self.max_body_size)

        # Create new request object with limited receive
        return StarletteRequest(
            scope=request.scope,
            receive=limited_receive
        )
