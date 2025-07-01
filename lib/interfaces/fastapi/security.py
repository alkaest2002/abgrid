"""
Filename: security.py

Description: JWT token verification and authentication handling for Auth0 integration with FastAPI security middleware.

Author: Pierpaolo Calanna

Date Created: Jul 1, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
import jwt
from typing import Optional, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import SecurityScopes, HTTPAuthorizationCredentials, HTTPBearer

from .settings import get_settings


class UnauthorizedException(HTTPException):
    """Exception for unauthorized access, results in HTTP 403 error."""
    
    def __init__(self, detail: str, **kwargs: Any) -> None:
        """Initialize with detail message and optional keyword arguments."""
        super().__init__(status.HTTP_403_FORBIDDEN, detail=detail)


class UnauthenticatedException(HTTPException):
    """Exception for unauthenticated access, results in HTTP 401 error."""
    
    def __init__(self) -> None:
        """Initialize with a predefined detail message for unauthenticated access."""
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Requires authentication"
        )

class VerifyToken:
    """Handles token verification using PyJWT."""

    def __init__(self) -> None:
        """Initialize the verifier with configuration settings and JWKS client."""
        self.config = get_settings()

        # Get the JWKS URL to handle key verification
        jwks_url = f'https://{self.config.auth0_domain}/.well-known/jwks.json'
        self.jwks_client = jwt.PyJWKClient(jwks_url)

    async def verify(
        self,
        security_scopes: SecurityScopes,
        token: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer())
    ) -> dict:
        """
        Verify the provided JWT token against the JWKS.

        Args:
            security_scopes (SecurityScopes): Required security scopes for the operation.
            token (Optional[HTTPAuthorizationCredentials]): JWT token for authentication, defaults to using HTTPBearer.

        Returns:
            dict: Decoded JWT payload if verification is successful.

        Raises:
            UnauthenticatedException: If no token is provided.
            UnauthorizedException: If there's an error in token decoding or the token does not match required claims.
        """
        if token is None:
            raise UnauthenticatedException

        try:
            # Retrieve the signing key from the JWKS using the token's key ID
            signing_key = self.jwks_client.get_signing_key_from_jwt(token.credentials).key
        except jwt.exceptions.PyJWKClientError as error:
            raise UnauthorizedException(str(error))
        except jwt.exceptions.DecodeError as error:
            raise UnauthorizedException(str(error))

        try:
            # Decode and validate the token
            payload = jwt.decode(
                token.credentials,
                signing_key,
                algorithms=self.config.auth0_algorithms,
                audience=self.config.auth0_api_audience,
                issuer=self.config.auth0_issuer,
            )
        except Exception as error:
            raise UnauthorizedException(str(error))

        # Check for required scopes in the token claims
        if len(security_scopes.scopes) > 0:
            self._check_claims(payload, 'scope', security_scopes.scopes)

        return payload

    def _check_claims(self, payload: dict, claim_name: str, expected_value: list) -> None:
        """
        Check if the expected claims are present in the token payload.

        Args:
            payload (dict): The JWT payload.
            claim_name (str): The name of the claim to check.
            expected_value (list): List of expected values for the claim.

        Raises:
            UnauthorizedException: If the claim is missing or does not contain the expected values.
        """
        if claim_name not in payload:
            raise UnauthorizedException(detail=f'No claim "{claim_name}" found in token')

        payload_claim = payload[claim_name]

        if claim_name == 'scope':
            payload_claim = payload[claim_name].split(' ')

        for value in expected_value:
            if value not in payload_claim:
                raise UnauthorizedException(detail=f'Missing "{claim_name}" scope')
