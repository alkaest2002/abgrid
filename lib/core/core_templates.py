"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
from typing import Any

from jinja2 import (
    Environment,
    FileSystemBytecodeCache,
    FileSystemLoader,
    StrictUndefined,
    select_autoescape,
)
from jinja2.exceptions import (
    TemplateNotFound,
    TemplateRuntimeError,
    TemplateSyntaxError,
    UndefinedError,
)


# Define cache directory
TEMPLATE_CACHE_DIR = "./lib/core/templates/.cache"

# Initialize Jinja2 environment with a file system loader for templates
try:
    abgrid_jinja_env = Environment(
        loader=FileSystemLoader(["./lib/core/templates"]),
        # Enable strict undefined handling to catch missing variables
        undefined=StrictUndefined,
        # Auto-escape HTML for security
        autoescape=select_autoescape(["html", "xml"]),
        # Add bytecode cache for performance
        bytecode_cache=FileSystemBytecodeCache(TEMPLATE_CACHE_DIR)
    )

except Exception as e:
    error_message = f"Failed to initialize Jinja2 environment: {e}"
    raise RuntimeError(error_message) from e


class TemplateRenderError(Exception):
    """Custom exception for template rendering errors."""


class CoreRenderer:
    """Renders jinja templates."""

    def render(self, template_path_str: str, template_data: dict[str, Any]) -> str:
        """Render Jinja2 template with provided template_data.

        Args:
            template_path_str: Path (as string) to the Jinja2 template file
            template_data: Template context data

        Returns:
            Rendered template

        Raises:
            FileNotFoundError: If template file is not found
            TemplateRenderError: If template rendering fails due to syntax or runtime errors
            ValueError: If input parameters are invalid
        """
        # Ensure template_path
        if not template_path_str:
            error_message = "Template path cannot be empty or None."
            raise ValueError(error_message)

        # Ensure template_data
        if not isinstance(template_data, dict):
            error_message = "Template data must be a dictionary."
            raise TypeError(error_message)

        try:
            # Try to load template
            template = abgrid_jinja_env.get_template(template_path_str)

        except TemplateNotFound as e:
            error_message = f"Template file not found: {template_path_str}"
            raise FileNotFoundError(error_message) from e

        except Exception as e:
            error_message = f"Unexpected error loading template {template_path_str}: {e}."
            raise TemplateRenderError(error_message) from e

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
