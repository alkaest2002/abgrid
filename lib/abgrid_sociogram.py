"""
Filename: abgrid_sociogram.py
Description: Provides functionality to analyze directed networks (graphs) for sociometric analysis,
computing macro and micro-level statistics, node rankings, and generating polar visualizations.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

from typing import Any, List, Literal, Dict, Optional, TypedDict, Tuple, Union
from lib import CM_TO_INCHES
from lib.abgrid_utils import compute_descriptives, figure_to_base64_svg


class SociogramDict(TypedDict):
    """Dictionary structure for storing sociogram analysis results."""
    macro_stats: Optional[pd.Series]
    micro_stats: Optional[pd.DataFrame]
    descriptives: Optional[pd.DataFrame]
    rankings: Optional[Dict[str, pd.Series]]
    graph_ii: Optional[str]
    graph_ai: Optional[str]
    relevant_nodes_ab: Optional[Dict[str, List[Dict[str, Union[str, List[str], List[int], float]]]]]

# Define centrality metrics used for ranking nodes
CENTRALITY_METRICS = ["bl", "im", "ai", "ii"]

# Define sociometric status categories ordered from highest to lowest social desirability
STATUS_ORDER = [
    "popular", "appreciated", "marginal", "ambitendent",
    "controversial", "disliked", "rejected", "isolated"
]
        
class ABGridSociogram:
    """
    Analyzes and visualizes social networks by constructing sociometric components including 
    macro/micro statistics, node rankings, and polar graph visualizations.
    
    This class provides comprehensive sociometric analysis capabilities including:
    - Macro-level network statistics (cohesion and conflict indices)
    - Micro-level node statistics (centrality measures, sociometric status classification)
    - Node rankings based on various centrality metrics and status
    - Identification of most/least relevant nodes for positive/negative outcomes
    - Polar visualization of activity and integration index distributions
    
    Attributes:
        sna: Social network analysis data containing NetworkX graphs and adjacency matrices.
        sociogram: Dictionary containing all computed sociogram data and visualizations.
    """

    def __init__(self) -> None:
        """
        Initialize the ABGridSociogram instance.
        
        Sets up internal data structures for storing social network analysis data
        and computed sociogram results.
        """
        # Initialize social network analysis data storage
        self.sna: Optional[Dict[str, Any]] = None

        # Initialize sociogram results dictionary
        self.sociogram: SociogramDict = {
            "macro_stats": None,
            "micro_stats": None,
            "descriptives": None,
            "rankings": None,
            "graph_ii": None,
            "graph_ai": None,
            "relevant_nodes_ab": None
        }

    def get(self, sna: Dict[str, Any]) -> SociogramDict:
        """
        Compute and store comprehensive sociogram analysis from social network data.

        Args:
            sna: A dictionary containing social network analysis data with the following structure:
                - "network_a": NetworkX DiGraph for positive relationships
                - "network_b": NetworkX DiGraph for negative relationships  
                - "adjacency_a": NumPy adjacency matrix for positive relationships
                - "adjacency_b": NumPy adjacency matrix for negative relationships
                - "edges_types_a": Dictionary with edge type classifications for network A
                - "edges_types_b": Dictionary with edge type classifications for network B

        Returns:
            A dictionary containing complete sociogram analysis with the following structure:
                - "macro_stats": Series of network-level cohesion and conflict indices
                - "micro_stats": DataFrame of individual-level statistics and ranks for each node
                - "descriptives": DataFrame with aggregated descriptive statistics
                - "rankings": Dictionary with sorted node rankings by centrality metrics and status
                - "graph_ii": Base64-encoded SVG string of integration index polar visualization
                - "graph_ai": Base64-encoded SVG string of activity index polar visualization
                - "relevant_nodes_ab": Dictionary with most/least relevant nodes for positive/negative outcomes

        Side Effects:
            Updates the instance's `sna` and `sociogram` attributes with the computed data.
        """
        # Store social network analysis data
        self.sna = sna

        # Compute all sociogram components in sequence
        self.sociogram["macro_stats"] = self.compute_macro_stats()
        self.sociogram["micro_stats"] = self.compute_micro_stats()
        self.sociogram["descriptives"] = self.compute_descriptives()
        self.sociogram["rankings"] = self.compute_rankings()
        self.sociogram["relevant_nodes_ab"] = self.compute_relevant_nodes_ab()
        self.sociogram["graph_ai"] = self.create_graph("ai")
        self.sociogram["graph_ii"] = self.create_graph("ii")

        return self.sociogram

    def compute_macro_stats(self) -> pd.Series:
        """
        Compute macro-level sociogram statistics including cohesion and conflict indices.
        
        Calculates network-level metrics that summarize the overall structure and
        dynamics of positive and negative relationships in the network using
        Type I (edge-based) and Type II (node-based) index formulations.

        Returns:
            A pandas Series containing:
                - "ui_i": Type I cohesion index (ratio of bidirectional positive edges to total positive edges)
                - "ui_ii": Type II cohesion index (ratio of bidirectional positive edges to network size)
                - "wi_i": Type I conflict index (ratio of bidirectional negative edges to total negative edges)
                - "wi_ii": Type II conflict index (ratio of bidirectional negative edges to network size)
                
        Raises:
            AttributeError: If sna data has not been set via the get() method.
        """
        if self.sna is None:
            raise AttributeError("SNA data must be set before computing statistics")
            
        # Calculate cohesion indices based on mutual positive relationships
        cohesion_index_type_i = (
            len(self.sna["edges_types_a"]["type_ii"]) * 2) / len(self.sna["network_a"].edges()
        )
        cohesion_index_type_ii = (
            len(self.sna["edges_types_a"]["type_ii"]) / len(self.sna["network_a"])
        )
        
        # Calculate conflict indices based on mutual negative relationships
        conflict_index_type_i = (
            len(self.sna["edges_types_b"]["type_ii"]) * 2) / len(self.sna["network_b"].edges()
        )
        conflict_index_type_ii = (
            len(self.sna["edges_types_b"]["type_ii"]) / len(self.sna["network_b"])
        )

        return pd.Series({
            "ui_i": cohesion_index_type_i,
            "ui_ii": cohesion_index_type_ii,
            "wi_i": conflict_index_type_i,
            "wi_ii": conflict_index_type_ii
        })
    
    def compute_micro_stats(self) -> pd.DataFrame:
        """
        Compute comprehensive micro-level sociogram statistics for individual nodes.
        
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
                
        Raises:
            AttributeError: If sna data has not been set via the get() method.
        """
        if self.sna is None:
            raise AttributeError("SNA data must be set before computing statistics")
            
        # Retrieve network graphs and adjacency matrices
        network_a: nx.DiGraph = self.sna["network_a"]
        network_b: nx.DiGraph = self.sna["network_b"]
        adjacency_a: np.ndarray = self.sna["adjacency_a"]
        adjacency_b: np.ndarray = self.sna["adjacency_b"]
        
        # Initialize DataFrame with basic degree measures
        sociogram_micro_stats = pd.concat([
            pd.Series(dict(network_a.in_degree()), name="rp"), 
            pd.Series(dict(network_b.in_degree()), name="rr"),
            pd.Series(dict(network_a.out_degree()), name="gp"), 
            pd.Series(dict(network_b.out_degree()), name="gr"), 
        ], axis=1)

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
        sociogram_micro_stats["st"] = self.compute_status(sociogram_micro_stats)

        # Compute dense rankings for all numeric columns (lower rank = better performance)
        sociogram_micro_stats = pd.concat([
            sociogram_micro_stats,
            sociogram_micro_stats.rank(method="dense", ascending=False).add_suffix("_rank")
        ], axis=1)

        # Compute status ranking based on social desirability order
        sociogram_micro_stats["st_rank"] = (
            sociogram_micro_stats["st"]
                .apply(lambda x: STATUS_ORDER.index(x) + 1)
        )

        return sociogram_micro_stats.sort_index()
    
    def compute_status(self, sociogram_micro_stats: pd.DataFrame) -> pd.Series:
        """
        Determine sociometric status for each node based on relationship patterns.
        
        Classifies nodes into sociometric status categories using adaptive quantile-based
        thresholds that account for impact level (total received nominations) and
        balance type (dominance/prevalence of positive vs negative relationships).
        
        Args:
            sociogram_micro_stats: DataFrame containing micro-level statistics with
                columns for received/given positive/negative nominations and derived indices.
            
        Returns:
            A pandas Series with sociometric status labels for each node:
                - "isolated": No incoming or outgoing relationships at all
                - "marginal": Low overall social impact (below low impact threshold)
                - "popular": High positive impact with strong positive dominance or medium impact with positive dominance
                - "appreciated": High or medium positive impact with positive prevalence (but not dominance)
                - "rejected": High or medium negative impact with strong negative dominance
                - "disliked": High or medium negative impact with negative prevalence (but not dominance)
                - "controversial": High impact with balanced or neutral relationship patterns
                - "ambitendent": Medium impact with balanced or neutral relationship patterns
                
        Note:
            Uses adaptive quantile selection that tests multiple quantile pairs
            to find thresholds matching theoretical proportions within epsilon tolerance.
        """
        
        def select_best_quantiles(series: pd.Series) -> Tuple[float, float]:
            """
            Select quantile thresholds that best match theoretical proportions for classification.
            
            Tests multiple quantile pairs to find the first one where actual
            proportions are within epsilon tolerance of theoretical values,
            providing adaptive thresholding based on data distribution.
            
            Args:
                series: The data series to analyze for quantile threshold selection.
                
            Returns:
                A tuple containing (low_threshold, high_threshold) quantile values.
            """
            # Set epsilon tolerance for quantile proportion matching
            epsilon = 0.05

            # Define quantile pairs to test in order of preference (low_quantile, high_quantile)
            quantile_pairs = [(0.25, 0.75), (0.2, 0.8), (0.15, 0.85), (0.10, 0.90), (0.05, 0.95)]

            # Test each quantile pair for best theoretical proportion match
            for low_q, high_q in quantile_pairs:
                
                # Calculate actual quantile threshold values
                low_val = series.quantile(low_q)
                high_val = series.quantile(high_q)
                
                # Calculate actual proportions below/above thresholds
                actual_low_prop = (series < low_val).sum() / series.shape[0]
                actual_high_prop = (series > high_val).sum() / series.shape[0]
                
                # Calculate deviations from expected theoretical proportions
                low_deviation = abs(actual_low_prop - low_q)
                high_deviation = abs(actual_high_prop - (1 - high_q))

                # Return first quantile pair within epsilon tolerance
                if low_deviation <= epsilon and high_deviation <= epsilon:
                    return (low_val, high_val)
            
            # If no quantiles meet epsilon criteria, return the last tested pair as fallback
            return (low_val, high_val)
        
        # Cache relevant columns for computational efficiency
        impact = sociogram_micro_stats["im"]
        balance = sociogram_micro_stats["bl"]
        prefs_a = sociogram_micro_stats["rp"]
        prefs_b = sociogram_micro_stats["rr"]
        
        # Determine adaptive impact thresholds using best quantile matching
        impact_quantile_low, impact_quantile_high = select_best_quantiles(impact)
        
        # Create boolean masks for impact levels
        impact_low = impact.lt(impact_quantile_low)
        impact_high = impact.gt(impact_quantile_high)
        impact_median = impact.between(impact_quantile_low, impact_quantile_high, inclusive="both")
        
        # Determine adaptive balance thresholds using absolute balance values
        abs_balance = balance.abs()
        abs_balance_quantile_low, abs_balance_quantile_high = select_best_quantiles(abs_balance)
        abs_balance_high = abs_balance.gt(abs_balance_quantile_high)
        
        # Create boolean masks for balance/relationship types
        a_prevalent = balance.gt(0) & ~abs_balance_high  # Positive but not dominant
        b_prevalent = balance.lt(0) & ~abs_balance_high  # Negative but not dominant
        a_dominant = balance.gt(0) & abs_balance_high    # Strongly positive
        b_dominant = balance.lt(0) & abs_balance_high    # Strongly negative
        neutral = abs_balance.lt(abs_balance_quantile_low)  # Very balanced
        
        # Initialize status series with default placeholder values
        status = pd.Series(["-"] * sociogram_micro_stats.shape[0], index=sociogram_micro_stats.index)
        
        # Assign status classifications based on combined impact and balance patterns
        status.loc[sociogram_micro_stats.iloc[:, :4].sum(axis=1).eq(0)] = "isolated"
        status.loc[impact_low] = "marginal"
        
        # Popular: positive dominant with high or medium impact
        status.loc[a_dominant & impact_high] = "popular"
        status.loc[a_dominant & impact_median] = "popular"
        
        # Appreciated: positive prevalent (but not dominant) with high or medium impact
        status.loc[a_prevalent & impact_high] = "appreciated"
        status.loc[a_prevalent & impact_median] = "appreciated"
        
        # Rejected: negative dominant with high or medium impact
        status.loc[b_dominant & impact_high] = "rejected"
        status.loc[b_dominant & impact_median] = "rejected"
        
        # Disliked: negative prevalent (but not dominant) with high or medium impact
        status.loc[b_prevalent & impact_high] = "disliked"
        status.loc[b_prevalent & impact_median] = "disliked"
        
        # Controversial/Ambitendent: balanced relationships, differentiated by impact level
        status.loc[balance.eq(0) & impact_median] = "ambitendent"
        status.loc[balance.eq(0) & impact_high] = "controversial"
        status.loc[prefs_a.mul(prefs_b).gt(0) & neutral & impact_median] = "ambitendent"
        status.loc[prefs_a.mul(prefs_b).gt(0) & neutral & impact_high] = "controversial"
        
        return status

    def compute_descriptives(self) -> pd.DataFrame:
        """
        Compute macro-level descriptive statistics by aggregating micro-level node statistics.
        
        Aggregates individual node statistics to provide network-level summaries
        including measures of central tendency, dispersion, and distribution
        for all numeric columns in the micro-statistics.

        Returns:
            A DataFrame containing descriptive statistics (median, mean, std, IQR, sum, etc.)
            for all numeric columns in the micro-level statistics DataFrame.
            
        Raises:
            AttributeError: If micro_stats have not been computed yet.
        """
        if self.sociogram["micro_stats"] is None:
            raise AttributeError("Micro stats must be computed before descriptives")
            
        # Select only numeric columns for statistical aggregation
        sociogram_numeric_columns = self.sociogram["micro_stats"].select_dtypes(np.number)
        
        return compute_descriptives(sociogram_numeric_columns)
        
    def compute_rankings(self) -> Dict[str, pd.Series]:
        """
        Generate sorted node rankings based on centrality metrics and sociometric status.
        
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
            raise AttributeError("Micro stats must be computed before rankings")
            
        # Initialize rankings dictionary
        rankings: Dict[str, pd.Series] = {}
        
        # Get micro statistics data
        sociogram_micro_stats = self.sociogram["micro_stats"]
        
        # Add sorted rankings for centrality metrics and status
        for metric in [f"{m}_rank" for m in CENTRALITY_METRICS] + ["st_rank"]:
            rankings[metric] = sociogram_micro_stats[metric].sort_values()
        
        return rankings
    
    def compute_relevant_nodes_ab(self, threshold: float = 0.05) -> Dict[str, List[Dict[str, Union[str, List[str], List[int], float]]]]:
        """
        Identify most and least relevant nodes for positive and negative outcomes.
        
        Analyzes node rankings across all centrality metrics to identify nodes that
        consistently perform well (positive relevance) or poorly (negative relevance),
        with consolidated weighting based on multiple metric appearances.

        Args:
            threshold: Quantile threshold for selecting top/bottom performing nodes
                      (default 0.05 = top/bottom 5% of nodes per metric).

        Returns:
            A dictionary with keys "a" (positive relevance) and "b" (negative relevance),
            where values are lists of node dictionaries sorted by relevance weight:
                Each node dictionary contains:
                - "id": Node identifier as string
                - "metric": List of metric names where node appears in threshold
                - "rank": List of corresponding ranks for each metric
                - "weight": Cumulative relevance weight across all metrics
                
        Raises:
            ValueError: If sociogram rankings have not been computed yet.
        """
        # Validate that rankings data is available
        if self.sociogram["rankings"] is None or self.sociogram["micro_stats"] is None:
            raise ValueError("Sociogram micro statistics and rankings are required.")
        
        # Cahce micro_stats
        micro_stats = self.sociogram["micro_stats"]
        
        # Cahce rankings
        rankings = self.sociogram["rankings"]
        
        # Initialize nested dictionaries for node consolidation by valence
        relevant_nodes_ab = {"a": {}, "b": {}}
        
        # Process both positive (a) and negative (b) relevance directions
        for valence_key in relevant_nodes_ab.keys():
            
            # Iterate through all metric rankings
            for metric_rank_name, ranks_series in rankings.items():

                # clean metric name
                metric_name = re.sub("_rank", "", metric_rank_name)

                # Select strategy: a = best performers, b = worst performers
                if valence_key == "a":
                    # Get threshold for top performers (lower quantile = better ranks)
                    threshold_value = ranks_series.quantile(threshold)
                    
                    # Filter nodes with ranks at or below threshold (best performers)
                    relevant_nodes = ranks_series[ranks_series <= threshold_value]

                    # Calculate normalized ranks for weight computation (dense ranking, ascending)
                    normalized_ranks = relevant_nodes.rank(method="dense", ascending=True)

                else:
                    # Get threshold for bottom performers (higher quantile = worse ranks)
                    threshold_value = ranks_series.quantile(1 - threshold)
                    
                    # Filter nodes with ranks at or above threshold (worst performers)
                    relevant_nodes = ranks_series[ranks_series >= threshold_value]
                
                    # Calculate normalized ranks for weight computation (dense ranking, ascending)
                    normalized_ranks = relevant_nodes.rank(method="dense", ascending=False)
                
                # Process each selected node
                for node_id, original_rank in relevant_nodes.items():
                    
                    # Get normalized rank for this node within selected group
                    normalized_rank = normalized_ranks[node_id]
                    
                    # Calculate inverse exponential weight (better normalized rank = higher weight)
                    weight = float(10.0 / (normalized_rank ** 0.8))

                    # Get value
                    value = micro_stats.loc[node_id, metric_name]
                    
                    # Initialize new node entry or update existing one
                    if node_id not in relevant_nodes_ab[valence_key]:
                        relevant_nodes_ab[valence_key][node_id] = {
                            "id": node_id,
                            "metric": [metric_name],
                            "value": [value],
                            "rank": [ original_rank ],
                            "weight": weight
                        }
                    else:
                        # Consolidate multiple metric appearances: append lists and sum weights
                        relevant_nodes_ab[valence_key][node_id]["metric"].append(metric_name)
                        relevant_nodes_ab[valence_key][node_id]["value"].append(value)
                        relevant_nodes_ab[valence_key][node_id]["rank"].append(original_rank)
                        relevant_nodes_ab[valence_key][node_id]["weight"] += weight
        
        # Convert consolidated dictionaries to sorted lists by relevance weight (descending)
        return {
            "a": sorted(list(relevant_nodes_ab["a"].values()), key=lambda x: 1 / x["weight"]),
            "b": sorted(list(relevant_nodes_ab["b"].values()), key=lambda x: 1 / x["weight"])
        }

    def create_graph(self, coefficient: Literal["ai", "ii"]) -> str:
        """
        Generate a polar visualization of node distribution based on centrality coefficients.
        
        Creates a circular (polar) plot showing the spatial distribution of nodes based on their
        scores in the specified centrality coefficient. Nodes are arranged in concentric circles
        with groups determined by coefficient values, and jitter is applied to reduce overlap.

        Args:
            coefficient: The centrality coefficient to visualize. Must be either:
                - "ai": Activity index (balance + orientation indices)
                - "ii": Integration index (received positive + mutual positive connections)
        
        Returns:
            A base64-encoded SVG string representing the polar sociogram visualization.
            The plot shows nodes as scatter points with labels, arranged radially with
            groups organized by score levels and angular jitter applied to reduce overlap.
            
        Raises:
            AttributeError: If micro_stats have not been computed yet.
        """
        if self.sociogram["micro_stats"] is None:
            raise AttributeError("Micro stats must be computed before creating graphs")
            
        # Extract values for the specified centrality coefficient
        data = self.sociogram["micro_stats"].loc[:, [coefficient]].copy()
        
        # Normalize values to [0, 1] range and invert for radial display (center = high values)
        plot_data = data.sub(data.min()).div(data.max() - data.min())
        plot_data = plot_data.max() - plot_data
        
        # Create polar coordinate subplot with specified figure size
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
        theta_jitter_scale = 0.03  # Angular jitter magnitude
        r_jitter_scale = 0.01      # Radial jitter magnitude
        
        # Plot data points grouped by unique coefficient values
        for idx, (_, group_plot_data) in enumerate(plot_data.groupby(by=coefficient)):
            # Define angular offset pattern for current group (alternating and progressive)
            offset = idx % 2 * -np.pi + idx * 0.25
            
            # Calculate angular spacing to distribute points evenly within group
            slice_angle = (2 * np.pi) / group_plot_data[coefficient].shape[0]

            # Reset index to preserve node labels for annotation
            group_plot_data = group_plot_data.reset_index(names="node_labels")

            # Set base polar coordinates for this group
            r = group_plot_data[coefficient]  # Radial distance (normalized and inverted)
            theta = pd.Series(group_plot_data[coefficient].index.values).mul(slice_angle).add(offset)
            
            # Apply reproducible random jitter to reduce overlap (seeded by group index)
            np.random.seed(42 + idx)
            theta_jitter = np.random.normal(0, theta_jitter_scale, len(theta))
            r_jitter = np.random.normal(0, r_jitter_scale, len(r))
            
            # Apply jitter with bounds checking to keep points in valid range
            theta_jittered = theta + theta_jitter
            r_jittered = np.clip(r + r_jitter, 0, 1.1)
            
            # Plot data points as scatter plot with consistent styling
            ax.scatter(theta_jittered, r_jittered, c="#bbb", s=20)

            # Add node labels as text annotations at jittered positions
            for i, txt in enumerate(group_plot_data["node_labels"]):
                ax.annotate(txt, (theta_jittered.iloc[i], r_jittered.iloc[i]), 
                          color="blue", fontsize=12)

        return figure_to_base64_svg(fig)
