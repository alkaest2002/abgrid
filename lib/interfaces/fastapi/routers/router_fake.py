"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse


error_codes = {
    "duplicate_query_parameter_key": status.HTTP_400_BAD_REQUEST,
    "failed_to_generate_report": status.HTTP_500_INTERNAL_SERVER_ERROR,
    "failed_to_generate_token": status.HTTP_500_INTERNAL_SERVER_ERROR,
    "failed_to_render_group_template": status.HTTP_500_INTERNAL_SERVER_ERROR,
    "group_template_not_found_for_language": status.HTTP_404_NOT_FOUND,
    "header_is_too_large": status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    "invalid_content_length_header": status.HTTP_400_BAD_REQUEST,
    "invalid_language_code": status.HTTP_400_BAD_REQUEST,
    "invalid_or_expired_jwt_token": status.HTTP_401_UNAUTHORIZED,
    "invalid_report_data": status.HTTP_400_BAD_REQUEST,
    "invalid_with_sociogram_value": status.HTTP_400_BAD_REQUEST,
    "malformed_query_string": status.HTTP_400_BAD_REQUEST,
    "missing_required_language_parameter": status.HTTP_400_BAD_REQUEST,
    "not_authenticated": status.HTTP_401_UNAUTHORIZED,
    "not_authorized": status.HTTP_403_FORBIDDEN,
    "query_parameter_key_too_long": status.HTTP_400_BAD_REQUEST,
    "query_parameter_value_too_long": status.HTTP_400_BAD_REQUEST,
    "query_string_too_long": status.HTTP_400_BAD_REQUEST,
    "report_template_not_found_for_language": status.HTTP_404_NOT_FOUND,
    "request_body_too_large": status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    "request_timeout": status.HTTP_408_REQUEST_TIMEOUT,
    "requests_exceeded_rate_limit": status.HTTP_429_TOO_MANY_REQUESTS,
    "too_many_concurrent_requests": status.HTTP_429_TOO_MANY_REQUESTS,
    "too_many_query_parameters": status.HTTP_400_BAD_REQUEST,
    "unknown_query_parameter_key": status.HTTP_400_BAD_REQUEST,
}

def get_router_fake() -> APIRouter:
    """Create and configure the FastAPI router for fake endpoints."""
    # Initialize router
    router = APIRouter(prefix="/fake", include_in_schema=False)

    # Add endpoints
    @router.get("/error")
    async def get_error(error_type: str = Query(..., description="Error type to simulate")) -> JSONResponse:
        """Simulate an error response based on the provided error type.

        Args:
            error_type: The error type key that matches one of the predefined error codes

        Returns:
            JSONResponse: Error response with appropriate status code and detail message

        Status Codes:
            Various: Depends on the error_type parameter
            400: If error_type is not found in error_codes
        """
        if error_type in error_codes:
            return JSONResponse(
                status_code=error_codes[error_type],
                content={"detail": error_type}
            )

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "unknown_error_type"}
        )

    return router
