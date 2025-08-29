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


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """ASGI middleware to enforce request body size limits and prevent memory exhaustion attacks.

    Attributes:
        max_body_size: Maximum allowed request body size in bytes.
    """

    MAX_BODY_SIZE: ClassVar[int] = 524288  # Max size 512KB

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

        This method implements a two-phase approach to body size validation:
        1. Header-based validation using Content-Length header when available
        2. Streaming validation for chunked transfers or requests without Content-Length

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

        # Phase 1: Pre-validation using Content-Length header
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                declared_size = int(content_length)
                if declared_size > self.MAX_BODY_SIZE:
                    return self._size_exceeded_response()
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "invalid_content_length_header"}
                )

        # Phase 2: Streaming validation for chunked/unknown size requests
        should_wrap = (
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
        """Generate error response for size limit violations.

        Returns:
            JSONResponse: HTTP 413 response with error message.
        """
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": "request_body_too_large"}
        )

    async def _wrap_request_body(self, request: Request) -> Request:
        """Create a size-monitored wrapper around the request's body stream.

        Args:
            request (Request): The original request object to wrap.

        Returns:
            Request: A new Request object with size-monitored receive callable.

        Raises:
            ValueError: When the accumulated body size exceeds the configured limit.
        """
        class SizeLimitedBody:
            """ASGI receive callable wrapper that enforces cumulative body size limits."""

            def __init__(
                self,
                original_receive: Callable[[], Awaitable[MutableMapping[str, Any]]],
                max_size: int
            ) -> None:
                self.original_receive = original_receive
                self.max_size = max_size
                self.current_size = 0

            async def __call__(self) -> MutableMapping[str, Any]:
                """Process ASGI messages with size monitoring for request bodies.

                Returns:
                    MutableMapping[str, Any]: The original ASGI message unchanged.

                Raises:
                    ValueError: When the cumulative body size exceeds max_size.
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
        limited_receive = SizeLimitedBody(
            request.receive,
            self.MAX_BODY_SIZE
        )

        # Create new request object with limited receive
        return StarletteRequest(
            scope=request.scope,
            receive=limited_receive
        )
