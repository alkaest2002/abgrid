"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from ..security.auth import Auth

from fastapi import status

_auth = Auth()

def get_router_auth() -> APIRouter:
    
    router = APIRouter(prefix="/auth")

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

    return router