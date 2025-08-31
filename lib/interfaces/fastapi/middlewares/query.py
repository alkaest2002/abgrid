"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from collections.abc import Awaitable, Callable
from typing import ClassVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from fastapi import Request, status
from fastapi.responses import JSONResponse


class QueryMiddleware(BaseHTTPMiddleware):
    """Aggressive middleware for closed API server query parameter validation.

    Attributes:
        allowed_params: Set of allowed query parameter keys.
        valid_languages: Set of valid language codes.
        valid_sociogram_values: Set of valid values for the "with_sociogram" parameter.
        max_params_count: Maximum allowed number of query parameters.
    """

    ALLOWED_PARAMS: ClassVar[set[str]] = {"language", "with_sociogram"}
    VALID_LANGUAGES: ClassVar[set[str]] = {"en", "es", "de", "fr", "it"}
    VALID_SOCIOGRAM_VALUES: ClassVar[set[str]] = {"true", "false"}
    MAX_PARAMS_COUNT: ClassVar[int] = 2

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the query parameter validation middleware.

        Args:
            app: The ASGI application instance.

        Returns:
            None.
        """
        super().__init__(app)

    async def dispatch(self,
            request: Request,
            call_next: Callable[[Request], Awaitable[Response]]
        ) -> Response:
        """
        Validate query parameters.

        Empty query strings are allowed to pass through without any validation.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler.

        Returns:
            Response: Error response for violations or result from next handler.
        """
        query_params = request.query_params

        # Allow empty query strings to pass through
        if not query_params:
            return await call_next(request)

        # Check parameter count
        if len(query_params) > self.MAX_PARAMS_COUNT:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "malformed_query_string"}
            )

        # Validate each parameter
        for param_key in query_params:
            # Check if parameter is allowed
            if param_key not in self.ALLOWED_PARAMS:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "malformed_query_string"}
                )

            # Extract parameter value
            param_value = query_params.get(param_key)

            # Validate with_sociogram parameter
            if param_key == "with_sociogram" and param_value not in self.VALID_SOCIOGRAM_VALUES:
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"detail": "malformed_query_string"}
                    )
            # Validate language parameter
            if param_key == "language" and param_value not in self.VALID_LANGUAGES:
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"detail": "malformed_query_string"}
                    )

        return await call_next(request)
