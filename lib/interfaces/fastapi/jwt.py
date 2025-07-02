import jwt
import uuid
import time
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
        env_file = './lib/interfaces/fastapi/.env'
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
        Generate a new anonymous JWT token with UUID.

        Returns:
            A string representing the encoded JWT token.
        """
        now = datetime.now(timezone.utc)
        expires = now + self.token_lifetime

        payload = {
            "user_id": str(uuid.uuid4()),
            "issued_at": int(now.timestamp()),
            "expires_at": int(expires.timestamp())
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
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("expires_at", 0) < int(time.time()):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="JWT token expired"
                )
            return payload
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid JWT token"
            )

    def should_refresh(self, token: str) -> bool:
        """
        Check if a token should be refreshed (when 75% of lifetime has passed).

        Args:
            token: The JWT token to check.

        Returns:
            True if the token should be refreshed, False otherwise.
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            issued_at = payload.get("issued_at", 0)
            expires_at = payload.get("expires_at", 0)

            lifetime_seconds = expires_at - issued_at
            refresh_threshold = issued_at + (lifetime_seconds * 0.75)

            return int(time.time()) > refresh_threshold
        
        # Invalid token should be refreshed
        except jwt.InvalidTokenError:
            return True  
