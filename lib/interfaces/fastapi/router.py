"""
Filename: router.py

Description: FastAPI router with strict JWT authentication (except for /token endpoint).

Author: Pierpaolo Calanna

Date Created: Jul 1, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
from typing import Literal, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Depends, status, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from lib.core import SYMBOLS

from .auth import Auth
from .limiter import SimpleRateLimiter
from lib.core.core_data import CoreData
from lib.core.core_schemas import ABGridGroupSchema, ABGridReportSchema
from lib.core.core_templates import CoreRenderer
from lib.utils import to_json

def get_router() -> APIRouter:
    """
    Create and configure the FastAPI router.

    Returns:
        An instance of FastAPI APIRouter with configured endpoints.
    """
    router = APIRouter(prefix="/api")
    
    # Init components
    auth = Auth()
    abgrid_data = CoreData()
    abgrid_renderer = CoreRenderer()

    @router.get("/token")
    async def get_token() -> JSONResponse:
        """
        Get a new anonymous JWT token.

        This is the ONLY endpoint that doesn't require authentication.

        Returns:
            A dictionary containing the new token.
        """
        # Generate token
        token = auth.jwt_handler.generate_token()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"detail": token}
        )
    
    @router.post("/group")
    @SimpleRateLimiter(limit=1, window_seconds=5)
    async def create_group(
        request: Request,
        model: ABGridGroupSchema, 
        language: str = Query(..., description="Language of the group template"),
        user_data: Dict[str, Any] = Depends(auth.verify_token)
    ) -> PlainTextResponse:
        """
        Generate group configuration file. Anonymous JWT authentication is required.

        Args:
            request: HTTP request object.
            model: The schema model for the ABGrid group.
            language: The language of the generated group file.
            user_data: Decoded JWT token payload with user ID.
            
        Returns:
            The generated group configuration file as a YAML file.

        Raises:
            HTTPException: If group configuration file generation fails.
        """

        # Get report data
        template_data = abgrid_data.get_group_data(model)

        # Render the template with group-specific data
        try:
            template_path = f"/{language}/group.html"
            rendered_template = abgrid_renderer.render_html(template_path, template_data)
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to render template: {str(e)}"
            )
        
        # Generate safe filename
        safe_title = "".join(c for c in model.project_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')[:30]
        filename = f"{safe_title}_g{model.group}.yaml"
        
        return PlainTextResponse(
            content=rendered_template,
            media_type="text/yaml",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache"
            }
        )


    @router.post("/report")
    @SimpleRateLimiter(limit=1, window_seconds=15)
    async def get_report(
        request: Request,
        model: ABGridReportSchema, 
        language: str = Query(..., description="Language of the report"),
        type_of_report: Literal['html', 'json'] = Query(..., description="The type of report desired"),
        with_sociogram: bool = Query(..., description="Include sociogram"),
        user_data: Dict[str, Any] = Depends(auth.verify_token)
    ) -> Any:
        """
        Generate a report. Anonymous JWT authentication is required.

        Args:
            request: HTTP request object.
            model: The schema model for the ABGrid report.
            language: The language of the generated report.
            type_of_report: The type of the report ('html' or 'json').
            with_sociogram: Flag to include sociogram in report.
            user_data: Decoded JWT token payload with user ID.
            
        Returns:
            The generated report either as HTML or JSON response.

        Raises:
            HTTPException: If report generation fails or requested language is not available.
        """
        try:
            # Get report data
            report_data = abgrid_data.get_report_data(model, with_sociogram)

            if type_of_report == "html":
                return _generate_html_report(language, report_data)
            elif type_of_report == "json":
                return _generate_json_report(report_data)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": str(e)}
            )

    def _generate_html_report(language: str, template_data: Dict[str, Any]) -> HTMLResponse:
        """
        Generate an HTML report.

        Args:
            language: The language of the report.
            report_data: The data to render in the report.

        Returns:
            HTMLResponse object containing the rendered HTML.
        """
        template_path = f"./{language}/report.html"
        rendered_template = abgrid_renderer.render_html(template_path, template_data)
        return HTMLResponse(
            status_code=status.HTTP_200_OK,
            content={"detail": rendered_template}
        )

    def _generate_json_report(report_data: Dict[str, Any]) -> JSONResponse:
        """
        Generate a JSON report.

        Args:
            report_data: The data to serialize into JSON format.

        Returns:
            JSONResponse object containing the JSON data.
        """
        json_serializable_data = to_json(report_data)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"detail": json_serializable_data}
        )

    return router
