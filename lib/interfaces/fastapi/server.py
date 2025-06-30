from fastapi import Depends, FastAPI, HTTPException, Request, Query, Security
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer
from typing import Literal

from lib.core.core_data import CoreData
from lib.core.core_schemas import ABGridSchema, PydanticValidationException
from lib.core.core_templates import CoreRenderer
from .utils import VerifyToken
from lib.utils import to_json

def get_server() -> FastAPI:
    """
    Create and configure a FastAPI server instance.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """

    # Init Fastapi
    app = FastAPI()

    # Init auth
    auth = VerifyToken()
    
    # Instantiate CoreData
    core_data = CoreData()

    # Initialize core renderer
    renderer = CoreRenderer()

    @app.exception_handler(PydanticValidationException)
    async def custom_pydantic_validation_exception_handler(
        request: Request, exc: PydanticValidationException
    ) -> JSONResponse:
        """
        Custom exception handler for PydanticValidationException.

        Args:
            request (Request): The request that resulted in the exception.
            exc (PydanticValidationException): The exception instance.
        
        Returns:
            JSONResponse: A JSON response with status code 422 and error details.
        """
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors}
        )

    @app.get("/api/public")
    def public() -> dict:
        """
        Public endpoint that can be accessed without authentication.

        Returns:
            dict: A message indicating the endpoint is publicly accessible.
        """
        result = {
            "status": "success",
            "msg": ("Hello from a public endpoint! You don't need to be "
                    "authenticated to see this.")
        }
        return result

    @app.post("/api/report")
    def get_report(
        model: ABGridSchema, 
        language: str = Query(..., description="Language of the report"),
        type_of_report: Literal['html', 'json'] = Query(..., description="The type of report desired"),
        auth_result: str = Security(auth.verify)
    ):
        """
        Endpoint to retrieve report data based on a validated ABGridSchema model and specified type and language.

        Args:
            model (ABGridSchema): Parsed and validated instance of ABGridSchema from the request body.
            language (str): Language of the report.
            type_of_report (str): Type of the report, either 'html' or 'json'.
            token (str): Authorization token obtained via HTTPBearer.
        
        Returns:
            HTMLResponse or JSONResponse: The report data in the specified format.
        
        Raises:
            HTTPException: If a validation or unexpected error occurs during processing.
        """
        try:
            # Get Report data
            report_data = core_data.get_report_data(model, True)

            if type_of_report == 'html':
                return _generate_html_report(language, report_data)

            elif type_of_report == 'json':
                return _generate_json_report(report_data)

        except Exception as e:
            # General exceptions catch-all
            raise HTTPException(status_code=500, detail=str(e))

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
        rendered_report = renderer.render_html(report_template, report_data)
        return HTMLResponse(content=rendered_report)

    def _generate_json_report(report_data: dict) -> JSONResponse:
        """
        Generate JSON report from the report data.

        Args:
            report_data (dict): The report data to convert.
        
        Returns:
            JSONResponse: A JSON response containing the report data.
        """
        json_serializable_data = to_json(report_data)
        return JSONResponse(content=json_serializable_data)

    return app
