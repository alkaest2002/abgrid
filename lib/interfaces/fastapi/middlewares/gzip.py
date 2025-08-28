"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
import gzip
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from fastapi import Request
from fastapi.responses import Response
from lib.interfaces.fastapi.settings import Settings


settings: Settings = Settings.load()


class GzipCompressionMiddleware(BaseHTTPMiddleware):
    """Middleware to provide gzip compression for HTTP responses.

    This middleware provides response compression by implementing:
    - Automatic gzip compression for responses above minimum size threshold
    - Content-type filtering to compress only appropriate response types
    - Client capability detection via Accept-Encoding header validation
    - Configurable compression level and minimum response size

    The middleware applies compression based on:
    - Client support: Checks Accept-Encoding header for gzip support
    - Response size: Only compresses responses above minimum_size bytes
    - Content type: Compresses text-based and JSON content types
    - Existing encoding: Skips responses that are already encoded

    Attributes:
        minimum_size (int): Minimum response size in bytes to trigger compression
        compression_level (int): Gzip compression level (1-9, higher = better compression)
        compressible_types (set[str]): Content types eligible for compression
    """

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the middleware with compression settings.

        Sets up the middleware with compression parameters loaded from settings
        or using sensible defaults. Configures which content types should be
        compressed and the minimum response size threshold.

        Args:
            app (ASGIApp): The ASGI application instance to wrap with compression.

        Returns:
            None.

        Notes:
            Default minimum size is 1000 bytes to avoid compressing small responses.
            Default compression level is 6 (good balance of speed vs compression ratio).
            Only text-based content types are compressed by default.
        """
        super().__init__(app)
        self.minimum_size = getattr(settings, "gzip_minimum_size", 1000)
        self.compression_level = getattr(settings, "gzip_compression_level", 6)
        self.compressible_types = {
            "text/html",
            "text/plain",
            "text/css",
            "text/javascript",
            "application/json",
            "application/javascript",
            "application/xml",
            "text/xml",
            "application/rss+xml",
            "application/atom+xml",
        }

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process requests and apply gzip compression to eligible responses.

        Checks if the client supports gzip compression and applies it to responses
        that meet the compression criteria (size, content-type, encoding status).

        Args:
            request (Request): The incoming HTTP request object.
            call_next (Callable): The next middleware or route handler in the chain.

        Returns:
            Response: HTTP response, potentially compressed if eligible.

        Notes:
            Compression is only applied when all conditions are met:
            - Client accepts gzip encoding
            - Response is large enough (>= minimum_size)
            - Content-Type is compressible
            - Response is not already encoded
        """
        response = await call_next(request)

        # Check if client supports gzip
        if not self._client_accepts_gzip(request):
            return response

        # Check if response should be compressed
        if not self._should_compress_response(response):
            return response

        return self._compress_response(response)

    def _client_accepts_gzip(self, request: Request) -> bool:
        """Check if the client accepts gzip encoding.

        Examines the Accept-Encoding header to determine if the client
        supports gzip compression for the response.

        Args:
            request (Request): The HTTP request to check for gzip support.

        Returns:
            bool: True if client accepts gzip encoding, False otherwise.

        Notes:
            Checks for both "gzip" and "*" in the Accept-Encoding header.
            Missing Accept-Encoding header is treated as no gzip support.
        """
        accept_encoding = request.headers.get("accept-encoding", "")
        return "gzip" in accept_encoding.lower() or "*" in accept_encoding

    def _should_compress_response(self, response: Response) -> bool:
        """Determine if a response should be compressed.

        Evaluates response characteristics to decide if gzip compression
        should be applied based on size, content type, and encoding status.

        Args:
            response (Response): The HTTP response to evaluate for compression.

        Returns:
            bool: True if response should be compressed, False otherwise.

        Notes:
            Compression is skipped for:
            - Responses already encoded (Content-Encoding header present)
            - Responses smaller than minimum_size bytes
            - Non-compressible content types
            - Responses without body content
        """
        # Skip if already encoded
        if response.headers.get("content-encoding"):
            return False

        # Skip if no body content
        if not hasattr(response, "body") or not response.body:
            return False

        # Skip if too small
        body_size = len(response.body) if isinstance(response.body, bytes) else len(str(response.body).encode())
        if body_size < self.minimum_size:
            return False

        # Skip if non-compressible content type
        content_type = response.headers.get("content-type", "").split(";")[0].strip()
        return content_type not in self.compressible_types

    def _compress_response(self, response: Response) -> Response:
        """Apply gzip compression to a response.

        Compresses the response body using gzip and updates the appropriate
        headers to indicate the compressed content encoding.

        Args:
            response (Response): The HTTP response to compress.

        Returns:
            Response: The response with compressed body and updated headers.

        Raises:
            Exception: Compression errors are handled gracefully by returning
                      the original uncompressed response.

        Notes:
            Updates the following headers after compression:
            - Content-Encoding: Set to "gzip"
            - Content-Length: Updated to compressed body size
            - Vary: Adds "Accept-Encoding" for caching compatibility
        """
        try:
            # Get body as bytes
            if isinstance(response.body, bytes):
                body_bytes = response.body
            else:
                body_bytes = str(response.body).encode("utf-8")

            # Compress the body
            compressed_body = gzip.compress(body_bytes, compresslevel=self.compression_level)

            # Update response body and headers
            response.body = compressed_body
            response.headers["content-encoding"] = "gzip"
            response.headers["content-length"] = str(len(compressed_body))

            # Add Vary header for proper caching
            vary_header = response.headers.get("vary", "")
            if "Accept-Encoding" not in vary_header:
                vary_header = f"{vary_header}, Accept-Encoding" if vary_header else "Accept-Encoding"
                response.headers["vary"] = vary_header

        except Exception:
            # Return original response if compression fails
            return response

        return response
