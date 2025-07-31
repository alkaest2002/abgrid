"""
Filename: app_api.py

Description: FastAPI application entry point for AB-Grid REST API server with health monitoring and custom exception handling.

Author: Pierpaolo Calanna

Date Created: Jul 1, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from itertools import product
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from lib.core.core_schemas import PydanticValidationException
from lib.interfaces.fastapi.limiter import RateLimitException
from lib.interfaces.fastapi.middlewares.body import BodySizeLimitMiddleware
from lib.interfaces.fastapi.middlewares.query import QueryParamLimitMiddleware
from lib.interfaces.fastapi.middlewares.timeout import TimeoutProtectionMiddleware
from lib.interfaces.fastapi.router import get_router
from lib.interfaces.fastapi.middlewares.headers import HeaderSizeLimitMiddleware
from lib.utils import to_snake_case

# Initialization of FastAPI application
app = FastAPI()

# List of ports
fancy_ports = [ "53472", "53247", "53274", "53427", "53724", "53742" ]

# Define domains that should be allowed to access your server
domains = [ "https://localhost", "https://127.0.0.1", "http://localhost", "http://127.0.0.1" ]

# Define origines that should be allowed to access your server
origins = [f"{domain}:{port}" for domain, port in product(domains, fancy_ports)]

# Add render app origin
origins.append("https://abgrid-webapp.onrender.com")

#######################################################################################
# Middlewares
#######################################################################################

# 1. CORS - Should be first to handle preflight requests properly
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Restrict to the specific local port your app will use
    allow_credentials=True,  # Allow credentials for authentication
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Methods your app might use
    allow_headers=["Authorization", "Content-Type"],  # Common headers used in requests
)

# 2. Dynamic Timeout Protection - Early rejection based on system resources
app.add_middleware(
    TimeoutProtectionMiddleware,
    request_timeout=30,
    max_concurrent_requests=10,
    slow_request_threshold=10
)

# 3. Header Size Limit - Check headers before processing request further
app.add_middleware(
    HeaderSizeLimitMiddleware, # Restrict size of headers
    max_header_size=4096 # Max 4KB for headers
)

# 4. Query Parameter Limits - Validate query params early
app.add_middleware(
    QueryParamLimitMiddleware, 
    max_query_string_length=8192, # 8KB
    max_query_params_count=100,   # 100 params max
    max_query_param_length=1024   # 1KB
) 

# 5. Body Size Limit - Check body size last (most expensive validation)
app.add_middleware(
    BodySizeLimitMiddleware, # Restrict size of body
    max_body_size=.5 * 1024 * 1024  # Max 500KB for request bodies
)

#######################################################################################
# Routes
#######################################################################################

# Include application router
app.include_router(get_router())

# Add other routes
@app.get("/")
@app.get("/health")
def server_check() -> JSONResponse:
    """
    Public endpoint that can be accessed without authentication.

    Returns:
        JSONResponse: A message indicating the endpoint is publicly accessible.
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "detail": "up"
        }
    )

@app.get("/{path:path}")
def catchall(path: str) -> JSONResponse:
    """
    Catchall endpoint that returns a JSON response for undefined routes.
    """
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "detail": "route_not_found",
            "redirect_to": "/"
        }
    )

#######################################################################################
# Custom error handlers
#######################################################################################

@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
async def custom_401_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "not_authenticated"}
    )

@app.exception_handler(status.HTTP_403_FORBIDDEN)
async def custom_403_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": "not_authorized"}
    )

@app.exception_handler(PydanticValidationException)
async def custom_pydantic_validation_exception_handler(
    request: Request, exc: PydanticValidationException
) -> JSONResponse:
    """
    Custom exception handler for PydanticValidationException.

    Args:
        request (Request): The request that resulted in the exception.
        exc (PydanticValidationException): The exception instance.
    
    Returns:
        JSONResponse: A JSON response with status code 422 and error details.
    """
    print(exc)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc) -> JSONResponse:
    errors = []
    for error in exc.errors():
        # Create a copy of the error dict
        modified_error = error.copy()
        # Convert msg (if any) to snake_case
        if "msg" in error:
            modified_error["error_message"] = to_snake_case(error["msg"])
        # Convert loc (if any) to snake_case
        if "loc" in error:
            modified_error["location"] = error["loc"]
        errors.append(modified_error)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": errors}
    )

@app.exception_handler(RateLimitException)
async def rate_limit_exception_handler(
    request: Request, exc: RateLimitException
) -> JSONResponse:
    """
    Custom exception handler for RateLimitException.

    Args:
        request (Request): The request that triggered the exception.
        exc (RateLimitException): The exception instance.
    
    Returns:
        JSONResponse: A JSON response with status code 429 and error details.
    """
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": exc.message}
    )
