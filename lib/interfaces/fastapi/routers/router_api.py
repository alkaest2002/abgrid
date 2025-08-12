"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
# ruff: noqa: ARG001
# ruff: noqa: B008

import asyncio
from typing import Any

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse
from lib.core.core_data import CoreData
from lib.core.core_schemas_in import ABGridGroupSchemaIn, ABGridReportSchemaIn
from lib.core.core_templates import CoreRenderer
from lib.interfaces.fastapi.security.auth import Auth
from lib.interfaces.fastapi.security.limiter import SimpleRateLimiter
from lib.utils import to_json


# Initialize once at module level
_auth = Auth()
_abgrid_data = CoreData()
_abgrid_renderer = CoreRenderer()

def get_router_api() -> APIRouter:
    """
    Create and configure the FastAPI router with API endpoints.

    This function creates a FastAPI router with all the application endpoints
    configured with proper authentication, rate limiting, and error handling.
    All responses are returned as JSON, including error cases.

    Returns:
        APIRouter: Configured router instance with all endpoints registered

    Endpoints:
        POST /api/group: Generate group configuration file
        POST /api/report: Generate analysis report

    Note:
        All endpoints return consistent JSON responses with "detail" field
        containing either success data or error information.
    """
    # Initialize router
    router = APIRouter(prefix="/api")

    # Add endpoints
    @router.post("/group")
    @SimpleRateLimiter(limit=1, window_seconds=5)
    async def create_group(
        request: Request,
        model: ABGridGroupSchemaIn,
        language: str = Query(..., description="Language of the group template"),
        user_data: dict[str, Any] = Depends(_auth.verify_token)
    ) -> JSONResponse:
        """
        Generate group configuration file based on provided schema.

        This endpoint creates a YAML configuration file for a group analysis
        based on the provided group schema and language template.

        Args:
            request: The HTTP request object (used by rate limiter)
            model: Group configuration schema containing all group parameters
            language: Language code for template selection
            user_data: Authenticated user data from JWT token verification

        Returns:
            JSONResponse: Success response with rendered group configuration and metadata
                         containing "rendered_group" content and "metadata" with filename
                         and media type information

        Status Codes:
            200: Group configuration generated successfully
            400: Invalid request data, missing required fields, or template not found
            401: Authentication token invalid or missing
            429: Rate limit exceeded (1 request per 5 seconds)
            500: Template rendering failed or internal server error

        Rate Limiting:
            Limited to 1 request per 5 seconds per client
        """
        try:
            # Run CPU-bound group data processing in thread pool
            group_data: dict[str, Any] = await asyncio.to_thread(
                _abgrid_data.get_group_data,
                model
            )

            # Template rendering is typically I/O bound, but can also be threaded if heavy
            template_path = f"/{language}/group.yaml"
            rendered_group = await asyncio.to_thread(
                _abgrid_renderer.render,
                template_path,
                group_data
            )

            safe_title = "".join(c for c in model.project_title if c.isalnum() or c in (" ", "-", "_")).rstrip()
            safe_title = safe_title.replace(" ", "_")[:30]
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
    @SimpleRateLimiter(limit=1, window_seconds=15)
    async def get_report(
        request: Request,
        model: ABGridReportSchemaIn,
        language: str = Query(..., description="Language of the report"),
        with_sociogram: bool = Query(..., description="Include sociogram visualization"),
        user_data: dict[str, Any] = Depends(_auth.verify_token)
    ) -> JSONResponse:
        """
        Generate comprehensive analysis report based on provided data.

        This endpoint processes the report schema and generates both HTML and JSON
        formatted reports, optionally including sociogram visualizations.

        Args:
            request: The HTTP request object (used by rate limiter)
            model: Report data schema containing all analysis parameters
            language: Language code for report template
            with_sociogram: Whether to include sociogram visualization in the report
            user_data: Authenticated user data from JWT token verification

        Returns:
            JSONResponse: Success response with rendered HTML report and JSON data
                         containing "report_html" with the rendered template and
                         "report_json" with the structured data

        Status Codes:
            200: Report generated successfully
            400: Invalid request data, missing fields, or template not found
            401: Authentication token invalid or missing
            429: Rate limit exceeded (1 request per 15 seconds)
            500: Report generation failed or internal server error

        Rate Limiting:
            Limited to 1 request per 15 seconds per client due to computational intensity

        Note:
            Report generation is computationally intensive, hence the longer rate limit window.
            The sociogram parameter significantly affects processing time and resource usage.
            CPU-intensive operations are executed in thread pool to prevent blocking.
        """
        try:
            # Run heavy computation in thread pool to avoid blocking event loop
            report_data: dict[str, Any] = await asyncio.to_thread(
                _abgrid_data.get_report_data,
                model,
                with_sociogram
            )

            # Template rendering in thread pool as well
            template_path = f"./{language}/report.html"
            rendered_report = await asyncio.to_thread(
                _abgrid_renderer.render,
                template_path,
                report_data
            )

            # JSON serialization can also be CPU-intensive for large data
            report_json = await asyncio.to_thread(
                to_json,
                report_data
            )

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "detail": {
                        "report_html": rendered_report,
                        "report_json": report_json
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

    @router.post("/sna")
    @SimpleRateLimiter(limit=1, window_seconds=15)
    async def get_sna(
        request: Request,
        model: ABGridReportSchemaIn,
        language: str = Query(..., description="Language of the report"),
        user_data: dict[str, Any] = Depends(_auth.verify_token)
    ) -> JSONResponse:
        """
        Generate comprehensive analysis report based on provided data.

        This endpoint processes the report schema and generates both HTML and JSON
        formatted reports, optionally including sociogram visualizations.

        Args:
            request: The HTTP request object (used by rate limiter)
            model: Report data schema containing all analysis parameters
            language: Language code for report template
            user_data: Authenticated user data from JWT token verification

        Returns:
            JSONResponse: Success response with rendered HTML report and JSON data
                         containing "report_html" with the rendered template and
                         "report_json" with the structured data

        Status Codes:
            200: Report generated successfully
            401: Authentication token invalid or missing
            429: Rate limit exceeded (1 request per 15 seconds)
            500: Report generation failed or internal server error

        Rate Limiting:
            Limited to 1 request per 15 seconds per client due to computational intensity

        Note:
            Report generation is computationally intensive, hence the longer rate limit window.
            The sociogram parameter significantly affects processing time and resource usage.
            CPU-intensive operations are executed in thread pool to prevent blocking.
        """
        try:
            # Run heavy computation in thread pool to avoid blocking event loop
            sna_data: dict[str, Any] = await asyncio.to_thread(
                _abgrid_data.get_sna_data,
                model,
            )

            # JSON serialization can also be CPU-intensive for large data
            sna_json = await asyncio.to_thread(
                to_json,
                sna_data
            )

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "detail": sna_json
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

    return router
