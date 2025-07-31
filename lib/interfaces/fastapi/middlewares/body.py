"""
Author: Pierpaolo Calanna

Date Created: Jul 1, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
from typing import Callable, Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import Response


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to limit request body size and prevent memory exhaustion attacks.
    
    This middleware checks both the Content-Length header and streaming body content
    to ensure requests don't exceed the specified size limit. It handles both regular
    requests with Content-Length headers and chunked transfer encoding.
    
    Args:
        app: The ASGI application instance
        max_body_size: Maximum allowed body size in bytes (default: 100KB)
        
    Raises:
        JSONResponse: Returns 413 status for bodies exceeding the limit
        JSONResponse: Returns 400 status for invalid Content-Length headers
    """

    def __init__(self, app, max_body_size: int = 100 * 1024) -> None:
        """
        Initialize the middleware with size limit configuration.
        
        Args:
            app: The ASGI application instance
            max_body_size: Maximum allowed body size in bytes (default: 100KB)
        """
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        """
        Process incoming request and enforce body size limits.
        
        This method first checks the Content-Length header if present. For requests
        without Content-Length or using chunked encoding, it wraps the request body
        to monitor size during streaming.
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler in the chain
            
        Returns:
            Response: Either an error response for oversized bodies or the result
                     from the next handler in the chain
                     
        Raises:
            JSONResponse: 413 status if body exceeds size limit
            JSONResponse: 400 status if Content-Length header is invalid
        """
        # Check content-length header if present
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                body_size = int(content_length)
                if body_size > self.max_body_size:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "request_body_too_large"}
                    )
            except ValueError:
                # Invalid content-length header
                return JSONResponse(
                    status_code=400,
                    content={"detail": "invalid_content_length_header"}
                )

        # For chunked transfers or missing content-length, we need to read incrementally
        if not content_length or request.headers.get("transfer-encoding") == "chunked":
            request = await self._wrap_request_body(request)

        response = await call_next(request)
        return response

    async def _wrap_request_body(self, request: Request) -> Request:
        """
        Wrap request to limit body size during streaming.
        
        Creates a size-limited wrapper around the request's receive callable
        to monitor and enforce size limits for streaming request bodies.
        
        Args:
            request: The original HTTP request to wrap
            
        Returns:
            Request: A new request object with size-limited body reading
            
        Note:
            This method is used for requests with chunked encoding or missing
            Content-Length headers where the body size cannot be determined upfront.
        """

        class SizeLimitedBody:
            """
            Wrapper class that limits the size of streaming request bodies.
            
            This class intercepts ASGI messages and tracks the cumulative size
            of body chunks, rejecting requests that exceed the configured limit.
            """
            
            def __init__(self, original_receive: Callable[[], Dict[str, Any]], max_size: int) -> None:
                """
                Initialize the size-limited body wrapper.
                
                Args:
                    original_receive: The original ASGI receive callable
                    max_size: Maximum allowed body size in bytes
                """
                self.original_receive = original_receive
                self.max_size = max_size
                self.current_size = 0

            async def __call__(self) -> Dict[str, Any]:
                """
                Process ASGI messages and enforce size limits.
                
                Intercepts 'http.request' messages to track body size and
                reject oversized requests.
                
                Returns:
                    Dict[str, Any]: The ASGI message or error response
                    
                Raises:
                    JSONResponse: 413 status if accumulated body size exceeds limit
                """
                message = await self.original_receive()

                if message["type"] == "http.request":
                    body = message.get("body", b"")
                    self.current_size += len(body)

                    if self.current_size > self.max_size:
                        return JSONResponse(
                            status_code=413,
                            content={"detail": "request_body_too_large"}
                        )

                return message

        # Create new request with size-limited body
        limited_receive = SizeLimitedBody(request.receive, self.max_body_size)

        # Create new request object with limited receive
        from starlette.requests import Request as StarletteRequest
        limited_request = StarletteRequest(
            scope=request.scope,
            receive=limited_receive
        )

        return limited_request
