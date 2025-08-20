"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
import datetime
from typing import Any

import pandas as pd

from lib.core import SYMBOLS
from lib.core.core_schemas import (
    ABGridIsolatedNodesSchema,
    ABGridRelevantNodesSchema,
)
from lib.core.core_schemas_in import (
    ABGridGroupSchemaIn,
    ABGridReportSchemaIn,
)
from lib.core.core_schemas_out import (
    ABGridGroupSchemaOut,
    ABGridReportSchemaOut,
)
from lib.core.core_sna import CoreSna
from lib.core.core_sociogram import CoreSociogram


class CoreData:
    """Processes AB-Grid data for report generation."""

    def get_group_data(self, validated_group_data: ABGridGroupSchemaIn) -> dict[str, Any]:
        """Extracts and processes group data from a validated ABGridGroupSchemaIn model.

        Args:
            validated_group_data: An instance of ABGridGroupSchemaIn containing validated group data.

        Returns:
            Dict containing the group data from the validated ABGridGroupSchemaIn model.
        """
        # Extract group data from the validated model
        group_data: dict[str, Any] = validated_group_data.model_dump()

        # Add members list to group data, using SYMBOLS for member symbols
        group_data["members"] = SYMBOLS[:group_data["members"]]

        # Validate and convert group data to ABGridGroupSchemaOut
        validated_group_data_out: ABGridGroupSchemaOut = ABGridGroupSchemaOut(**group_data)

        return validated_group_data_out.model_dump()


    def get_report_data(self, validated_survey_data: ABGridReportSchemaIn, with_sociogram: bool = False) -> dict[str, Any]:
        """Generate comprehensive report data with SNA and optional sociogram analysis.

        Args:
            validated_survey_data: Validated ABGrid report data schema instance
            with_sociogram: Whether to include sociogram analysis

        Returns:
            Dict containing complete report data with analysis results

        Notes:
            Combines SNA results with optional sociogram analysis and identifies
            relevant nodes across both analysis types
        """
        # Initialize SNA analysis class
        abgrid_sna: CoreSna = CoreSna(validated_survey_data.choices_a, validated_survey_data.choices_b)

        # Compute SNA results from group choice data
        sna_results: dict[str, Any] = abgrid_sna.get()

        # Compute Sociogram results if requested
        if with_sociogram:

            # Initialize Sociogram analysis class
            abgrid_sociogram: CoreSociogram = CoreSociogram(validated_survey_data.choices_a, validated_survey_data.choices_b)

            # Compute Sociogram results from group choice data
            sociogram_results: dict[str, Any] = abgrid_sociogram.get()

        # Get isolated and relevat nodes
        isolated_and_relevant_nodes = self._add_isolated_and_relevant_nodes(sna_results, sociogram_results, with_sociogram)

        # Prepare the comprehensive report data structure
        report_data = {
            "year": datetime.datetime.now(datetime.UTC).year,
            "project_title": validated_survey_data.project_title,
            "question_a": validated_survey_data.question_a,
            "question_b": validated_survey_data.question_b,
            "group": validated_survey_data.group,
            "group_size": len(validated_survey_data.choices_a),
            "sna": sna_results,
            "sociogram": sociogram_results if with_sociogram else None,
            **isolated_and_relevant_nodes
        }

        # Validate and convert report data to ABGridReportSchemaOut
        validated_report_data_out: ABGridReportSchemaOut = ABGridReportSchemaOut(**report_data)

        return validated_report_data_out.model_dump()

    def _add_isolated_and_relevant_nodes(
        self,
        sna_results: dict[str, Any],
        sociogram_results: dict[str, Any],
        with_sociogram: bool
    ) -> dict[str, Any]:
        """Prepare the final report output with isolated nodes, relevant nodes, and validation.

        Args:
            sna_results: Results from SNA analysis
            sociogram_results: Results from Sociogram analysis
            with_sociogram: Whether to include sociogram analysis

        Returns:
            Dict containing the validated report data output
        """
        # Extract data
        sna_isolated_a = sna_results["isolated_nodes_a"]
        sna_isolated_b = sna_results["isolated_nodes_b"]
        sna_relevant_a = sna_results["relevant_nodes_a"]
        sna_relevant_b = sna_results["relevant_nodes_b"]
        sociogram_relevant = sociogram_results["relevant_nodes"]
        sociogram_relevant_a = sociogram_relevant["a"]
        sociogram_relevant_b = sociogram_relevant["b"]

        # Prepare isolated nodes
        isolated_nodes_model: ABGridIsolatedNodesSchema = ABGridIsolatedNodesSchema(
            a=sna_isolated_a.copy()
                if isinstance(sna_isolated_a, pd.Index)
                else pd.Index(sna_isolated_a),
            b=sna_isolated_b.copy()
                if isinstance(sna_isolated_b, pd.Index)
                else pd.Index(sna_isolated_b)
        )

        # Prepare relevant nodes from SNA
        relevant_nodes_sna: dict[str, pd.DataFrame] = {
            "a": sna_relevant_a.copy()
                if isinstance(sna_relevant_a, pd.DataFrame)
                else pd.DataFrame.from_dict(sna_relevant_a, orient="index"),
            "b": sna_relevant_b.copy()
                if isinstance(sna_relevant_b, pd.DataFrame)
                else pd.DataFrame.from_dict(sna_relevant_b, orient="index")
        }

        # Prepare relevant nodes from sociogram
        if with_sociogram:
            relevant_nodes_sociogram: dict[str, pd.DataFrame] = (
                sociogram_relevant.copy()
                    if all(isinstance(x, pd.DataFrame) for x in sociogram_relevant.values())
                    else {
                        "a": pd.DataFrame.from_dict(sociogram_relevant_a, orient="index"),
                        "b": pd.DataFrame.from_dict(sociogram_relevant_b, orient="index")
                    }
            )
        else:
            relevant_nodes_sociogram = {
                "a": pd.DataFrame(),
                "b": pd.DataFrame()
            }

        # Init dictionary
        relevant_nodes: dict[str, pd.DataFrame] = {}

        # Loop through relevant_nodes keys
        for valence_type in ("a", "b"):

            # Get isolated nodes
            isolated_nodes: pd.Index = getattr(isolated_nodes_model, valence_type)

            # Concat relevant nodes from sna and sociogram
            nodes: pd.DataFrame = (
                pd.concat(
                    [
                        relevant_nodes_sna[valence_type],
                        relevant_nodes_sociogram[valence_type]
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
            relevant_nodes[valence_type] = (
                nodes
                    # Keep nodes with multiple metrics only
                    .loc[nodes["metric"].str.len() > 1, :]
                    # Add 10 more points to weight of nodes with metrics from both sna and sociogram
                    .assign(weight=nodes["weight"] + nodes["evidence_type"].str.len().gt(1).mul(10))
                    # Sort nodes by weight
                    .sort_values(by="weight", ascending=False)
            )

        # Create RelevantNodesSchema
        relevant_nodes_model: ABGridRelevantNodesSchema = ABGridRelevantNodesSchema(**relevant_nodes)

        return {
            "isolated_nodes": isolated_nodes_model.model_dump(),
            "relevant_nodes": relevant_nodes_model.model_dump()
        }
