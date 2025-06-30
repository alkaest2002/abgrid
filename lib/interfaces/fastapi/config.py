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
    auth0_algorithms: str

    class Config:
        """Configuration for the Settings class."""
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """
    Get the application settings using caching to avoid reloading.

    Returns:
        Settings: The application settings instance.
    """
    return Settings()
