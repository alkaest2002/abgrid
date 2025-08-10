"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings configuration using Pydantic BaseSettings.

    This class manages application configuration by loading settings from
    environment variables and .env files. It provides type validation,
    default values, and caching for optimal performance.

    The settings are automatically loaded from:
    1. Environment variables (highest priority)
    2. .env file in the project root
    3. Default values defined in the class

    Attributes:
        auth_secret: Secret key used for authentication token generation and validation.
                    This is a required field that must be provided via AUTH_SECRET
                    environment variable.
        max_concurrent_requests_for_group: Maximum number of concurrent requests allowed
                                         for /api/group endpoint. Defaults to 15.
        max_concurrent_requests_for_report: Maximum number of concurrent requests allowed
                                          for /api/report endpoint. Defaults to 5.

    Environment Variables:
        AUTH_SECRET: Required secret key for authentication
        MAX_CONCURRENT_REQUESTS_FOR_GROUP: Optional concurrent request limit for group endpoint (default: 15)
        MAX_CONCURRENT_REQUESTS_FOR_REPORT: Optional concurrent request limit for report endpoints (default: 5)

    Note:
        Settings are cached using @lru_cache() for performance. The same instance
        is returned on subsequent calls to load().
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="allow"
    )

    auth_secret: str = Field(
        default=...,
        description="Secret key for authentication token generation and validation",
        validation_alias="AUTH_SECRET"
    )

    max_concurrent_requests_for_group: int = Field(
        default=15,
        description="Maximum number of concurrent requests allowed for /api/group endpoint",
        validation_alias="MAX_CONCURRENT_REQUESTS_FOR_GROUP",
        ge=1,  # Must allow at least 1 request
        le=1000  # Reasonable upper limit
    )

    max_concurrent_requests_for_report: int = Field(
        default=5,
        description="Maximum number of concurrent requests allowed for /api/report endpoint",
        validation_alias="MAX_CONCURRENT_REQUESTS_FOR_REPORT",
        ge=1,  # Must allow at least 1 request
        le=1000  # Reasonable upper limit
    )

    @classmethod
    @lru_cache
    def load(cls) -> "Settings":
        """
        Load and cache application settings.

        This method creates and returns a Settings instance, loading configuration
        from environment variables and .env file. The result is cached using
        @lru_cache() to ensure the same instance is returned on subsequent calls,
        improving performance and ensuring consistency.

        Returns:
            Settings: A configured Settings instance with all values loaded and validated

        Raises:
            ValidationError: If required settings are missing or invalid
            FileNotFoundError: If .env file is specified but not found (non-fatal)

        Note:
            The @lru_cache() decorator ensures this method returns the same instance
            across multiple calls, making it safe to call Settings.load() anywhere
            in the application without performance concerns.
        """
        return cls()  # type: ignore[call-arg]
