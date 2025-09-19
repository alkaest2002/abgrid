"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
from typing import Any

from jinja2 import (
    Environment,
    FileSystemBytecodeCache,
    PackageLoader,
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

def universal_iter_rows(data: Any) -> Any:
    """Universal iterator filter that works with both DataFrames and Python objects.

    Returns an iterator of (key, value) tuples:
    - For DataFrames: uses iterrows() -> (index, Series)
    - For dicts: uses items() -> (key, value)
    - For lists/tuples: uses enumerate() -> (index, item)
    - For other iterables: uses enumerate() -> (index, item)
    - For single values: wraps in list as [(0, value)]

    Args:
        data: Input data to iterate over.

    Returns:
        Iterator of (key, value) tuples.
    """
   # Pandas DataFrame
    if hasattr(data, "iterrows"):
        try:
            return data.iterrows()
        except AttributeError:
            pass

    # Dictionary
    if isinstance(data, dict):
        return data.items()

    # List or tuple
    if isinstance(data, list | tuple):
        return enumerate(data)

    # Other iterables (sets, generators, etc.)
    if hasattr(data, "__iter__") and not isinstance(data, str | bytes):
        return enumerate(data)

    # Single value - wrap in list
    return [(0, data)]


try:
    # Initialize Jinja2 environment with a file system loader for templates
    abgrid_jinja_env = Environment(
        loader=PackageLoader(package_name="lib.core", package_path="templates"),
        # Enable strict undefined handling to catch missing variables
        undefined=StrictUndefined,
        # Auto-escape HTML for security
        autoescape=select_autoescape(["html", "xml"]),
        # Add bytecode cache for performance
        bytecode_cache=FileSystemBytecodeCache(TEMPLATE_CACHE_DIR)
    )

    # Add custom filters
    abgrid_jinja_env.filters["universal_iter_rows"] = universal_iter_rows

except Exception as e:
    error_message = f"Failed to initialize Jinja2 environment: {e}"
    raise RuntimeError(error_message) from e


class TemplateRenderError(Exception):
    """Custom exception for template rendering errors."""


class CoreRenderer:
    """Renders Jinja2 templates using the configured AB-Grid environment.

    Provides template rendering capabilities with comprehensive error handling
    for template loading and rendering operations.
    """

    def render(self, template_path_str: str, template_data: dict[str, Any]) -> str:
        """Render Jinja2 template with provided template_data.

        Args:
            template_path_str: Path (as string) to the Jinja2 template file relative to template directory.
            template_data: Dictionary containing template context variables and data.

        Returns:
            Rendered template as string.

        Raises:
            - FileNotFoundError: If template file is not found.
            - TemplateRenderError: If template rendering fails due to syntax or runtime errors.
            - ValueError: If input parameters are invalid.
        """
        # Ensure template_path
        if not template_path_str:
            error_message = "Template path cannot be empty or None."
            raise ValueError(error_message)

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
