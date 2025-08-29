"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
import gzip
import zlib
from collections.abc import Awaitable, Callable
from typing import ClassVar

import orjson
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from fastapi import Request
from fastapi.responses import JSONResponse, Response


class DecompressionMiddleware(BaseHTTPMiddleware):
    """Middleware to decompress gzip/deflate compressed request bodies.

    Attributes:
        max_decompressed_size: Maximum allowed size for decompressed request bodies.
    """

    MAX_DECOMPRESSED_SIZE: ClassVar[int] = 1 * 1024 * 1024 # 1MB

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the middleware with decompression settings.

        Args:
            app: The ASGI application instance to wrap with decompression.

        Returns:
            None.
        """
        super().__init__(app)

    async def dispatch(  # noqa: PLR0911
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process requests and decompress compressed request bodies.

        Checks if the request has a compressed body and decompresses it if
        the content encoding is supported (gzip or deflate). Validates the
        decompressed content and updates request headers accordingly.

        Args:
            request: The incoming HTTP request object with potentially compressed body.
            call_next: The next middleware or route handler in the chain.

        Returns:
            HTTP response from downstream handlers, or error response if
            decompression fails, size limits are exceeded, or content is invalid.

        Notes:
            Returns specific error responses for different failure modes:
            - 413 (Payload Too Large): Decompressed data exceeds size limit
            - 400 (Bad Request): Decompression failed or invalid JSON content
        """
        # Skip requests without body
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return await call_next(request)

        content_encoding = request.headers.get("content-encoding", "").lower()

        # Skip if no compression
        if content_encoding not in ("gzip", "deflate"):
            return await call_next(request)

        try:
            compressed_body = await request.body()

            # Check if body is empty
            if not compressed_body:
                return await call_next(request)

            # Decompress based on encoding type
            decompressed_body = self._decompress_body(compressed_body, content_encoding)

            # Validate decompressed size
            if not self._is_size_valid(decompressed_body):
                return JSONResponse(
                    status_code=413,
                    content={"detail": "decompressed_data_too_large"}
                )

            # Validate JSON content
            if not self._is_json_valid(decompressed_body):
                return JSONResponse(
                    status_code=400,
                    content={"detail": "invalid_json_after_decompression"}
                )

            # Update request with decompressed content
            self._update_request(request, decompressed_body)

        except Exception:
            return JSONResponse(
                status_code=400,
                content={"detail": "decompression_failed"}
            )

        return await call_next(request)

    def _decompress_body(self, compressed_body: bytes, encoding: str) -> bytes:
        """Decompress request body based on content encoding.

        Applies the appropriate decompression algorithm based on the
        Content-Encoding header value.

        Args:
            compressed_body: The compressed request body data.
            encoding: The compression encoding type ("gzip" or "deflate").

        Returns:
            The decompressed request body data.

        Raises:
            Exception: Decompression errors are propagated to the caller
                      for appropriate error response handling.

        Notes:
            Supports both gzip and deflate compression algorithms.
            Decompression errors indicate corrupted or invalid compressed data.
        """
        if encoding == "gzip":
            return gzip.decompress(compressed_body)
        return zlib.decompress(compressed_body)

    def _is_size_valid(self, decompressed_body: bytes) -> bool:
        """Check if decompressed body size is within allowed limits.

        Validates that the decompressed content doesn't exceed the configured
        maximum size limit to prevent memory exhaustion attacks.

        Args:
            decompressed_body: The decompressed request body data.

        Returns:
            True if size is within limits, False if too large.

        Notes:
            Size validation prevents compression bomb attacks where small
            compressed data expands to enormous decompressed sizes.
        """
        return len(decompressed_body) <= self.MAX_DECOMPRESSED_SIZE

    def _is_json_valid(self, decompressed_body: bytes) -> bool:
        """Validate that decompressed content is valid JSON.

        Attempts to parse the decompressed content as JSON to ensure
        data integrity after decompression.

        Args:
            decompressed_body: The decompressed request body data.

        Returns:
            True if content is valid JSON, False otherwise.

        Notes:
            Validation catches both JSON parsing errors and UTF-8 decoding errors.
            This ensures the decompressed data is usable by downstream handlers.
        """
        try:
            orjson.loads(decompressed_body.decode("utf-8"))
        except (orjson.JSONDecodeError, UnicodeDecodeError):
            return False
        return True


    def _update_request(self, request: Request, decompressed_body: bytes) -> None:
        """Update request object with decompressed body and corrected headers.

        Modifies the request to contain the decompressed body data and
        updates relevant headers to reflect the decompressed content.

        Args:
            request: The HTTP request object to modify.
            decompressed_body: The decompressed request body data.

        Returns:
            None.

        Notes:
            Updates the following:
            - Request body: Set to decompressed content
            - Content-Encoding header: Removed (no longer compressed)
            - Content-Length header: Updated to decompressed size
        """
        # Update request with decompressed body
        request._body = decompressed_body  # noqa: SLF001

        # Update headers
        mutable_headers = dict(request.headers)
        del mutable_headers["content-encoding"]
        mutable_headers["content-length"] = str(len(decompressed_body))

        request.scope["headers"] = [
            (key.encode().lower(), value.encode())
            for key, value in mutable_headers.items()
        ]
