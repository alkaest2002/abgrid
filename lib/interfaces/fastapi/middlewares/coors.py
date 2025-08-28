"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
from itertools import product
from typing import Any, cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def add_cors_middleware(app: FastAPI) -> None:
    """Add CORS middleware to the FastAPI application.

    Configures Cross-Origin Resource Sharing (CORS) middleware to allow
    web applications from specified origins to access the API. This includes
    local development servers on various ports and production deployments.

    The middleware configuration provides:
    - Origin validation for local development (localhost/127.0.0.1)
    - Support for multiple development ports for flexibility
    - Production origin allowlist for deployed applications
    - Credential support for authenticated requests
    - Standard HTTP methods and headers for API operations

    Args:
        app (FastAPI): The FastAPI application instance to configure with CORS middleware.

    Returns:
        None.

    Notes:
        Local development origins are generated for both HTTP and HTTPS protocols
        across multiple ports to support various development setups.
        Production origins must be explicitly added to the allowlist.
    """
    # Define development ports for local testing
    fancy_ports: list[str] = ["53472", "53247", "53274", "53427", "53724", "53742"]

    # Define base domains for local development
    domains: list[str] = ["https://localhost", "https://127.0.0.1", "http://localhost", "http://127.0.0.1"]

    # Generate all combinations of domains and ports for development
    origins: list[str] = [f"{domain}:{port}" for domain, port in product(domains, fancy_ports)]

    # Add production origin
    origins.append("https://abgrid-webapp.onrender.com")

    # Configure CORS middleware with comprehensive settings
    app.add_middleware(
        cast("Any", CORSMiddleware),
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Content-Encoding",
            "Accept-Encoding",
        ],
        expose_headers=["Content-Encoding"],
    )
