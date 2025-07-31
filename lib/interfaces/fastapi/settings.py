"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings


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
        token_lifetime_hours: Duration in hours for authentication token validity.
                            Defaults to 12 hours if not specified.
        max_concurrent_requests: Maximum number of concurrent requests allowed by
                               the request protection middleware. Defaults to 10.
                               
    Environment Variables:
        AUTH_SECRET: Required secret key for authentication
        TOKEN_LIFETIME_HOURS: Optional token lifetime in hours (default: 12)
        MAX_CONCURRENT_REQUESTS: Optional concurrent request limit (default: 10)
        
    Note:
        Settings are cached using @lru_cache() for performance. The same instance
        is returned on subsequent calls to load().
    """
    
    auth_secret: str = Field(
        ..., 
        env='AUTH_SECRET',
        description="Secret key for authentication token generation and validation"
    )
    
    token_lifetime_hours: int = Field(
        default=12, 
        env='TOKEN_LIFETIME_HOURS',
        description="Authentication token lifetime in hours",
        ge=1,  # Must be at least 1 hour
        le=168  # Maximum 1 week (168 hours)
    )
    
    max_concurrent_requests: int = Field(
        default=10, 
        env='MAX_CONCURRENT_REQUESTS',
        description="Maximum number of concurrent requests allowed",
        ge=1,  # Must allow at least 1 request
        le=1000  # Reasonable upper limit
    )

    class Config:
        """
        Pydantic configuration for settings loading behavior.
        
        Attributes:
            env_file: Path to the environment file to load (.env)
            case_sensitive: Whether environment variable names are case sensitive
        """
        env_file = '.env'
        case_sensitive = False

    @classmethod
    @lru_cache()
    def load(cls) -> 'Settings':
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
        return cls()
