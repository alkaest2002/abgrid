"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
import gzip
import io
import zlib
from collections.abc import Awaitable, Callable
from typing import ClassVar

import orjson
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from fastapi import Request
from fastapi.responses import JSONResponse, Response


class DecompressError(Exception):
    """Raised when decompression fails or exceeds size limits."""

class DecompressMiddleware(BaseHTTPMiddleware):
    """Middleware to decompress gzip/deflate compressed request bodies.

    Attributes:
        max_decompressed_size: Maximum allowed size for decompressed request bodies.
        chunk_size: Size of each chunk read during decompression.
    """

    MAX_DECOMPRESSED_SIZE: ClassVar[int] = 1058456  # Max size 1MB
    CHUNK_SIZE: ClassVar[int] = 8192  # 8KB read chunks

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

            # Validate JSON content
            if not self._is_json_valid(decompressed_body):
                return JSONResponse(
                    status_code=400,
                    content={"detail": "invalid_json_after_decompression"}
                )

            # Update request with decompressed content
            self._update_request(request, decompressed_body)

        except DecompressError:
            return JSONResponse(
                status_code=413,
                content={"detail": "decompressed_data_too_large"}
            )
        except Exception:
            return JSONResponse(
                status_code=400,
                content={"detail": "decompression_failed"}
            )

        return await call_next(request)

    def _decompress_body(self, compressed_body: bytes, encoding: str) -> bytes:
        """Decompress request body based on content encoding with size limits.

        Applies the appropriate decompression algorithm based on the
        Content-Encoding header value, reading in chunks to prevent
        decompression bombs.

        Args:
            compressed_body: The compressed request body data.
            encoding: The compression encoding type ("gzip" or "deflate").

        Returns:
            The decompressed request body data.

        Raises:
            DecompressError: If decompressed data exceeds size limit.
            Exception: Other decompression errors are propagated to the caller
                      for appropriate error response handling.

        Notes:
            Supports both gzip and deflate compression algorithms.
            Decompression is done in chunks to prevent memory exhaustion.
        """
        if encoding == "gzip":
            return self._decompress_gzip(compressed_body)
        return self._decompress_deflate(compressed_body)

    def _decompress_gzip(self, compressed_body: bytes) -> bytes:
        """Decompress gzip data in chunks with size validation.

        Args:
            compressed_body: The compressed request body data.

        Returns:
            The decompressed request body data.
        """
        decompressed_data = io.BytesIO()
        total_size = 0

        with gzip.GzipFile(fileobj=io.BytesIO(compressed_body)) as gz:
            while True:
                # Read the next chunk
                chunk = gz.read(self.CHUNK_SIZE)

                # Check if chunk is empty
                if not chunk:
                    break

                # Update total size
                total_size += len(chunk)

                # If total size exceeds limit, raise error
                if total_size > self.MAX_DECOMPRESSED_SIZE:
                    error_message = "decompressed_data_exceeds_size_limit"
                    raise DecompressError(error_message)

                # Write the decompressed chunk to the output
                decompressed_data.write(chunk)

        return decompressed_data.getvalue()

    def _decompress_deflate(self, compressed_body: bytes) -> bytes:
        """Decompress deflate data in chunks with size validation.

        Args:
            compressed_body: The compressed request body data.

        Returns:
            The decompressed request body data.
        """
        decompressor = zlib.decompressobj()
        decompressed_data = io.BytesIO()
        total_size = 0

        # Process compressed data in chunks
        for i in range(0, len(compressed_body), self.CHUNK_SIZE):
            # Get the next chunk
            chunk = compressed_body[i:i + self.CHUNK_SIZE]

            # Decompress the chunk
            decompressed_chunk = decompressor.decompress(chunk)

            # Update total size
            total_size += len(decompressed_chunk)

            # If total size exceeds limit, raise error
            if total_size > self.MAX_DECOMPRESSED_SIZE:
                error_message = "Decompressed data exceeds size limit"
                raise DecompressError(error_message)

            # Write the decompressed chunk to the output
            decompressed_data.write(decompressed_chunk)

        # Flush any remaining data
        final_chunk = decompressor.flush()

        # Update total size
        total_size += len(final_chunk)

        # If total size exceeds limit, raise error
        if total_size > self.MAX_DECOMPRESSED_SIZE:
            error_message = "Decompressed data exceeds size limit"
            raise DecompressError(error_message)

        # Write the final chunk to the output
        decompressed_data.write(final_chunk)

        return decompressed_data.getvalue()

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
