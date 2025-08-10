"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
# ruff: noqa: B008

from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .jwt import AnonymousJWT


class Auth:
    """Simple JWT token verification for anonymous users."""

    def __init__(self) -> None:
        """Initialize an Auth instance with an AnonymousJWT handler."""
        self.jwt_handler = AnonymousJWT()

    async def verify_token(
        self,
        token: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False))
    ) -> dict[str, Any]:
        """"Verify JWT token.

        Args:
            token: JWT token from Authorization header, automatically handled by FastAPI.

        Returns:
            A dictionary containing the decoded token payload.

        Raises:
            HTTPException: If the token is invalid or expired (HTTP 401).
        """
        if token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="required_jwt_token"
            )
        return self.jwt_handler.verify_token(token.credentials)
