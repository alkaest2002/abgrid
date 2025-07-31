from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

class HeaderSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_header_size: int = 8192):
        super().__init__(app)
        self.max_header_size = max_header_size

    async def dispatch(self, request: Request, call_next):
        for header_name, header_value in request.headers.items():
            if len(header_value) > self.max_header_size:
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"header_'{header_name}'_is_too_large"}
                )
        
        response = await call_next(request)
        return response
