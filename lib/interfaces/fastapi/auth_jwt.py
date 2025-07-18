import jwt
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from fastapi import HTTPException, status
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    auth_secret: str = Field(..., env='AUTH_SECRET')
    token_lifetime_hours: int = Field(default=12, env='TOKEN_LIFETIME_HOURS')

    class Config:
        env_file = '.env'
        case_sensitive = False

    @classmethod
    @lru_cache()
    def load(cls):
        return cls()

class AnonymousJWT:
    """Simple JWT handler for anonymous user tracking."""

    def __init__(self, settings: Settings = Settings.load()) -> None:
        """
        Initializes an AnonymousJWT instance.

        Args:
            settings: An instance of Settings for configuration.
        """
        self.secret_key = settings.auth_secret
        self.algorithm = "HS256"
        self.token_lifetime = timedelta(hours=settings.token_lifetime_hours)

    def generate_token(self) -> str:
        """
        Generate a new anonymous JWT token with a unique identifier.

        Returns:
            A string representing the encoded JWT token containing a UUID as subject,
            issued at timestamp, and expiration time.
        """
        now = datetime.now(timezone.utc)
        expires = now + self.token_lifetime

        payload = {
            "sub": str(uuid.uuid4()),
            "iat": now,                
            "exp": expires 
        }
    
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)


    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT token.

        Args:
            token: The JWT token to verify.

        Returns:
            A dictionary containing the decoded token payload.

        Raises:
            HTTPException: If the token is expired or invalid.
        """
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid_or_expired_jwt_token"
            )
