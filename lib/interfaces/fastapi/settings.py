"""
Filename: settings.py

Description: Application configuration management using Pydantic Settings for Auth0 authentication and environment variable handling.

Author: Pierpaolo Calanna

Date Created: Jul 1, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    A class that holds the application's configuration settings.

    Attributes:
        auth0_domain (str): The domain for Auth0 configuration.
        auth0_api_audience (str): The API audience for Auth0.
        auth0_issuer (str): The issuer identifier for Auth0.
        auth0_algorithms (str): The algorithms used for Auth0.
    """
    auth0_domain: str
    auth0_api_audience: str
    auth0_issuer: str
    auth0_algorithms: str = "RS256"

    class Config:
        """Configuration for the Settings class."""
        env_file = "./lib/interfaces/fastapi/.env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get the application settings using caching to avoid reloading.

    Returns:
        Settings: The application settings instance.
        
    Raises:
        ValidationError: If required environment variables are missing.
    """
    try:
        return Settings()
    except Exception as e:
        print(f"Error loading settings: {e}")
        print("Please ensure you have a .env file with the required Auth0 configuration.")
        raise
