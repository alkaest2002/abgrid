"""
Filename: jwt.py

Description: Simple anonymous JWT token system for tracking and rate limiting.

Author: Pierpaolo Calanna

Date Created: Jul 1, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import os
import jwt
import uuid
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from fastapi import HTTPException, status
from dotenv import load_dotenv

load_dotenv() 

class AnonymousJWT:
    """Simple JWT handler for anonymous user tracking."""

    def __init__(self, secret_key: str = os.getenv("AUTH_SECRET"), token_lifetime_hours: int = 12) -> None:
        """
        Initializes an AnonymousJWT instance.

        Args:
            secret_key: The secret key for signing JWTs.
            token_lifetime_hours: The lifetime of a token in hours.
        """
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.token_lifetime = timedelta(hours=token_lifetime_hours)
    
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
            
            # Check if token is expired
            if payload.get("expires_at", 0) < int(time.time()):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )
            
            return payload
        
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
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
            
            # Calculate 75% of token lifetime
            lifetime_seconds = expires_at - issued_at
            refresh_threshold = issued_at + (lifetime_seconds * 0.75)
            
            return int(time.time()) > refresh_threshold
        
        except jwt.InvalidTokenError:
            return True  # Invalid token should be refreshed
