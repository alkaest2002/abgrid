"""
Filename: settings.py

Description: FastApi router with strict JWT authentication (except /token endpoint)

Author: Pierpaolo Calanna

Date Created: Jul 1, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Depends, status, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse

from .security import Auth
from .limiter import SimpleRateLimiter
from lib.core.core_data import CoreData
from lib.core.core_schemas import ABGridSchema
from lib.core.core_templates import CoreRenderer
from lib.utils import to_json


def get_router() -> APIRouter:
    router = APIRouter(prefix="/api")
    
    # Init components
    auth = Auth()
    abgrid_data = CoreData()
    abgrid_renderer = CoreRenderer()

    # Token generation endpoint - NO AUTH REQUIRED
    @router.get("/token")
    async def get_token():
        """Get a new anonymous JWT token. This is the ONLY endpoint that doesn't require auth."""
        new_token = auth.jwt_handler.generate_token()
        return {"token": new_token}

    # Protected endpoint - AUTH REQUIRED
    @router.post("/report")
    @SimpleRateLimiter(limit=1, window_seconds=5)       # Burst protection
    @SimpleRateLimiter(limit=100, window_seconds=3600)  # Hourly limit
    async def get_report(
        request: Request,
        response: Response, 
        model: ABGridSchema, 
        language: str = Query(..., description="Language of the report"),
        type_of_report: Literal['html', 'json'] = Query(..., description="The type of report desired"),
        with_sociogram: bool = Query(..., description="Include sociogram"),
        user_data: dict = Depends(auth.verify_token)  # JWT TOKEN REQUIRED
    ):
        """Generate report with anonymous JWT authentication. JWT token is REQUIRED."""
        try:
            # Get report data
            report_data = abgrid_data.get_report_data(model, with_sociogram)

            if type_of_report == "html":
                return _generate_html_report(language, report_data)
            elif type_of_report == "json":
                return _generate_json_report(report_data)

        except FileNotFoundError as e:
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Language {language} is not available"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=str(e)
            )

    def _generate_html_report(language: str, report_data: dict) -> HTMLResponse:
        report_template = f"./{language}/report.html"
        rendered_report = abgrid_renderer.render_html(report_template, report_data)
        return HTMLResponse(
            status_code=status.HTTP_200_OK,
            content=rendered_report
        )

    def _generate_json_report(report_data: dict) -> JSONResponse:
        json_serializable_data = to_json(report_data)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_serializable_data
        )

    return router
