"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
import datetime
import pandas as pd
from typing import Dict,Any 

from lib.core import SYMBOLS
from lib.core.core_schemas import (
    ABGridGroupSchemaIn, 
    ABGridReportSchemaIn,
    ABGridGroupSchemaOut,
    ABGridReportSchemaOut,
    ABGridRelevantNodesSchema,
    ABGridIsolatedNodesSchema
)
from lib.core.core_sna import CoreSna, SNADict
from lib.core.core_sociogram import CoreSociogram, SociogramDict


class CoreData:
    """Processes AB-Grid data for report generation."""

    def get_group_data(self, validated_group_data_in: ABGridGroupSchemaIn) -> Dict[str, Any]:
        """Extracts and processes group data from a validated ABGridGroupSchemaIn model.

        Args:
            validated_group_data_in: An instance of ABGridGroupSchemaIn containing validated group data.

        Returns:
            Dict containing the group data from the validated ABGridGroupSchemaIn model.
        """
        # Extract group data from the validated model
        group_data: Dict[str, Any] = validated_group_data_in.model_dump()
        
        # Add members list to group data, using SYMBOLS for member symbols
        group_data["members"] = SYMBOLS[:group_data["members"]]

        # Validate and convert group data to ABGridGroupSchemaOut
        validated_group_data_out: ABGridGroupSchemaOut = ABGridGroupSchemaOut(**group_data)
        
        return validated_group_data_out.model_dump()

          
    def get_report_data(self, validated_report_data_in: ABGridReportSchemaIn, with_sociogram: bool = False) -> Dict[str, Any]:
        """Generate comprehensive report data with SNA and optional sociogram analysis.
        
        Args:
            validated_model: Validated ABGrid schema instance
            with_sociogram: Whether to include sociogram analysis
            
        Returns:
            Dict containing complete report data with analysis results
            
        Notes:
            Combines SNA results with optional sociogram analysis and identifies
            relevant nodes across both analysis types
        """
        # Initialize SNA analysis class
        abgrid_sna: CoreSna = CoreSna()
        
        # Initialize sociogram analysis class
        abgrid_sociogram: CoreSociogram = CoreSociogram()
        
        # Compute SNA results from group choice data
        sna_results: SNADict = abgrid_sna.get(validated_report_data_in.choices_a, validated_report_data_in.choices_b)
        
        # Compute sociogram results from SNA data
        sociogram_results: SociogramDict = abgrid_sociogram.get(dict(sna_results))
       
        # Prepare isolated nodes
        isolated_nodes_ab: ABGridIsolatedNodesSchema = ABGridIsolatedNodesSchema(
            a=sna_results["micro_stats_a"].loc[sna_results["micro_stats_a"]["nd"].eq(3)].index,
            b=sna_results["micro_stats_b"].loc[sna_results["micro_stats_b"]["nd"].eq(3)].index
        )

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

            # Get isolated nodes
            isolated_nodes: pd.Index = getattr(isolated_nodes_ab, valence_type)

            # Concat relevant nodes from sna and sociogram
            nodes: pd.DataFrame = (
                pd.concat(
                    [
                        relevant_nodes_ab_sna[valence_type], 
                        relevant_nodes_ab_sociogram[valence_type]
                    ]
                )
            )

            # Group nodes with same id and consolidate their values
            nodes = (
                # Omit isolated nodes first
                nodes.loc[~nodes["node_id"].isin(isolated_nodes), :]
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
            
            # Do some other calculation with nodes
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
        
        # Create RelevantNodesSchema
        relevant_nodes_model = ABGridRelevantNodesSchema(**relevant_nodes_ab)
        
        # Prepare the comprehensive report data structure
        report_data = {
            "year": datetime.datetime.now(datetime.UTC).year,
            "project_title": validated_report_data_in.project_title,
            "question_a": validated_report_data_in.question_a,
            "question_b": validated_report_data_in.question_b,
            "group": validated_report_data_in.group,
            "group_size": len(validated_report_data_in.choices_a),
            "sna": sna_results,
            "sociogram": sociogram_results if with_sociogram else None,
            "isolated_nodes_ab": isolated_nodes_ab,
            "relevant_nodes_ab": relevant_nodes_model
        }
        
        # Validate and convert report data to ABGridReportSchemaOut
        validated_report_data_out: ABGridReportSchemaOut = ABGridReportSchemaOut(**report_data)
        
        return validated_report_data_out.model_dump()