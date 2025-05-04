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
    
    def __init__(self, project: str, project_folderpath: Path, project_filepath: Path, groups_filepaths: list[Path]):
        """
        Initialize the main handler for grid projects by setting up relevant file paths.

        Args:
            project (str): The name of the project.
            project_folderpath (Path): The folder path where the project files are stored.
            project_filepath (Path): The full path to the main project file.
            groups_filepaths (list[Path]): A list of Paths to group files that are associated with the project.

        This method sets up the initial configuration for handling grid-related projects by storing these configurations
        into the `ABGridData` data class instance. The paths provided are essential for accessing and managing project data.
        """
        # Store instantiated ABGrid data class
        self.abgrid_data = ABGridData(
            project, project_folderpath, project_filepath, groups_filepaths, ABGridYAML())

    @staticmethod
    @notify_decorator("init project")
    def init_project(project_folderpath: Path, project: str, groups: int, members_per_group: int):
        """
        Initialize a new project folder structure with necessary files.
        
        Args:
            project_folderpath (Path): The path to the project folder.
            project (str): The name of the project.
            groups (int): Number of groups in the project.
            members_per_group (int): Number of members in each group.
        """
        
        # Create necessary directories for the project
        os.makedirs(project_folderpath)
        os.makedirs(project_folderpath / "reports")
        os.makedirs(project_folderpath / "answersheets")
        
        # Generate project-specific files
        ABGridMain.generate_project_file(project_folderpath, project, groups, members_per_group)
        ABGridMain.generate_group_inputs(project_folderpath, project, groups, members_per_group)

    @staticmethod
    @notify_decorator("create project")
    def generate_project_file(project_folderpath: Path, project: str, groups: int, members_per_group: int):
        """
        Generate the main project YAML file using a template.

        Args:
            project_folderpath (Path): Folder where the project files are stored.
            project (str): The name of the project.
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
        with open(project_folderpath / f"{project}.yaml", 'w') as fout:
            yaml.dump(yaml_data, fout, sort_keys=False)

    @staticmethod
    @notify_decorator("generate group inputs files")
    def generate_group_inputs(project_folderpath: Path, project: str, groups: int, members_per_group: int):
        """
        Generate input files for each group based on a Jinja2 HTML template.

        Args:
            project_folderpath (Path): Folder where the project files are stored.
            project (str): The name of the project.
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
            with open(project_folderpath / f"{project}_gruppo_{group_id}.yaml", "w") as file:
                file.write(rendered_template)

    @notify_decorator("generate answersheet file")
    def generate_answer_sheets(self):
        """
        Generate and render answer sheets for the project using PDF format.

        Raises:
            ValueError: If there are errors in answersheet data validation.
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
            
            # Notify
            print(f"generating report: groupID {report_data['group_id']}")
        
            # Add the current group's data to the collection
            all_data[f"{self.abgrid_data.project}_gruppo_{report_data['group_id']}"] = report_data
        
            # Render the current group's report
            self.render_pdf("report", report_data, f"gruppo_{report_data['group_id']}")
        
        # Save all collected data to a JSON file
        with open(self.abgrid_data.project_folderpath / f"{self.abgrid_data.project}_data.json", "w") as fout:
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
        
        # Define the folder path where the PDF will be saved
        folder_path = self.abgrid_data.project_folderpath / doc_type
        
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
