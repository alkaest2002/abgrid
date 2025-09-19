"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
# ruff: noqa: ARG001

import asyncio
from typing import Any

import httpx

from fastapi import APIRouter, Query, Request, status
from fastapi.responses import JSONResponse
from lib.core.core_data import CoreData
from lib.core.core_export import CoreExport
from lib.core.core_schemas_in import (
    ABGridGroupSchemaIn,
    ABGridReportSchemaIn,
    ABGridReportStep1SchemaIn,
    ABGridReportStep2SchemaIn,
    ABGridReportStep3SchemaIn,
)
from lib.core.core_templates import CoreRenderer
from lib.interfaces.fastapi.security.limiter import SimpleRateLimiter
from lib.interfaces.fastapi.settings import Settings


# Create a type alias for all report schemas
type ABGridReportSchemas = ABGridReportSchemaIn | ABGridReportStep1SchemaIn | ABGridReportStep2SchemaIn

# Initialize once at module level
_abgrid_data = CoreData()
_abgrid_renderer = CoreRenderer()

# Create rate limiters for all endpoints
api_limiter_3s = SimpleRateLimiter(
    limit=1,
    window_seconds=3,
    max_cache_size=1000,
    skip_options=True
)

api_limiter_10s = SimpleRateLimiter(
    limit=1,
    window_seconds=10,
    max_cache_size=1000,
    skip_options=True
)

settings: Settings = Settings.load()

