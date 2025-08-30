"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
# ruff: noqa: ARG001
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, ORJSONResponse

from lib.core.core_schemas_errors import PydanticValidationError
from lib.interfaces.fastapi.middlewares.body import BodyMiddleware
from lib.interfaces.fastapi.middlewares.compress import CompressMiddleware
from lib.interfaces.fastapi.middlewares.coors import CORSMiddleware
from lib.interfaces.fastapi.middlewares.decompress import DecompressMiddleware
from lib.interfaces.fastapi.middlewares.header import HeaderMiddleware
from lib.interfaces.fastapi.middlewares.query import QueryMiddleware
from lib.interfaces.fastapi.middlewares.request import RequestMiddleware
from lib.interfaces.fastapi.routers.router_api import get_router_api
from lib.interfaces.fastapi.security.limiter import RateLimitError
from lib.utils import to_snake_case


# Initialization of FastAPI application
app = FastAPI(default_response_class=ORJSONResponse)

#######################################################################################
# Middlewares (processed in reverse order)
#######################################################################################

# 7. Compress
app.add_middleware(CompressMiddleware)

# 6. Decompress
app.add_middleware(DecompressMiddleware)

# 5. Body
app.add_middleware(BodyMiddleware)

# 4. Request
app.add_middleware(RequestMiddleware)

# 3. Query
app.add_middleware(QueryMiddleware)

# 2. Header
app.add_middleware(HeaderMiddleware)

# 1. CORS
app.add_middleware(CORSMiddleware, **CORSMiddleware.get_params())


#######################################################################################
# Routes
#######################################################################################

# Include api router
app.include_router(get_router_api())

# Add other routes
@app.get("/")
@app.get("/health")
def server_check() -> JSONResponse:
    """Health check endpoint that can be accessed without authentication.

    Provides a simple health check for the API service, accessible at both
    root path (/) and /health endpoints.

    Returns:
        JSONResponse: A message indicating the service is up and running.
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "detail": "up"
        }
    )

@app.get("/{path:path}")
def catchall(path: str) -> JSONResponse:
    """Catchall endpoint that returns a JSON response for undefined routes.

    Args:
        path: The requested path that doesn't match any defined routes.

    Returns:
        JSONResponse: 404 error response with redirect suggestion to root path.
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
async def custom_401_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Custom handler for 401 Unauthorized errors.

    Args:
        request: The HTTP request object.
        exc: The HTTPException that was raised.

    Returns:
        JSONResponse: Standardized 401 error response.
    """
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "not_authenticated"}
    )

@app.exception_handler(status.HTTP_403_FORBIDDEN)
async def custom_403_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Custom handler for 403 Forbidden errors.

    Args:
        request: The HTTP request object.
        exc: The HTTPException that was raised.

    Returns:
        JSONResponse: Standardized 403 error response.
    """
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": "not_authorized"}
    )

@app.exception_handler(PydanticValidationError)
async def custom_pydantic_validation_exception_handler(
    request: Request, exc: PydanticValidationError
) -> JSONResponse:
    """Custom handler for PydanticValidationError errors.

    Args:
        request: The HTTP request object.
        exc: The PydanticValidationError that was raised.

    Returns:
        JSONResponse: Standardized validation error response with error details.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Custom handler for RequestValidationError errors.

    Processes validation errors and converts field names and messages to snake_case
    for consistent API response formatting.

    Args:
        request: The HTTP request object.
        exc: The RequestValidationError that was raised.

    Returns:
        JSONResponse: Standardized validation error response with formatted error details.
    """
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

@app.exception_handler(RateLimitError)
async def rate_limit_exception_handler(
    request: Request, exc: RateLimitError
) -> JSONResponse:
    """Custom handler for RateLimitError errors.

    Args:
        request: The HTTP request object.
        exc: The RateLimitError that was raised.

    Returns:
        JSONResponse: Standardized rate limit error response.
    """
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": exc.message}
    )
