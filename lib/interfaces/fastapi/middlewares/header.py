from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import HTTPException, Request

class HeaderSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_header_size: int = 8192):
        super().__init__(app)
        self.max_header_size = max_header_size

    async def dispatch(self, request: Request, call_next):
        for _, header_value in request.headers.items():
            if len(header_value) > self.max_header_size:
                raise HTTPException(
                    status_code=413, 
                    detail=f"Headers_are_too_large"
                )
        
        response = await call_next(request)
        return response
