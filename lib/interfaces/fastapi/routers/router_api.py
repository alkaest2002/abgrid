"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from typing import Any, Dict
from fastapi import APIRouter, Query, Depends, status, Request
from fastapi.responses import JSONResponse

from ..security.auth import Auth
from ..security.limiter import SimpleRateLimiter
from lib.core.core_data import CoreData
from lib.core.core_schemas import ABGridGroupSchema, ABGridReportSchema
from lib.core.core_templates import CoreRenderer
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
        GET /api/token: Generate anonymous JWT token
        POST /api/group: Generate group configuration file
        POST /api/report: Generate analysis report
        
    Note:
        All endpoints return consistent JSON responses with "detail" field
        containing either success data or error information.
    """
    router = APIRouter(prefix="/api")

    @router.get("/token")
    async def get_token() -> JSONResponse:
        """
        Generate a new anonymous JWT token for API authentication.
        
        This endpoint provides anonymous authentication tokens that can be used
        to access protected endpoints. No credentials are required.
        
        Returns:
            JSONResponse: Success response containing the JWT token in the "detail" field
            
        Status Codes:
            200: Token generated successfully
            500: Internal server error during token generation
        """
        try:
            token = _auth.jwt_handler.generate_token()
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"detail": token}
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "failed_to_generate_token"}
            )
    
    @router.post("/group")
    @SimpleRateLimiter(limit=1, window_seconds=5)
    async def create_group(
        request: Request,
        model: ABGridGroupSchema, 
        language: str = Query(..., description="Language of the group template"),
        user_data: Dict[str, Any] = Depends(_auth.verify_token)
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
            group_data = _abgrid_data.get_group_data(model)

            # Render the group template
            template_path = f"/{language}/group.yaml"
            rendered_group = _abgrid_renderer.render(template_path, group_data)
            
            # Generate safe filename
            safe_title = "".join(c for c in model.project_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')[:30]
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
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "failed_to_render_group_template"}
            )

    @router.post("/report")
    @SimpleRateLimiter(limit=1, window_seconds=15)
    async def get_report(
        request: Request,
        model: ABGridReportSchema, 
        language: str = Query(..., description="Language of the report"),
        with_sociogram: bool = Query(..., description="Include sociogram visualization"),
        user_data: Dict[str, Any] = Depends(_auth.verify_token)
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
        """
        try:
            # Generate report data
            report_data = _abgrid_data.get_report_data(model, with_sociogram)
            
            # Render report template
            template_path = f"./{language}/report.html"
            rendered_report = _abgrid_renderer.render(template_path, report_data)

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "detail": {
                        "report_html": rendered_report,
                        "report_json": to_json(report_data)
                    }
                }
            )
            
        except FileNotFoundError:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "report_template_not_found_for_language"}
            )
        except ValueError as e:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "invalid_report_data"}
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "failed_to_generate_report"}
            )

    return router
