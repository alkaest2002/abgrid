"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from collections.abc import Awaitable, Callable
from typing import ClassVar
from urllib.parse import parse_qs

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from fastapi import Request, status
from fastapi.responses import JSONResponse


class QueryParamLimitMiddleware(BaseHTTPMiddleware):
    """Aggressive middleware for closed API server query parameter validation.

    This middleware provides strict validation for a closed API that only accepts:
    - language: Always required (e.g., 'it' for Italian)
    - with_sociogram: Optional boolean ('true' or 'false')

    Any deviation from these exact requirements results in immediate rejection.
    Empty query strings are allowed to pass through without validation.

    Early rejection criteria:
    - Unusually long query strings (>200 chars)
    - Unknown query parameters
    - Missing required 'language' parameter (when params are present)
    - Invalid boolean values for 'with_sociogram'
    - Malformed query strings
    - Excessive parameter counts

    Args:
        app: The ASGI application instance.

    Raises:
        JSONResponse: Returns 400 status for various validation failures.

    Notes:
        This middleware is designed for maximum efficiency and security in a
        controlled API environment where parameter specifications are strict.
        Empty query strings bypass all validation.
    """
    # Valid parameter names for this closed API
    ALLOWED_PARAMS: ClassVar[set[str]] = {"language", "with_sociogram"}
    VALID_SOCIOGRAM_VALUES: ClassVar[set[str]] = {"true", "false"}

    # Aggressive limits for closed API
    MAX_QUERY_STRING_LENGTH: ClassVar[int] = 200  # Very conservative for closed API
    MAX_PARAM_KEY_LENGTH: ClassVar[int] = 20      # "with_sociogram" is 14 chars
    MAX_PARAM_VALUE_LENGTH: ClassVar[int] = 10    # Language codes are typically 2-5 chars
    MAX_PARAMS_COUNT: ClassVar[int] = 2           # Only 2 possible parameters

    def __init__(self, app: ASGIApp) -> None:
        """Initialize the aggressive query parameter validation middleware.

        Args:
            app: The ASGI application instance.

        Returns:
            None.
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:  # noqa: PLR0911, PLR0912
        """
        Aggressively validate query parameters with early rejection.

        Empty query strings are allowed to pass through without any validation.

        Performs validation in order of computational efficiency:
        1. Empty query string check (bypass all validation)
        2. Query string length check (fastest)
        3. Basic parsing validation
        4. Parameter count validation
        5. Parameter name/value validation
        6. Business logic validation (required params, valid values)

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler.

        Returns:
            Response: Error response for violations or result from next handler.
        """
        query_string = str(request.url.query)

        # Allow empty query strings to pass through without validation
        if not query_string:
            return await call_next(request)

        # Early rejection: Check total query string length first (most efficient)
        if len(query_string) > self.MAX_QUERY_STRING_LENGTH:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "query_string_too_long"}
            )

        # Parse and validate query parameters
        try:
            query_params: dict[str, list[str]] = parse_qs(
                query_string,
                keep_blank_values=False,  # Reject empty values
                strict_parsing=True       # Strict parsing mode
            )
        except (ValueError, UnicodeDecodeError):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "malformed_query_string"}
            )

        # Early rejection: Check parameter count
        if len(query_params) > self.MAX_PARAMS_COUNT:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "too_many_parameters"}
            )

        # Validate each parameter
        for param_key, param_values in query_params.items():

            # Check parameter key length
            if len(param_key) > self.MAX_PARAM_KEY_LENGTH:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "query_parameter_key_too_long"}
                )

            # Check if parameter is allowed
            if param_key not in self.ALLOWED_PARAMS:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "unknown_query_parameter_key"}
                )

            # Check for duplicate parameters (same key multiple times)
            if len(param_values) > 1:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "duplicate_query_parameter_key"}
                )

            # Validate parameter value
            param_value = param_values[0]  # We know there's exactly one value

            # Check parameter value length
            if len(param_value) > self.MAX_PARAM_VALUE_LENGTH:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "query_parameter_value_too_long"}
                )

            # Validate specific parameter business logic
            if param_key == "with_sociogram":
                if param_value not in self.VALID_SOCIOGRAM_VALUES:
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"detail": "invalid_with_sociogram_value"}
                    )

            elif param_key == "language":
                # Basic language code validation (2 letters)
                max_letters = 2
                if not (len(param_value) == max_letters and param_value.isalpha()):
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"detail": "invalid_language_code"}
                    )

        # Check required parameters (only when query parameters are present)
        if "language" not in query_params:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "missing_required_language_parameter"}
            )

        # All validations passed, proceed to next handler
        return await call_next(request)
