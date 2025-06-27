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

from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import ValidationError

from lib.core.core_schemas import ProjectSchema, GroupSchema
from lib.core.core_sna import CoreSna, SNADict
from lib.core.core_sociogram import SociogramDict, CoreSociogram

class CoreData:
    """
    Core data processing class for AB-Grid project and group data management.
    
    Provides validation, processing, and analysis of project and group data,
    integrating social network analysis and sociogram generation capabilities.
    Handles data validation using Pydantic schemas and prepares comprehensive
    report data structures.
    """
    
    def get_project_data(self, project_data: Dict[str, Any]) -> Tuple[Optional[ProjectSchema], Optional[str]]:
        """
        Validate and process project configuration data.
        
        Validates project data against the ProjectSchema and returns either
        the validated Pydantic model or detailed error information for debugging.
        
        Args:
            project_data: Raw project data dictionary to validate
        
        Returns:
            Tuple containing validated ProjectSchema instance (or None) and error string (or None)
        
        Notes:
            - Uses Pydantic validation with automatic type conversion
            - Returns formatted error messages for validation failures
            - Validated model provides attribute access and serialization methods
        """
        try:
            validated_model = ProjectSchema.model_validate(project_data)
            return validated_model, None
        except ValidationError as error:
            return None, self._get_pydantic_errors(error)

    def get_group_data(self, group_data: Dict[str, Any]) -> Tuple[Optional[GroupSchema], Optional[str]]:
        """
        Validate and process group data structure.
        
        Validates group data against the GroupSchema including choice data
        for both A and B valence types, handling optional/empty choices.
        
        Args:
            group_data: Raw group data dictionary to validate
        
        Returns:
            Tuple containing validated GroupSchema instance (or None) and error string (or None)
        
        Notes:
            - Validates group identifier and choice data structure
            - Handles None values in choice selections
            - Validated model provides attribute access and serialization methods
        """
        try:
            validated_model = GroupSchema.model_validate(group_data)
            return validated_model, None
        except ValidationError as error:
            return None, self._get_pydantic_errors(error)
        
    def get_report_data(
            self, project_data: Dict[str, Any], group_data: Dict[str, Any], with_sociogram: bool = False
        ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Generate comprehensive report data by combining project and group data with analysis results.
        
        Validates input data, performs social network analysis, optionally generates sociograms,
        and creates a complete report data structure with relevant and isolated node analysis.
        
        Args:
            project_data: Raw project configuration data to validate
            group_data: Raw group choice data to validate
            with_sociogram: Whether to include sociogram analysis in the report
        
        Returns:
            Tuple containing complete report data dictionary (or None) and error string (or None)
        
        Notes:
            - Integrates SNA and optional sociogram analysis
            - Identifies relevant nodes across both analysis types
            - Calculates isolated nodes based on network degree
            - Adds current year timestamp to report data
            - Returns dictionary for flexible template rendering
        """
        # Validate project data
        validated_project_data, error_msg = self.get_project_data(project_data)
        if error_msg:
            return None, error_msg
        
        # Validate group data
        validated_group_data, error_msg = self.get_group_data(group_data)
        if error_msg:
            return None, error_msg

        # Initialize SNA analysis class
        abgrid_sna: CoreSna = CoreSna()

        # Initialize sociogram analysis class
        abgrid_sociogram: CoreSociogram = CoreSociogram()
        
        # Compute SNA results from group choice data
        sna_results: SNADict = abgrid_sna.get(validated_group_data.choices_a, validated_group_data.choices_b)

        # Compute sociogram results from SNA data
        sociogram_results: SociogramDict = abgrid_sociogram.get(sna_results)
        
        # Prepare the comprehensive report data structure
        report_data: Dict[str, Any] = {
            "project_title": validated_project_data.project_title,
            "year": datetime.datetime.now(datetime.UTC).year,
            "group": validated_group_data.group,
            "members_per_group": len(validated_group_data.choices_a),
            "question_a": validated_project_data.question_a,
            "question_b": validated_project_data.question_b,
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
