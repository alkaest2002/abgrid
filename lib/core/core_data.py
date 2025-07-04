"""
Filename: core_data.py

Description: Manages and processes data related to AB-Grid networks.

Author: Pierpaolo Calanna

Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
import datetime
import pandas as pd
from typing import Any, Dict, Optional, TypedDict

from lib.core.core_schemas import ABGridReportSchema
from lib.core.core_sna import CoreSna, SNADict
from lib.core.core_sociogram import CoreSociogram, SociogramDict

class RelevantNodesDict(TypedDict):
    """Dictionary structure for relevant nodes analysis results."""
    a: pd.DataFrame  # Positive relevance nodes DataFrame
    b: pd.DataFrame  # Negative relevance nodes DataFrame

class IsolatedNodesDict(TypedDict):
    """Dictionary structure for isolated nodes by network type."""
    a: pd.Index  # Isolated nodes from network A
    b: pd.Index  # Isolated nodes from network B


class ReportDataDict(TypedDict):
    """
    Complete type definition for report data structure returned by get_report_data().
    
    Contains comprehensive analysis results including project metadata, network analysis,
    sociogram data (optional), relevant nodes identification, and isolated nodes detection.
    """
    year: int  # Current year when report was generated
    project_title: str  # Title of the AB-Grid project
    question_a: str  # Text of question A from the survey
    question_b: str  # Text of question B from the survey
    group: int  # Group identifier (1-50)
    members_per_group: int  # Number of participants in the group
    sna: SNADict  # Complete social network analysis results
    sociogram: Optional[SociogramDict]  # Sociogram analysis results (None if not requested)
    relevant_nodes_ab: RelevantNodesDict  # Most/least relevant nodes for positive/negative outcomes
    isolated_nodes_ab: IsolatedNodesDict  # Nodes with no connections in each network


class CoreData:
    """Processes AB-Grid data for report generation."""
          
    def get_report_data(self, validated_model: ABGridReportSchema, with_sociogram: bool = False) -> Dict[str, Any]:
        """Generate comprehensive report data with SNA and optional sociogram analysis.
        
        Args:
            validated_model: Validated ABGrid schema instance
            with_sociogram: Whether to include sociogram analysis
            
        Returns:
            Dictionary containing complete report data with analysis results
            
        Notes:
            Combines SNA results with optional sociogram analysis and identifies
            relevant nodes across both analysis types
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

        # Add sociogram data to report data, if requested
        report_data["sociogram"] = sociogram_results if with_sociogram else None

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
        
        return report_data
