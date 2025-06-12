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
import jinja2

from pathlib import Path
from typing import Literal, Dict, Any
from weasyprint import HTML
from lib.abgrid_utils import to_json_serializable
from lib import SYMBOLS
from lib.abgrid_yaml import ABGridYAML
from lib.abigrid_data import ABGridData
from lib.abgrid_utils import notify_decorator

# Initialize Jinja2 environment with file system loader for templates
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(["./lib/templates"]))


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
    def init_project(project: str, project_folderpath: Path, language: str):
        """
        Initialize a new project folder structure with necessary files.
        
        Args:
            project (str): The name of the project.
            project_folderpath (Path): The path to the project folder.
            language (str): The language in which the answer sheets should be rendered.
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
        
        # Persist project data to disk
        with open(project_folderpath / f"{project}.yaml", 'w') as fout:
            yaml.dump(yaml_data, fout, sort_keys=False)

    @notify_decorator("generate group inputs files")
    def generate_group_inputs(self, groups: range, members_per_group: int, language: str):
        """
        Generate input files for each group.

        Args:
            groups (range): groups to creaate
            members_per_group (int): Number of members in each group.
            language (str): The language in which the answer sheets should be rendered.
        """

        # Get group template
        group_template = jinja_env.get_template(f"/{language}/group.html")
        
        # Build a list of member letters (e.g., for five members: A, B, C, D, E)
        members_per_group_letters = SYMBOLS[:members_per_group]
        
        # Loop through each group and generate input files
        for group in groups:
            
            # Prepare data for current group
            template_data = dict(group=group, members=members_per_group_letters)
            
            # Render current group with the data (+ remove blank lines)
            rendered_group_template = group_template.render(template_data)
            rendered_group_template = "\n".join([line for line in rendered_group_template.split("\n") if len(line) > 0])
                
            # Persist current group to disk
            with open(self.abgrid_data.project_folderpath / f"{self.abgrid_data.project}_g{group}.yaml", "w") as file:
                file.write(rendered_group_template)
            
    @notify_decorator("generate answersheet file")
    def generate_answer_sheets(self, language: str):
        """
        Generate and render answer sheets for the project using PDF format.

        Args:
            language (str): The language in which the answer sheets should be rendered.

        Raises:
            ValueError: 
                If there are errors in the answersheet data validation.
                If there are errors in report data validation for any group.
        """
        # Load sheets data
        sheets_data, sheets_data_errors = self.abgrid_data.get_project_data()

        # Notify on sheets data errors
        if sheets_data_errors:
            raise ValueError(sheets_data_errors)

        # Loop through each group file and generate answersheet
        for group_file in self.abgrid_data.groups_filepaths:

            # Load report data for the current group
            group_data, group_data_errors = self.abgrid_data.get_group_data(group_file)

            # Notify on group data errors
            if group_data_errors:
                raise ValueError(group_data_errors)

            # Add relevant data to sheets data
            sheets_data["group"] = int(re.search(r'(\d+)$', group_file.stem).group(0))
            sheets_data["likert"] = SYMBOLS[:len(group_data["choices_a"])]

            # Notify user
            print(f"generating answersheet: {group_file.name}")
            
            # Persist answersheet to disk
            self.render_pdf("answersheet", sheets_data, group_file.stem, language)

    @notify_decorator("generate AB-Grid reports")
    def generate_reports(self, language: str, with_sociogram: bool = False):
        """
        Generate and render reports for project groups, and save the summarized data 
        in a JSON format.

        Args:
            language (str): The language in which the reports should be rendered.
            with_sociogram (bool): A flag indicating whether to include sociograms in the reports.

        Raises:
            ValueError: If any errors occur during report data validation, such as missing 
            or invalid data, the process is halted and a ValueError is raised with 
            specific error information.
        """
        # Initialize data object for all reports
        all_data = {}
        
        # Loop through each group file to generate report
        for group_file in self.abgrid_data.groups_filepaths:

            # Load report data for the current group
            report_data, report_errors = self.abgrid_data.get_report_data(group_file, with_sociogram)
        
            # Notify on report data errors
            if report_errors:
                raise ValueError(report_errors)
        
            # Add current group data to the collection
            # Omit graphs from final json file
            all_data[f"{group_file.stem}"] = to_json_serializable(
                report_data, 
                keys_to_omit = [
                    "sna.graph_a", 
                    "sna.graph_b", 
                    "sociogram.graph_ic", 
                    "sociogram.graph_ac",
                ],
                keys_regex_to_omit = [
                    r"sna\.micro_stats\..*_rank",
                    r"sna\.micro_stats\..*_pctile",
                    r".*_robust_z",
                ]
            )

            # Notify user
            print(f"generating report: {group_file.name}")
        
            # Persist current group report to disk
            self.render_pdf("report", { **report_data, "with_sociogram": with_sociogram }, group_file.stem, language)
        
        # Persist all collected to disk
        with open(self.abgrid_data.project_folderpath / f"{self.abgrid_data.project}_data.json", "w") as fout:
            fout.write(json.dumps(all_data, indent=4))

    def render_pdf(self, doc_type: Literal["report", "answersheet"], doc_data: Dict[str, Any], doc_suffix: str, language: str):
        """
        Render the document template as a PDF file and save to the specified location.

        Args:
            doc_type (Literal["report", "answersheet"]): Type of document to render (either 'report' or 'answersheet').
            doc_data (dict): Data dictionary to be used for template rendering.
            doc_suffix (str): Suffix to append to the filename.
        """
        
        # Get the appropriate template for the document type
        match doc_type:
            
            # Document type is answersheet
            case "answersheet":
                template = jinja_env.get_template(f"./{language}/answersheet.html")
            
            # Document type is report and group
            case "report":
                template = jinja_env.get_template(f"./{language}/report_multi_page.html")
        
        # Render report
        rendered_template = template.render(doc_data)
        
        # Define the folder path where report will be saved
        folder_path = self.abgrid_data.project_folderpath / f"{doc_type}s"
        
        # Construct the filename, ensuring no leading/trailing underscores
        filename = re.sub("^_|_$", "", f"{self.abgrid_data.project}_{doc_type}_{doc_suffix}")
        
        # Persist report to disk
        HTML(string=rendered_template).write_pdf(folder_path / f"{filename}.pdf")
        
        # -----------------------------------------------------------------------------------
        # FOR DEBUGGING PURPOSES - Uncomment below to save HTML files for inspection
        # -----------------------------------------------------------------------------------
        # with open(folder_path / f"{filename}.html", "w") as file:
        #     file.write(rendered_template)
        # -----------------------------------------------------------------------------------
