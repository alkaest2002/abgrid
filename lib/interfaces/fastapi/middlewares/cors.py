"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
from itertools import product
from typing import Any, ClassVar

from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware


class CORSMiddleware(FastAPICORSMiddleware):
    """CORS middleware for closed API server origin validation.

    Attributes:
        development_ports: List of allowed development ports.
        local_domains: List of local development domains.
        production_origins: List of production origin URLs.
        allowed_methods: List of allowed HTTP methods.
        allowed_headers: List of allowed HTTP headers.
        exposed_headers: List of headers to expose to the client.
    """

    DEVELOPMENT_PORTS: ClassVar[list[str]] = ["53472", "53247", "53274", "53427", "53724", "53742"]
    LOCAL_DOMAINS: ClassVar[list[str]] = ["https://localhost", "https://127.0.0.1", "http://localhost", "http://127.0.0.1"]
    PRODUCTION_DOMAINS: ClassVar[list[str]] = ["https://abgrid-webapp.onrender.com"]
    ALLOWED_METHODS: ClassVar[list[str]] = ["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: ClassVar[list[str]] = ["Authorization", "Content-Type", "Content-Encoding", "Accept-Encoding"]
    EXPOSED_HEADERS: ClassVar[list[str]] = ["Content-Encoding"]

    @classmethod
    def _get_development_origins(cls) -> list[str]:
        """Generate all combinations of domains and ports for development.

        Returns:
            list[str]: List of development origin URLs.
        """
        return [
            f"{domain}:{port}"
            for domain, port in product(cls.LOCAL_DOMAINS, cls.DEVELOPMENT_PORTS)
        ]

    @classmethod
    def _get_all_origins(cls) -> list[str]:
        """Get all allowed origins including development and production.

        Returns:
            list[str]: Complete list of allowed origins.
        """
        # Start with development origins
        origins = cls._get_development_origins()
        # Add production domains
        origins.extend(cls.PRODUCTION_DOMAINS)

        return origins

    @classmethod
    def get_params(cls) -> dict[str, Any]:
        """Get parameters for CORS middleware configuration.

        Returns configuration parameters for Cross-Origin Resource Sharing (CORS)
        middleware to allow web applications from specified origins to access the API.
        This includes local development servers on various ports and production deployments.

        The configuration provides:
        - Origin validation for local development (localhost/127.0.0.1)
        - Support for multiple development ports for flexibility
        - Production origin allowlist for deployed applications
        - Credential support for authenticated requests
        - Standard HTTP methods and headers for API operations

        Returns:
            dict[str, Any]: Configuration dictionary with CORS parameters.

        Notes:
            Local development origins are generated for both HTTP and HTTPS protocols
            across multiple ports to support various development setups.
            Production origins must be explicitly added to the allowlist.
        """
        return {
            "allow_origins": cls._get_all_origins(),
            "allow_credentials": True,
            "allow_methods": cls.ALLOWED_METHODS,
            "allow_headers": cls.ALLOWED_HEADERS,
            "expose_headers": cls.EXPOSED_HEADERS,
        }
