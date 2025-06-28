"""
Filename: core_templates.py
Description: Provides functionality to render SNA/Sociogra data via templates.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
import re
from pathlib import Path
from weasyprint import HTML
from typing import Any, Dict
from lib import jinja_env


class CoreRenderer:
    """Renders templates to PDF documents using Jinja2 and WeasyPrint."""

    def render_html(self, template_path: Path, data: Dict[str, Any]) -> str:
        """Render Jinja2 template with provided data.
        
        Args:
            template_path: Path to the Jinja2 template file
            data: Template context data
            
        Returns:
            Rendered HTML string
            
        Raises:
            FileNotFoundError: If template file is not found
            ValueError: If template rendering fails
        """
        try:
            template = jinja_env.get_template(template_path)
        except Exception as e:
            raise FileNotFoundError(f"Template {template_path} not found.") from e
        
        try:
            rendered_html = template.render(data)
        except Exception as e:
            raise ValueError(f"Template rendering failed for {template_path}: {e}") from e
        
        return rendered_html

    def generate_answersheets_pdf(self, template_path: Path, data: Dict[str, Any], suffix: str, output_directory: Path) -> None:
        """Generate answersheet PDF from template.
        
        Args:
            template_path: Path to the Jinja2 template file
            data: Template context data
            suffix: Suffix used in filename
            output_directory: Directory to save the PDF file
            
        Raises:
            FileNotFoundError: If template file is not found
            ValueError: If template rendering fails
            OSError: If output directory doesn't exist or PDF generation fails
        """
        rendered_template = self.render_html(template_path, data)
        self._generate_pdf("answersheet", rendered_template, suffix, output_directory)

    def generate_report_pdf(self, template_path: Path, data: Dict[str, Any], suffix: str, output_directory: Path) -> None:
        """Generate report PDF from template.
        
        Args:
            template_path: Path to the Jinja2 template file
            data: Template context data
            suffix: Suffix used in filename
            output_directory: Directory to save the PDF file
            
        Raises:
            FileNotFoundError: If template file is not found
            ValueError: If template rendering fails
            OSError: If output directory doesn't exist or PDF generation fails
        """
        rendered_template = self.render_html(template_path, data)
        self._generate_pdf("report", rendered_template, suffix, output_directory)
    
    def _generate_html(self, doc_type: str, rendered_template: str, suffix: str, output_directory: Path) -> None:
        """Save rendered HTML template to file.
        
        Args:
            doc_type: Type of document for filename prefix
            rendered_template: HTML content as string
            suffix: Suffix used in filename
            output_directory: Directory to save the HTML file
            
        Raises:
            OSError: If output directory doesn't exist or file write fails
            
        Notes:
            Filename format: {doc_type}_{suffix}.html
            Leading/trailing underscores are automatically removed from filename
        """
        
        # Ensure output directory exists
        if not output_directory.exists():
            raise OSError(f"Output directory {output_directory} does not exist.")
        
        # Construct and sanitize the filename
        # Remove leading/trailing underscores and ensure clean naming
        base_filename = f"{doc_type}_{suffix}"
        sanitized_filename = re.sub(r"^_+|_+$", "", base_filename)
        output_path = output_directory / f"{sanitized_filename}.html"
        
        try:
            with open(output_path, "w", encoding='utf-8') as file:
                file.write(rendered_template)
        except Exception as e:
            raise OSError(f"HTML file generation failed for {output_path}: {e}") from e
    
    def _generate_pdf(self, doc_type: str, rendered_template: str, suffix: str, output_directory: Path) -> None:
        """Convert HTML template to PDF and save to output directory.
        
        Args:
            doc_type: Type of document for filename prefix
            rendered_template: HTML content as string
            suffix: Suffix used in filename
            output_directory: Directory to save the PDF file
            
        Raises:
            OSError: If output directory doesn't exist or PDF generation fails
            
        Notes:
            Filename format: {doc_type}_{suffix}.pdf
            Leading/trailing underscores are automatically removed from filename
        """
        
        # Ensure output directory exists
        if not output_directory.exists():
            raise OSError(f"Output directory {output_directory} does not exist.")
        
        # Construct and sanitize the filename
        # Remove leading/trailing underscores and ensure clean naming
        base_filename = f"{doc_type}_{suffix}"
        sanitized_filename = re.sub(r"^_+|_+$", "", base_filename)
        output_path = output_directory / f"{sanitized_filename}.pdf"
        
        # Convert HTML to PDF and save to disk
        try:
            HTML(string=rendered_template).write_pdf(output_path)
        except Exception as e:
            raise OSError(f"PDF generation failed for {output_path}: {e}") from e
