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
from lib.abgrid_yaml import ABGridYAML
from lib.abgrid_data import ABGridData
from lib.abgrid_utils import to_json_serializable, handle_errors_decorator
from lib.abgrid_dispatcher import EventDispatcher
from lib.abgrid_logger_print import PrintLogger
from lib import EVENT_ERROR, EVENT_START, EVENT_END, SYMBOLS, jinja_env

ProjectData = Dict[str, Any]
GroupData = Dict[str, Any]
ReportData = Dict[str, Any]
ValidationErrors = List[str]
DataWithErrors = Tuple[Dict[str, Any], ValidationErrors]

# Initialize global event system for operation tracking and error handling
event_dispatcher = EventDispatcher()
event_logger = PrintLogger()

# Subscribe the print logger to all event types (start, end, error)
# The error decorator will automatically use this dispatcher for exception handling
event_logger.subscribe_to(event_dispatcher, EVENT_START, EVENT_END, EVENT_ERROR)

class ABGridMain:
    """
    Main orchestrator class for AB-Grid project management and operations.
    
    This class provides a comprehensive interface for creating and managing AB-Grid projects,
    including project initialization, group file generation, answer sheet creation, and 
    report generation with optional sociograms. It handles the complete project lifecycle
    from setup to final report delivery.
    
    All public methods are decorated with error handling that automatically captures
    exceptions and dispatches error events through the event system, providing consistent
    error reporting and logging across all operations.
    
    Attributes:
        abgrid_data (ABGridData): Core data management instance containing all project-related
                                 data, file paths, and operations for the current project.
    
    Examples:
        >>> # Initialize a new project (static method with error handling)
        >>> ABGridMain.init_project("MyProject", Path("./projects"), "en")
        
        >>> # Create main instance for existing project
        >>> main = ABGridMain("MyProject", project_folder, project_file, group_files)
        >>> main.generate_answersheets("en")  # Automatically handles errors
        >>> main.generate_reports("en", with_sociogram=True)  # Automatically handles errors
    """
    
    def __init__(
        self, 
        project: str, 
        project_folderpath: Path, 
        project_filepath: Path, 
        groups_filepaths: List[Path]
    ) -> None:
        """
        Initialize the ABGridMain instance with project configuration and file paths.

        Sets up the core data management system and prepares the instance for project
        operations. This constructor does not use the error decorator as it should
        fail fast if initialization parameters are invalid.

        Args:
            project (str): The unique name identifier for the project. Used for file
                          naming and project identification throughout the system.
            project_folderpath (Path): The root directory path where all project files
                                     and subdirectories are located or will be created.
            project_filepath (Path): The full path to the main project configuration file
                                   (typically a YAML file containing project metadata).
            groups_filepaths (List[Path]): List of file paths to group configuration files
                                         that contain individual group data and settings.

        Raises:
            FileNotFoundError: If any of the provided file paths don't exist.
            PermissionError: If the system lacks read/write permissions for the paths.
            TypeError: If any path arguments are not Path objects or strings.
            
        Note:
            This constructor creates an ABGridData instance that serves as the central
            data management hub for all project operations. Unlike other methods in this
            class, __init__ does not use error decoration to allow immediate failure
            detection during object creation.
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
    @handle_errors_decorator(event_dispatcher)
    def init_project(
        project: str, 
        project_folderpath: Path, 
        language: str
    ) -> None:
        """
        Initialize a new AB-Grid project with required directory structure and configuration.
        
        Creates a complete project structure including all necessary directories and
        generates the main project configuration file from a language-specific template.
        This method sets up everything needed to begin working with a new AB-Grid project.
        
        The method is decorated with error handling that automatically captures any
        exceptions and dispatches them as error events through the event system.
        
        Args:
            project (str): The name of the project to initialize. This will be used as
                          the project identifier and for naming the main configuration file.
            project_folderpath (Path): The directory path where the project structure
                                     will be created. Parent directories will be created
                                     if they don't exist.
            language (str): The language code for template selection (e.g., 'en', 'it', 'es').
                           This determines which language-specific templates will be used
                           for generating project files and reports.
            
        Raises:
            OSError: If directory creation fails due to insufficient permissions,
                    disk space issues, or invalid path specifications.
            FileNotFoundError: If the specified language template file doesn't exist
                             in the lib/templates/{language}/ directory.
            yaml.YAMLError: If there's an error parsing or processing the YAML template
                           file, typically due to malformed template content.
            PermissionError: If the system lacks write permissions for the target directory.
            
        Note:
            This method creates the following directory structure:
            - project_folderpath/
              - reports/           (for generated PDF reports)
              - answersheets/      (for generated answer sheet PDFs)
              - {project}.yaml     (main project configuration file)
            
            All exceptions are automatically handled by the decorator and dispatched as
            error events with detailed traceback information.
              
        Examples:
            >>> ABGridMain.init_project("TeamStudy2025", Path("./projects"), "en")
            >>> # Creates: ./projects/TeamStudy2025/ with subdirectories and config file
            >>> # Any errors are automatically logged through the event system
        """
        # Signal the start of project initialization
        event_dispatcher.dispatch({
            "event_type": EVENT_START, 
            "event_message": f"Initializing project '{project}' with language '{language}'"
        })

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

        # Signal successful completion
        event_dispatcher.dispatch({
            "event_type": EVENT_END, 
            "event_message": f"Project '{project}' successfully initialized at {project_folderpath}"
        })

    @handle_errors_decorator(event_dispatcher)
    def generate_group_inputs(
        self, 
        groups: range, 
        members_per_group: int, 
        language: str
    ) -> None:
        """
        Generate individual input configuration files for each group in the project.

        Creates YAML configuration files for each group based on a standardized template.
        Each group file contains the structure needed for data collection, including
        member identification using letter-based naming (A, B, C, etc.) and all
        necessary configuration fields for AB-Grid analysis.
        
        This method is decorated with automatic error handling that captures exceptions
        and dispatches them as error events through the event system.

        Args:
            groups (range): A range object specifying the group numbers to generate files for.
                           For example, range(1, 6) creates groups 1, 2, 3, 4, 5.
            members_per_group (int): The number of members in each group. This determines
                                   how many member identifiers (letters) will be included
                                   in each group configuration file. Must be positive.
            language (str): The language code for template selection (e.g., 'en', 'it').
                           This determines which language-specific template will be used.
            
        Raises:
            TemplateNotFound: If the group template for the specified language doesn't exist
                            in the lib/templates/{language}/ directory structure.
            OSError: If file writing operations fail due to permissions, disk space,
                    or other system-level issues.
            jinja2.TemplateError: If there are errors during template rendering,
                                typically due to malformed template syntax or missing variables.
            ValueError: If members_per_group is not positive or exceeds available SYMBOLS.
            
        Note:
            - Member identification uses consecutive letters from the SYMBOLS constant
            - Generated files are named using the pattern: {project}_g{group_number}.yaml
            - Each file contains the complete structure needed for group data collection
            - Files are saved in the main project directory alongside the project config
            - All exceptions are handled by the decorator and dispatched as error events
            
        Examples:
            >>> # Generate files for groups 1-5 with 4 members each
            >>> main.generate_group_inputs(range(1, 6), 4, "en")
            >>> # Creates: project_g1.yaml, project_g2.yaml, ..., project_g5.yaml
            >>> # Each file will have members: A, B, C, D
        """
        # Signal the start of group file generation
        event_dispatcher.dispatch({
            "event_type": EVENT_START, 
            "event_message": f"Generating {len(groups)} group input files for project '{self.abgrid_data.project}'"
        })

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
            # Signal the start of individual group file generation
            event_dispatcher.dispatch({
                "event_type": EVENT_START, 
                "event_message": f"Generating configuration for group {group_number}"
            })
            
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
          
        # Signal successful completion of all group file generation
        event_dispatcher.dispatch({
            "event_type": EVENT_END, 
            "event_message": f"Successfully generated {len(generated_files)} group input files: {', '.join(generated_files)}"
        })

    @handle_errors_decorator(event_dispatcher)
    def generate_answersheets(self, language: str) -> None:
        """
        Generate and render PDF answer sheets for all project groups.

        Creates professionally formatted PDF answer sheets for each group using project
        configuration and group-specific data. The answer sheets contain all necessary
        fields for data collection including member identification, question sections,
        and response areas formatted according to the AB-Grid methodology.
        
        This method is decorated with automatic error handling that captures exceptions
        and dispatches them as error events through the event system.

        Args:
            language (str): The language code for template selection and rendering.
                           This determines the language of labels, instructions, and
                           formatting used in the generated answer sheets.

        Raises:
            ValueError: If there are validation errors in project data or any group data.
                       This includes missing required fields, invalid data types, or
                       inconsistent configurations across project and group files.
            TemplateNotFound: If the answersheet template doesn't exist for the specified
                            language in the lib/templates/{language}/ directory.
            OSError: If PDF generation fails due to system issues, or if file saving
                    operations encounter permission or disk space problems.
            weasyprint.HTML.Error: If HTML to PDF conversion fails due to rendering issues,
                                 typically caused by malformed HTML or CSS problems.
            
        Note:
            - This method validates both project-level and group-level data before generation
            - All validation errors are collected and reported together for efficiency
            - Generated PDFs are saved in the project's answersheets/ subdirectory
            - Each answer sheet is customized with group-specific information and member lists
            - The method handles Likert scale configuration automatically based on group data
            - All exceptions are handled by the decorator and dispatched as error events
            
        Examples:
            >>> main.generate_answersheets("en")
            >>> # Generates PDF answer sheets for all groups in English
            >>> # Files saved as: answersheets/{project}_answersheet_{group_stem}.pdf
        """
        # Signal the start of answer sheet generation
        event_dispatcher.dispatch({
            "event_type": EVENT_START, 
            "event_message": f"Generating PDF answer sheets for project '{self.abgrid_data.project}'"
        })

        # Validate that group files exist
        if not self.abgrid_data.groups_filepaths:
            raise ValueError("No group files found. Please generate group inputs first.")

        # Load and validate project-level data
        event_dispatcher.dispatch({
            "event_type": EVENT_START, 
            "event_message": "Loading and validating project configuration"
        })
        
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
            # Signal processing of individual group
            event_dispatcher.dispatch({
                "event_type": EVENT_START, 
                "event_message": f"Processing group file '{group_file.name}'"
            })
            
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

            # Signal the start of individual answer sheet generation
            event_dispatcher.dispatch({
                "event_type": EVENT_START, 
                "event_message": f"Generating PDF answer sheet for group {group_number}"
            })
            
            # Generate and save the PDF answer sheet
            self._render_pdf("answersheet", sheets_data_copy, group_file.stem, language)
            generated_sheets.append(f"group_{group_number}")

        # Signal successful completion of all answer sheet generation
        event_dispatcher.dispatch({
            "event_type": EVENT_END, 
            "event_message": f"Successfully generated {len(generated_sheets)} answer sheets for groups: {', '.join(generated_sheets)}"
        })

    @handle_errors_decorator(event_dispatcher)
    def generate_reports(
        self, 
        language: str, 
        with_sociogram: bool = False
    ) -> None:
        """
        Generate comprehensive analytical reports for all project groups with data export.

        Creates detailed PDF reports for each group containing statistical analysis,
        network metrics, and optional sociogram visualizations. Additionally exports
        all analytical data to a structured JSON file for further analysis or integration
        with other tools.
        
        This method is decorated with automatic error handling that captures exceptions
        and dispatches them as error events through the event system.

        Args:
            language (str): The language code for template selection and rendering.
                           This determines the language of labels, headings, and
                           explanatory text used in the generated reports.
            with_sociogram (bool, optional): Whether to include sociogram visualizations
                                           in the reports. Defaults to False. When True,
                                           generates network diagrams showing relationship
                                           patterns and group dynamics.

        Raises:
            ValueError: If there are validation errors in report data for any group.
                       This includes missing required fields, invalid statistical data,
                       or inconsistent network analysis results.
            TemplateNotFound: If the report template doesn't exist for the specified
                            language in the lib/templates/{language}/ directory.
            OSError: If PDF generation, JSON export, or other file operations fail
                    due to system issues, permissions, or disk space problems.
            json.JSONEncodeError: If data serialization to JSON fails due to
                                non-serializable data types or circular references.
            weasyprint.HTML.Error: If HTML to PDF conversion fails during report rendering.
            
        Note:
            - Generated reports include statistical analysis, network metrics, and rankings
            - The exported JSON excludes graphics and certain bulky statistical data
            - Reports are saved in the project's reports/ subdirectory
            - JSON data is saved as {project}_data.json in the main project directory
            - Sociogram generation significantly increases processing time but provides valuable insights
            - All exceptions are handled by the decorator and dispatched as error events
            
        Examples:
            >>> # Generate basic reports without sociograms
            >>> main.generate_reports("en")
            
            >>> # Generate comprehensive reports with sociograms
            >>> main.generate_reports("en", with_sociogram=True)
            >>> # Creates: reports/{project}_report_{group_stem}.pdf, {project}_data.json
        """
        # Signal the start of report generation
        sociogram_status = "with sociograms" if with_sociogram else "without sociograms"
        event_dispatcher.dispatch({
            "event_type": EVENT_START, 
            "event_message": f"Generating reports for project '{self.abgrid_data.project}' ({sociogram_status})"
        })

        # Validate that group files exist
        if not self.abgrid_data.groups_filepaths:
            raise ValueError("No group files found. Please ensure group data is available.")

        # Initialize storage for aggregated data from all groups
        all_groups_data: Dict[str, Any] = {}
        generated_reports = []
        
        # Process each group file to generate individual reports
        for group_file in self.abgrid_data.groups_filepaths:
            
            # Signal processing of individual group
            event_dispatcher.dispatch({
                "event_type": EVENT_START, 
                "event_message": f"Processing report data for '{group_file.name}'"
            })
            
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
            
            # Signal the start of individual report generation
            event_dispatcher.dispatch({
                "event_type": EVENT_START, 
                "event_message": f"Generating PDF report for {group_identifier}"
            })
           
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
        
        # Export all collected data to JSON file for external analysis
        event_dispatcher.dispatch({
            "event_type": EVENT_START, 
            "event_message": "Exporting aggregated data to JSON file"
        })
        
        json_export_path = self.abgrid_data.project_folderpath / f"{self.abgrid_data.project}_data.json"
        
        try:
            with open(json_export_path, "w", encoding='utf-8') as fout:
                json.dump(all_groups_data, fout, indent=4, ensure_ascii=False)
        except Exception as e:
            raise OSError(f"Failed to export data to JSON file {json_export_path}: {e}") from e

        # Signal successful completion of all report generation
        event_dispatcher.dispatch({
            "event_type": EVENT_END, 
            "event_message": f"Generated {len(generated_reports)} reports and exported json data"
        })

    def _render_pdf(
        self, 
        doc_type: Literal["report", "answersheet"], 
        doc_data: Dict[str, Any], 
        doc_suffix: str, 
        language: str
    ) -> None:
        """
        Render a document template to PDF format and save to the appropriate location.

        This internal method handles the complete PDF generation pipeline from template
        loading through HTML rendering to final PDF creation. It manages template
        selection, data injection, HTML generation, and PDF conversion using WeasyPrint.
        
        This method is NOT decorated with error handling as it's an internal method
        that should propagate exceptions to its callers (which are decorated).

        Args:
            doc_type (Literal["report", "answersheet"]): The type of document to render.
                                                        Determines which template to use
                                                        and which subdirectory to save to.
            doc_data (Dict[str, Any]): Complete data dictionary containing all variables
                                     needed for template rendering. This includes project
                                     configuration, group data, and analytical results.
            doc_suffix (str): Suffix to append to the generated filename, typically
                            containing group identification (e.g., "g1_stem", "g2_stem").
            language (str): The language code for template selection, determining
                          which language-specific template will be used.

        Raises:
            TemplateNotFound: If the specified template doesn't exist for the given
                            language and document type combination.
            OSError: If PDF generation or file saving operations fail due to system
                    issues, permissions, or disk space problems.
            weasyprint.HTML.Error: If HTML to PDF conversion fails, typically due to
                                 malformed HTML, CSS issues, or rendering problems.
            jinja2.TemplateError: If template rendering fails due to syntax errors,
                                missing variables, or other template-related issues.
            
        Note:
            - Generated PDF files are saved in type-specific subdirectories (reports/ or answersheets/)
            - Filenames are automatically sanitized to remove problematic characters
            - The method includes debugging support for HTML output (commented out by default)
            - WeasyPrint handles CSS styling and professional PDF formatting automatically
            - This method propagates exceptions to decorated calling methods for proper error handling
            
        Examples:
            >>> # Internal usage - not called directly by users
            >>> self._render_pdf("report", report_data, "project_g1", "en")
            >>> # Generates: reports/project_report_project_g1.pdf
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

    def get_project_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about the current project.
        
        Returns:
            Dict[str, Any]: Dictionary containing project metadata, file paths,
                           and configuration information.
        """
        return {
            "project_name": self.abgrid_data.project,
            "project_path": str(self.abgrid_data.project_folderpath),
            "project_file": str(self.abgrid_data.project_filepath),
            "group_files": [str(path) for path in self.abgrid_data.groups_filepaths],
            "group_count": len(self.abgrid_data.groups_filepaths),
            "dispatcher_subscriptions": event_logger.get_active_subscriptions()
        }

    def cleanup(self) -> None:
        """
        Clean up resources and subscriptions.
        
        This method should be called when the ABGridMain instance is no longer needed
        to ensure proper cleanup of event subscriptions and resources.
        """
        event_logger.unsubscribe_all()
        event_dispatcher.dispatch({
            "event_type": EVENT_END, 
            "event_message": f"Cleaned up resources for project '{self.abgrid_data.project}'"
        })

    def __str__(self) -> str:
        """String representation of the ABGridMain instance."""
        return f"ABGridMain(project='{self.abgrid_data.project}', groups={len(self.abgrid_data.groups_filepaths)})"

    def __repr__(self) -> str:
        """Developer representation of the ABGridMain instance."""
        return (f"ABGridMain(project='{self.abgrid_data.project}', "
                f"project_path='{self.abgrid_data.project_folderpath}', "
                f"groups={len(self.abgrid_data.groups_filepaths)})")