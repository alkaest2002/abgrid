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

from typing import Any, Dict, List, Literal, Optional, Tuple, TypedDict

from pydantic import ValidationError

from lib.core.core_schemas import ProjectSchema, GroupSchema
from lib.core.core_sna import SNADict, ABGridSna
from lib.core.core_sociogram import SociogramDict, ABGridSociogram

class ProjectData(TypedDict):
    """Structure for project configuration data loaded from project files."""
    project_title: str
    explanation: str
    question_a: str
    question_a_choices: str
    question_b: str
    question_b_choices: str

class GroupData(TypedDict):
    """Structure for group data loaded from group files."""
    group: int
    choices_a: List[Dict[str, Optional[str]]]  # Values can be None (empty choices)
    choices_b: List[Dict[str, Optional[str]]]  # Values can be None (empty choices)

class ReportData(TypedDict, total=False):
    """
    Structure for comprehensive report data passed to Jinja templates.
    
    This TypedDict defines the expected structure of data used in report generation,
    ensuring type safety and providing clear documentation of the template context.
    Note: sociogram is optional (total=False) and only present when with_sociogram=True.
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
    """
    
    def get_project_data(self, project_data: ProjectData) -> Tuple[Optional[ProjectData], Optional[str]]:
        """
        """
        # Validate project data
        project_data, validation_errors = self._validate_data("project", project_data)

        # Return project data and errors
        if validation_errors:
            return None, self._get_pydantic_errors(validation_errors)
        else:
            return project_data, None

    def get_group_data(self, group_data: GroupData) -> Tuple[Optional[GroupData], Optional[str]]:
        """
        """
        # Validate group data
        group_data, validation_errors = self._validate_data("group", group_data)

        # Return None as group data and validation errors
        if validation_errors:
            return None, self._get_pydantic_errors(validation_errors)
        
        # Return group data and None as validation errors
        return group_data, None
        
    def get_report_data(
            self, project_data: ProjectData, group_data: GroupData, with_sociogram: bool = False
        ) -> Tuple[Optional[ReportData], Optional[str]]:
        """
        """
        # Validate project data
        project_data, validation_errors = self._validate_data("project", project_data)

        # Return None as project data and validation errrors
        if validation_errors:
            return None, self._get_pydantic_errors(validation_errors)
        
        # Validate group data
        group_data, validation_errors = self._validate_data("group", group_data)

        # Return None as group data and validation errrors
        if validation_errors:
            return None, self._get_pydantic_errors(validation_errors)

        # Initialize SNA analysis class
        abgrid_sna = ABGridSna()

        # Initialize sociogram analysis class
        abgrid_sociogram = ABGridSociogram()
        
        # Compute SNA results from group choice data
        sna_results = abgrid_sna.get(group_data["choices_a"], group_data["choices_b"])

        # Compute sociogram results from SNA data
        sociogram_results = abgrid_sociogram.get(sna_results)
        
        # Prepare the comprehensive report data structure
        report_data: ReportData = {
            "project_title": project_data["project_title"],
            "year": datetime.datetime.now(datetime.UTC).year,
            "group": group_data["group"],
            "members_per_group": len(group_data["choices_a"]),
            "question_a": project_data["question_a"],
            "question_b": project_data["question_b"],
            "sna": sna_results,
        }

        # Conditionally include sociogram data if requested
        if with_sociogram:
            # Add sociogram data to report data
            report_data["sociogram"] = sociogram_results

        # Get relevant nodes from both SNA and sociogram analyses
        relevant_nodes_ab_sna = sna_results["relevant_nodes_ab"].copy()
        relevant_nodes_ab_sociogram = (
            sociogram_results["relevant_nodes_ab"].copy() if with_sociogram else 
            {"a": pd.DataFrame(), "b": pd.DataFrame()}
        )
        
        # Init dict
        relevant_nodes_ab = {}

        # Loop through relevant_nodes_ab keys
        for valence_type in ("a", "b"):
            # Group nodes with same id and consolidate their values
            nodes = (
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

    def _validate_data(self, data_type: Literal["project", "group"], yaml_data: Dict[str, Any]) -> Optional[ValidationError]:
        """
        """
        if not data_type in ["project", "group"]:
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
        """
        errors = validation_error.errors()
        if not errors:
            return ""
        
        formatted_errors = []
        
        for error in errors:
            loc = error.get('loc', ())
            msg = error.get('msg', 'Unknown error')
            
            # Build location string
            if loc:
                location = '.'.join(str(part) for part in loc)
                error_msg = f"{location}: {msg}"
            else:
                error_msg = msg
            
            # Add context if provided
            if context:
                error_msg = f"[{context}] {error_msg}"
            
            # Append error to list
            formatted_errors.append(error_msg)
        
        # Join all errors into a single string
        return  "; ".join(formatted_errors)

