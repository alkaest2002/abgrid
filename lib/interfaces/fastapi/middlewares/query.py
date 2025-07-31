"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from typing import Callable, Dict, List
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.responses import Response
from urllib.parse import parse_qs


class QueryParamLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to limit query parameter size and count to prevent query-based attacks.
    
    This middleware provides comprehensive protection against query parameter abuse by
    enforcing limits on:
    - Total query string length
    - Number of query parameters
    - Individual parameter key and value sizes
    
    This helps prevent denial of service attacks through oversized or excessive
    query parameters that could cause memory exhaustion or processing delays.
    
    Args:
        app: The ASGI application instance
        max_query_string_length: Maximum allowed total query string length in bytes 
                               (default: ~8KB)
        max_query_params_count: Maximum number of query parameters allowed 
                              (default: 100)
        max_query_param_length: Maximum length for individual parameter keys and 
                              values in bytes (default: 1KB)
                              
    Raises:
        JSONResponse: Returns 413 status for various size/count limit violations
        JSONResponse: Returns 400 status for malformed query strings
        
    Note:
        The middleware counts parameters with multiple values (e.g., ?tags=a&tags=b)
        as separate parameters for the total count limit.
    """
    
    def __init__(
        self, 
        app,
        max_query_string_length: int = 8 * 1024,  # Fixed typo: was 1014
        max_query_params_count: int = 100, 
        max_query_param_length: int = 1 * 1024
    ) -> None:
        """
        Initialize the middleware with query parameter limit configuration.
        
        Args:
            app: The ASGI application instance
            max_query_string_length: Maximum allowed total query string length 
                                   in bytes (default: 8KB)
            max_query_params_count: Maximum number of query parameters allowed
                                  (default: 100)
            max_query_param_length: Maximum length for individual parameter keys
                                  and values in bytes (default: 1KB)
        """
        super().__init__(app)
        self.max_query_string_length = max_query_string_length
        self.max_query_params_count = max_query_params_count
        self.max_query_param_length = max_query_param_length

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        """
        Process incoming request and enforce query parameter limits.
        
        Validates the request's query string against all configured limits:
        1. Total query string length
        2. Number of query parameters
        3. Individual parameter key and value sizes
        
        Args:
            request: The incoming HTTP request with query parameters to validate
            call_next: The next middleware or route handler in the chain
            
        Returns:
            Response: Either an error response for limit violations or the result
                     from the next handler in the chain
                     
        Raises:
            JSONResponse: Various 413 responses for different limit violations:
                - "query_string_too_large": Total query string exceeds length limit
                - "too_many_query_parameters": Parameter count exceeds limit
                - "query_parameter_key_too_large": Parameter key exceeds length limit
                - "query_parameter_value_too_large": Parameter value exceeds length limit
            JSONResponse: 400 response for malformed query strings that cannot be parsed
        """
        query_string = str(request.url.query)
        
        # Check total query string length
        if len(query_string) > self.max_query_string_length:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "query_string_too_large"}
            )
        
        # Parse and validate parameters
        if query_string:
            try:
                query_params: Dict[str, List[str]] = parse_qs(query_string, keep_blank_values=True)
                
                # Count total parameters (including multiple values for same key)
                total_params = sum(len(values) for values in query_params.values())
                if total_params > self.max_query_params_count:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={"detail": "too_many_query_parameters"}
                    )
                
                # Check individual parameter and value sizes
                for key, values in query_params.items():
                    if len(key) > self.max_query_param_length:
                        return JSONResponse(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            content={"detail": "query_parameter_key_too_large"}
                        )
                    
                    for value in values:
                        if len(value) > self.max_query_param_length:
                            return JSONResponse(
                                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                                content={"detail": "query_parameter_value_too_large"}
                            )
                            
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "malformed_query_string"}
                )
        
        response = await call_next(request)
        return response
