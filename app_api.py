"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
# ruff: noqa: ARG001

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from lib.core.core_schemas_errors import PydanticValidationError
from lib.interfaces.fastapi.middlewares.body import BodySizeLimitMiddleware
from lib.interfaces.fastapi.middlewares.coors import (
    add_cors_middleware,  # Import the CORS function
)
from lib.interfaces.fastapi.middlewares.header import HeaderSizeLimitMiddleware
from lib.interfaces.fastapi.middlewares.query import QueryParamLimitMiddleware
from lib.interfaces.fastapi.middlewares.request import RequestProtectionMiddleware
from lib.interfaces.fastapi.routers.router_api import get_router_api
from lib.interfaces.fastapi.routers.router_fake import get_router_fake
from lib.interfaces.fastapi.security.limiter import RateLimitError
from lib.utils import to_snake_case


# Initialization of FastAPI application
app = FastAPI()

#######################################################################################
# Middlewares
#######################################################################################

# 1. CORS
add_cors_middleware(app)

# 2. Request limits protection
app.add_middleware(RequestProtectionMiddleware)

# 3. Header limits protection
app.add_middleware(HeaderSizeLimitMiddleware)

# 4. Query parameters limits protection
app.add_middleware(QueryParamLimitMiddleware)

# 5. Body limits protection
app.add_middleware(BodySizeLimitMiddleware)

#######################################################################################
# Routes
#######################################################################################

# Include api router
app.include_router(get_router_api())

# Include api router
app.include_router(get_router_fake())

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
    """Catchall endpoint that returns a JSON response for undefined routes."""
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
    """Custom handler for 401 Unauthorized errors."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "not_authenticated"}
    )

@app.exception_handler(status.HTTP_403_FORBIDDEN)
async def custom_403_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Custom handler for 403 Forbidden errors."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": "not_authorized"}
    )

@app.exception_handler(PydanticValidationError)
async def custom_pydantic_validation_exception_handler(
    request: Request, exc: PydanticValidationError
) -> JSONResponse:
    """Custom handler for PydanticValidationError errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Custom handler for RequestValidationError errors."""
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
    """Custom handler for RateLimitError errors."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": exc.message}
    )
