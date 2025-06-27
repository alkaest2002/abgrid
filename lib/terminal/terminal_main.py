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
from typing import Literal, Dict, Any, List, Tuple
from weasyprint import HTML
from lib.terminal.terminal_yaml import ABGridYAML
from lib.terminal.terminal_logger import logger_decorator
from lib.core import SYMBOLS
from lib.core.core_data import ABGridData
from lib.abgrid_utils import to_json_serializable
from lib import jinja_env

ProjectData = Dict[str, Any]
GroupData = Dict[str, Any]
ReportData = Dict[str, Any]
ValidationErrors = List[str]
DataWithErrors = Tuple[Dict[str, Any], ValidationErrors]

class TerminalMain:
    """
    Main orchestrator for AB-Grid project lifecycle management and document generation.
    
    Provides comprehensive functionality for creating, configuring, and processing AB-Grid
    projects from initialization through final report generation. Manages project directory
    structure, configuration files, group data processing, answer sheet creation, and
    analytical report generation with optional network visualizations.
    
    All public methods implement automatic error handling through decorators that capture
    exceptions and dispatch error events for consistent logging and error reporting.
    
    Integrates with the AB-Grid event system for operation tracking and provides a unified
    interface for all project-related operations through the ABGridData management system.
    
    Attributes:
        abgrid_data (ABGridData): Core data management instance containing project paths,
                                 configuration data, and file operations for the current
                                 project workspace.
    """
    
    def __init__(
        self, 
        project: str, 
        project_folderpath: Path, 
        project_filepath: Path, 
        groups_filepaths: List[Path]
    ) -> None:
        """
        Initialize ABGridMain instance with project configuration and file system paths.

        Creates the core data management system and prepares the instance for project
        operations. Validates path accessibility and initializes the internal ABGridData
        system that serves as the central hub for all project data operations.

        Args:
            project: Unique project identifier used for file naming and project reference.
            project_folderpath: Root directory containing all project files and subdirectories.
            project_filepath: Path to main project configuration file (YAML format).
            groups_filepaths: List of paths to individual group configuration files.

        Raises:
            FileNotFoundError: If specified file paths do not exist.
            PermissionError: If insufficient read/write permissions for specified paths.
            TypeError: If path arguments are not Path objects or convertible strings.
            
        Note:
            This constructor does not use error decoration to allow immediate failure
            detection during object creation. Path validation occurs during ABGridData
            initialization.
        """
        # Initialize the core data management system with project configuration
        self.abgrid_data: ABGridData = ABGridData(
            project, 
            project_folderpath, 
            project_filepath, 
            groups_filepaths, 
            ABGridYAML()
        )

    @staticmethod
    @logger_decorator(("initialize project", "end of project initialization"))
    def init_project(
        project: str, 
        project_folderpath: Path, 
        language: str
    ) -> None:
        """
        Initialize new AB-Grid project with complete directory structure and configuration.
        
        Creates project workspace including directory hierarchy, configuration files, and
        language-specific templates. Sets up all necessary components for AB-Grid project
        operations including reports and answersheets subdirectories.
        
        Generates main project configuration file from language-specific template with
        customized project metadata. Ensures project workspace is ready for group
        configuration and data collection operations.

        Args:
            project: Name identifier for the new project, used for directory and file naming.
            project_folderpath: Target directory where project structure will be created.
                               Parent directories created automatically if needed.
            language: Language code for template selection (e.g., 'en', 'it', 'es').
                     Determines language-specific templates and localization.

        Raises:
            OSError: If directory creation fails due to permissions, disk space, or path issues.
            FileNotFoundError: If language-specific template files are not found.
            yaml.YAMLError: If template parsing or YAML processing fails.
            FileExistsError: If project directory already exists (via os.makedirs exist_ok=False).
            PermissionError: If insufficient write permissions for target directory.
            
        Note:
            Creates directory structure: project_folderpath/{reports/, answersheets/, project.yaml}.
            Fails if project directory already exists to prevent accidental overwrites.
            All errors automatically handled by decorator and dispatched as error events.
        """
        # Create the main project directory structure
        # os.makedirs will create intermediate directories if they don't exist
        os.makedirs(project_folderpath, exist_ok=False)  # Fail if project already exists
        
        # Create subdirectories for reports and answer sheets
        reports_dir = project_folderpath / "reports"
        answersheets_dir = project_folderpath / "answersheets"
        os.makedirs(reports_dir)
        os.makedirs(answersheets_dir)
        
        # Load the project configuration template for the specified language
        template_path = Path(f"./lib/templates/{language}/project.yaml")
        
        if not template_path.exists():
            raise FileNotFoundError(f"Project template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as fin:
            yaml_data: ProjectData = yaml.safe_load(fin)
        
        # Validate that template was loaded successfully
        if not yaml_data:
            raise ValueError(f"Empty or invalid project template: {template_path}")
        
        # Customize the template with the project name
        yaml_data["project_title"] = project
        
        # Write the customized configuration to the project directory
        config_file_path = project_folderpath / f"{project}.yaml"
        with open(config_file_path, 'w', encoding='utf-8') as fout:
            yaml.dump(yaml_data, fout, sort_keys=False, allow_unicode=True)

    @logger_decorator(("generate group files", "end of group files generation"))
    def generate_group_inputs(
        self, 
        groups: range, 
        members_per_group: int, 
        language: str
    ) -> None:
        """
        Generate standardized input configuration files for specified project groups.

        Creates individual YAML configuration files for each group using language-specific
        templates. Each file contains structured data collection fields, member identification
        using alphabetic symbols, and all configuration parameters required for AB-Grid
        analysis and data processing.
        
        Files are generated with consistent naming conventions and member identification
        schemes to ensure compatibility with downstream processing and analysis operations.

        Args:
            groups: Range object specifying group numbers for file generation.
                   Iterates through range to create individual group files.
            members_per_group: Number of members per group, determines alphabetic identifiers
                              assigned to each member (A, B, C, etc.). Must be positive.
            language: Language code for template selection determining localization and
                     template content for generated group configuration files.

        Raises:
            TemplateNotFound: If group template for specified language is not found.
            OSError: If file writing operations fail due to system-level issues.
            jinja2.TemplateError: If template rendering fails due to syntax or variable errors.
            ValueError: If members_per_group is non-positive or exceeds available symbols.
            
        Output:
            Creates files named: {project}_g{group_number}.yaml in project root directory.
            Each file contains complete group configuration structure with member identifiers.
            
        Note:
            Member identification uses consecutive letters from SYMBOLS constant.
            Template rendering removes blank lines for cleaner output formatting.
            All errors handled by decorator and dispatched through event system.
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

        # Load the group template for the specified language
        template_path = f"/{language}/group.html"
        
        try:
            group_template = jinja_env.get_template(template_path)
        except Exception as e:
            raise FileNotFoundError(f"Group template not found: {template_path}") from e
        
        # Extract member letters based on the number of members per group
        # SYMBOLS contains the alphabet letters used for member identification
        members_per_group_letters: List[str] = SYMBOLS[:members_per_group]
        
        # Track successfully generated files for reporting
        generated_files = []
        
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
            group_file_path = (
                self.abgrid_data.project_folderpath / 
                f"{self.abgrid_data.project}_g{group_number}.yaml"
            )
            
            # Write the rendered template to disk
            with open(group_file_path, "w", encoding='utf-8') as file:
                file.write(rendered_group_template)
            
            generated_files.append(group_file_path.name)
          
    @logger_decorator(("generate answersheets", "end of answersheets generation"))
    def generate_answersheets(self, language: str) -> None:
        """
        Generate formatted PDF answer sheets for all configured project groups.

        Creates professionally formatted answer sheets combining project configuration
        with group-specific data. Each sheet contains structured data collection areas,
        member identification sections, question fields, and response areas formatted
        according to AB-Grid methodology requirements.
        
        Validates both project-level and group-level data integrity before generation
        to ensure consistency and completeness of generated documents. Uses WeasyPrint
        for high-quality PDF rendering with professional styling and layout.

        Args:
            language: Language code determining template selection, localization, and
                     content language for generated answer sheet documents.

        Raises:
            ValueError: If validation fails for project data or any group configuration.
                       Includes missing fields, invalid data types, or inconsistent settings.
            TemplateNotFound: If answersheet template not found for specified language.
            OSError: If PDF generation or file operations fail due to system issues.
            weasyprint.HTML.Error: If HTML to PDF conversion fails during rendering.
            
        Output:
            Creates PDF files in answersheets/ subdirectory with naming pattern:
            {project}_answersheet_{group_stem}.pdf for each configured group.
            
        Note:
            Performs comprehensive data validation before generation starts.
            Configures Likert scales automatically based on group choice configurations.
            Each answer sheet customized with group-specific information and member lists.
            All errors handled by decorator and dispatched through event system.
        """
        # Validate that group files exist
        if not self.abgrid_data.groups_filepaths:
            raise ValueError("No group files found. Please generate group inputs first.")

        sheets_data: ProjectData
        sheets_data_errors: ValidationErrors
        sheets_data, sheets_data_errors = self.abgrid_data.get_project_data()

        # Check for project-level validation errors
        if sheets_data_errors:
            error_message = f"Project data validation failed: {'; '.join(sheets_data_errors)}"
            raise ValueError(error_message)

        # Track successfully generated answer sheets
        generated_sheets = []

        # Process each group file to generate individual answer sheets
        for group_file in self.abgrid_data.groups_filepaths:
            # Load and validate group-specific data
            group_data: GroupData
            group_data_errors: ValidationErrors
            group_data, group_data_errors = self.abgrid_data.get_group_data(group_file)

            # Check for group-level validation errors
            if group_data_errors:
                error_message = f"Group data validation failed for {group_file.name}: {'; '.join(group_data_errors)}"
                raise ValueError(error_message)

            # Extract group number from filename using regex
            group_number_match = re.search(r'(\d+)$', group_file.stem)
            if not group_number_match:
                raise ValueError(f"Could not extract group number from filename: {group_file.name}")
            
            group_number = int(group_number_match.group(0))
            
            # Enhance sheets data with group-specific information
            sheets_data_copy = sheets_data.copy()  # Don't modify original
            sheets_data_copy["group"] = group_number
            
            # Configure Likert scale based on the number of choices in group data
            # SYMBOLS provides the letter labels for Likert scale options
            if "choices_a" in group_data and group_data["choices_a"]:
                sheets_data_copy["likert"] = SYMBOLS[:len(group_data["choices_a"])]
            else:
                raise ValueError(f"No choices_a found in group data for {group_file.name}")

            # Generate and save the PDF answer sheet
            self._render_pdf("answersheet", sheets_data_copy, group_file.stem, language)
            generated_sheets.append(f"group_{group_number}")

    @logger_decorator(("generate reports", "end of reporst generation"))
    def generate_reports(
        self, 
        language: str, 
        with_sociogram: bool = False
    ) -> None:
        """
        Generate comprehensive analytical reports with statistical analysis and data export.

        Creates detailed PDF reports for each group containing statistical analysis,
        network metrics, relationship patterns, and optional sociogram visualizations.
        Performs complete data analysis pipeline including social network analysis,
        centrality measurements, and group dynamics assessment.
        
        Additionally exports structured analytical data to JSON format for integration
        with external tools, further analysis, or archival purposes. JSON export excludes
        graphics and bulky statistical data while preserving essential analytical results.

        Args:
            language: Language code determining template selection, localization, and
                     content language for generated report documents.
            with_sociogram: Flag controlling inclusion of network visualization diagrams.
                           When True, generates sociogram graphics showing relationship
                           patterns and network structures within each group.

        Raises:
            ValueError: If validation fails for report data or analytical computations.
                       Includes incomplete analysis, missing statistical data, or
                       inconsistent network analysis results.
            TemplateNotFound: If report template not found for specified language.
            OSError: If PDF generation, JSON export, or file operations fail.
            json.JSONEncodeError: If data serialization fails due to non-serializable types.
            weasyprint.HTML.Error: If HTML to PDF conversion fails during rendering.
            
        Output:
            Creates PDF reports in reports/ subdirectory with naming pattern:
            {project}_report_{group_stem}.pdf and exports aggregated data as
            {project}_data.json in project root directory.
            
        Note:
            Sociogram generation significantly increases processing time but provides
            valuable network visualization insights. JSON export includes filtered
            data optimized for external analysis and integration workflows.
            All errors handled by decorator and dispatched through event system.
        """
        # Signal the start of report generation
        sociogram_status = "with sociograms" if with_sociogram else "without sociograms"

        # Validate that group files exist
        if not self.abgrid_data.groups_filepaths:
            raise ValueError("No group files found. Please ensure group data is available.")

        # Initialize storage for aggregated data from all groups
        all_groups_data: Dict[str, Any] = {}
        generated_reports = []
        
        # Process each group file to generate individual reports
        for group_file in self.abgrid_data.groups_filepaths:
            
            # Load and validate report data for the current group
            report_data: ReportData
            report_errors: ValidationErrors
            report_data, report_errors = self.abgrid_data.get_report_data(
                group_file, 
                with_sociogram
            )
            
            # Check for report-level validation errors
            if report_errors:
                raise ValueError(f"Report data validation failed for {group_file.name}: {'; '.join(report_errors)}")
            
            # Extract group identifier for reporting
            group_number_match = re.search(r'(\d+)$', group_file.stem)
            group_identifier = f"group_{group_number_match.group(0)}" if group_number_match else group_file.stem
            
            # Generate the PDF report with sociogram configuration
            enhanced_report_data = {
                **report_data, 
                "with_sociogram": with_sociogram
            }
            self._render_pdf("report", enhanced_report_data, group_file.stem, language)
            generated_reports.append(group_identifier)
            
            filtered_data = to_json_serializable(
                report_data, 
                keep=[
                    "project_title",              # Project identification
                    "members_per_group",          # Group size information
                    "sna.macro_stats_a",         # Social network analysis - macro level A
                    "sna.macro_stats_b",         # Social network analysis - macro level B
                    "sna.micro_stats_a",         # Social network analysis - micro level A
                    "sna.micro_stats_b",         # Social network analysis - micro level B
                    "sociogram.macro_stats",     # Sociogram macro statistics
                    "sociogram.micro_stats",     # Sociogram micro statistics
                    "relevant_nodes_ab.*",       # Key relationship nodes (pattern match)
                ],
            )
            
            # Add the filtered data to the collection
            all_groups_data[group_file.stem] = filtered_data
        
        json_export_path = self.abgrid_data.project_folderpath / f"{self.abgrid_data.project}_data.json"
        
        try:
            with open(json_export_path, "w", encoding='utf-8') as fout:
                json.dump(all_groups_data, fout, indent=4, ensure_ascii=False)
        except Exception as e:
            raise OSError(f"Failed to export data to JSON file {json_export_path}: {e}") from e

    @logger_decorator(("generating PDF document", "end of PDF document generation"))
    def _render_pdf(
        self, 
        doc_type: Literal["report", "answersheet"], 
        doc_data: Dict[str, Any], 
        doc_suffix: str, 
        language: str
    ) -> None:
        """
        Internal method for rendering document templates to PDF format with professional styling.

        Handles complete PDF generation pipeline from template loading through HTML rendering
        to final PDF creation. Manages template selection based on document type and language,
        data injection into templates, HTML generation, and PDF conversion using WeasyPrint
        for high-quality output with CSS styling support.
        
        This internal method propagates exceptions to decorated calling methods for proper
        error handling and event dispatching through the established error handling system.

        Args:
            doc_type: Document type determining template selection and output directory.
                     Controls which template to load and where to save generated PDF.
            doc_data: Complete data dictionary containing all variables required for
                     template rendering including project config and analytical results.
            doc_suffix: Filename suffix for generated file, typically containing group
                       identification for unique file naming across project groups.
            language: Language code for template selection determining which localized
                     template will be used for document generation.

        Raises:
            TemplateNotFound: If specified template does not exist for given language and type.
            OSError: If PDF generation or file operations fail due to system issues.
            weasyprint.HTML.Error: If HTML to PDF conversion fails during rendering process.
            jinja2.TemplateError: If template rendering fails due to syntax or variable errors.
            ValueError: If unsupported document type is specified.
            
        Output:
            Creates PDF file in appropriate subdirectory (reports/ or answersheets/) with
            sanitized filename based on project name, document type, and suffix.
            
        Note:
            Includes commented debugging section for HTML output inspection.
            Automatically sanitizes filenames to remove problematic characters.
            Validates output directory existence before attempting file creation.
            Propagates exceptions to decorated calling methods for error handling.
        """
        # Select the appropriate template based on document type
        template_path: str
        match doc_type:
            case "answersheet":
                template_path = f"./{language}/answersheet.html"
            case "report":
                template_path = f"./{language}/report_multi_page.html"
            case _:
                raise ValueError(f"Unsupported document type: {doc_type}. Supported types: 'report', 'answersheet'")
        
        # Load and render the template with provided data
        try:
            template = jinja_env.get_template(template_path)
        except Exception as e:
            raise FileNotFoundError(f"Template not found: {template_path}") from e
        
        try:
            rendered_html: str = template.render(doc_data)
        except Exception as e:
            raise ValueError(f"Template rendering failed for {template_path}: {e}") from e
        
        # Determine the output directory based on document type
        output_directory = self.abgrid_data.project_folderpath / f"{doc_type}s"
        
        # Ensure output directory exists
        if not output_directory.exists():
            raise OSError(f"Output directory does not exist: {output_directory}")
        
        # Construct and sanitize the filename
        # Remove leading/trailing underscores and ensure clean naming
        base_filename = f"{self.abgrid_data.project}_{doc_type}_{doc_suffix}"
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