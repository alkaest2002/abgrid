"""
Simple anonymous JWT security for FastAPI.
"""
from typing import Optional, Any, Dict
from fastapi import Depends, HTTPException, status, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .jwt import AnonymousJWT


class UnauthenticatedException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Requires authentication"
        )

class Auth:
    """Simple JWT token verification for anonymous users."""

    def __init__(self) -> None:
        self.jwt_handler = AnonymousJWT()

    async def verify_token(
        self,
        response: Response,
        token: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
    ) -> Dict[str, Any]:
        """
        Verify JWT token and auto-refresh if needed.
        
        Args:
            response: FastAPI response object for setting new token header
            token: JWT token from Authorization header
            
        Returns:
            dict: Token payload with user_id
        """
        # If no token provided, generate a new one
        if not token:
            new_token = self.jwt_handler.generate_token()
            response.headers["X-New-Token"] = new_token
            
            # Return payload for new token
            return self.jwt_handler.verify_token(new_token)
        
        try:
            # Verify existing token
            payload = self.jwt_handler.verify_token(token.credentials)
            
            # Check if token should be refreshed
            if self.jwt_handler.should_refresh(token.credentials):
                new_token = self.jwt_handler.generate_token()
                response.headers["X-Refresh-Token"] = new_token
            
            return payload
            
        except HTTPException:
            # Token is invalid/expired, generate new one
            new_token = self.jwt_handler.generate_token()
            response.headers["X-New-Token"] = new_token
            
            return self.jwt_handler.verify_token(new_token)
