"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings configuration using Pydantic BaseSettings.

    This class manages application configuration by loading settings from
    environment variables and .env files. It provides type validation,
    default values, and caching for optimal performance.

    The settings are automatically loaded from:
    1. Environment variables (highest priority)
    2. .env file in the project root
    3. Default values defined in the class

    Attributes:
        auth_secret: Secret key used for authentication jwt token generation and validation.
        fastapi_max_concurrent_requests: Maximum number of concurrent requests allowed
        fastapi_response_compression_enabled: Enable or disable response compression middleware
        fastapi_body_inspect_enabled: Enable or disable request body inspection middleware
        aws_function_url: AWS Lambda Function URL

    Notes:
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

    fastapi_is_development: bool = Field(
        default=False,
        description="Enable or disable development mode",
        validation_alias="FASTAPI_IS_DEVELOPMENT"
    )

    fastapi_max_concurrent_requests: int = Field(
        default=5,
        description="Maximum number of concurrent requests allowed for /api endpoints",
        validation_alias="FASTAPI_MAX_CONCURRENT_REQUESTS",
        ge=1,  # Must allow at least 1 request
        le=1000  # Reasonable upper limit
    )

    fastapi_response_compression_enabled: bool = Field(
        default=False,
        description="Enable or disable response compression",
        validation_alias="FASTAPI_RESPONSE_COMPRESSION_ENABLED"
    )

    fastapi_body_inspect_enabled: bool = Field(
        default=False,
        description="Enable or disable request body inspection middleware",
        validation_alias="FASTAPI_BODY_INSPECT_ENABLED"
    )

    aws_function_url: str | None = Field(
        default=None,
        description="AWS Lambda Function URL for serverless deployment",
        validation_alias="AWS_FUNCTION_URL"
    )

    aws_api_key: str | None = Field(
        default=None,
        description="API Key for AWS Lambda Function URL if required",
        validation_alias="AWS_API_KEY"
    )

    @classmethod
    @lru_cache
    def load(cls) -> "Settings":
        """Load and cache application settings.

        This method creates and returns a Settings instance, loading configuration
        from environment variables and .env file. The result is cached using
        @lru_cache() to ensure the same instance is returned on subsequent calls,
        improving performance and ensuring consistency.

        Returns:
            Settings: A configured Settings instance with all values loaded and validated.

        Raises:
            - ValidationError: If required settings are missing or invalid.
            - FileNotFoundError: If .env file is specified but not found (non-fatal).

        Notes:
            The @lru_cache() decorator ensures this method returns the same instance
            across multiple calls, making it safe to call Settings.load() anywhere
            in the application without performance concerns.
        """
        return cls()
