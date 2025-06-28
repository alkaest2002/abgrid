"""
Filename: core_templates.py
Description: Provides functionality to render SNA/Sociogra data via templates.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
import jinja2
from pathlib import Path
from typing import Any, Dict

# Initialize Jinja2 environment with a file system loader for templates
abgrid_jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(["./lib/core/templates"])
)

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
            ValueError: If template rendering fails
        """
        try:
            # Try to load template
            template = abgrid_jinja_env.get_template(template_path)
        except Exception as e:
            raise FileNotFoundError(f"Template {template_path} not found.") from e
        
        try:
            # Try to render template with template data
            rendered_html = template.render(template_data)
        except Exception as e:
            raise ValueError(f"Template rendering failed for {template_path}: {e}.") from e
        
        return rendered_html