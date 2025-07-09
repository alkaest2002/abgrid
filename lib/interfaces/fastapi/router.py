from typing import Any, Dict, Literal
from fastapi import APIRouter, HTTPException, Query, Depends, status, Request
from fastapi.responses import JSONResponse

from .auth import Auth
from .limiter import SimpleRateLimiter
from lib.core.core_data import CoreData
from lib.core.core_schemas import ABGridGroupSchema, ABGridReportSchema
from lib.core.core_templates import CoreRenderer
from lib.utils import to_json

def get_router() -> APIRouter:
    """
    Create and configure the FastAPI router.
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
    ) -> JSONResponse:
        """
        Generate group configuration file.
        """
        # Get report data
        group_data = abgrid_data.get_group_data(model)

        # Render the template with group-specific data
        try:
            template_path = f"/{language}/group.html"
            rendered_group = abgrid_renderer.render_html(template_path, group_data)
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to render template: {str(e)}"
            )
        
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

    @router.post("/report")
    @SimpleRateLimiter(limit=1, window_seconds=15)
    async def get_report(
        request: Request,
        model: ABGridReportSchema, 
        language: str = Query(..., description="Language of the report"),
        with_sociogram: bool = Query(..., description="Include sociogram"),
        user_data: Dict[str, Any] = Depends(auth.verify_token)
    ) -> JSONResponse:
        """
        Generate a report.
        """
        try:
            # Get report data
            report_data = abgrid_data.get_report_data(model, with_sociogram)

            # Render report
            template_path = f"./{language}/report.html"
            rendered_report = abgrid_renderer.render_html(template_path, report_data)

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "detail": {
                        "report_html": rendered_report,
                        "report_json": to_json(report_data)
                    }
                }
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    return router