def get_router_api() -> APIRouter:  # noqa: PLR0915
    """Create and configure the FastAPI router with API endpoints.

    This function creates a FastAPI router with all the application endpoints
    configured with rate limiting, and error handling.
    All responses are returned as JSON, including error cases.

    Returns:
        APIRouter: Configured router instance with all endpoints registered.

    Endpoints:
        POST /api/group: Generate group configuration file.
        POST /api/report: Generate single-step report.
        POST /api/report/step_1: Generate multi-step report, step 1.
        POST /api/report/step_2: Generate multi-step report, step 2.
        POST /api/report/step_3: Generate multi-step report, step 3.

    Notes:
        All endpoints return consistent JSON responses with "detail" field.
        Rate limiting varies by endpoint: /group uses 3s window, /report uses 10s window,
        multi-step endpoints use 3s window.
    """
    # Initialize router
    router = APIRouter(prefix="/api")

    # Add endpoints
    @router.post("/group")
    @api_limiter_3s
    async def create_group(
        request: Request,
        model: ABGridGroupSchemaIn,
        language: str = Query(..., description="Language of the group template"),
    ) -> JSONResponse:
        """Generate group configuration file based on provided data.

        This endpoint creates a YAML configuration file for a group analysis.

        Args:
            request: The HTTP request object (used by rate limiter).
            model: Group schema containing all group parameters.
            language: Language code for template selection.

        Returns:
            JSONResponse: Success response with rendered group and metadata
                        containing "rendered_group" content and "metadata" with filename
                        and media type information.

        Status Codes:
            - 200: Group generated successfully.
            - 400: Invalid request data, missing required fields, or template not found.
            - 401: Authentication token invalid or missing.
            - 429: Rate limit exceeded (1 request per 3 seconds).
            - 500: Template rendering failed or internal server error.

        Rate Limiting:
            Rate limited to 1 request per 3 seconds due to computational intensity.
        """
        try:
            # Get data
            data: dict[str, Any] = await asyncio.to_thread(
                _abgrid_data.get_group_data,
                model
            )

            # Get Template path
            template_path = f"/{language}/group.yaml"

            # Render Template
            rendered_group = await asyncio.to_thread(
                _abgrid_renderer.render,
                template_path,
                data
            )

            # Generate safe filename
            safe_title = "".join(c for c in model.project_title if c.isalnum() or c in (" ", "-", "_")).rstrip()
            safe_title = safe_title.replace(" ", "_")[:50]  # Limit to 50 characters
            filename = f"{safe_title}_g{model.group}.yaml"

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "detail": {
                        "rendered_group": rendered_group,
                        "metadata": {
                            "filename": filename,
                            "media_type": "text/yaml",
                        },
                    }
                }
            )

        except FileNotFoundError:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "group_template_not_found_for_language"}
            )
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "failed_to_render_group_template"}
            )


    @router.post("/report")
    @api_limiter_10s
    async def create_report(
        request: Request,
        model: ABGridReportSchemaIn,
        language: str = Query(..., description="Language of the report"),
        with_sociogram: bool = Query(..., description="Include sociogram visualization"),
    ) -> JSONResponse:
        """Generate analysis report based on provided data.

        This endpoint processes the report schema and generates both JSON data and
        an HTML formatted report.

        Args:
            request: The HTTP request object (used by rate limiter).
            model: Report schema containing collected data.
            language: Language code for report template.
            with_sociogram: Whether to include sociogram visualization in the report.

        Returns:
            JSONResponse: Success response with rendered HTML report and JSON data
                        containing "report_html" with the rendered template and
                        "report_json" with the structured data.

        Status Codes:
            - 200: Report generated successfully.
            - 400: Invalid request data, missing fields, or template not found.
            - 401: Authentication token invalid or missing.
            - 429: Rate limit exceeded (1 request per 10 seconds).
            - 500: Report generation failed or internal server error.

        Rate Limiting:
            Rate limited to 1 request per 10 seconds due to computational intensity.
        """
        try:
            # if we are calling aws lambda
            if (settings.aws_function_url):

                # Get data via aws lambda
                data = await _get_report_via_aws(
                    settings.aws_function_url,
                    model,
                    language,
                    with_sociogram
                )

                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={
                        "detail": {
                            "report_html": data.get("rendered_report"),
                            "report_json": data.get("data_json")
                        }
                    }
                )

            # Get data
            data = await asyncio.to_thread(
                _abgrid_data.get_report_data,
                model,
                with_sociogram
            )

            # Render template and Serialize data concurrently
            template_path = f"./{language}/report.html"
            rendered_report, data_json = await asyncio.gather(
                asyncio.to_thread(_abgrid_renderer.render, template_path, data),
                asyncio.to_thread(CoreExport.to_json, data)
            )

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "detail": {
                        "report_html": rendered_report,
                        "report_json": data_json
                    }
                }
            )

        except FileNotFoundError:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "report_template_not_found_for_language"}
            )
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "invalid_report_data"}
            )
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "failed_to_generate_report"}
            )


    @router.post("/report/step_1")
    @api_limiter_3s
    async def multi_step_step_1(
        request: Request,
        model: ABGridReportStep1SchemaIn,
    ) -> JSONResponse:
        """Generate step 1 data for multi-step report generation.

        This endpoint is the first step in the multi-step report generation process.
        It processes the report schema and generates JSON data containing group
        analysis and social network analysis information.

        Args:
            request: The HTTP request object (used by rate limiter).
            model: Report schema containing collected survey data.

        Returns:
            JSONResponse: Success response with JSON data.

        Status Codes:
            - 200: Group and SNA data generated successfully.
            - 400: Invalid report data or missing required fields.
            - 401: Authentication token invalid or missing.
            - 429: Rate limit exceeded (1 request per 3 seconds).
            - 500: Data generation failed or internal server error.

        Rate Limiting:
            Rate limited to 1 request per 3 seconds due to computational intensity.

        Notes:
            This is step 1 of a 3-step process. The returned data should be used
            as input for subsequent steps in the multi-step report generation workflow.
        """
        try:
            # Get data
            data = await asyncio.to_thread(
                _abgrid_data.get_multistep_step_1,
                model,
            )

            # JSON serialization
            data_json = await asyncio.to_thread(
                CoreExport.to_json_report_step_1,
                data,
            )

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "detail": data_json
                }
            )

        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "invalid_report_data"}
            )
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "failed_to_generate_report"}
            )


    @router.post("/report/step_2")
    @api_limiter_3s
    async def multi_step_step_2(
        request: Request,
        model: ABGridReportStep2SchemaIn,
        with_sociogram: bool = Query(..., description="Include sociogram visualization"),
    ) -> JSONResponse:
        """Generate step 2 data for multi-step report generation.

        This endpoint is the second step in the multi-step report generation process.
        It processes the report schema and generates JSON data containing group related
        data, SNA, sociogram, isolated nodes and relevant nodes.

        Args:
            request: The HTTP request object (used by rate limiter).
            model: Report schema containing collected data.
            with_sociogram: Whether to include sociogram visualization in the report.

        Returns:
            JSONResponse: Success response with JSON data.

        Status Codes:
            - 200: Sociogram data generated successfully.
            - 400: Invalid report data or missing required fields.
            - 401: Authentication token invalid or missing.
            - 429: Rate limit exceeded (1 request per 3 seconds).
            - 500: Sociogram generation failed or internal server error.

        Rate Limiting:
            Rate limited to 1 request per 3 seconds due to computational intensity.

        Notes:
            This is step 2 of a 3-step process. The returned sociogram data should be
            combined with step 1 results for final report generation in step 3.
        """
        try:
            # Get data
            data = await asyncio.to_thread(
                _abgrid_data.get_multistep_step_2,
                model,
                with_sociogram
            )

            # JSON serialization
            data_json = await asyncio.to_thread(
                CoreExport.to_json_report_step_2,
                data
            )

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "detail": data_json
                }
            )

        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "invalid_report_data"}
            )
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "failed_to_generate_report"}
            )


    @router.post("/report/step_3")
    @api_limiter_3s
    async def multi_step_step_3(
        request: Request,
        model: ABGridReportStep3SchemaIn,
        language: str = Query(..., description="Language of the report template"),
    ) -> JSONResponse:
        """Generate HTML report.

        This endpoint is the final step in the multi-step report generation process.
        It takes the combined data from previous steps (1, 2) and renders it into a complete
        HTML report using the specified language template.

        Args:
            request: The HTTP request object (used by rate limiter).
            model: Multi-step report schema containing data from previous steps.
            language: Language code for report template selection.

        Returns:
            JSONResponse: Success response with rendered HTML report content.

        Status Codes:
            - 200: Final HTML report generated successfully.
            - 400: Invalid multi-step report data or missing required fields.
            - 401: Authentication token invalid or missing.
            - 404: Report template not found for specified language.
            - 429: Rate limit exceeded (1 request per 3 seconds).
            - 500: Template rendering failed or internal server error.

        Rate Limiting:
            Rate limited to 1 request per 3 seconds due to computational intensity.

        Notes:
            This is the final step (step 3) of the multi-step process. It requires
            data from both step 1 and step 2 to generate the complete report.
        """
        try:

            # Get data
            data: dict[str, Any] = await asyncio.to_thread(
                _abgrid_data.get_multistep_step3,
                model,
            )

            # Template path
            template_path = f"./{language}/report.html"

            # Template rendering
            rendered_report = await asyncio.to_thread(
                _abgrid_renderer.render,
                template_path,
                data
            )

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "detail": rendered_report,
                }
            )

        except FileNotFoundError:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "report_template_not_found_for_language"}
            )
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "invalid_report_data"}
            )
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "failed_to_generate_report"}
            )

    return router


