"""
Filename: abgrid_main.py
Description: Main module for managing project initialization, file generation, and report rendering.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import os
import yaml
import re
import json

from pathlib import Path
from typing import Literal, Dict, Any, List
from weasyprint import HTML

from lib import SYMBOLS, jinja_env
from lib.abgrid_yaml import ABGridYAML
from lib.abgrid_data import ABGridData
from lib.abgrid_utils import notify_decorator, to_json_serializable


class ABGridMain:
    """
    Main class for managing project initialization, file generation, and report rendering 
    for grid-based projects.
    
    This class provides a comprehensive interface for creating and managing AB-Grid projects,
    including project initialization, group file generation, answer sheet creation, and 
    report generation with optional sociograms.
    
    Attributes:
        abgrid_data (ABGridData): Instance containing all project-related data and file paths.
    """
    
    def __init__(
        self, 
        project: str, 
        project_folderpath: Path, 
        project_filepath: Path, 
        groups_filepaths: List[Path]
    ) -> None:
        """
        Initialize the ABGridMain instance with project configuration.

        Args:
            project: The name of the project.
            project_folderpath: The folder path where the project files are stored.
            project_filepath: The full path to the main project file.
            groups_filepaths: A list of Paths to group files associated with the project.

        Note:
            This method creates an ABGridData instance to manage all project-related data
            and file operations throughout the project lifecycle.
        """
        self.abgrid_data = ABGridData(
            project, project_folderpath, project_filepath, groups_filepaths, ABGridYAML()
        )

    @staticmethod
    @notify_decorator("init project")
    def init_project(project: str, project_folderpath: Path, language: str) -> None:
        """
        Initialize a new project with the required folder structure and configuration files.
        
        Creates the necessary directory structure and generates the main project configuration
        file from a language-specific template.
        
        Args:
            project: The name of the project to initialize.
            project_folderpath: The path where the project folder will be created.
            language: The language code for template selection (e.g., 'en', 'it').
            
        Raises:
            OSError: If directory creation fails due to permissions or disk space.
            FileNotFoundError: If the language template file doesn't exist.
            yaml.YAMLError: If there's an error processing the YAML template.
        """
        # Create necessary directories for the project
        os.makedirs(project_folderpath)
        os.makedirs(project_folderpath / "reports")
        os.makedirs(project_folderpath / "answersheets")
        
        # Load the project data from template
        with open(Path(f"./lib/templates/{language}/project.yaml"), 'r') as fin:
            yaml_data = yaml.safe_load(fin)
        
        # Update project data with project title
        yaml_data["project_title"] = project
        
        # Save project data to disk
        with open(project_folderpath / f"{project}.yaml", 'w') as fout:
            yaml.dump(yaml_data, fout, sort_keys=False)

    @notify_decorator("generate group inputs files")
    def generate_group_inputs(
        self, 
        groups: range, 
        members_per_group: int, 
        language: str
    ) -> None:
        """
        Generate input YAML files for each group in the project.

        Creates individual group configuration files based on a template, with each group
        containing the specified number of members identified by letters (A, B, C, etc.).

        Args:
            groups: A range object representing the group numbers to create.
            members_per_group: The number of members in each group (determines letter assignments).
            language: The language code for template selection.
            
        Raises:
            TemplateNotFound: If the group template for the specified language doesn't exist.
            OSError: If file writing fails due to permissions or disk space issues.
            
        Note:
            Member identification uses the first N letters from the SYMBOLS constant,
            where N is the value of members_per_group.
        """
        # Get group template
        group_template = jinja_env.get_template(f"/{language}/group.html")
        
        # Build a list of member letters (e.g., for five members: A, B, C, D, E)
        members_per_group_letters = SYMBOLS[:members_per_group]
        
        # Loop through each group and generate input files
        for group in groups:
            # Prepare data for the current group
            template_data = dict(group=group, members=members_per_group_letters)
            
            # Render the current group with the data (+ remove blank lines)
            rendered_group_template = group_template.render(template_data)
            rendered_group_template = "\n".join([
                line for line in rendered_group_template.split("\n") if line.strip()
            ])
                
            # Save the current group to disk
            with open(
                self.abgrid_data.project_folderpath / f"{self.abgrid_data.project}_g{group}.yaml", 
                "w"
            ) as file:
                file.write(rendered_group_template)
            
    @notify_decorator("generate answersheet file")
    def generate_answer_sheets(self, language: str) -> None:
        """
        Generate and render PDF answer sheets for all project groups.

        Creates PDF answer sheets for each group using project data and group-specific
        configurations. The sheets are saved in the project's answersheets folder.

        Args:
            language: The language code for template selection and rendering.

        Raises:
            ValueError: If there are validation errors in project data or group data.
            TemplateNotFound: If the answersheet template doesn't exist for the language.
            OSError: If PDF generation or file saving fails.
            
        Note:
            This method validates both project-level and group-level data before
            generating answer sheets. All validation errors are collected and
            reported together.
        """
        # Load sheets data
        sheets_data, sheets_data_errors = self.abgrid_data.get_project_data()

        if sheets_data_errors:
            raise ValueError(sheets_data_errors)

        # Iterate over each group file and generate answersheet
        for group_file in self.abgrid_data.groups_filepaths:
            group_data, group_data_errors = self.abgrid_data.get_group_data(group_file)

            if group_data_errors:
                raise ValueError(group_data_errors)

            # Add relevant data to sheets data
            sheets_data["group"] = int(re.search(r'(\d+)$', group_file.stem).group(0))
            sheets_data["likert"] = SYMBOLS[:len(group_data["choices_a"])]

            # Notify user
            print(f"Generating answersheet: {group_file.name}")
            
            # Persist answersheet to disk
            self.render_pdf("answersheet", sheets_data, group_file.stem, language)

    @notify_decorator("generate AB-Grid reports")
    def generate_reports(self, language: str, with_sociogram: bool = False) -> None:
        """
        Generate comprehensive reports for all project groups and export summarized data.

        Creates detailed PDF reports for each group and exports all data to a JSON file
        for further analysis. Reports can optionally include sociogram visualizations.

        Args:
            language: The language code for template selection and rendering.
            with_sociogram: Whether to include sociogram visualizations in reports.
                          Defaults to False.

        Raises:
            ValueError: If there are validation errors in report data for any group.
            TemplateNotFound: If the report template doesn't exist for the language.
            OSError: If PDF generation, JSON export, or file operations fail.
            json.JSONEncodeError: If data serialization to JSON fails.
            
        Note:
            The exported JSON data excludes graphics and certain statistical rankings
            to reduce file size and improve readability. All reports are saved in
            the project's reports folder.
        """
        all_data = {}
        
        # Iterate over each group file to generate a report
        for group_file in self.abgrid_data.groups_filepaths:
            report_data, report_errors = self.abgrid_data.get_report_data(group_file, with_sociogram)
            
            if report_errors:
                raise ValueError(report_errors)
            
            # Persist current group's report to disk
            self.render_pdf("report", {**report_data, "with_sociogram": with_sociogram}, group_file.stem, language)
        
            # Add current group data to the collection, omitting graphics for JSON
            all_data[group_file.stem] = to_json_serializable(
                report_data, 
                keys_to_omit=[
                    "sna.graph_a", 
                    "sna.graph_b",
                    "sna.network_a", 
                    "sna.network_b", 
                    "sna.adjacency_a", 
                    "sna.adjacency_b",
                    "sna.descriptives_a",
                    "sna.descriptives_b",
                    "sna.rankings_ab",
                    "sna.loc_a",
                    "sna.loc_b",
                    "sociogram.graph_ai",
                    "sociogram.graph_ii",
                ],
                keys_regex_to_omit=[
                    r"sna\.micro_stats_[a|b]\..*_rank",
                ]
            )

            # Notify user
            print(f"Generating report: {group_file.name}")                   
        
        # Persist all collected data to disk as JSON
        with open(self.abgrid_data.project_folderpath / f"{self.abgrid_data.project}_data.json", "w") as fout:
            json.dump(all_data, fout, indent=4)

    def render_pdf(
        self, 
        doc_type: Literal["report", "answersheet"], 
        doc_data: Dict[str, Any], 
        doc_suffix: str, 
        language: str
    ) -> None:
        """
        Render a document template as a PDF file and save it to the appropriate location.

        Processes the specified document type using Jinja2 templates and converts the
        rendered HTML to PDF format using WeasyPrint.

        Args:
            doc_type: The type of document to render ('report' or 'answersheet').
            doc_data: Data dictionary containing all variables needed for template rendering.
            doc_suffix: Suffix to append to the generated filename (typically group identifier).
            language: The language code for template selection.

        Raises:
            TemplateNotFound: If the specified template doesn't exist for the language.
            OSError: If PDF generation or file saving fails.
            weasyprint.HTML.Error: If HTML to PDF conversion fails.
            
        Note:
            The generated PDF files are saved in language-specific subfolders within
            the project directory. Filenames are automatically sanitized to remove
            leading or trailing underscores.
        """
        # Select and render the appropriate template for the document type
        match doc_type:
            case "answersheet":
                template = jinja_env.get_template(f"./{language}/answersheet.html")
            case "report":
                template = jinja_env.get_template(f"./{language}/report_multi_page.html")
        
        # Render the template into a string
        rendered_template = template.render(doc_data)
        
        # Define the folder path where the report will be saved
        folder_path = self.abgrid_data.project_folderpath / f"{doc_type}s"
        
        # Construct the filename, ensuring no leading/trailing underscores
        filename = re.sub("^_|_$", "", f"{self.abgrid_data.project}_{doc_type}_{doc_suffix}")
        
        # Save the rendered PDF to disk
        HTML(string=rendered_template).write_pdf(folder_path / f"{filename}.pdf")
        
        # -----------------------------------------------------------------------------------
        # FOR DEBUGGING PURPOSES - Uncomment below to save HTML files for inspection
        # -----------------------------------------------------------------------------------
        # with open(folder_path / f"{filename}.html", "w") as file:
        #     file.write(rendered_template)
        # -----------------------------------------------------------------------------------
