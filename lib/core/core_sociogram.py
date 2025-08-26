"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import asyncio
import re
from typing import TYPE_CHECKING, Any, Literal

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from lib.core import CM_TO_INCHES
from lib.core.core_schemas import ABGridSociogramSchema
from lib.core.core_utils import (
    compute_descriptives,
    figure_to_base64_svg,
    run_in_executor,
    unpack_network_edges,
    unpack_network_nodes,
)


if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


class CoreSociogram:
    """Analyzes and visualizes social networks by constructing sociometric components including macro/micro statistics, node rankings, and circular polar graph visualizations.

    This class provides comprehensive sociometric analysis capabilities including:
    - Macro-level network statistics (cohesion and conflict indices)
    - Micro-level node statistics (centrality measures, sociometric status classification)
    - Node rankings based on various centrality metrics and status
    - Identification of most/least relevant nodes for positive/negative outcomes
    - Circular polar visualization of activity and integration index distributions with radial arrangement

    Attributes:
        packed_edges_a: List of packed edge data for positive relationships (network A).
        packed_edges_b: List of packed edge data for negative relationships (network B).
        sna: Social network analysis data containing NetworkX graphs and adjacency matrices.
        sociogram: Dictionary containing all computed sociogram data and visualizations.
    """
    def __init__(self,
            packed_edges_a: list[dict[str, str | None]],
            packed_edges_b: list[dict[str, str | None]]) -> None:
        """Initialize the CoreSociogram instance with packed edge data for both networks.

        Args:
            packed_edges_a: List of dictionaries containing edge data for positive relationships.
                Each dictionary should contain source and target node identifiers.
            packed_edges_b: List of dictionaries containing edge data for negative relationships.
                Each dictionary should contain source and target node identifiers.

        Returns:
            None.
        """
        # Store packed edges for later use
        self.packed_edges_a = packed_edges_a
        self.packed_edges_b = packed_edges_b

        # Initialize social network analysis dictionary
        self.sna: dict[str, Any] = {}

        # Initialize sociogram results dictionary
        self.sociogram: dict[str, Any] = {}

    def get(self) -> dict[str, Any]:
        """Compute comprehensive sociogram analysis and return validated results.

        Runs the complete sociogram analysis pipeline asynchronously, then validates
        the results using Pydantic schema validation before returning.

        Returns:
            A validated dictionary containing complete sociogram analysis with the following structure:
                - "macro_stats": Series of network-level cohesion and conflict indices
                - "micro_stats": DataFrame of individual-level statistics and ranks for each node
                - "descriptives": DataFrame with aggregated descriptive statistics
                - "rankings": Dictionary with sorted node rankings by centrality metrics and status
                - "graph_ii": Base64-encoded SVG string of integration index polar visualization
                - "graph_ai": Base64-encoded SVG string of activity index polar visualization
                - "relevant_nodes": Dictionary with most/least relevant nodes for positive/negative outcomes
        """
        # Get data
        data = asyncio.run(self._get_async())

        # Validate data
        validated_data = ABGridSociogramSchema(**data)

        return validated_data.model_dump()


    ##################################################################################################################
    #   PRIVATE METHODS
    ##################################################################################################################

    async def _get_async(self) -> dict[str, Any]:
        """Asynchronously compute and store comprehensive sociogram analysis from social network data.

        Uses concurrent execution where possible to optimize performance while respecting
        data dependencies between different computations.

        Returns:
            A dictionary containing complete sociogram analysis with all computed metrics,
            statistics, rankings, and visualizations.
        """
        # STEP 1: Create networks (must happen first)
        await run_in_executor(self._create_networks)

        # STEP 2: Concurrent computation using TaskGroups

        # Batch 1: Independent computations that only depend on step 1
        async with asyncio.TaskGroup() as tg:
            macro_stats_task = tg.create_task(
                run_in_executor(self._compute_macro_stats)
            )
            micro_stats_task = tg.create_task(
                run_in_executor(self._compute_micro_stats)
            )

        # Store batch 1 results
        self.sociogram["macro_stats"] = macro_stats_task.result()
        self.sociogram["micro_stats"] = micro_stats_task.result()

        # Batch 2: Computations that depend on micro_stats
        async with asyncio.TaskGroup() as tg:
            descriptives_task = tg.create_task(
                run_in_executor(self._compute_descriptives)
            )
            rankings_task = tg.create_task(
                run_in_executor(self._compute_rankings)
            )
            graph_ai_task = tg.create_task(
                run_in_executor(self._create_graph, "ai")
            )
            graph_ii_task = tg.create_task(
                run_in_executor(self._create_graph, "ii")
            )

        # Store batch 2 results
        self.sociogram["descriptives"] = descriptives_task.result()
        self.sociogram["rankings"] = rankings_task.result()
        self.sociogram["graph_ai"] = graph_ai_task.result()
        self.sociogram["graph_ii"] = graph_ii_task.result()

        # Batch 3: Computations that depend on both micro_stats and rankings
        async with asyncio.TaskGroup() as tg:
            relevant_nodes_task = tg.create_task(
                run_in_executor(self._compute_relevant_nodes)
            )

        # Store batch 3 results
        self.sociogram["relevant_nodes"] = relevant_nodes_task.result()

        return self.sociogram

    def _get_sync(self) -> dict[str, Any]:
        """Synchronously compute comprehensive sociogram analysis from social network data.

        Executes all computation steps sequentially without async concurrency.
        Used internally as a fallback synchronous implementation.

        Returns:
            A dictionary containing complete sociogram analysis with all computed metrics,
            statistics, rankings, and visualizations.
        """
        # Create networks first
        self._create_networks()

        # Compute all sociogram components in sequence
        self.sociogram["macro_stats"] = self._compute_macro_stats()
        self.sociogram["micro_stats"] = self._compute_micro_stats()
        self.sociogram["descriptives"] = self._compute_descriptives()
        self.sociogram["rankings"] = self._compute_rankings()
        self.sociogram["relevant_nodes"] = self._compute_relevant_nodes()
        self.sociogram["graph_ai"] = self._create_graph("ai")
        self.sociogram["graph_ii"] = self._create_graph("ii")

        return self.sociogram

    def _create_networks(self) -> None:
        """Create NetworkX directed graphs from packed edge data and generate adjacency matrices.

        Unpacks the stored edge data to create separate networks for positive (A) and negative (B)
        relationships, adds any isolated nodes, and generates pandas adjacency matrices for
        mathematical operations.
        """
        # Set network data
        network_edges: list[tuple[Literal["a", "b"], Any]] = [
            ("a", self.packed_edges_a),
            ("b", self.packed_edges_b)
        ]

        # Store network A and B nodes and edges
        for network_type, packed_edges in network_edges:
            self.sna[f"nodes_{network_type}"] = unpack_network_nodes(packed_edges)
            self.sna[f"edges_{network_type}"] = unpack_network_edges(packed_edges)
            self.sna[f"network_{network_type}"] = nx.DiGraph(self.sna[f"edges_{network_type}"])

        # Add isolated nodes to networks A and B
        network_data: list[tuple[Literal["a", "b"], Any, Any]] = [
            ("a", self.sna["network_a"], self.sna["nodes_a"]),
            ("b", self.sna["network_b"], self.sna["nodes_b"])
        ]

        for network_type, network, nodes in network_data:
            # Find isolated nodes
            isolated_nodes: set[str] = set(network).symmetric_difference(set(nodes))

            # Add isolated nodes to current network
            network.add_nodes_from(isolated_nodes)

            # Store current network adjacency matrix
            self.sna[f"adjacency_{network_type}"] = nx.to_pandas_adjacency(network, nodelist=nodes)

    def _compute_macro_stats(self) -> pd.Series:
        """Compute macro-level sociogram statistics including cohesion and conflict indices.

        Calculates network-level metrics that summarize the overall structure and
        dynamics of positive and negative relationships in the network using
        Type I (edge-based) and Type II (node-based) index formulations.

        Returns:
            A pandas Series containing:
                - "ui_i": Type I cohesion index (ratio of bidirectional positive edges to total positive edges)
                - "ui_ii": Type II cohesion index (ratio of bidirectional positive edges to network size)
                - "wi_i": Type I conflict index (ratio of bidirectional negative edges to total negative edges)
                - "wi_ii": Type II conflict index (ratio of bidirectional negative edges to network size)
        """
        # Get typed references to networks and adjacency matrices
        network_a: nx.DiGraph = self.sna["network_a"] # type: ignore[type-arg]
        network_b: nx.DiGraph = self.sna["network_b"] # type: ignore[type-arg]
        adjacency_a: pd.DataFrame = self.sna["adjacency_a"]
        adjacency_b: pd.DataFrame = self.sna["adjacency_b"]

        # Compute mutual relationships directly from adjacency matrices
        # Element-wise multiplication of adjacency with its transpose gives mutual edges
        mutual_a: pd.DataFrame = adjacency_a * adjacency_a.T
        mutual_b: pd.DataFrame = adjacency_b * adjacency_b.T

        # Count mutual relationships (sum of upper triangular to avoid double counting)
        mutual_count_a: int = np.triu(mutual_a).sum()
        mutual_count_b: int = np.triu(mutual_b).sum()

        # Get total edge counts
        total_edges_a: int = len(network_a.edges())
        total_edges_b: int = len(network_b.edges())

        # Get network sizes
        network_size_a: int = len(network_a)
        network_size_b: int = len(network_b)

        # Compute cohesion indices based on mutual positive relationships
        cohesion_index_type_i: float = (
            (mutual_count_a * 2) / total_edges_a
        ) if total_edges_a > 0 else 0.0

        cohesion_index_type_ii: float = (
            mutual_count_a / network_size_a
        ) if network_size_a > 0 else 0.0

        # Compute conflict indices based on mutual negative relationships
        conflict_index_type_i: float = (
            (mutual_count_b * 2) / total_edges_b
        ) if total_edges_b > 0 else 0.0

        conflict_index_type_ii: float = (
            mutual_count_b / network_size_b
        ) if network_size_b > 0 else 0.0

        return pd.Series({
            "ui_i": cohesion_index_type_i,
            "ui_ii": cohesion_index_type_ii,
            "wi_i": conflict_index_type_i,
            "wi_ii": conflict_index_type_ii
        })

    def _compute_micro_stats(self) -> pd.DataFrame:
        """Compute comprehensive micro-level sociogram statistics for individual nodes.

        Calculates node-level metrics including basic degree measures, mutual connections,
        derived centrality indices, sociometric status classification, and rankings
        for all metrics including status.

        Returns:
            A DataFrame with rows representing nodes and columns containing:
                - "rp": Received positive nominations (in-degree from positive network)
                - "rr": Received negative nominations (in-degree from negative network)
                - "gp": Given positive nominations (out-degree from positive network)
                - "gr": Given negative nominations (out-degree from negative network)
                - "mp": Mutual positive connections (bidirectional positive edges)
                - "mr": Mutual negative connections (bidirectional negative edges)
                - "bl": Balance index (rp - rr)
                - "or": Orientation index (gp - gr)
                - "im": Impact index (rp + rr)
                - "ai": Activity index (bl + or)
                - "ii": Integration index (rp + mp)
                - "st": Sociometric status classification (categorical)
                - "*_rank": Dense ranking for each numeric metric and status (lower rank = better)
        """
        # Retrieve network graphs and adjacency matrices
        network_a: nx.DiGraph = self.sna["network_a"]  # type: ignore[type-arg]
        network_b: nx.DiGraph = self.sna["network_b"]  # type: ignore[type-arg]
        adjacency_a: pd.DataFrame = self.sna["adjacency_a"]
        adjacency_b: pd.DataFrame = self.sna["adjacency_b"]

        # Initialize DataFrame with basic degree measures
        sociogram_micro_stats = pd.DataFrame({
            "rp": dict(network_a.in_degree()),  # type: ignore[call-overload]
            "rr": dict(network_b.in_degree()),  # type: ignore[call-overload]
            "gp": dict(network_a.out_degree()), # type: ignore[call-overload]
            "gr": dict(network_b.out_degree()), # type: ignore[call-overload]
        })

        # Compute mutual connections using matrix multiplication
        sociogram_micro_stats["mp"] = (adjacency_a * adjacency_a.T).sum(axis=1).astype(int)
        sociogram_micro_stats["mr"] = (adjacency_b * adjacency_b.T).sum(axis=1).astype(int)

        # Compute derived centrality indices
        sociogram_micro_stats["bl"] = sociogram_micro_stats["rp"].sub(sociogram_micro_stats["rr"])
        sociogram_micro_stats["or"] = sociogram_micro_stats["gp"].sub(sociogram_micro_stats["gr"])
        sociogram_micro_stats["im"] = sociogram_micro_stats["rp"].add(sociogram_micro_stats["rr"])
        sociogram_micro_stats["ai"] = sociogram_micro_stats["bl"].add(sociogram_micro_stats["or"])
        sociogram_micro_stats["ii"] = sociogram_micro_stats["rp"].add(sociogram_micro_stats["mp"])

        # Compute sociometric status classification
        sociogram_micro_stats["st"] = self._compute_status(sociogram_micro_stats)

        # Compute dense rankings for all numeric columns (lower rank = better performance)
        numeric_ranks: pd.DataFrame = (
            sociogram_micro_stats
                .rank(method="dense", ascending=False)
                .add_suffix("_rank")
            )
        sociogram_micro_stats = pd.concat([sociogram_micro_stats, numeric_ranks], axis=1)

        # Compute status ranking based on social desirability order
        status_order: list[str] = [
            "popular", "appreciated", "marginal", "-", "isolated", "ambitendent",
            "controversial", "disliked", "rejected"
        ]
        sociogram_micro_stats["st_rank"] = (
            sociogram_micro_stats["st"]
                .apply(lambda x: status_order.index(x) + 1)
        )

        return sociogram_micro_stats.sort_index()

    def _compute_descriptives(self) -> pd.DataFrame:
        """Compute macro-level descriptive statistics by aggregating micro-level node statistics.

        Aggregates individual node statistics to provide network-level summaries
        including measures of central tendency, dispersion, and distribution
        for all numeric columns in the micro-statistics.

        Returns:
            A DataFrame containing descriptive statistics (median, mean, std, IQR, sum, etc.)
            for all numeric columns in the micro-level statistics DataFrame.
        """
        # Select only non-rank numeric columns for statistical aggregation
        sociogram_numeric_columns: pd.DataFrame = (
            self.sociogram["micro_stats"]
                .select_dtypes(np.number)
                .filter(regex=r"^.*(?<!_rank)$")
        )

        return compute_descriptives(sociogram_numeric_columns)

    def _compute_rankings(self) -> dict[str, pd.Series]:
        """Generate sorted node rankings based on centrality metrics and sociometric status.

        Creates ordinal rankings for nodes based on their scores in various centrality
        measures and their sociometric status categories. All rankings are sorted
        from best (rank 1) to worst, with ties handled using dense ranking.

        Returns:
            A dictionary where keys are metric names with "_rank" suffix and values are
            pandas Series containing node-to-rank mappings sorted by rank:
                - "bl_rank": Balance index rankings (sorted ascending by rank)
                - "im_rank": Impact index rankings (sorted ascending by rank)
                - "ai_rank": Activity index rankings (sorted ascending by rank)
                - "ii_rank": Integration index rankings (sorted ascending by rank)
                - "st_rank": Status rankings (sorted by social desirability order)

        Raises:
            AttributeError: If micro_stats have not been computed yet.
        """
        if self.sociogram["micro_stats"] is None:
            message_error = "Micro stats must be computed before rankings."
            raise AttributeError(message_error)

        # Initialize rankings dictionary
        rankings: dict[str, pd.Series] = {}

        # Get micro statistics data
        sociogram_micro_stats: pd.DataFrame = self.sociogram["micro_stats"]

        # Add sorted rankings for centrality metrics and status
        rank_metrics: list[str] = [f"{m}_rank" for m in ["bl", "im", "ai", "ii", "st"]]
        for metric in rank_metrics:
            rankings[metric] = sociogram_micro_stats[metric].sort_values()

        return rankings

    def _compute_relevant_nodes(self, threshold: float = 0.05) -> dict[str, pd.DataFrame]:
        """Identify most and least relevant nodes for positive and negative outcomes.

        Analyzes node rankings across all sociometric centrality metrics to identify nodes that
        consistently perform well (positive relevance) or poorly (negative relevance).
        Processes sociogram rankings to find top performers (valence 'a') and bottom
        performers (valence 'b') across different sociometric measures.

        Args:
            threshold: Quantile threshold for selecting top/bottom performing nodes
                      (default 0.05 = top/bottom 5% of nodes per metric).

        Returns:
            Dictionary with keys 'a' (positive relevance) and 'b' (negative relevance),
            each containing a DataFrame of relevant nodes.
            Each DataFrame has columns:
            - 'node_id': node identifier.
            - 'metric': metric name without '_rank' suffix.
            - 'original_rank': original rank position from micro_stats rankings.
            - 'recomputed_rank': re-computed dense rank position, ascending for 'a', descending for 'b'.
            - 'value': original metric value from micro_stats.
            - 'weight': computed weight using formula 10 / (recomputed_rank ** 0.8).
            - 'evidence_type': always 'sociogram'.

        Notes:
            - For valence 'a': selects nodes with ranks <= threshold quantile (best performers).
            - For valence 'b': selects nodes with ranks >= (1-threshold) quantile (worst performers).
            - Processes all ranking columns ending with '_rank' from sociogram rankings.
        """
        # Select micro_stats and rankings to use
        micro_stats: pd.DataFrame = self.sociogram["micro_stats"]
        rankings: dict[str, pd.Series] = self.sociogram["rankings"]

        # Initialize dicttionary with empty sub-dictionaries for storing relevant nodes
        relevant_nodes: dict[str, pd.DataFrame] = {"a": pd.DataFrame(), "b": pd.DataFrame()}

        # Process both positive (a) and negative (b) relevance directions
        for valence_type in ["a", "b"]:

            # Loop through metrics and associated ranks
            for metric_rank_name, ranks_series in rankings.items():

                # Initialize vars
                current_relevant_ranks: pd.Series
                threshold_value: float
                ascending: bool

                # Clean metric name
                metric_name: str = re.sub("_rank", "", metric_rank_name)

                # Select strategy: a = best performers, b = worst performers
                if valence_type == "a":
                    # Get threshold for top performers (lower quantile = better ranks)
                    threshold_value = ranks_series.quantile(threshold)

                    # Filter nodes with ranks at or below threshold (best performers)
                    current_relevant_ranks = ranks_series[ranks_series.le(threshold_value)]

                    # Set ascending so that smaller ranks are considered more important
                    ascending = True

                else:
                    # Get threshold for bottom performers (higher quantile = worse ranks)
                    threshold_value = ranks_series.quantile(1 - threshold)

                    # Filter nodes with ranks at or above threshold (worst performers)
                    current_relevant_ranks = ranks_series[ranks_series.ge(threshold_value)]

                    # Set ascending so that higher ranks are considered more important
                    ascending = False

                # Compute relevant nodes data
                current_relevant_nodes: pd.DataFrame = (
                    current_relevant_ranks
                        .to_frame()
                        .assign(
                            metric=metric_name,
                            recomputed_rank=current_relevant_ranks.rank(method="dense", ascending=ascending),
                            value=micro_stats.loc[current_relevant_ranks.index, metric_name],
                            weight=lambda x: x["recomputed_rank"].pow(.8).rdiv(10),
                            evidence_type="sociogram"
                        )
                        .reset_index(drop=False, names="node_id")
                        .rename(columns={
                            metric_rank_name: "original_rank"
                        })
                )

                # Add relevant nodes to dataframe
                relevant_nodes[valence_type] = pd.concat([
                    relevant_nodes[valence_type],
                    current_relevant_nodes
                ], ignore_index=True)

        return relevant_nodes

    def _compute_status(self, sociogram_micro_stats: pd.DataFrame) -> pd.Series:
        """Determine sociometric status for each node based on relationship patterns.

        Classifies nodes into sociometric status categories using adaptive quantile-based
        thresholds that account for impact level (total received nominations) and
        balance type (dominance/prevalence of positive vs negative relationships).

        Args:
            sociogram_micro_stats: DataFrame containing micro-level statistics with
                columns for received/given positive/negative nominations and derived indices.

        Returns:
            A pandas Series with sociometric status labels for each node:
                - "isolated": No incoming or outgoing relationships at all.
                - "marginal": Low overall social impact (below low impact threshold).
                - "popular": High positive impact with strong positive dominance or medium impact with positive dominance.
                - "appreciated": High or medium positive impact with positive prevalence (but not dominance).
                - "rejected": High or medium negative impact with strong negative dominance.
                - "disliked": High or medium negative impact with negative prevalence (but not dominance).
                - "controversial": High impact with balanced or neutral relationship patterns.
                - "ambitendent": Medium impact with balanced or neutral relationship patterns.

        Notes:
            Uses adaptive quantile selection that tests multiple quantile pairs
            to find thresholds matching theoretical proportions within epsilon tolerance.
        """

        def _select_best_quantiles(series: pd.Series) -> tuple[float, float]:
            """Select quantile thresholds that best match theoretical proportions for classification.

            Tests multiple quantile pairs to find the first one where actual
            proportions are within epsilon tolerance of theoretical values,
            providing adaptive thresholding based on data distribution.

            Args:
                series: The data series to analyze for quantile threshold selection.

            Returns:
                A tuple containing (low_threshold, high_threshold) quantile values.
            """
            # Tolerance for matching actual vs theoretical quantile proportions
            epsilon: float = 0.05

            # Quantile pairs ordered by preference: (low_quantile, high_quantile)
            # Starting with moderate splits and moving to more extreme ones
            quantile_pairs: list[tuple[float, float]] = [(0.25, 0.75), (0.2, 0.8), (0.15, 0.85), (0.10, 0.90), (0.05, 0.95)]

            # Initialize variables for fallback
            low_val: float = 0.0
            high_val: float = 0.0

            # Test each quantile pair to find best match between actual and theoretical proportions
            for low_q, high_q in quantile_pairs:

                # Calculate threshold values at specified quantiles
                low_val = series.quantile(low_q)
                high_val = series.quantile(high_q)

                # Calculate actual proportions of data below/above thresholds
                actual_low_proportion: float = (series < low_val).sum() / series.shape[0]
                actual_high_proportion: float = (series > high_val).sum() / series.shape[0]

                # Calculate deviations between actual and expected proportions
                # Expected: low_q proportion below threshold, (1-high_q) proportion above threshold
                low_deviation: float = abs(actual_low_proportion - low_q)
                high_deviation: float = abs(actual_high_proportion - (1 - high_q))

                # Return first quantile pair where both deviations are within tolerance
                if low_deviation <= epsilon and high_deviation <= epsilon:
                    return (low_val, high_val)

            # Fallback: return last tested pair if none meet tolerance criteria
            return (low_val, high_val)

        # Extract key metrics from sociogram statistics for efficient repeated access
        impact: pd.Series = sociogram_micro_stats["im"]  # Impact measure
        balance: pd.Series = sociogram_micro_stats["bl"] # Balance between positive/negative preferences
        prefs_a: pd.Series = sociogram_micro_stats["rp"] # Received preferences (positive)
        prefs_b: pd.Series = sociogram_micro_stats["rr"] # Received rejections (negative)

        # Calculate adaptive impact thresholds using quantile matching algorithm
        impact_quantile_low: float
        impact_quantile_high: float
        impact_quantile_low, impact_quantile_high = _select_best_quantiles(impact)

        # Create impact level classification masks
        impact_low: pd.Series = impact.lt(impact_quantile_low) # Low impact individuals
        impact_high: pd.Series = impact.gt(impact_quantile_high) # High impact individuals
        impact_median: pd.Series = impact.between(impact_quantile_low, impact_quantile_high, inclusive="both") # Medium impact

        # Calculate adaptive balance thresholds using absolute balance values
        # Absolute balance removes direction, focusing on magnitude of imbalance
        abs_balance: pd.Series = balance.abs()
        abs_balance_quantile_low: float
        abs_balance_quantile_high: float
        abs_balance_quantile_low, abs_balance_quantile_high = _select_best_quantiles(abs_balance)
        abs_balance_high: pd.Series = abs_balance.gt(abs_balance_quantile_high)  # High absolute balance (strong imbalance)

        # Create balance type classification masks
        # Prevalent: moderate imbalance (positive or negative bias but not extreme)
        a_prevalent: pd.Series = balance.gt(0) & ~abs_balance_high # Moderately positive balance
        b_prevalent: pd.Series = balance.lt(0) & ~abs_balance_high # Moderately negative balance

        # Dominant: extreme imbalance (strong positive or negative bias)
        a_dominant: pd.Series = balance.gt(0) & abs_balance_high # Strongly positive balance
        b_dominant: pd.Series = balance.lt(0) & abs_balance_high # Strongly negative balance

        # Neutral: low absolute balance (minimal preference imbalance)
        neutral: pd.Series = abs_balance.lt(abs_balance_quantile_low)

        # Initialize status classification array
        status: pd.Series = pd.Series(["-"] * sociogram_micro_stats.shape[0], index=sociogram_micro_stats.index)

        # Assign sociometric status classifications based on impact and balance patterns

        # Isolated: individuals with no recorded preferences (sum of first 4 columns = 0)
        status.loc[sociogram_micro_stats.iloc[:, :4].sum(axis=1).eq(0)] = "isolated"

        # Marginal: low impact regardless of balance pattern
        status.loc[impact_low] = "marginal"

        # Popular: positive dominant balance with significant impact (high or medium)
        status.loc[a_dominant & impact_high] = "popular"
        status.loc[a_dominant & impact_median] = "popular"

        # Appreciated: positive prevalent balance with significant impact
        status.loc[a_prevalent & impact_high] = "appreciated"
        status.loc[a_prevalent & impact_median] = "appreciated"

        # Rejected: negative dominant balance with significant impact
        status.loc[b_dominant & impact_high] = "rejected"
        status.loc[b_dominant & impact_median] = "rejected"

        # Disliked: negative prevalent balance with significant impact
        status.loc[b_prevalent & impact_high] = "disliked"
        status.loc[b_prevalent & impact_median] = "disliked"

        # Handle perfectly balanced cases (balance exactly equals 0)
        status.loc[balance.eq(0) & impact_median] = "ambitendent" # Medium impact, perfect balance
        status.loc[balance.eq(0) & impact_high] = "controversial" # High impact, perfect balance

        # Handle near-balanced cases (neutral category with both positive and negative preferences)
        # Condition 1: prefs_a.mul(prefs_b).gt(0) ensures both preference types > 0
        # Condition 2: neutral ensures low absolute balance (near-balanced)
        # Condition 3: impact level determines ambitendent vs controversial classification
        status.loc[prefs_a.mul(prefs_b).gt(0) & neutral & impact_median] = "ambitendent"
        status.loc[prefs_a.mul(prefs_b).gt(0) & neutral & impact_high] = "controversial"

        return status

    def _create_graph(self, coefficient: Literal["ai", "ii"]) -> str:
        """Generate a circular polar visualization of node distribution based on centrality coefficients.

        Creates a polar plot showing nodes arranged radially by their centrality scores. Values are
        normalized to [0,1] and inverted so high-scoring nodes appear near the center. Nodes are
        grouped by coefficient value and distributed angularly with jitter to reduce overlap.

        Args:
            coefficient: The centrality coefficient to visualize. Must be either:
                - "ai": Activity index (balance + orientation indices).
                - "ii": Integration index (received positive + mutual positive connections).

        Returns:
            A base64-encoded SVG string representing the polar sociogram visualization.
            The plot shows nodes as labeled scatter points arranged in concentric circles,
            with high-value nodes near the center and groups organized radially with
            angular jitter applied to reduce overlap.
        """
        # Extract values for the specified centrality coefficient
        data: pd.DataFrame = self.sociogram["micro_stats"].loc[:, [coefficient]].copy()

        # Normalize values to [0, 1] range and invert for radial display (center = high values)
        plot_data: pd.DataFrame = data.sub(data.min()).div(data.max() - data.min())
        plot_data = plot_data.max() - plot_data

        # Create polar coordinate subplot with specified figure size
        fig: Figure
        ax: Axes
        fig, ax = plt.subplots(
            constrained_layout=True,
            figsize=(19 * CM_TO_INCHES, 19 * CM_TO_INCHES),
            subplot_kw={"projection": "polar"}
        )

        # Customize polar plot appearance (remove ticks, set limits, style grid)
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.get_xaxis().set_visible(False)
        ax.set_ylim(0, 1.1)
        ax.grid(color="#bbb", linestyle="--", linewidth=.8)

        # Set jitter parameters to reduce visual overlap between nearby points
        theta_jitter_scale: float = 0.03  # Angular jitter magnitude
        r_jitter_scale: float = 0.01      # Radial jitter magnitude

        # Plot data points grouped by unique coefficient values
        for idx, (_, group_plot_data) in enumerate(plot_data.groupby(by=coefficient)):
            # Define angular offset pattern for current group (alternating and progressive)
            offset: float = idx % 2 * -np.pi + idx * 0.25

            # Compute angular spacing to distribute points evenly within group
            slice_angle: float = (2 * np.pi) / group_plot_data[coefficient].shape[0]

            # Reset index to preserve node labels for annotation
            group_plot_data = group_plot_data.reset_index(names="node_labels")  # noqa: PLW2901

            # Set base polar coordinates for this group
            r: pd.Series = group_plot_data[coefficient]  # Radial distance (normalized and inverted)
            theta: pd.Series = pd.Series(group_plot_data[coefficient].index.values).mul(slice_angle).add(offset)

            # Apply reproducible random jitter to reduce overlap (seeded by group index)
            np.random.seed(42 + idx)
            theta_jitter: np.ndarray = np.random.normal(0, theta_jitter_scale, len(theta))
            r_jitter: np.ndarray = np.random.normal(0, r_jitter_scale, len(r))

            # Apply jitter with bounds checking to keep points in valid range
            theta_jittered: pd.Series = theta + theta_jitter
            r_jittered: pd.Series = (r + r_jitter).clip(0, 1.1)

            # Plot data points as scatter plot with consistent styling
            ax.scatter(theta_jittered, r_jittered, c="#bbb", s=20)

            # Add node labels as text annotations at jittered positions
            for i, txt in enumerate(group_plot_data["node_labels"]):
                ax.annotate(txt, (theta_jittered.iloc[i], r_jittered.iloc[i]),
                          color="blue", fontsize=12)

        return figure_to_base64_svg(fig)
