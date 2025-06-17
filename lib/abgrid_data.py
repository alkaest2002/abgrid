"""
Filename: abgrid_data.py
Description: Manages and processes data related to AB-Grid networks.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import re
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple, Union, TypedDict

from lib.abgrid_sna import ABGridSna
from lib.abgrid_sociogram import ABGridSociogram
from lib.abgrid_sna import SNADict
from lib.abgrid_sociogram import SociogramDict

class ReportData(TypedDict, total=False):
    """
    Structure for comprehensive report data passed to Jinja templates.
    
    This TypedDict defines the expected structure of data used in report generation,
    ensuring type safety and providing clear documentation of the template context.
    """
    project_title: str
    year: int
    group: Union[int, str]
    members_per_group: int
    question_a: str
    question_b: str
    sna: SNADict
    sociogram: SociogramDict  # Optional field, only present when with_sociogram=True


class DataLoader(Protocol):
    """Protocol for data loading utilities."""
    
    def load_data(self, data_type: str, filepath: Path) -> Tuple[Optional[Dict[str, Any]], Optional[List[Dict[str, Any]]]]:
        """Load and validate data from a file.
        
        Args:
            data_type: Type of data to load ('project' or 'group')
            filepath: Path to the data file
            
        Returns:
            Tuple of (loaded_data, validation_errors)
        """
        ...


class ABGridData:
    """
    Manages and processes project data related to AB-Grid networks.
    
    This class handles loading, validation, and preparation of project and group data
    for AB-Grid network analysis, including Social Network Analysis (SNA) computations
    and sociogram generation.
    
    Attributes:
        project: The name of the project
        project_folderpath: Path to the project folder
        project_filepath: Path to the project's main configuration file
        groups_filepaths: Sorted list of paths to group-specific data files
        data_loader: Data loading utility for reading and validating YAML files
    """
    
    def __init__(
        self, 
        project: str, 
        project_folderpath: Path, 
        project_filepath: Path, 
        groups_filepaths: List[Path], 
        data_loader: DataLoader
    ) -> None:
        """
        Initialize the ABGridData object with project and group data paths.

        Args:
            project: The name of the project
            project_folderpath: The path to the project folder
            project_filepath: The path to the project's main configuration file
            groups_filepaths: A list of paths to group-specific data files
            data_loader: A data loading utility for reading and validating YAML 
                configuration files
                
        Note:
            Group file paths are automatically sorted numerically based on trailing
            digits in filenames. If numerical sorting fails, alphabetical sorting
            is used as fallback.
        """
        self.project = project
        self.project_folderpath = project_folderpath
        self.project_filepath = project_filepath
        self.data_loader = data_loader
        
        # Attempt to sort group file paths numerically based on trailing digits
        try:
            # Extract trailing digits from filename stems for numerical sorting
            self.groups_filepaths = sorted(
                groups_filepaths, 
                key=lambda x: int(re.search(r'\d+$', x.stem).group())
            )
        except (AttributeError, ValueError, TypeError):
            # Fallback to alphabetical sorting if numerical extraction fails
            self.groups_filepaths = sorted(groups_filepaths)

    def pydantic_errors_messages(self, errors: List[Dict[str, Any]]) -> str:
        """
        Format Pydantic validation error messages into a readable string.

        This method processes validation errors from Pydantic models and formats
        them into a user-friendly string representation with consistent prefixing.

        Args:
            errors: A list of error dictionaries from Pydantic validation,
                where each dictionary contains at least a 'msg' key with the
                error message

        Returns:
            A formatted string with each error message prefixed by "-->" and
            separated by newlines. Returns empty string if no errors provided.
            
        Example:
            >>> errors = [{'msg': 'field required'}, {'msg': 'invalid value'}]
            >>> formatter.pydantic_errors_messages(errors)
            '--> field required\n--> invalid value'
        """
        if not errors:
            return ""
        return "\n".join([f"--> {error.get('msg', 'Unknown error')}" for error in errors])

    def get_project_data(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Load and validate project configuration data.

        Attempts to load the project configuration file using the configured
        data loader and handles any validation errors that occur.

        Returns:
            A tuple containing:
            - First element: Project data dictionary if successful, None if failed
            - Second element: None if successful, formatted error string if failed
            
        Example:
            >>> data, error = abgrid_data.get_project_data()
            >>> if error:
            ...     print(f"Error loading project: {error}")
            >>> else:
            ...     print(f"Project title: {data['project_title']}")
        """
        project_data, validation_errors = self.data_loader.load_data(
            "project", self.project_filepath
        )

        if project_data is not None:
            return project_data, None
        else:
            error_message = self.pydantic_errors_messages(validation_errors or [])
            return None, error_message

    def get_group_data(self, group_filepath: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Load and validate group data from the specified file path.

        Args:
            group_filepath: Path object representing the file path to the group
                data file to be loaded and validated

        Returns:
            A tuple containing:
            - First element: Group data dictionary if successful, None if failed
            - Second element: None if successful, formatted error string if failed
            
        Raises:
            FileNotFoundError: If the group file does not exist (propagated from data_loader)
            
        Example:
            >>> group_path = Path("groups/group_1.yaml")
            >>> data, error = abgrid_data.get_group_data(group_path)
            >>> if error:
            ...     print(f"Error loading group: {error}")
        """
        group_data, validation_errors = self.data_loader.load_data(
            "group", group_filepath
        )

        if group_data is not None:
            return group_data, None
        else:
            error_message = self.pydantic_errors_messages(validation_errors or [])
            return None, error_message
        
    def get_report_data(
        self, 
        group_filepath: Path, 
        with_sociogram: bool = False
    ) -> Tuple[Optional[ReportData], Optional[str]]:
        """
        Load and prepare comprehensive data for generating a group's analysis report.

        This method combines project and group data, performs Social Network Analysis
        (SNA) computations, and optionally generates sociogram data for report creation.

        Args:
            group_filepath: Path to the group-specific data file
            with_sociogram: Whether to include sociogram data in the report.
                Sociogram generation can be computationally expensive for large
                networks. Defaults to False.

        Returns:
            A tuple containing:
            - First element: Complete report data dictionary if successful, None if failed
            - Second element: None if successful, formatted error string if failed
            
        Note:
            The report data includes:
            - Project metadata (title, questions)
            - Group information (number, size)
            - SNA analysis results
            - Sociogram data (if requested)
            - Current year for report dating
            
        Example:
            >>> report_data, error = abgrid_data.get_report_data(
            ...     Path("groups/group_1.yaml"), 
            ...     with_sociogram=True
            ... )
            >>> if not error:
            ...     print(f"Group {report_data['group']} has {report_data['members_per_group']} members")
        """
        # Load and validate project data
        project_data, project_validation_errors = self.data_loader.load_data(
            "project", self.project_filepath
        )

        # On error loading project data
        if project_data is None:
            error_message = self.pydantic_errors_messages(project_validation_errors or [])
            return None, error_message

        # Load and validate group data
        group_data, group_validation_errors = self.data_loader.load_data(
            "group", group_filepath
        )
        
        # On error loading group data
        if group_data is None:
            error_message = self.pydantic_errors_messages(group_validation_errors or [])
            return None, error_message

        # Initialize SNA and compute network analysis
        abgrid_sna = ABGridSna()
        sna_results = abgrid_sna.get(
            group_data["choices_a"], 
            group_data["choices_b"]
        )
        
        # Extract group number from filename (assumes format ending with digits)
        try:
            group_number = int(re.search(r'(\d+)$', group_filepath.stem).group(0))
        except (AttributeError, ValueError):
            # Fallback: use filename stem if no trailing digits found
            group_number = group_filepath.stem
        
        # Prepare the comprehensive report data structure
        report_data: ReportData = {
            "project_title": project_data["project_title"],
            "year": datetime.datetime.now(datetime.UTC).year,
            "group": group_number,
            "members_per_group": len(group_data["choices_a"]),
            "question_a": project_data["question_a"],
            "question_b": project_data["question_b"],
            "sna": sna_results,
        }

        # Optionally include sociogram data
        if with_sociogram:
            # Init sociogram class
            abgrid_sociogram = ABGridSociogram()

            # Compute sociogram
            sociogram_results = abgrid_sociogram.get(sna_results)

            # Add sociogram data to report data
            report_data["sociogram"] = sociogram_results        
        
        return report_data, None
