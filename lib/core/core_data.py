"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
import datetime
import gc
from typing import Any, cast

import orjson
import pandas as pd

from lib.core import SYMBOLS
from lib.core.core_schemas import (
    ABGridIsolatedNodesSchema,
    ABGridRelevantNodesSchema,
)
from lib.core.core_schemas_in import (
    ABGridGroupSchemaIn,
    ABGridReportSchemaIn,
    ABGridReportStep1SchemaIn,
    ABGridReportStep2SchemaIn,
    ABGridReportStep3SchemaIn,
)
from lib.core.core_schemas_out import (
    ABGridGroupSchemaOut,
    ABGridReportSchemaOut,
    ABGridReportStep1SchemaOut,
    ABGridReportStep2SchemaOut,
    ABGridReportStep3SchemaOut,
)
from lib.core.core_sna import CoreSna
from lib.core.core_sociogram import CoreSociogram


class CoreData:
    """Processes AB-Grid data for report generation."""

    def get_group_data(self, validated_data: ABGridGroupSchemaIn) -> dict[str, Any]:
        """Generate and validate group data.

        Args:
            validated_data: Validated data schema instance.

        Returns:
            Dict containing the group data with added member symbols.
        """
        # Get validated model dump
        group_data: dict[str, Any] = validated_data.model_dump()

        # Add members list to group data, using SYMBOLS for members
        group_data["members"] = SYMBOLS[:group_data.get("members", 8)]

        # Validate and convert group data
        group_data_out: ABGridGroupSchemaOut = ABGridGroupSchemaOut(**group_data)

        return group_data_out.model_dump()

    ##################################################################################################################
    #   SINGLE STEP REPORT
    ##################################################################################################################
    #
    #   This method handles the report generation process in a single request
    #   For high specs servers or terminal apps
    #
    ##################################################################################################################

    def get_report_data(self, validated_data: ABGridReportSchemaIn, with_sociogram: bool = False) -> dict[str, Any]:
        """Generate report data.

        Args:
            validated_data: Validated data schema instance.
            with_sociogram: Whether to include sociogram analysis.

        Returns:
            Dict containing complete report data with SNA analysis and optional sociogram results.
        """
        # Get validated model dump
        group_data: dict[str, Any] = validated_data.model_dump()

        # Initialize SNA analysis class
        abgrid_sna: CoreSna = CoreSna(validated_data.choices_a, validated_data.choices_b)

        # Compute SNA results
        sna_data: dict[str, Any] = abgrid_sna.get()

        # Delete SNA class and garbage collect
        del abgrid_sna
        gc.collect()

        # Initialize Sociogram dictionary data
        sociogram_data: dict[str, Any] = {}

        # Compute Sociogram results if requested
        if with_sociogram:
            # Initialize Sociogram analysis class
            abgrid_sociogram: CoreSociogram = CoreSociogram(validated_data.choices_a, validated_data.choices_b)

            # Compute Sociogram results
            sociogram_data = abgrid_sociogram.get()

            # Delete Sociogram class and garbage collect to free memory
            del abgrid_sociogram
            gc.collect()

        # Build final data
        final_data: dict[str, Any] = self._build_report_data_out(
            group_data,
            sna_data,
            sociogram_data,
            with_sociogram
        )

        # Validate and convert final data
        validated_report_data_out: ABGridReportSchemaOut = ABGridReportSchemaOut(**final_data)

        return validated_report_data_out.model_dump()

    ##################################################################################################################
    #   MULTI STEP REPORT
    ##################################################################################################################
    #
    #   These methods split the report generation process into three steps
    #   For low specs servers
    #
    ##################################################################################################################

    def get_multistep_step_1(self, validated_data: ABGridReportStep1SchemaIn) -> dict[str, Any]:
        """Generate step 1 data for multi-step report generation.

        Args:
            validated_data: Validated data schema instance.

        Returns:
            Dict containing group and SNA analysis data.
        """
        # Get validated model dump
        group_data: dict[str, Any] = validated_data.model_dump()

        # Initialize SNA analysis class
        abgrid_sna: CoreSna = CoreSna(validated_data.choices_a, validated_data.choices_b)

        # Compute SNA data
        sna_data: dict[str, Any] = abgrid_sna.get()

        # Delete SNA class and garbage collect to free memory
        del abgrid_sna
        gc.collect()

        # Build final data
        final_data: dict[str, Any]  = {
            "group_data": group_data,
            "sna_data": sna_data
        }

        # Validate and convert final data
        final_data_out: ABGridReportStep1SchemaOut = ABGridReportStep1SchemaOut(**final_data)

        return final_data_out.model_dump()

    def get_multistep_step_2(self, validated_data: ABGridReportStep2SchemaIn, with_sociogram: bool = False) -> dict[str, Any]:
        """Generate step 2 data for multi-step report generation.

        Args:
            validated_data: Validated Group data schema instance.
            with_sociogram: Whether to include sociogram analysis.

        Returns:
            Dict containing project related data, sna, sociogra, isolated nodes and relevant nodes.
        """
        # Get validated model dump
        data: dict[str, Any] = validated_data.model_dump()

        # Get stringified data to parse
        data_to_parse: str = cast("str", data.get("stringified_data"))

        # Decode and json-parse data
        parsed_data = orjson.loads(data_to_parse)

        # Extract group data
        group_data = parsed_data.get("group_data", {})

        # Extract SNA data
        sna_data = parsed_data.get("sna_data", {})

        # Initialize Sociogram data
        sociogram_data: dict[str, Any] = {}

        # Compute Sociogram results if requested
        if with_sociogram:
            # Initialize Sociogram analysis class
            abgrid_sociogram: CoreSociogram = CoreSociogram(
                group_data.get("choices_a", []),
                group_data.get("choices_b", [])
            )

            # Get Sociogram data
            sociogram_data = abgrid_sociogram.get()

            # Delete Sociogram class and garbage collect to free memory
            del abgrid_sociogram
            gc.collect()

        # Build final data
        final_data: dict[str, Any] = self._build_report_data_out(
            group_data,
            sna_data,
            sociogram_data,
            with_sociogram
        )

        # Validate and convert final data
        final_data_out: ABGridReportStep2SchemaOut = ABGridReportStep2SchemaOut(**final_data)

        return final_data_out.model_dump()

    def get_multistep_step3(self, validated_data: ABGridReportStep3SchemaIn) -> dict[str, Any]:
        """Generate comprehensive report data.

        Args:
            validated_data: Validated ABGrid multi-step report data schema instance.

        Returns:
            Dict containing complete report data with isolated and relevant nodes analysis.
        """
        # Get validated model dump
        data: dict[str, Any] = validated_data.model_dump()

        # Get data to decode
        data_to_parse: str = cast("str", data.get("stringified_data"))

        # Decode and json-parse data
        parsed_data = orjson.loads(data_to_parse)

        # Validate and convert report data
        final_data_out: ABGridReportStep3SchemaOut = ABGridReportStep3SchemaOut(**parsed_data)

        # Delete parsed data and garbage collect to free memory
        del parsed_data
        gc.collect()

        return final_data_out.model_dump()

    ##################################################################################################################
    #   PRIVATE METHODS
    ##################################################################################################################

    def _add_isolated_and_relevant_nodes(
        self,
        sna_data: dict[str, Any],
        sociogram_data: dict[str, Any],
        with_sociogram: bool
    ) -> dict[str, Any]:
        """Analyze and combine isolated and relevant nodes from SNA and optional sociogram data.

        This method processes nodes to identify:
        - Isolated nodes (from SNA analysis).
        - Relevant nodes (combining SNA and sociogram metrics, excluding isolated nodes).
        - Nodes with multiple metrics receive additional weight scoring.

        Args:
            sna_data: Results from SNA analysis containing isolated and relevant nodes.
            sociogram_data: Results from Sociogram analysis (may be empty if not requested).
            with_sociogram: Whether to include sociogram analysis in node relevance calculation.

        Returns:
            Dict containing:
            - isolated_nodes: Nodes with no connections in each network.
            - relevant_nodes: Nodes with multiple metrics, weighted by evidence strength.
        """
        # Extract isolated nodes data from SNA results
        sna_isolated_a = sna_data.get("isolated_nodes_a", {})
        sna_isolated_b = sna_data.get("isolated_nodes_b", {})
        sna_relevant_a = sna_data.get("relevant_nodes_a", {})
        sna_relevant_b = sna_data.get("relevant_nodes_b", {})

        # Prepare isolated nodes schema (convert to pandas Index if needed)
        isolated_nodes_model: ABGridIsolatedNodesSchema = ABGridIsolatedNodesSchema(
            a=sna_isolated_a.copy()
                if isinstance(sna_isolated_a, pd.Index)
                else pd.Index(sna_isolated_a),
            b=sna_isolated_b.copy()
                if isinstance(sna_isolated_b, pd.Index)
                else pd.Index(sna_isolated_b)
        )

        # Prepare relevant nodes from SNA (convert to pandas DataFrame if needed)
        relevant_nodes_sna: dict[str, pd.DataFrame] = {
            "a": sna_relevant_a.copy()
                if isinstance(sna_relevant_a, pd.DataFrame)
                else pd.DataFrame.from_dict(sna_relevant_a, orient="index"),
            "b": sna_relevant_b.copy()
                if isinstance(sna_relevant_b, pd.DataFrame)
                else pd.DataFrame.from_dict(sna_relevant_b, orient="index")
        }

        # Process sociogram relevant nodes if included
        if with_sociogram:
            # Extract relevant nodes from sociogram results
            sociogram_relevant = sociogram_data.get("relevant_nodes", {})
            sociogram_relevant_a = sociogram_relevant.get("a", {})
            sociogram_relevant_b = sociogram_relevant.get("b", {})

            # Prepare relevant nodes from sociogram (convert to DataFrame if needed)
            relevant_nodes_sociogram: dict[str, pd.DataFrame] = (
                sociogram_relevant.copy()
                    if all(isinstance(x, pd.DataFrame) for x in sociogram_relevant.values())
                    else {
                        "a": pd.DataFrame.from_dict(sociogram_relevant_a, orient="index"),
                        "b": pd.DataFrame.from_dict(sociogram_relevant_b, orient="index")
                    }
            )
        else:
            # Create empty DataFrames when sociogram is not included
            relevant_nodes_sociogram = {
                "a": pd.DataFrame(),
                "b": pd.DataFrame()
            }

        # Initialize final relevant nodes dictionary
        relevant_nodes: dict[str, pd.DataFrame] = {}

        # Process each network type (a and b)
        for network_type in ("a", "b"):

            # Get isolated nodes for this network type
            isolated_nodes: pd.Index = getattr(isolated_nodes_model, network_type)

            # Combine relevant nodes from SNA and sociogram
            relevant_nodes_combo: pd.DataFrame = (
                pd.concat(
                    [
                        relevant_nodes_sna.get(network_type, pd.DataFrame()),
                        relevant_nodes_sociogram.get(network_type, pd.DataFrame())
                    ]
                )
            )

            # Group nodes with same id and consolidate their metrics
            relevant_nodes_combo = (
                # Exclude isolated nodes from relevant nodes
                relevant_nodes_combo.loc[~relevant_nodes_combo["node_id"].isin(isolated_nodes), :]
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

            # Filter and weight nodes based on multiple metrics
            relevant_nodes[network_type] = (
                relevant_nodes_combo
                    # Keep only nodes with multiple metrics
                    .loc[relevant_nodes_combo["metric"].str.len() > 1, :]
                    # Add bonus weight (10 points) for nodes with evidence from multiple sources
                    .assign(weight=relevant_nodes_combo["weight"] + relevant_nodes_combo["evidence_type"].str.len().gt(1).mul(10))
                    # Sort nodes by weight (highest first)
                    .sort_values(by="weight", ascending=False)
            )

        # Create validated RelevantNodesSchema
        relevant_nodes_model: ABGridRelevantNodesSchema = ABGridRelevantNodesSchema(**relevant_nodes)

        return {
            "isolated_nodes": isolated_nodes_model.model_dump(),
            "relevant_nodes": relevant_nodes_model.model_dump()
        }

    def _build_report_data_out(self,
            group_data: dict[str, Any],
            sna_data: dict[str, Any],
            sociogram_data: dict[str, Any],
            with_sociogram: bool
            ) -> dict[str, Any]:
        """Build the final report data structure.

        Args:
            group_data: Validated group data.
            sna_data: Computed SNA analysis results.
            sociogram_data: The computed sociogram analysis results (may be empty).
            with_sociogram: Whether to include sociogram data in the final output.

        Returns:
            Dict containing the complete report data structure.
        """
        # Return the comprehensive report data structure
        return {
            "year": datetime.datetime.now(datetime.UTC).year,
            "project_title": group_data.get("project_title", ""),
            "question_a": group_data.get("question_a", ""),
            "question_b": group_data.get("question_b", ""),
            "group": group_data.get("group", ""),
            "group_size": len(group_data.get("choices_a", [])),
            "sna": sna_data,
            "sociogram": sociogram_data,
            **self._add_isolated_and_relevant_nodes(sna_data, sociogram_data, with_sociogram)
        }
