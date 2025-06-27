"""
Filename: abgrid_data.py
Description: Manages and processes data related to AB-Grid networks, including project and group data
loading, validation, and preparation for social network analysis and report generation.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import datetime
import pandas as pd

from typing import Any, Dict, List, Literal, Optional, Tuple, TypedDict, Union

from pydantic import ValidationError

from lib.core.core_schemas import ProjectSchema, GroupSchema
from lib.core.core_sna import CoreSna, SNADict
from lib.core.core_sociogram import SociogramDict, CoreSociogram

class ProjectData(TypedDict):
    """
    TypedDict representing validated project configuration data.
    
    Contains essential project metadata including title, explanations, and question definitions
    for both A and B valence types used in AB-Grid analysis.
    """
    project_title: str
    explanation: str
    question_a: str
    question_a_choices: str
    question_b: str
    question_b_choices: str

class GroupData(TypedDict):
    """
    TypedDict representing validated group data structure.
    
    Contains group identifier and choice data for both A and B valence types,
    where choices can include None values for empty selections.
    """
    group: int
    choices_a: List[Dict[str, Optional[str]]]  # Values can be None (empty choices)
    choices_b: List[Dict[str, Optional[str]]]  # Values can be None (empty choices)

class ReportData(TypedDict, total=False):
    """
    TypedDict representing comprehensive report data structure.
    
    Contains all data required for report generation including project metadata,
    social network analysis results, optional sociogram data, and node analysis.
    Uses total=False to allow optional fields like sociogram data.
    """
    project_title: str
    year: int
    group: int
    members_per_group: int
    question_a: str
    question_b: str
    sna: SNADict
    sociogram: SociogramDict  # Optional present when with_sociogram=True
    relevant_nodes_ab: Dict[str, pd.DataFrame]
    isolated_nodes_ab: Dict[str, pd.Index]

class CoreData:
    """
    Core data processing class for AB-Grid project and group data management.
    
    Provides validation, processing, and analysis of project and group data,
    integrating social network analysis and sociogram generation capabilities.
    Handles data validation using Pydantic schemas and prepares comprehensive
    report data structures.
    """
    
    def get_project_data(self, project_data: Dict[str, Any]) -> Tuple[Optional[ProjectData], Optional[str]]:
        """
        Validate and process project configuration data.
        
        Validates project data against the ProjectSchema and returns either
        the validated data or detailed error information for debugging.
        
        Args:
            project_data: Raw project data dictionary to validate
        
        Returns:
            Tuple containing validated ProjectData (or None) and error string (or None)
        
        Notes:
            - Uses Pydantic validation through ProjectSchema
            - Returns formatted error messages for validation failures
        """
        # Validate project data
        validated_data, validation_errors = self._validate_data("project", project_data)

        # Return project data and errors
        if validation_errors:
            return None, self._get_pydantic_errors(validation_errors)
        else:
            return validated_data, None

    def get_group_data(self, group_data: Dict[str, Any]) -> Tuple[Optional[GroupData], Optional[str]]:
        """
        Validate and process group data structure.
        
        Validates group data against the GroupSchema including choice data
        for both A and B valence types, handling optional/empty choices.
        
        Args:
            group_data: Raw group data dictionary to validate
        
        Returns:
            Tuple containing validated GroupData (or None) and error string (or None)
        
        Notes:
            - Validates group identifier and choice data structure
            - Handles None values in choice selections
        """
        # Validate group data
        validated_data, validation_errors = self._validate_data("group", group_data)

        # Return None as group data and validation errors
        if validation_errors:
            return None, self._get_pydantic_errors(validation_errors)
        
        # Return group data and None as validation errors
        return validated_data, None
        
    def get_report_data(
            self, project_data: Dict[str, Any], group_data: Dict[str, Any], with_sociogram: bool = False
        ) -> Tuple[Optional[ReportData], Optional[str]]:
        """
        Generate comprehensive report data by combining project and group data with analysis results.
        
        Validates input data, performs social network analysis, optionally generates sociograms,
        and creates a complete report data structure with relevant and isolated node analysis.
        
        Args:
            project_data: Raw project configuration data to validate
            group_data: Raw group choice data to validate
            with_sociogram: Whether to include sociogram analysis in the report
        
        Returns:
            Tuple containing complete ReportData (or None) and error string (or None)
        
        Notes:
            - Integrates SNA and optional sociogram analysis
            - Identifies relevant nodes across both analysis types
            - Calculates isolated nodes based on network degree
            - Adds current year timestamp to report data
        """
        # Validate project data
        validated_project_data, validation_errors = self._validate_data("project", project_data)

        # Return None as project data and validation errrors
        if validation_errors:
            return None, self._get_pydantic_errors(validation_errors)
        
        # Validate group data
        validated_group_data, validation_errors = self._validate_data("group", group_data)

        # Return None as group data and validation errrors
        if validation_errors:
            return None, self._get_pydantic_errors(validation_errors)

        # Initialize SNA analysis class
        abgrid_sna: CoreSna = CoreSna()

        # Initialize sociogram analysis class
        abgrid_sociogram: CoreSociogram = CoreSociogram()
        
        # Compute SNA results from group choice data
        sna_results: SNADict = abgrid_sna.get(validated_group_data["choices_a"], validated_group_data["choices_b"])

        # Compute sociogram results from SNA data
        sociogram_results: SociogramDict = abgrid_sociogram.get(sna_results)
        
        # Prepare the comprehensive report data structure
        report_data: ReportData = {
            "project_title": validated_project_data["project_title"],
            "year": datetime.datetime.now(datetime.UTC).year,
            "group": validated_group_data["group"],
            "members_per_group": len(validated_group_data["choices_a"]),
            "question_a": validated_project_data["question_a"],
            "question_b": validated_project_data["question_b"],
            "sna": sna_results,
        }

        # Conditionally include sociogram data if requested
        if with_sociogram:
            # Add sociogram data to report data
            report_data["sociogram"] = sociogram_results

        # Get relevant nodes from both SNA and sociogram analyses
        relevant_nodes_ab_sna: Dict[str, pd.DataFrame] = sna_results["relevant_nodes_ab"].copy()
        relevant_nodes_ab_sociogram: Dict[str, pd.DataFrame] = (
            sociogram_results["relevant_nodes_ab"].copy() if with_sociogram else 
            {"a": pd.DataFrame(), "b": pd.DataFrame()}
        )
        
        # Init dict
        relevant_nodes_ab: Dict[str, pd.DataFrame] = {}

        # Loop through relevant_nodes_ab keys
        for valence_type in ("a", "b"):
            # Group nodes with same id and consolidate their values
            nodes: pd.DataFrame = (
                pd.concat(
                    [
                        relevant_nodes_ab_sna[valence_type], 
                        relevant_nodes_ab_sociogram[valence_type]
                    ]
                )
                .groupby(by="node_id")
                    .aggregate({
                        "metric": list,
                        "value": list,
                        "original_rank": list,
                        "recomputed_rank": list,
                        "weight": "sum",
                        "evidence_type": lambda x: list(set(x)),
                    })
            )
            nodes = (
                nodes
                    # Keep nodes with multiple metrics only
                    .loc[nodes["metric"].str.len() > 1, :]
                    # Add 10 more points to weight of nodes with metrics from both sna and sociogram
                    .assign(weight=nodes["weight"] + nodes["evidence_type"].str.len().gt(1).mul(10))
                    # Sort nodes by weight
                    .sort_values(by="weight", ascending=False)
            )
            
            # Add relevant nodes of specific valence type to relevant_nodes_ab
            relevant_nodes_ab[valence_type] = nodes
            

        # Add relevant_nodes_ab to report data
        report_data["relevant_nodes_ab"] = relevant_nodes_ab

        # Add isolated nodes to report data
        report_data["isolated_nodes_ab"] = {
            "a": sna_results["micro_stats_a"].loc[sna_results["micro_stats_a"]["nd"].eq(3)].index,
            "b": sna_results["micro_stats_b"].loc[sna_results["micro_stats_b"]["nd"].eq(3)].index
        }
        
        return report_data, None

    def _validate_data(self, data_type: Literal["project", "group"], yaml_data: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[ValidationError]]:
        """
        Validate data using appropriate Pydantic schema based on data type.
        
        Internal method that applies the correct validation schema (ProjectSchema or GroupSchema)
        to the provided data and returns validated data or validation errors.
        
        Args:
            data_type: Type of data to validate ("project" or "group")
            yaml_data: Raw data dictionary to validate
        
        Returns:
            Tuple containing validated data dict (or None) and ValidationError (or None)
        
        Notes:
            - Raises ValueError for unsupported data types
            - Uses Pydantic model validation and returns model_dump() output
        """
        if data_type not in ["project", "group"]:
            raise ValueError(f"{data_type} cannot be validated")
        try:
            if data_type == "project":
                return ProjectSchema.model_validate(yaml_data).model_dump(), None
            if data_type == "group":
                return GroupSchema.model_validate(yaml_data).model_dump(), None
        except ValidationError as error:
            return None, error

    def _get_pydantic_errors(self, validation_error: ValidationError, context: str = "") -> str:
        """
        Format Pydantic validation errors into human-readable error messages.
        
        Converts ValidationError objects into formatted strings that provide
        clear information about field locations and error descriptions.
        
        Args:
            validation_error: Pydantic ValidationError object containing error details
            context: Optional context string to prepend to error messages
        
        Returns:
            Formatted string containing all validation errors separated by semicolons
        
        Notes:
            - Builds location paths using dot notation for nested fields
            - Supports optional context prefixes for error categorization
            - Returns empty string if no errors are present
        """
        errors: List[Dict[str, Any]] = validation_error.errors()
        if not errors:
            return ""
        
        formatted_errors: List[str] = []
        
        for error in errors:
            loc: Tuple[Union[str, int], ...] = error.get('loc', ())
            msg: str = error.get('msg', 'Unknown error')
            
            # Build location string
            if loc:
                location: str = '.'.join(str(part) for part in loc)
                error_msg: str = f"{location}: {msg}"
            else:
                error_msg = msg
            
            # Add context if provided
            if context:
                error_msg = f"[{context}] {error_msg}"
            
            # Append error to list
            formatted_errors.append(error_msg)
        
        # Join all errors into a single string
        return "; ".join(formatted_errors)
