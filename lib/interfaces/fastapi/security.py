"""
Filename: security.py

Description: Auth class to verify JWT tokens.

Author: Pierpaolo Calanna

Date Created: Jul 1, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from typing import Optional, Any, Dict
from fastapi import Depends, HTTPException, status, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .jwt import AnonymousJWT

class UnauthenticatedException(HTTPException):
    """
    Exception raised when a JWT token is required but not provided.
    """
    def __init__(self) -> None:
        """Initialize an UnauthenticatedException with a 401 status code."""
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="JWT token required"
        )

class Auth:
    """Simple JWT token verification for anonymous users."""

    def __init__(self) -> None:
        """Initialize an Auth instance with an AnonymousJWT handler."""
        self.jwt_handler = AnonymousJWT()

    async def verify_token(
        self,
        response: Response,
        token: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=True))
    ) -> Dict[str, Any]:
        """
        Verify JWT token and auto-refresh if needed.
        
        Args:
            response: FastAPI response object for setting the new token header.
            token: JWT token from Authorization header (REQUIRED).
            
        Returns:
            A dictionary containing the token payload with user_id.
            
        Raises:
            UnauthenticatedException: If no token is provided.
        """
        # HTTPBearer with auto_error=True will automatically raise 401 if no token
        if not token:
            raise UnauthenticatedException()
        
        try:
            # Verify the existing token
            payload = self.jwt_handler.verify_token(token.credentials)
            
            # Check if the token should be refreshed
            if self.jwt_handler.should_refresh(token.credentials):
                new_token = self.jwt_handler.generate_token()
                response.headers["X-Refresh-Token"] = new_token
            
            return payload
            
        except HTTPException:
            # Token is invalid/expired - don't generate a new one, just fail
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
