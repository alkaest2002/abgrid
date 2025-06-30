from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from lib.core.core_data import CoreData
from lib.core.core_schemas import ABGridSchema, PydanticValidationException
from lib.core.core_templates import CoreRenderer


def get_server():

    app = FastAPI()

    # Instantiate CoreData
    core_data = CoreData()

    # Initialize core renderer
    renderer = CoreRenderer()

    @app.exception_handler(PydanticValidationException)
    async def custom_pydantic_validation_exception_handler(request: Request, exc: PydanticValidationException) -> JSONResponse:
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

    @app.post("/report_data")
    def report_data(model: ABGridSchema) -> HTMLResponse:
        """
        Endpoint to retrieve and render report data based on a validated ABGridSchema model.

        Args:
            model (ABGridSchema): Parsed and validated instance of ABGridSchema from request body.
        
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
            print(rendered_report)
            return HTMLResponse(content=rendered_report)
            
        except Exception as e:
            # General exceptions catch-all
            raise HTTPException(status_code=500, detail=str(e))

    return app