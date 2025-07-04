"""
Filename: abgrid_main.py

Description: Terminal main module for managing project initialization, file generation, and report rendering.

Author: Pierpaolo Calanna

Date Created: Wed Jun 25 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import os
from weasyprint import HTML
import yaml
import json

from pathlib import Path
from typing import Dict, Any, List, Tuple, Union
from lib.utils import to_json
from lib.core import SYMBOLS
from lib.core.core_schemas import ABGridSchema
from lib.core.core_data import CoreData
from lib.core.core_templates import abgrid_jinja_env, CoreRenderer
from lib.interfaces.terminal.terminal_logger import logger_decorator

ProjectData = Dict[str, Any]
GroupData = Dict[str, Any]
ReportData = Dict[str, Any]
ValidationErrors = List[str]
DataWithErrors = Tuple[Dict[str, Any], ValidationErrors]

class TerminalMain:
    """
    Main class for AB-Grid project management and document generation.
    
    This class provides comprehensive functionality for managing AB-Grid projects
    including initialization, group file generation, and
    report generation with optional sociogram support.
    """
    
    def __init__(
        self,
        project: str,
        project_folderpath: Path, 
        groups_filepaths: List[Path],
        language: str,
    ) -> None:
        """
        Initialize TerminalMain instance with project configuration.
        
        Args:
            project: Name of the project
            project_folderpath: Path to the project directory
            groups_filepaths: List of paths to group configuration files
            language: language used in templates

        Returns:
            None
        """
        # Populate props
        self.project = project
        self.project_folderpath = project_folderpath
        self.groups_filepaths = groups_filepaths
        self.reports_path = project_folderpath / "reports"
        self.language = language
        
        # Ensure rerport directory exists
        if not self.reports_path.exists():
            raise OSError(f"Output directory {self.reports_path} does not exist.")
        
        # Initialize core data
        self.core_data = CoreData()

        # Initialze core renderer
        self.renderer = CoreRenderer()

    @staticmethod
    @logger_decorator
    def init_project(
        project: str, 
        project_folderpath: Path, 
    ) -> None:
        """
        Initialize a new AB-Grid project with directory structure.
        
        Creates the project directory structure including subdirectories for reports.
        
        Args:
            project: Name of the project to initialize
            project_folderpath: Path where the project directory will be created
        
        Returns:
            None
        
        Notes:
            - Fails if project directory already exists
            - Creates 'reports' subdirectory
        """
        # Create the main project directory structure
        # os.makedirs will create intermediate directories if they don't exist
        os.makedirs(project_folderpath, exist_ok=False)  # Fail if project already exists
        os.makedirs(project_folderpath / "reports")
        
        # Notify user
        print(f"Project {project} correctly initialized.")

    @logger_decorator
    def generate_group(
        self, 
        groups: range, 
        members_per_group: int, 
        language: str
    ) -> None:
        """
        Generate group configuration files for specified groups.
        
        Creates individual YAML configuration files for each group using the
        language-specific template.
        
        Args:
            groups: Range object specifying which group numbers to generate
            members_per_group: Number of members in each group
            language: Language code for template selection
        
        Returns:
            None
        
        Notes:
            - Maximum supported group size is limited by available SYMBOLS
            - Generated files follow naming pattern: {project}_g{group_number}.yaml
            - Uses Jinja2 templates for HTML rendering within YAML structure
        """
        # Validate input parameters
        if not groups:
            raise ValueError("Groups range cannot be empty.")
        
        if members_per_group <= 0:
            raise ValueError(f"members_per_group must be positive, got {members_per_group}.")
        
        if members_per_group > len(SYMBOLS):
            raise ValueError(
                f"members_per_group ({members_per_group}) exceeds available symbols ({len(SYMBOLS)})."
                f"Maximum supported group size is {len(SYMBOLS)} members."
            )

        # template for the language-specific group template
        template_path = f"/{language}/group.html"
        
        # Load template for the language-specific group template
        group_template = abgrid_jinja_env.get_template(template_path)
        
        # Generate a configuration file for each group
        for group_number in groups:
            
            # Prepare template data for the current group
            template_data = { "group": group_number, "members": SYMBOLS[:members_per_group] }
            
            # Render the template with group-specific data
            rendered_group_template = group_template.render(template_data)
            
            # Generate the group file path
            group_file_path = self.project_folderpath / f"{self.project}_g{group_number}.yaml"
            
            # Write the rendered template to disk
            with open(group_file_path, "w", encoding='utf-8') as file:
                file.write(rendered_group_template)

        # Notify user
        print(f"{group_number} group(s) succesfully generated.")
            
    @logger_decorator
    def generate_reports(self, with_sociogram: bool = False) -> None:
        """
        Generate comprehensive PDF reports for all groups with optional sociograms.
        
        Creates detailed reports for each group including social network analysis,
        statistics, and optional sociogram visualizations. Also exports aggregated
        data in JSON format for further analysis.
        
        Args:
            with_sociogram: Whether to include sociogram visualizations in reports
        
        Returns:
            None
        
        Notes:
            - Reports are saved in the 'reports' subdirectory
            - JSON export includes filtered data for macro/micro statistics
            - Sociogram generation requires additional computational resources
        """
        # Validate that group files exist
        if not self.groups_filepaths:
            raise ValueError("No group files found.")
        
        # Initialize storage for aggregated data from all groups
        all_groups_data = {}

        # Process each group file to generate individual reports
        for group_file in self.groups_filepaths:

            # Notify user
            print(f"Generating report for {group_file.stem}. Please, wait...")
            
            # Load current group data
            group_data = self._load_yaml_data(group_file)
            
            # Validate current group data
            validated_data = ABGridSchema.model_validate(group_data)
            
            # Get report Data
            report_data = self.core_data.get_report_data(validated_data, with_sociogram)
            
            # Render report html template
            rendered_report = self.renderer.render_html(f"./{self.language}/report.html", report_data)

            # Generate PDF report
            self._generate_pdf("report", rendered_report, group_file.stem, self.reports_path)

            # Notify user
            print(f"Report for {group_file.stem} succesfully generated.")
            
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

