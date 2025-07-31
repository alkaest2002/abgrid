from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from starlette.responses import Response

class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to limit request body size and prevent memory exhaustion attacks.

    Args:
        max_body_size: Maximum allowed body size in bytes (default: 1MB)
    """

    def __init__(self, app, max_body_size: int = 1024 * 1024):  # 1MB default
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next) -> Response:
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
        """Wrap request to limit body size during streaming."""

        class SizeLimitedBody:
            def __init__(self, original_receive, max_size: int):
                self.original_receive = original_receive
                self.max_size = max_size
                self.current_size = 0

            async def __call__(self) -> dict:
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
