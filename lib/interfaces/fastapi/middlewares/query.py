from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import HTTPException, Request
from urllib.parse import parse_qs

class QueryParamLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to limit query parameter size and count.
    """
    
    def __init__(
        self, 
        app,
        max_query_string_length: int = 8192,
        max_query_params_count: int = 100, 
        max_query_param_length: int = 1024
    ):
        super().__init__(app)
        self.max_query_string_length = max_query_string_length
        self.max_query_params_count = max_query_params_count
        self.max_query_param_length = max_query_param_length

    async def dispatch(self, request: Request, call_next):
        query_string = str(request.url.query)
        
        # Check total query string length
        if len(query_string) > self.max_query_string_length:
            raise HTTPException(status_code=413, detail="query_string_too_large")
        
        # Parse and validate parameters
        if query_string:
            try:
                query_params = parse_qs(query_string, keep_blank_values=True)
                
                # Count total parameters (including multiple values for same key)
                total_params = sum(len(values) for values in query_params.values())
                if total_params > self.max_query_params_count:
                    raise HTTPException(
                        status_code=413, 
                        detail="too_many_query_parameters"
                    )
                
                # Check individual parameter and value sizes
                for key, values in query_params.items():
                    if len(key) > self.max_query_param_length:
                        raise HTTPException(
                            status_code=413, 
                            detail="query_parameter_key_too_large"
                        )
                    
                    for value in values:
                        if len(value) > self.max_query_param_length:
                            raise HTTPException(
                                status_code=413, 
                                detail="query_parameter_value_too_large"
                            )
                            
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail="malformed_query_string"
                )
        
        response = await call_next(request)
        return response
