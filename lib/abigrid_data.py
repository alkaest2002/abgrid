"""
Filename: abgrid_data.py
Description: Manages and processes data related to AB-Grid networks.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import string
import datetime

from pathlib import Path
from typing import Any, Tuple, Dict, Optional
from lib.abgrid_network import ABGridNetwork

class ABGridData:
    """
    Class for managing and processing project data related to AB-Grid networks.
    """

    def __init__(
        self, project: str, 
        project_folderpath: Path, 
        project_filepath: Path, 
        groups_filepaths: list[Path], 
        data_loader: Any
    ):
        """
        Initialize the ABGridData object with project and group data paths.

        Args:
            project (str): The name of the project.
            project_folderpath (Path): Path to the project folder.
            project_filepath (Path): Path to the the project's main configuration file.
            groups_filepaths (list[Path]): List of paths to group-specific data files.
            data_loader (Any): Data loading utility for reading and validating YAML configuration files.
        """
        self.project = project
        self.project_folderpath = project_folderpath
        self.project_filepath = project_filepath
        self.groups_filepaths = groups_filepaths
        self.data_loader = data_loader

    def get_answersheets_data(self) -> Tuple[Optional[Dict[str, Any]], Optional[Any]]:
        """
        Load and prepare data for generating answer sheets.

        Returns:
            Tuple[Optional[Dict[str, Any]], Optional[Any]]: A tuple containing answer sheet data or validation errors.
        """
        # Load project data
        data, validation_errors = self.data_loader.load_data("project", self.project_filepath)
        
        if data is not None:
            # Prepare answer sheet data
            answersheet_data = {
                "project": data["progetto"],
                "groups": list(range(1, data["numero_gruppi"] + 1)),
                "likert": string.ascii_uppercase[:data["numero_partecipanti_per_gruppo"]],
                "explanation": data["consegna"],
                "question_a": data["domanda_a"],
                "question_a_hint": data["domanda_a_scelte"],
                "question_b": data["domanda_b"],
                "question_b_hint": data["domanda_b_scelte"]
            }
            # Return answer sheet data
            return answersheet_data, None
        else:
            # Return validation errors if loading failed
            return None, validation_errors

    def get_report_data(self, group_filepath: Path) -> Tuple[Optional[Dict[str, Any]], Optional[Any]]:
        """
        Load and prepare data for generating a group's report.

        Args:
            group_filepath (Path): Path to the group-specific data file.

        Returns:
            Tuple[Optional[Dict[str, Any]], Optional[Any]]: A tuple containing the report data or validation errors.
        """
        # Load project data
        project_data, project_validation_errors = self.data_loader.load_data("project", self.project_filepath)
        
        # If project data was correctly loaded
        if project_data is not None:
            
            # Load group data
            group_data, group_validation_errors = self.data_loader.load_data("group", group_filepath)
            
            # If group data was correctly loaded
            if group_data is not None:
                
                # Initialize and compute network statistics
                ntw = ABGridNetwork((group_data["scelte_a"], group_data["scelte_b"]))
                ntw.compute_networks()
                
                # Prepare report data
                report_data = {
                    "project": project_data["progetto"],
                    "year": datetime.datetime.now(datetime.UTC).year,
                    "group": group_data["gruppo"],
                    "question_a": project_data["domanda_a"],
                    "question_b": project_data["domanda_b"],
                    "edges_a": ntw.edges_a,
                    "edges_b": ntw.edges_b,
                    "macro_a": ntw.macro_a,
                    "macro_b": ntw.macro_b,
                    "micro_a": ntw.micro_a.to_dict("index"),
                    "micro_b": ntw.micro_b.to_dict("index"),
                    "graph_a": ntw.graph_a,
                    "graph_b": ntw.graph_b
                }
                
                # Return report data
                return report_data, None
            else:
                # Return validation errors if group data loading failed
                return None, group_validation_errors
        else:
            # Return validation errors if project data loading failed
            return None, project_validation_errors
