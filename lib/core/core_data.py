"""
Filename: core_data.py
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

from lib.core.core_schemas import ABGridSchema
from lib.core.core_sna import CoreSna, SNADict
from lib.core.core_sociogram import CoreSociogram, SociogramDict
from lib.core.core_schemas import ValidationException

class CoreData:
    """
    Core data processing class for AB-Grid project and group data management.
    
    Provides validation, processing, and analysis of project and group data,
    integrating social network analysis and sociogram generation capabilities.
    Handles data validation using Pydantic schemas and prepares comprehensive
    report data structures.
    """
    
    def validate_input_data(self, data: Dict[str, Any]) -> Tuple[Optional[ABGridSchema], Optional[str]]:
        """
        Validate input data using Pydantic schema.
        
        Args:
            data: Raw data dictionary to validate
            
        Returns:
            Tuple containing validated ABGridSchema model (or None) and error string (or None)
            
        Raises:
            ValidationError: If data doesn't match schema requirements
        """
        try:
            validated_model = ABGridSchema.model_validate(data)
            return validated_model, None
        except ValidationException as error:
            return None, self._get_pydantic_errors(error)
          
    def get_data(self, validated_model: ABGridSchema, with_sociogram: bool = False) -> Dict[str, Any]:
        """
        Generate comprehensive report data by combining validated data with analysis results.
        
        Performs social network analysis, optionally generates sociograms,
        and creates a complete report data structure with relevant and isolated node analysis.
        
        Args:
            validated_model: Pre-validated ABGridSchema model
            with_sociogram: Whether to include sociogram analysis in the report
        
        Returns:
            Complete report data dictionary ready for template rendering
        
        Notes:
            - Integrates SNA and optional sociogram analysis
            - Identifies relevant nodes across both analysis types
            - Calculates isolated nodes based on network degree
            - Adds current year timestamp to report data
        """
        # Initialize SNA analysis class
        abgrid_sna: CoreSna = CoreSna()

        # Initialize sociogram analysis class
        abgrid_sociogram: CoreSociogram = CoreSociogram()
        
        # Compute SNA results from group choice data
        sna_results: SNADict = abgrid_sna.get(validated_model.choices_a, validated_model.choices_b)

        # Compute sociogram results from SNA data
        sociogram_results: SociogramDict = abgrid_sociogram.get(sna_results)
        
        # Prepare the comprehensive report data structure
        report_data: Dict[str, Any] = {
            "year": datetime.datetime.now(datetime.UTC).year,
            "project_title": validated_model.project_title,
            "question_a": validated_model.question_a,
            "question_b": validated_model.question_b,
            "group": validated_model.group,
            "members_per_group": len(validated_model.choices_a),
            "sna": sna_results,
        }

        # Add sociogram data to report data
        report_data["sociogram"] = sociogram_results if with_sociogram else None

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
        
        return report_data

    def _get_pydantic_errors(self, validation_exception: ValidationException, context: str = "") -> str:
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
        # Init formatted errors
        formatted_errors: List[str] = []
        
        # Loop through errors
        for error in validation_exception.errors:  
            
            # Get location of error
            location = error.get('location', None)
            
            # Get error message
            error_message = error.get('error_message', 'Unknown error')
            
            # Add error location if provided
            if location:
                error_msg: str = f"{location}: {error_message}"
            
            # Add error context if provided
            if context:
                error_msg = f"[{context}] {error_msg}"
            
            # Append error to list
            formatted_errors.append(error_msg)
        
        # Join all errors into a single string
        return "\n".join(formatted_errors)
