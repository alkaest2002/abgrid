from fastapi.security import HTTPBearer
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from lib.core.core_data import CoreData
from lib.core.core_schemas import ABGridSchema, PydanticValidationException
from lib.core.core_templates import CoreRenderer
from lib.utils import to_json

def get_server() -> FastAPI:
    """
    Create and configure a FastAPI server instance.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    # Scheme for the Authorization header
    token_auth_scheme = HTTPBearer()

    app = FastAPI()

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

    @app.post("/api/report_html")
    def get_report_as_html(
        model: ABGridSchema, token: str = Depends(token_auth_scheme)
    ) -> HTMLResponse:
        """
        Endpoint to retrieve and render report data based on a validated ABGridSchema model.

        Args:
            model (ABGridSchema): Parsed and validated instance of ABGridSchema from the request body.
            token (str): Authorization token obtained via HTTPBearer.
        
        Returns:
            HTMLResponse: An HTML response containing the rendered report data.
        
        Raises:
            HTTPException: If a validation or unexpected error occurs during processing.
        """
        try:
            # Get Report data
            report_data = core_data.get_report_data(model, True)
            
            # Render report HTML template with report data
            rendered_report = renderer.render_html("./it/report.html", report_data)
            
            # Return HTML fragment
            return HTMLResponse(content=rendered_report)
            
        except Exception as e:
            # General exceptions catch-all
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/report_json")
    def get_report_as_json(
        model: ABGridSchema, token: str = Depends(token_auth_scheme)
    ) -> JSONResponse:
        """
        Endpoint to retrieve report data as JSON based on a validated ABGridSchema model.

        Args:
            model (ABGridSchema): Parsed and validated instance of ABGridSchema from request body.
            token (str): Authorization token obtained via HTTPBearer.
        
        Returns:
            JSONResponse: A JSON response containing the complete report data in serializable format.
            
        Raises:
            HTTPException: If a validation or unexpected error occurs during processing.
        """
        try:
            # Get Report data with sociogram analysis
            report_data = core_data.get_report_data(model, True)
            
            # Convert to JSON-serializable format
            json_serializable_data = to_json(report_data)
            
            # Return JSON response
            return JSONResponse(content=json_serializable_data)
            
        except Exception as e:
            # General exceptions catch-all
            raise HTTPException(status_code=500, detail=str(e))

    return app
