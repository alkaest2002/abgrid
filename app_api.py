from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from lib.core.core_schemas import PydanticValidationException
from lib.interfaces.fastapi.router import get_router

app = FastAPI()
app.include_router(get_router())

@app.get("/public")
def public() -> JSONResponse:
    """
    Public endpoint that can be accessed without authentication.

    Returns:
        dict: A message indicating the endpoint is publicly accessible.
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"msg": "AB-Grid server is up and running"}
    )

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
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors}
    )