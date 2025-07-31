import asyncio
import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import HTTPException, Request
from starlette.responses import JSONResponse
from lib.interfaces.fastapi.settings import Settings

settings = Settings.load()

class TimeoutProtectionMiddleware(BaseHTTPMiddleware):
    def __init__(
        self, 
        app, 
        request_timeout: int = 60,  # seconds
        slow_request_threshold: int = 30,  # seconds
        max_concurrent_requests: int = settings.max_concurrent_requests,
    ):
        super().__init__(app)
        self.request_timeout = request_timeout
        self.slow_request_threshold = slow_request_threshold
        self.max_concurrent_requests = max_concurrent_requests
        self.active_requests = 0
        self._lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next):
        # Check concurrent request limit
        async with self._lock:
            if self.active_requests >= self.max_concurrent_requests:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "too_many_concurrent_requests"}
                )
            self.active_requests += 1

        start_time = time.time()
        
        try:
            # Create timeout for the request
            response = await asyncio.wait_for(
                call_next(request),
                timeout=self.request_timeout
            )
                
            return response
            
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=408, 
                detail="request_timeout"
            )
        finally:
            # Always decrement active requests counter
            async with self._lock:
                self.active_requests -= 1
