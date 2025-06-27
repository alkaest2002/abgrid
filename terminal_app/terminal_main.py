"""
Filename: abgrid_main.py
Description: Main module for managing project initialization, file generation, and report rendering.

This module serves as the primary interface for AB-Grid project operations, providing
comprehensive functionality for project lifecycle management including initialization,
group configuration, answer sheet generation, and report creation with optional sociograms.

The module uses a decorator-based error handling system that automatically captures
exceptions and dispatches error events through the event system for consistent logging
and error reporting across all operations.

Author: Pierpaolo Calanna
Date Created: Wed Jun 25 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import os
import yaml
import re
import json

from pathlib import Path
from typing import Literal, Dict, Any, List, Tuple, Union
from weasyprint import HTML
from lib import jinja_env
from lib.core import SYMBOLS
from lib.core.core_data import CoreData
from terminal_app.terminal_logger import logger_decorator, pretty_print
from lib.abgrid_utils import to_json_serializable

ProjectData = Dict[str, Any]
GroupData = Dict[str, Any]
ReportData = Dict[str, Any]
ValidationErrors = List[str]
DataWithErrors = Tuple[Dict[str, Any], ValidationErrors]

class TerminalMain:
    """
    Main class for AB-Grid project management and document generation.
    
    This class provides comprehensive functionality for managing AB-Grid projects
    including initialization, group file generation, answer sheet creation, and
    report generation with optional sociogram support.
    """
    
    def __init__(
        self,
        project: str,
        project_folderpath: Path, 
        project_filepath: Path, 
        groups_filepaths: List[Path]
    ) -> None:
        """
        Initialize TerminalMain instance with project configuration.
        
        Args:
            project: Name of the project
            project_folderpath: Path to the project directory
            project_filepath: Path to the main project configuration file
            groups_filepaths: List of paths to group configuration files
        
        Returns:
            None
        """
        # Populate props
        self.project = project
        self.project_folderpath = project_folderpath
        self.project_filepath = project_filepath 
        self.groups_filepaths = groups_filepaths

        # Initialize core data
        self.core_data = CoreData()

    @staticmethod
    @logger_decorator
    def init_project(
        project: str, 
        project_folderpath: Path, 
        language: str
    ) -> None:
        """
        Initialize a new AB-Grid project with directory structure and configuration.
        
        Creates the project directory structure including subdirectories for reports
        and answer sheets, then generates a project configuration file based on the
        specified language template.
        
        Args:
            project: Name of the project to initialize
            project_folderpath: Path where the project directory will be created
            language: Language code for template selection (e.g., 'en', 'it')
        
        Returns:
            None
        
        Notes:
            - Fails if project directory already exists
            - Creates 'reports' and 'answersheets' subdirectories
            - Uses language-specific templates from lib/templates/{language}/
        """
        # Create the main project directory structure
        # os.makedirs will create intermediate directories if they don't exist
        os.makedirs(project_folderpath, exist_ok=False)  # Fail if project already exists
        
        # Create subdirectories for reports and answer sheets
        reports_dir = project_folderpath / "reports"
        answersheets_dir = project_folderpath / "answersheets"
        os.makedirs(reports_dir)
        os.makedirs(answersheets_dir)
        
        # Get path for the language-specific project configuration template
        template_path = Path(f"./lib/templates/{language}/project.yaml")
        
        # If language-specific project configuration template does not exist
        if not template_path.exists():
            raise FileNotFoundError(f"Project template not found: {template_path}")
        
        # Open language-specific project configuration template
        with open(template_path, 'r', encoding='utf-8') as fin:
            yaml_data = yaml.safe_load(fin)
        
        # Validate that template was loaded successfully
        if not yaml_data:
            raise ValueError(f"Empty project template: {template_path}")
        
        # Customize the template with the project name
        yaml_data["project_title"] = project
        
        # Write the customized configuration to the project directory
        config_file_path = project_folderpath / f"{project}.yaml"
        with open(config_file_path, 'w', encoding='utf-8') as fout:
            yaml.dump(yaml_data, fout, sort_keys=False, allow_unicode=True)

        # Notify user
        pretty_print(f"Project {project} correctly initialized.")

    @logger_decorator
    def generate_group_inputs(
        self, 
        groups: range, 
        members_per_group: int, 
        language: str
    ) -> None:
        """
        Generate group configuration files for specified groups.
        
        Creates individual YAML configuration files for each group using the
        language-specific template. Each file contains group-specific data
        including member assignments using alphabetical symbols.
        
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
            raise ValueError("Groups range cannot be empty")
        
        if members_per_group <= 0:
            raise ValueError(f"members_per_group must be positive, got {members_per_group}")
        
        if members_per_group > len(SYMBOLS):
            raise ValueError(
                f"members_per_group ({members_per_group}) exceeds available symbols ({len(SYMBOLS)}). "
                f"Maximum supported group size is {len(SYMBOLS)} members."
            )

        # template for the language-specific group template
        template_path = f"/{language}/group.html"
        
        try:
            # Try to load template for the language-specific group template
            group_template = jinja_env.get_template(template_path)
        except Exception as e:
            raise FileNotFoundError(f"Group template not found: {template_path}") from e
        
        # Extract member letters based on the number of members per group
        # SYMBOLS contains the alphabet letters used for member identification
        members_per_group_letters = SYMBOLS[:members_per_group]
        
        # Generate a configuration file for each group
        for group_number in groups:
            
            # Prepare template data for the current group
            template_data: Dict[str, Any] = {
                "group": group_number, 
                "members": members_per_group_letters
            }
            
            # Render the template with group-specific data
            rendered_group_template: str = group_template.render(template_data)
            
            # Remove blank lines from the rendered template for cleaner output
            rendered_group_template = "\n".join([
                line for line in rendered_group_template.split("\n") 
                if line.strip()
            ])

            # Generate the group file path
            group_file_path = (self.project_folderpath / f"{self.project}_g{group_number}.yaml")
            
            # Write the rendered template to disk
            with open(group_file_path, "w", encoding='utf-8') as file:
                file.write(rendered_group_template)

        # Notify user
        pretty_print(f"{group_number} group(s) succesfully generated.")
            
    @logger_decorator
    def generate_answersheets(self, language: str) -> None:
        """
        Generate PDF answer sheets for all configured groups.
        
        Creates individual PDF answer sheets for each group by combining project
        configuration data with group-specific data. Each answer sheet includes
        Likert scale configuration based on group choices.
        
        Args:
            language: Language code for template selection
        
        Returns:
            None
        
        Notes:
            - Requires existing group files and valid project configuration
            - Answer sheets are saved in the 'answersheets' subdirectory
            - Likert scale symbols are automatically configured based on choices_a
        """
        # Validate that group files exist
        if not self.groups_filepaths:
            raise ValueError("No group files found. Please generate group inputs first.")

        # Load project data and validate it
        project_data = self._load_yaml_data(self.project_filepath)
        project_data, project_data_errors = self.core_data.get_project_data(project_data)

        # Check for project-level validation errors
        if project_data_errors:
            raise ValueError(f"Data validation failed for project {self.project}:\n{project_data_errors}")
        # Process each group file to generate individual answer sheets
        for group_file in self.groups_filepaths:
            
            # Load and validate group-specific data
            group_data = self._load_yaml_data(group_file)
            group_data, group_data_errors = self.core_data.get_group_data(group_data)

            # Check for group-level validation errors
            if group_data_errors:
                raise ValueError(f"Group data validation failed for {group_file.name}: {group_data_errors}")

            # Init sheets data
            sheets_data = project_data.model_dump()
            
            # Extend sheets data
            sheets_data["group"] = group_data.group
            sheets_data["likert"] = sum(map(lambda x: list(x.keys()), group_data.choices_a), [])

            # Notify user
            pretty_print(f"Generating answersheets for {group_file.stem}. Please, wait...")

            # Generate and save the PDF answer sheet
            self._render_pdf("answersheet", sheets_data, group_file.stem, language)

            # Notify user
            pretty_print(f"Answersheets for {group_file.stem} succesfully generated.")

    @logger_decorator
    def generate_reports(self, language: str, with_sociogram: bool = False) -> None:
        """
        Generate comprehensive PDF reports for all groups with optional sociograms.
        
        Creates detailed reports for each group including social network analysis,
        statistics, and optional sociogram visualizations. Also exports aggregated
        data in JSON format for further analysis.
        
        Args:
            language: Language code for template selection
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

        # Load project data
        project_data = self._load_yaml_data(self.project_filepath)
        
        # Process each group file to generate individual reports
        for group_file in self.groups_filepaths:
            
            # Load group data for the current group
            group_data = self._load_yaml_data(group_file)
            
            # Validate report data, i.e. project data + report data
            report_data, report_data_errors = (
                self.core_data.get_report_data(
                    dict(project_data=project_data, group_data=group_data), 
                    with_sociogram
                )
            )
            
            # Check for report-level validation errors
            if report_data_errors:
                raise ValueError(f"Report data validation failed for {group_file.name}: {report_data_errors}")
            
            # Notify user
            pretty_print(f"Generating report for {group_file.stem}. Please, wait...")
            
            # Generate the PDF report with sociogram configuration
            report_data.update({ "with_sociogram": with_sociogram })
            self._render_pdf("report", report_data, group_file.stem, language)

            # Notify user
            pretty_print(f"Report for {group_file.stem} succesfully generated.")
            
            filtered_data = to_json_serializable(
                report_data, 
                keep=[
                    "project_title",         # Project identification
                    "members_per_group",     # Group size information
                    "sna.macro_stats_a",     # Social network analysis - macro level A
                    "sna.macro_stats_b",     # Social network analysis - macro level B
                    "sna.micro_stats_a",     # Social network analysis - micro level A
                    "sna.micro_stats_b",     # Social network analysis - micro level B
                    "sociogram.macro_stats", # Sociogram macro statistics
                    "sociogram.micro_stats", # Sociogram micro statistics
                    "relevant_nodes_ab.*",   # Key relationship nodes (pattern match)
                ],
            )
            
            # Add the filtered data to the collection
            all_groups_data[group_file.stem] = filtered_data
        
        try:
            # Define json export file path
            json_export_path = self.project_folderpath / f"{self.project}_data.json"

            # Persist json file to disk
            with open(json_export_path, "w", encoding='utf-8') as fout:
                json.dump(all_groups_data, fout, indent=4, ensure_ascii=False)
       
        except Exception as e:
            raise OSError(f"Failed to export data to JSON file {json_export_path}:\n{e}") from e

    @logger_decorator
    def _render_pdf(
        self, 
        doc_type: Literal["report", "answersheet"], 
        doc_data: Dict[str, Any], 
        doc_suffix: str, 
        language: str
    ) -> None:
        """
        Render HTML template to PDF document using WeasyPrint.
        
        Converts structured data into PDF documents by rendering Jinja2 templates
        and converting the resulting HTML to PDF format. Handles both report and
        answer sheet document types with appropriate template selection.
        
        Args:
            doc_type: Type of document to generate ("report" or "answersheet")
            doc_data: Data dictionary to populate the template
            doc_suffix: Suffix to append to the filename (typically group identifier)
            language: Language code for template selection
        
        Returns:
            None
        
        Notes:
            - Uses WeasyPrint for HTML to PDF conversion
            - Filename sanitization removes leading/trailing underscores
            - Debug HTML output can be enabled by uncommenting debug section
        """
        # Select the appropriate template based on document type
        match doc_type:
            case "answersheet":
                template_path = f"./{language}/answersheet.html"
            case "report":
                template_path = f"./{language}/report_multi_page.html"
            case _:
                raise ValueError(f"Unsupported document type: {doc_type}.")
        
        # Load and render the template with provided data
        try:
            template = jinja_env.get_template(template_path)
        except Exception as e:
            raise FileNotFoundError(f"Template {template_path} not found.") from e
        
        try:
            rendered_html = template.render(doc_data)
        except Exception as e:
            raise ValueError(f"Template rendering failed for {template_path}: {e}") from e
        
        # Determine the output directory based on document type
        output_directory = self.project_folderpath / f"{doc_type}s"
        
        # Ensure output directory exists
        if not output_directory.exists():
            raise OSError(f"Output directory {output_directory} does not exist.")
        
        # Construct and sanitize the filename
        # Remove leading/trailing underscores and ensure clean naming
        base_filename = f"{self.project}_{doc_type}_{doc_suffix}"
        sanitized_filename = re.sub(r"^_+|_+$", "", base_filename)
        output_path = output_directory / f"{sanitized_filename}.pdf"
        
        # Convert HTML to PDF and save to disk
        try:
            HTML(string=rendered_html).write_pdf(output_path)
        except Exception as e:
            raise OSError(f"PDF generation failed for {output_path}: {e}") from e
        
        # -----------------------------------------------------------------------------------
        # DEBUGGING SECTION - Uncomment to save HTML files for template inspection
        # -----------------------------------------------------------------------------------
        # debug_html_path = output_directory / f"{sanitized_filename}.html"
        # with open(debug_html_path, "w", encoding='utf-8') as file:
        #     file.write(rendered_html)
        # -----------------------------------------------------------------------------------

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
        
        except FileNotFoundError:
            raise FileNotFoundError(f"{yaml_file_path.name} could not be found.")
        
        except yaml.YAMLError:
            raise ValueError(f"{yaml_file_path.name} could not be parsed.")
