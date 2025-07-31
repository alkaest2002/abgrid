"""
Author: Pierpaolo Calanna

Date Created: Wed Jun 25 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import os
import re
import argparse
from weasyprint import HTML
import yaml
import json

from pathlib import Path
from typing import Dict, Any, List, Union
from lib.utils import to_json
from lib.core import SYMBOLS
from lib.core.core_schemas import ABGridReportSchema
from lib.core.core_data import CoreData
from lib.core.core_templates import abgrid_jinja_env, CoreRenderer
from lib.interfaces.terminal.terminal_logger import logger_decorator


class TerminalMain:
    """
    Main class for AB-Grid project management and document generation.
    
    This class provides comprehensive functionality for managing AB-Grid projects
    including initialization, group file generation, and
    report generation with optional sociogram support.
    """
    
    def __init__(self, args: argparse.Namespace) -> None:
        """
        Initialize TerminalMain instance with project configuration from args.
        
        Args:
            args: Parsed command line arguments containing project configuration
                 Must have: user, project, language, action
                 May have: members_per_group, with_sociogram

        Returns:
            None
        """
        # Store args and extract properties
        self.args = args
        self.project = args.project
        self.language = args.language
        
        # Build paths from args
        data_path = Path("./data")
        self.user_folderpath = data_path / args.user
        self.project_folderpath = self.user_folderpath / args.project
        self.groups_filepaths = self._get_group_filepaths()
        self.reports_path = self.project_folderpath / "reports"
        
        # Ensure report directory exists for report actions
        if args.action in ["report"] and not self.reports_path.exists():
            raise OSError(f"Output directory {self.reports_path} does not exist.")
        
        # Initialize core components
        self.core_data = CoreData()
        self.renderer = CoreRenderer()

    @logger_decorator
    def init_project(self) -> None:
        """
        Initialize a new AB-Grid project with directory structure.
        
        Creates the project directory structure including subdirectories for reports.
        
        Returns:
            None
        
        Notes:
            - Fails if project directory already exists
            - Creates 'reports' subdirectory
        """
        # Create the main project directory structure
        os.makedirs(self.project_folderpath, exist_ok=False) # Fail if project already exists
        os.makedirs(self.project_folderpath / "reports")

    @logger_decorator
    def generate_group(self) -> None:
        """
        Generate group configuration files for the next available group.
        
        Creates a YAML configuration file for the next group using the
        language-specific template.
        
        Returns:
            None
        
        Notes:
            - Maximum supported group size is limited by available SYMBOLS
            - Generated files follow naming pattern: {project}_g{group_number}.yaml
            - Uses Jinja2 templates for HTML rendering within YAML structure
        """
        # Calculate next group number
        groups_already_created = len(self.groups_filepaths)
        next_group = groups_already_created + 1
        
        # Get members_per_group from args
        members_per_group = self.args.members_per_group
        
        # Template for the language-specific group template
        template_path = f"/{self.language}/group.yaml"
        
        # Load template for the language-specific group template
        group_template = abgrid_jinja_env.get_template(template_path)
        
        # Prepare template data for the current group
        template_data = { 
            "project_title": self.project,
            "question_a": "",
            "question_b": "",
            "group": next_group, 
            "members": SYMBOLS[:members_per_group] 
        }
        
        # Render the template with group-specific data
        rendered_group_template = group_template.render(template_data)
        
        # Generate the group file path
        group_file_path = self.project_folderpath / f"{self.project}_g{next_group}.yaml"
        
        # Write the rendered template to disk
        with open(group_file_path, "w", encoding='utf-8') as file:
            file.write(rendered_group_template)

        # Update internal state
        self.groups_filepaths = self._get_group_filepaths()
        
    @logger_decorator
    def generate_report(self) -> None:
        """
        Generate comprehensive PDF report with optional sociograms.
        
        Creates detailed reports for each group including social network analysis,
        statistics, and optional sociogram visualizations. Also exports aggregated
        data in JSON format for further analysis.
        
        Returns:
            None
        
        Notes:
            - Reports are saved in the 'reports' subdirectory
            - JSON export includes filtered data for macro/micro statistics
            - Sociogram generation requires additional computational resources
        """
        
        # Validate that group files exist
        if not self.groups_filepaths:
            from app_terminal import ABGridError
            raise ABGridError(f"No group files found in project '{self.project}'")
        
        # Get with_sociogram from args
        with_sociogram = self.args.with_sociogram
        
        # Initialize storage for aggregated data from all groups
        all_groups_data = {}

        # Process each group file to generate individual reports
        for group_file in self.groups_filepaths:

            print(f"Generating report for {group_file.stem}. Please, wait...")
            
            # Load current group data
            group_data = self._load_yaml_data(group_file)
            
            # Validate current group data
            validated_data = ABGridReportSchema.model_validate(group_data)
            
            # Get report data
            report_data = self.core_data.get_report_data(validated_data, with_sociogram)
            
            # Render report html template
            rendered_report = self.renderer.render(f"./{self.language}/report.html", report_data)

            # Generate PDF report
            self._generate_pdf("report", rendered_report, group_file.stem, self.reports_path)

            print(f"Report for {group_file.stem} successfully generated.")
            
            # Convert report data to json
            filtered_data = to_json(report_data)
            
            # Add the filtered data to the collection
            all_groups_data[group_file.stem] = filtered_data
        
        # Define json export file path
        json_export_path = self.project_folderpath / f"{self.project}_data.json"

        # Persist json file to disk
        with open(json_export_path, "w", encoding='utf-8') as fout:
            json.dump(all_groups_data, fout, indent=4, ensure_ascii=False)

    @logger_decorator
    def _get_group_filepaths(self) -> List[Path]:
        """Get list of group file paths matching the pattern."""
        if not self.project_folderpath.exists():
            return []
        return [path for path in self.project_folderpath.glob("*_g*.*") 
                if re.search(r"_g\d+\.\w+$", path.name)]
        
    @logger_decorator
    def _load_yaml_data(self, yaml_file_path: Path) -> Union[Dict[str, Any], None]:
        """
        Load and parse YAML data from file with error handling.
        
        Safely loads YAML configuration files and handles common errors such as
        missing files and parsing issues. Returns structured data or None with
        appropriate error information.
        
        Args:
            yaml_file_path: Path to the YAML file to load
        
        Returns:
            Dictionary containing parsed YAML data, or None if loading failed
        
        Notes:
            - Handles FileNotFoundError and YAMLError exceptions gracefully
            - Returns error messages for debugging purposes
        """
        try:
            with open(yaml_file_path, 'r') as file:
                yaml_data = yaml.safe_load(file)
            return yaml_data
        
        except yaml.YAMLError:
            raise ValueError(f"{yaml_file_path.name} could not be parsed.")
        
    def _generate_pdf(self, template_type: str, rendered_template: str, suffix: str, output_directory: Path) -> None:
        """Convert HTML template to PDF and save to output directory.
        
        Args:
            template_type: Type of document for filename prefix
            rendered_template: HTML content as string
            suffix: Suffix used in filename
            output_directory: Directory to save the PDF file
            
        Notes:
            Filename format: {template_type}_{suffix}.pdf
            Leading/trailing underscores are automatically removed from filename
        """
        
        # Build file path
        file_path = output_directory / f"{template_type}_{suffix}.pdf"
        
        # Convert HTML to PDF and save to disk
        try:
            HTML(string=rendered_template).write_pdf(file_path)
        
        except Exception as e:
            raise OSError(f"PDF generation failed for {file_path}: {e}.") from e