##################################################################################################################
#   PRIVATE METHODS
##################################################################################################################

async def _get_report_via_aws(
        aws_url: str,
        model: ABGridReportSchemaIn | ABGridReportStep1SchemaIn | ABGridReportStep2SchemaIn,
        language: str,
        with_sociogram: bool,
    ) -> Any:
    """Retrieve report data using either AWS Lambda function or local processing.

    This function attempts to fetch report data through an AWS Lambda function if
    configured, otherwise falls back to local data processing using the provided retriever.

    Args:
        aws_url: URL of the AWS Lambda function for report generation.
        model: Pydantic model containing the input data for report generation.
               Supports multiple schema types for different report steps.
        with_sociogram: Boolean indicating whether to include sociogram visualization.
        language: Language code for report template selection.

    Returns:
        dict[str, Any]: Dictionary containing the processed report data. When using AWS Lambda,
                       returns the 'detail' field from the response data. When using local
                       processing, returns the result from the provided retriever function.

    Raises:
        httpx.RequestError: If the AWS Lambda function request fails.
        httpx.HTTPStatusError: If the AWS Lambda function returns a non-2xx status code.
        Exception: Any exception that might occur during local data processing.
    """
    # httpx async client
    async with httpx.AsyncClient() as client:
        # Set json payload
        json_payload: dict[str, Any] = {
            "data": model.model_dump(),
            "with_sociogram": with_sociogram,
            "language": language,
        }

        # Make request to aws lambda function
        response = await client.post(
            aws_url,
            json=json_payload,
            timeout=45.0
        )

        # Raise for status
        response.raise_for_status()

        return response.json()
