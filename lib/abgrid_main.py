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
import string
import json
import jinja2

from pathlib import Path
from typing import Literal, Dict, Any
from weasyprint import HTML
from lib.abgrid_yaml import ABGridYAML
from lib.abigrid_data import ABGridData
from lib.abgrid_utils import notify_decorator

# Initialize Jinja2 environment with file system loader for templates
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(["./lib/templates", "./templates"]))


class ABGridMain:
    """
    Main class to manage project initialization, file generation, and report rendering for a grid-based project.
    """
    
    def __init__(self, project: str, project_folder_path: Path, project_filepath: Path, groups_filepaths: list[Path]):
        """
        Initialize the main handler for grid projects by setting up relevant file paths.
        
        Args:
            project (str): Name of the project.
        Raises:
            FileNotFoundError: If necessary project files are missing.
        """
        # Store instantiated ABGrid data class
        self.abgrid_data = ABGridData(
            project, project_folder_path, project_filepath, groups_filepaths, ABGridYAML())

    @staticmethod
    def init_project(project: str, groups: int, members_per_group: int):
        """
        Initialize a new project folder structure with necessary files.
        
        Args:
            project (str): Name of the project.
            groups (int): Number of groups in the project.
            members_per_group (int): Number of members in each group.
        
        Raises:
            FileExistsError: If a project with the same name already exists.
        """
        # Set project folder path
        project_folder_path = Path("./data") / project
        
        # Make sure project folder does not already exist
        if project_folder_path.exists():
            raise FileExistsError(f"{project} already exists in data folder.")
        
        # Create necessary directories for the project
        os.makedirs(project_folder_path)
        os.makedirs(project_folder_path / "reports")
        os.makedirs(project_folder_path / "answersheets")
        
        # Generate project-specific files
        ABGridMain.generate_project_file(project_folder_path, project, groups, members_per_group)
        ABGridMain.generate_group_inputs(project_folder_path, project, groups, members_per_group)

    @staticmethod
    @notify_decorator("create project")
    def generate_project_file(project_folder_path: Path, project: str, groups: int, members_per_group: int):
        """
        Generate the main project YAML file using a template.

        Args:
            project_folder_path (Path): Directory where the project files are stored.
            project (str): Name of the project.
            groups (int): Number of groups in the project.
            members_per_group (int): Number of members in each group.
        """
        # Load the project YAML template
        with open(Path("./lib/templates/project.yaml"), 'r') as fin:
            yaml_data = yaml.safe_load(fin)
        
        # Update YAML data with project-specific information
        yaml_data["titolo"] = project
        yaml_data["numero_gruppi"] = groups
        yaml_data["numero_partecipanti_per_gruppo"] = members_per_group
        
        # Write the updated project YAML data to a file
        with open(project_folder_path / f"{project}.yaml", 'w') as fout:
            yaml.dump(yaml_data, fout, sort_keys=False)

    @staticmethod
    @notify_decorator("generate group inputs files")
    def generate_group_inputs(project_folder_path: Path, project: str, groups: int, members_per_group: int):
        """
        Generate input files for each group based on a Jinja2 HTML template.

        Args:
            project_folder_path (Path): Directory where the project files are stored.
            project (str): Name of the project.
            groups (int): Number of groups in the project.
            members_per_group (int): Number of members in each group.
        """
        # Build a list of member letters (e.g., for five members: A, B, C, D, E)
        members_per_group_letters = string.ascii_uppercase[:members_per_group]
        
        # Get the group HTML template
        template = jinja_env.get_template("group.html")
        
        # Loop through each group and generate input files
        for group_id in range(1, groups + 1):
            
            # Prepare data for the template
            template_data = dict(groupId=group_id, members=members_per_group_letters)
            
            # Render the current group template with the data
            rendered_template = template.render(template_data)
            
            # Remove any blank lines from rendered template
            rendered_template = "\n".join([line for line in rendered_template.split("\n") if len(line) > 0])
            
            # Write the rendered template to a file
            with open(project_folder_path / f"{project}_gruppo_{group_id}.yaml", "w") as file:
                file.write(rendered_template)

    @notify_decorator("generate answersheet file")
    def generate_answer_sheets(self):
        """
        Generate and render answer sheets for the project using PDF format.
        """
        # Load answer sheet data
        sheets_data, sheets_errors = self.abgrid_data.get_answersheets_data()
        
        # Notify on error
        if sheets_errors:
            raise ValueError(sheets_errors)
        
        # Render answer sheets as PDF
        self.render_pdf("answersheet", sheets_data, "")

    @notify_decorator("generate AB-Grid reports")
    def generate_reports(self):
        """
        Generate and render reports for the project groups, and save the data in a JSON format.
        
        Raises:
            FileNotFoundError: If any group file is missing.
            ValueError: If there are errors in report data validation.
        """
        # Initialize data object for all reports
        all_data = {}
        
        # Loop through each group file to generate report
        for group_file in self.abgrid_data.groups_filepaths:
        
            # Load report data for the current group
            report_data, report_errors = self.abgrid_data.get_report_data(group_file)
        
            # Raise error if validation fails
            if report_errors:
                raise ValueError(report_errors)
        
            # Add the current group's data to the collection
            all_data[f"{self.abgrid_data.project}_gruppo_{report_data['group_id']}"] = report_data
        
            # Render the current group's report
            self.render_pdf("report", report_data, f"gruppo_{report_data['group_id']}")
        
        # Save all collected data to a JSON file
        with open(Path("./data") / self.abgrid_data.project / f"{self.abgrid_data.project}_data.json", "w") as fout:
            fout.write(json.dumps(all_data, indent=4))

    def render_pdf(self, doc_type: Literal["report", "answersheet"], doc_data: Dict[str, Any], doc_suffix: str):
        """
        Render the document template as a PDF file and save to the specified location.

        Args:
            doc_type (Literal["report", "answersheet"]): Type of document to render (either 'report' or 'answersheet').
            doc_data (dict): Data dictionary to be used for template rendering.
            doc_suffix (str): Suffix to append to the filename.
        """
        # Get the appropriate template for the document type
        template = jinja_env.get_template(f"{doc_type}.html")
        
        # Render the template with the provided data
        rendered_template = template.render(doc_data)
        
        # Define the directory path where the PDF will be saved
        folder_path = Path(f"./data/{self.abgrid_data.project}/{doc_type}")
        
        # Construct the filename, ensuring no leading/trailing underscores
        filename = re.sub("^_|_$", "", f"{self.abgrid_data.project}_{doc_type}_{doc_suffix}")
        
        # Convert the rendered HTML template to a PDF and save it
        HTML(string=rendered_template).write_pdf(folder_path / f"{filename}.pdf")
        
        # -----------------------------------------------------------------------------------
        # FOR DEBUGGING PURPOSES - Uncomment below to save HTML files for inspection
        # -----------------------------------------------------------------------------------
        # with open(folder_path / f"{filename}.html", "w") as file:
        #     file.write(rendered_template)
        # -----------------------------------------------------------------------------------
