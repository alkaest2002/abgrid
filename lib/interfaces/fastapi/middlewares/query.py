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
    """Middleware for query parameter validation.

    Attributes:
        valid_languages: Set of valid language codes.
        valid_sociogram_values: Set of valid values for the "with_sociogram" parameter.
    """

    VALID_LANGUAGES: ClassVar[set[str]] = {"en", "es", "de", "fr", "it"}
    VALID_SOCIOGRAM_VALUES: ClassVar[set[str]] = {"true", "false"}

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the query parameter validation middleware.

        Args:
            app: The ASGI application instance.

        Returns:
            None
        """
        super().__init__(app)

    async def dispatch(self,
            request: Request,
            call_next: Callable[[Request], Awaitable[Response]]
        ) -> Response:
        """Validate query parameters.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler.

        Returns:
            The HTTP response.
        """
        query_params = request.query_params

        # Allow empty query strings
        if not query_params:
            return await call_next(request)

        # Get first two parameter keys
        param_keys = list(query_params.keys())[:2]

        # Check if all keys are valid (must be subset of {language, with_sociogram})
        if not set(param_keys).issubset({"language", "with_sociogram"}):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "malformed_query_string"}
            )

        # Validate parameter values
        for param_key in param_keys:

            # Get the parameter value
            param_value = query_params.get(param_key)

            # Validate with_sociogram
            if param_key == "with_sociogram" and param_value not in self.VALID_SOCIOGRAM_VALUES:
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"detail": "malformed_query_string"}
                    )

            # Validate language
            if param_key == "language" and param_value not in self.VALID_LANGUAGES:
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"detail": "malformed_query_string"}
                    )

        return await call_next(request)
