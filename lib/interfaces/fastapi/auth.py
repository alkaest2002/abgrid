"""
Filename: auth.py

Description: Auth class to verify JWT tokens.

Author: Pierpaolo Calanna

Date Created: Jul 1, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from typing import Optional, Any, Dict
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .jwt import AnonymousJWT

class Auth:
    """Simple JWT token verification for anonymous users."""

    def __init__(self) -> None:
        """Initialize an Auth instance with an AnonymousJWT handler."""
        self.jwt_handler = AnonymousJWT()

    async def verify_token(
        self,
        token: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=True))
    ) -> Dict[str, Any]:
        """
        Verify JWT token and auto-refresh if needed.
        
        Args:
            token: JWT token from Authorization header, automatically handled by FastAPI.
            
        Returns:
            A dictionary containing the token payload with user_id.

        Raises:
            HTTPException: If the token is invalid or expired (HTTP 401).
        """
        return self.jwt_handler.verify_token(token.credentials)