"""
CORS Middleware Configuration

Author: Pierpaolo Calanna
The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from itertools import product
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


def add_cors_middleware(app: FastAPI) -> None:
    """
    Add CORS middleware to the FastAPI application.
    
    Args:
        app (FastAPI): The FastAPI application instance
    """
    # List of ports
    fancy_ports = ["53472", "53247", "53274", "53427", "53724", "53742"]

    # Define domains that should be allowed to access your server
    domains = ["https://localhost", "https://127.0.0.1", "http://localhost", "http://127.0.0.1"]

    # Define origins that should be allowed to access your server
    origins = [f"{domain}:{port}" for domain, port in product(domains, fancy_ports)]

    # Add render webapp origin
    origins.append("https://abgrid-webapp.onrender.com")

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
