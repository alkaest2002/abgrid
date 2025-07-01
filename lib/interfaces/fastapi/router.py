
from typing import Literal
from xmlrpc.client import Boolean

from fastapi import APIRouter, HTTPException, Query, Security, status
from fastapi.responses import HTMLResponse, JSONResponse

from .security import VerifyToken
from lib.core.core_data import CoreData
from lib.core.core_schemas import ABGridSchema
from lib.core.core_templates import CoreRenderer
from lib.utils import to_json

def get_router() -> APIRouter:
    """
    Create and configure a FastAPI router instance.

    Returns:
        FastAPI: Configured FastAPI router instance.
    """

    # Init router
    router = APIRouter(prefix="/api")

    # Init auth
    auth = VerifyToken()
    
    # Init abgrid data
    abgrid_data = CoreData()

    # Init abgrid renderer
    abgrid_renderer = CoreRenderer()

    @router.post("/report")
    def get_report(
        model: ABGridSchema, 
        language: str = Query(..., description="Language of the report"),
        type_of_report: Literal['html', 'json'] = Query(..., description="The type of report desired"),
        with_sociogram: Boolean = Query(..., description="Include sociogram"),
        _: dict = Security(auth.verify)
    ):
        """
        Endpoint to retrieve report based on a validated ABGridSchema model and specified type and language.

        Args:
            model (ABGridSchema): Parsed and validated instance of ABGridSchema from the request body.
            language (str): Language of the report.
            type_of_report (str): Type of the report, either 'html' or 'json'.
            with_sociogram: (bool) include sociogram
            token (str): Authorization token obtained via HTTPBearer.
        
        Returns:
            HTMLResponse or JSONResponse: The report data in the specified format.
        
        Raises:
            FileNotFoundError if the requested html template is not found
            HTTPException: If a validation or unexpected error occurs during processing.
        """
        try:
            # Get report data
            report_data = abgrid_data.get_report_data(model, with_sociogram)

            # User requested html report
            if type_of_report == "html":
                return _generate_html_report(language, report_data)

            # User requested report json data
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
        """
        Generate HTML report from the report data.

        Args:
            language (str): Language of the report.
            report_data (dict): The report data to render.
        
        Returns:
            HTMLResponse: An HTML response containing the rendered report.
        """
        report_template = f"./{language}/report.html"
        rendered_report = abgrid_renderer.render_html(report_template, report_data)
        return HTMLResponse(
            status_code=status.HTTP_200_OK,
            content=rendered_report
        )

    def _generate_json_report(report_data: dict) -> JSONResponse:
        """
        Generate JSON report from the report data.

        Args:
            report_data (dict): The report data to convert.
        
        Returns:
            JSONResponse: A JSON response containing the report data.
        """
        json_serializable_data = to_json(report_data)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=json_serializable_data
        )

    return router
