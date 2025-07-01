"""
Filename: core_templates.py

Description: Provides functionality to render SNA/Sociogram data via templates.

Author: Pierpaolo Calanna

Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
import os
from pathlib import Path
from typing import Any, Dict
from jinja2 import Environment, FileSystemLoader, StrictUndefined, FileSystemBytecodeCache, select_autoescape
from jinja2.exceptions import TemplateNotFound, TemplateSyntaxError, TemplateRuntimeError, UndefinedError

# Define cache directory
TEMPLATE_CACHE_DIR = Path("./lib/core/templates/.cache")

# Initialize Jinja2 environment with a file system loader for templates
try:
    abgrid_jinja_env = Environment(
        loader=FileSystemLoader(["./lib/core/templates"]),
        # Enable strict undefined handling to catch missing variables
        undefined=StrictUndefined,
        # Auto-escape HTML for security
        autoescape=select_autoescape(['html', 'xml']),
        # Add bytecode cache for performance
        bytecode_cache=FileSystemBytecodeCache(TEMPLATE_CACHE_DIR)
    )

except Exception as e:
    raise RuntimeError(f"Failed to initialize Jinja2 environment: {e}")


class TemplateRenderError(Exception):
    """Custom exception for template rendering errors."""
    pass


class CoreRenderer:
    """Renders templates to PDF documents using Jinja2 and WeasyPrint."""

    def render_html(self, template_path: Path, template_data: Dict[str, Any]) -> str:
        """Render Jinja2 template with provided template_data.
        
        Args:
            template_path: Path to the Jinja2 template file
            template_data: Template context data
            
        Returns:
            Rendered HTML string
            
        Raises:
            FileNotFoundError: If template file is not found
            TemplateRenderError: If template rendering fails due to syntax or runtime errors
            ValueError: If input parameters are invalid
        """
        # Ensure template_path
        if not template_path:
            raise ValueError("Template path cannot be empty or None.")
        
        # Ensure template_data
        if not isinstance(template_data, dict):
            raise ValueError("Template data must be a dictionary.")
        
        # Convert Path object to string for Jinja2
        template_path_str = str(template_path)
        
        try:
            # Try to load template
            template = abgrid_jinja_env.get_template(template_path_str)
            
        except TemplateNotFound as e:
            raise FileNotFoundError(f"Template file not found: {template_path_str}") from e
            
        except Exception as e:
            raise TemplateRenderError( f"Unexpected error loading template {template_path_str}: {e}.") from e
        
        try:
            
            # Try to render template with template data
            return template.render(template_data)
            
        except TemplateSyntaxError as e:
            error_msg = f"Template syntax error in {template_path_str}: {e.message} at line {e.lineno}."
            raise TemplateRenderError(error_msg) from e
            
        except TemplateRuntimeError as e:
            error_msg = f"Template runtime error in {template_path_str}: {e.message}."
            raise TemplateRenderError(error_msg) from e
            
        except UndefinedError as e:
            error_msg = f"Undefined variable in template {template_path_str}: {e.message}."
            raise TemplateRenderError(error_msg) from e
            
        except Exception as e:
            error_msg = f"Unexpected error rendering template {template_path_str}: {e}."
            raise TemplateRenderError(error_msg) from e
