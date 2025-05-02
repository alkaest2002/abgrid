import string
import datetime

from pathlib import Path
from typing import Any, Tuple, Dict, Optional
from lib.abgrid_network import ABGridNetwork

class ABGridData:
    """
    Class for managing and processing project data related to AB grid networks.
    """

    def __init__(
        self, project: str, 
        project_path: Path, 
        project_filepath: Path, 
        groups_filepaths: list[Path], 
        data_loader: Any
    ):
        """
        Initialize the ABGridData object with project and group data paths.

        Args:
            project (str): The name of the project.
            project_path (Path): Path to the project directory.
            project_filepath (Path): Path to the the project's main configuration file.
            groups_filepaths (list[Path]): List of paths to group-specific data files.
            data_loader (Any): Data loading utility for reading and validating YAML configuration files.
        """
        self.project = project
        self.project_path = project_path
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
            answersheet_data: Dict[str, Any] = {
                "title": data["titolo"],
                "groups": list(range(1, data["numero_gruppi"] + 1)),
                "likert": string.ascii_uppercase[:data["numero_partecipanti_per_gruppo"]],
                "explanation": data["consegna"],
                "ga_question": data["domandaA"],
                "ga_question_hint": data["domandaA_scelte"],
                "gb_question": data["domandaB"],
                "gb_question_hint": data["domandaB_scelte"]
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
                ntw = ABGridNetwork((group_data["scelteA"], group_data["scelteB"]))
                ntw.compute_networks()
                
                # Prepare report data
                report_data: Dict[str, Any] = {
                    "assessment_info": project_data["titolo"],
                    "group_id": group_data["IDGruppo"],
                    "ga_question": project_data["domandaA"],
                    "gb_question": project_data["domandaB"],
                    "edges_a": ntw.edges_a,
                    "edges_b": ntw.edges_b,
                    "year": datetime.datetime.now(datetime.UTC).year,
                    "ga_info": ntw.Ga_info,
                    "ga_data": ntw.Ga_data.to_dict("index"),
                    "ga_graph": ntw.graphA,
                    "gb_info": ntw.Gb_info,
                    "gb_data": ntw.Gb_data.to_dict("index"),
                    "gb_graph": ntw.graphB
                }
                
                # Return report data
                return report_data, None
            else:
                # Return validation errors if group data loading failed
                return None, group_validation_errors
        else:
            # Return validation errors if project data loading failed
            return None, project_validation_errors
