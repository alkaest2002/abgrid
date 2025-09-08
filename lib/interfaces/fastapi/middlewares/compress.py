"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
import gzip
from typing import ClassVar

from starlette.types import ASGIApp, Message, Receive, Scope, Send


class CompressMiddleware:
    """ASGI-level compression middleware.

    Attributes:
        min_body_size: Minimum body size in bytes to trigger compression.
        compression_level: Compression level (1-9).
        compressible_types: Set of MIME types eligible for compression.
    """

    MIN_BODY_SIZE: ClassVar[int] = 1000  # Minimum size in bytes to trigger compression
    COMPRESSION_LEVEL: ClassVar[int] = 6  # Compression level (1-9)
    COMPRESSIBLE_TYPES: ClassVar[set[str]] = {
        "application/atom+xml", "application/javascript", "application/json", "application/xml",
        "text/css", "text/javascript", "text/html", "text/plain","application/rss+xml",
        "text/xml"
    }  # Compressible MIME types

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the compression middleware.

        Args:
            app: The ASGI application to wrap with compression.

        Returns:
            None
        """
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Handle ASGI requests with optional gzip compression.

        Args:
            scope: The ASGI scope containing request information.
            receive: Callable to receive ASGI messages.
            send: Callable to send ASGI messages.

        Returns:
            None
        """
        # Only handle HTTP requests
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Check Accept-Encoding header
        headers = dict(scope.get("headers", []))
        accept_encoding = headers.get(b"accept-encoding", b"").decode("latin1")

        # If gzip is not accepted, proceed without compression
        if not ("gzip" in accept_encoding.lower() or "*" in accept_encoding):
            await self.app(scope, receive, send)
            return

        # Variables to track response state
        response_started = False
        response_body = bytearray()
        response_headers = {}

        # Wrap the send function to intercept response
        async def _send_wrapper(message: Message) -> None:
            """Wrapper function to intercept and potentially compress response messages.

            Args:
                message: The ASGI message to process.

            Returns:
                None
            """
            # Use nonlocal to modify outer scope variables
            nonlocal response_started, response_body, response_headers

            # Handle response start
            if message["type"] == "http.response.start":
                response_started = True
                response_headers = dict(message.get("headers", []))

                # Don't compress if already encoded or streaming
                if b"content-encoding" in response_headers:
                    await send(message)
                    return

                # Store the start message, we'll send it later
                self.start_message = message

            # Handle response body
            elif message["type"] == "http.response.body":

                # Get body and more_body
                body = message.get("body", b"")
                more_body = message.get("more_body", False)

                # Collect response body
                response_body.extend(body)

                # Final chunk
                if not more_body:

                    # Check if we should compress
                    if self._should_compress(response_headers, bytes(response_body)):

                        # Compress body
                        compressed_body = gzip.compress(bytes(response_body), compresslevel=self.COMPRESSION_LEVEL)

                        # Update headers
                        self.start_message["headers"] = [
                            (k, v) for k, v in self.start_message["headers"]
                            if k.lower() not in [b"content-length", b"content-encoding"]
                        ]
                        self.start_message["headers"].extend([
                            (b"content-encoding", b"gzip"),
                            (b"content-length", str(len(compressed_body)).encode()),
                            (b"vary", b"Accept-Encoding"),
                        ])

                        # Send compressed response
                        await send(self.start_message)
                        await send({
                            "type": "http.response.body",
                            "body": compressed_body,
                            "more_body": False
                        })
                    else:
                        # Send original response
                        await send(self.start_message)
                        await send(message)
                else:
                    # Still more body coming, continue collecting
                    pass
            else:
                await send(message)

        await self.app(scope, receive, _send_wrapper)

    def _should_compress(self, headers: dict[bytes, bytes], body: bytes) -> bool:
        """Check if response should be compressed.

        Args:
            headers: The response headers.
            body: The response body.

        Returns:
            bool: True if the response should be compressed, False otherwise.
        """
        if len(body) < self.MIN_BODY_SIZE:
            return False
        content_type = headers.get(b"content-type", b"").decode("latin1").split(";")[0].strip()
        return content_type in self.COMPRESSIBLE_TYPES
