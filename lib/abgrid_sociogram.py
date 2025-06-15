"""
Filename: abgrid_sociogram.py
Description: Provides functionality to analyze directed networks (graphs) for a given set of edges.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

from typing import Any, Literal, Dict, Optional, TypedDict, Tuple
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


class ABGridSociogram:
    """
    Analyzes and visualizes social networks by constructing components like macro/micro statistics,
    rankings, and graphical representations of sociograms.
    
    This class provides comprehensive social network analysis capabilities including:
    - Macro-level network statistics (cohesion and conflict indices)
    - Micro-level node statistics (centrality measures, status classification)
    - Node rankings based on various centrality metrics
    - Visualization of sociometric status distributions
    
    Attributes:
        sna: Social network analysis data containing network graphs and adjacency matrices.
        sociogram: Dictionary containing all computed sociogram data and visualizations.
    """

    def __init__(self) -> None:
        """
        Initialize the ABGridSociogram instance.
        
        Sets up internal data structures for storing social network analysis data
        and computed sociogram results.
        """
        # Init sna data
        self.sna: Optional[Dict[str, Any]] = None

        # Init sociogram data
        self.sociogram: SociogramDict = {
            "macro_stats": None,
            "micro_stats": None,
            "descriptives": None,
            "rankings": None,
            "graph_ii": None,
            "graph_ai": None,
        }

    def get(self, sna: Dict[str, Any]) -> SociogramDict:
        """
        Compute and store sociogram-related data from the provided social network analysis (SNA) data.

        Args:
            sna: A dictionary containing social network analysis data with the following structure:
                - "network_a": NetworkX graph for positive relationships
                - "network_b": NetworkX graph for negative relationships  
                - "adjacency_a": Adjacency matrix for positive relationships
                - "adjacency_b": Adjacency matrix for negative relationships
                - "edges_types_a": Dictionary of edge types for network A
                - "edges_types_b": Dictionary of edge types for network B

        Returns:
            A dictionary containing detailed sociogram data with the following structure:
                - "macro_stats": Series of network-level statistics (cohesion/conflict indices)
                - "micro_stats": DataFrame of individual-level statistics for each node
                - "descriptives": DataFrame with macro-level descriptive statistics
                - "rankings": Dictionary with node rankings based on centrality metrics
                - "graph_ii": Base64-encoded SVG string of integration index visualization
                - "graph_ai": Base64-encoded SVG string of activity index visualization

        Side Effects:
            Updates the instance's `sna` and `sociogram` attributes with the computed data.
        """
        # Store sna data
        self.sna = sna

        # Create graphs
        self.sociogram["macro_stats"] = self.compute_macro_stats()
        self.sociogram["micro_stats"] = self.compute_micro_stats()
        self.sociogram["descriptives"] = self.compute_descriptives()
        self.sociogram["rankings"] = self.compute_rankings()
        self.sociogram["graph_ai"] = self.create_graph("ai")
        self.sociogram["graph_ii"] = self.create_graph("ii")

        # Return sociogram data
        return self.sociogram

    def compute_macro_stats(self) -> pd.Series:
        """
        Compute macro-level sociogram statistics including cohesion and conflict indices.
        
        Calculates network-level metrics that summarize the overall structure and
        dynamics of positive and negative relationships in the network.

        Returns:
            A pandas Series containing:
                - "ui_i": Type I cohesion index (ratio of mutual positive edges to total positive edges)
                - "ui_ii": Type II cohesion index (ratio of mutual positive edges to network size)
                - "wi_i": Type I conflict index (ratio of mutual negative edges to total negative edges)
                - "wi_ii": Type II conflict index (ratio of mutual negative edges to network size)
                
        Raises:
            AttributeError: If sna data has not been set via the get() method.
        """
        if self.sna is None:
            raise AttributeError("SNA data must be set before computing statistics")
            
        # Calculate cohesion and conflict indices
        cohesion_index_type_i = (
            len(self.sna["edges_types_a"]["type_ii"]) * 2) / len(self.sna["network_a"].edges()
        )
        cohesion_index_type_ii = (
            len(self.sna["edges_types_a"]["type_ii"]) / len(self.sna["network_a"])
        )
        conflict_index_type_i = (
            len(self.sna["edges_types_b"]["type_ii"]) * 2) / len(self.sna["network_b"].edges()
        )
        conflict_index_type_ii = (
            len(self.sna["edges_types_b"]["type_ii"]) / len(self.sna["network_b"])
        )

        # Return sociogram macro statistics
        return pd.Series({
            "ui_i": cohesion_index_type_i,
            "ui_ii": cohesion_index_type_ii,
            "wi_i": conflict_index_type_i,
            "wi_ii": conflict_index_type_ii
        })
    
    def compute_micro_stats(self) -> pd.DataFrame:
        """
        Compute micro-level sociogram statistics for individual nodes.
        
        Calculates comprehensive node-level metrics including centrality measures,
        preference indices, and sociometric status classification for each node
        in the network.

        Returns:
            A DataFrame with rows representing nodes and columns containing:
                - "rp": Received positive nominations (in-degree from positive network)
                - "rr": Received negative nominations (in-degree from negative network)
                - "gp": Given positive nominations (out-degree from positive network)
                - "gr": Given negative nominations (out-degree from negative network)
                - "mp": Mutual positive connections
                - "mr": Mutual negative connections
                - "bl": Balance index (difference between positive and negative received)
                - "or": Orientation index (difference between positive and negative given)
                - "im": Impact index (sum of all received nominations)
                - "ai": Activity index (sum of balance and orientation indices)
                - "ii": Integration index (sum of received positive and mutual positive)
                - "st": Sociometric status classification
                
        Raises:
            AttributeError: If sna data has not been set via the get() method.
        """
        if self.sna is None:
            raise AttributeError("SNA data must be set before computing statistics")
            
        # Retrieve network and adjacency matrices
        network_a: nx.DiGraph = self.sna["network_a"]
        network_b: nx.DiGraph = self.sna["network_b"]
        adjacency_a: np.ndarray = self.sna["adjacency_a"]
        adjacency_b: np.ndarray = self.sna["adjacency_b"]
        
        # Init sociogram micro df
        sociogram_micro_stats = pd.concat([
            pd.Series(dict(network_a.in_degree()), name="rp"), 
            pd.Series(dict(network_b.in_degree()), name="rr"),
            pd.Series(dict(network_a.out_degree()), name="gp"), 
            pd.Series(dict(network_b.out_degree()), name="gr"), 
        ], axis=1)

        # Compute relevant metrics
        sociogram_micro_stats["mp"] = (adjacency_a * adjacency_a.T).sum(axis=1).astype(int)
        sociogram_micro_stats["mr"] = (adjacency_b * adjacency_b.T).sum(axis=1).astype(int)
        sociogram_micro_stats["bl"] = sociogram_micro_stats["rp"].sub(sociogram_micro_stats["rr"])
        sociogram_micro_stats["or"] = sociogram_micro_stats["gp"].sub(sociogram_micro_stats["gr"])
        sociogram_micro_stats["im"] = sociogram_micro_stats["rp"].add(sociogram_micro_stats["rr"])
        sociogram_micro_stats["ai"] = sociogram_micro_stats["bl"].add(sociogram_micro_stats["or"])
        sociogram_micro_stats["ii"] = sociogram_micro_stats["rp"].add(sociogram_micro_stats["mp"])
        
        # Compute status
        sociogram_micro_stats["st"] = self.compute_status(sociogram_micro_stats)

        # Return sociogram micro statistics
        return sociogram_micro_stats.sort_index()

    def compute_descriptives(self) -> pd.DataFrame:
        """
        Compute macro-level descriptive statistics based on micro-level node statistics.
        
        Aggregates individual node statistics to provide network-level summaries
        including measures of central tendency, dispersion, and distribution.

        Returns:
            A DataFrame containing descriptive statistics (median, IQR, total sum, etc.)
            for all numeric columns in the micro-level statistics.
            
        Raises:
            AttributeError: If micro_stats have not been computed yet.
        """
        if self.sociogram["micro_stats"] is None:
            raise AttributeError("Micro stats must be computed before descriptives")
            
        # Select numeric columns only
        sociogram_numeric_columns = self.sociogram["micro_stats"].select_dtypes(np.number)
        
        # Return sociogram macro statistics
        return compute_descriptives(sociogram_numeric_columns)
        
    def compute_rankings(self) -> Dict[str, pd.Series]:
        """
        Generate node rankings based on centrality metrics and sociometric status.
        
        Creates ordinal rankings for nodes based on their scores in various centrality
        measures and their sociometric status categories, with higher scores receiving
        better (lower) rank numbers.

        Returns:
            A dictionary where keys are metric names and values are pandas Series
            containing node-to-rank mappings:
                - "bl": Balance index rankings (higher balance = better rank)
                - "im": Impact index rankings (higher impact = better rank)  
                - "ai": Activity index rankings (higher activity = better rank)
                - "ii": Integration index rankings (higher integration = better rank)
                - "st": Status rankings (ordered by social desirability)
                
        Raises:
            AttributeError: If micro_stats have not been computed yet.
        """
        if self.sociogram["micro_stats"] is None:
            raise AttributeError("Micro stats must be computed before rankings")
            
        # Define metrics to rank
        CENTRALITY_METRICS = ["bl", "im", "ai", "ii"]
        
        # Define status ordering (from highest to lowest social status)
        STATUS_ORDER = [
            "popular", "appreciated", "ambitendent", "marginal",
            "controversial", "disliked", "rejected", "isolated"
        ]
        
        # Init dicts
        rankings: Dict[str, pd.Series] = {}
        
        # Rank centrality metrics (higher scores get better ranks)
        sociogram_micro_stats = self.sociogram["micro_stats"]
        centrality_data = sociogram_micro_stats.loc[:, CENTRALITY_METRICS]
        ranked_metrics = centrality_data.rank(method="dense", ascending=False).astype(int)
        
        # Add centrality rankings to results
        for metric in CENTRALITY_METRICS:
            rankings[metric] = ranked_metrics[metric].sort_values()
        
        # Handle status ordering (categorical ranking)
        status_series = sociogram_micro_stats["st"]
        
        # Create a mapping from status to order position
        status_to_order = {status: idx for idx, status in enumerate(STATUS_ORDER)}
        
        # Convert status to numerical order for sorting
        status_with_order = status_series.map(status_to_order)
        
        # Sort by status order FIRST, then by index as secondary sort
        # Create a DataFrame with both status order and original index for sorting
        sort_df = pd.DataFrame({
            'status_order': status_with_order,
            'original_index': sociogram_micro_stats.index
        })
        
        # Sort by status_order first, then by original_index
        sorted_indices = sort_df.sort_values(['status_order', 'original_index']).index
        
        # Return the status series in the new order
        rankings["st"] = status_series.loc[sorted_indices]
        
        # Return rankings
        return rankings
    
    def compute_status(self, sociogram_micro_stats: pd.DataFrame) -> pd.Series:
        """
        Determine sociometric status for each node based on relationship patterns.
        
        Classifies nodes into sociometric status categories based on their pattern
        of positive and negative relationships received and given. Uses quantile-based
        thresholds to distinguish between different levels of social impact and balance.
        
        Args:
            sociogram_micro_stats: DataFrame containing micro-level statistics with
                columns for received/given positive/negative nominations and derived indices.
            
        Returns:
            A pandas Series with sociometric status labels for each node:
                - "isolated": No incoming or outgoing relationships
                - "marginal": Low overall social impact
                - "popular": High positive impact with strong positive dominance
                - "appreciated": Moderate positive impact with positive prevalence  
                - "rejected": High negative impact with strong negative dominance
                - "disliked": Moderate negative impact with negative prevalence
                - "controversial": High impact with balanced positive/negative reception
                - "ambitendent": Moderate impact with balanced positive/negative reception
                
        Note:
            Uses adaptive quantile selection to find thresholds that best match
            theoretical proportions for different impact and balance levels.
        """
        
        def select_best_quantiles(series: pd.Series) -> Tuple[float, float]:
            """
            Select quantile thresholds that best match theoretical proportions.
            
            Tests multiple quantile pairs to find the first one where actual
            proportions are within epsilon tolerance of theoretical values.
            
            Args:
                series: The data series to analyze for quantile selection.
                
            Returns:
                A tuple containing (low_threshold, high_threshold) values.
            """
            # Set epsilon tolerance for quantile matching
            epsilon = 0.05

            # Define quantile pairs to test (low_quantile, high_quantile)
            quantile_pairs = [(0.25, 0.75), (0.2, 0.8), (0.15, 0.85), (0.10, 0.90), (0.05, 0.95)]

            # Test each quantile tuple for best match
            for low_q, high_q in quantile_pairs:
                
                # Calculate quantile values
                low_val = series.quantile(low_q)
                high_val = series.quantile(high_q)
                
                # Calculate actual proportions
                actual_low_prop = (series < low_val).sum() / series.shape[0]
                actual_high_prop = (series > high_val).sum() / series.shape[0]
                
                # Calculate deviations from theoretical proportions
                low_deviation = abs(actual_low_prop - low_q)
                high_deviation = abs(actual_high_prop - (1 - high_q))

                # Return first quantile pair within epsilon tolerance
                if low_deviation <= epsilon and high_deviation <= epsilon:
                    return (low_val, high_val)
            
            # If no quantiles are within epsilon tolerance, 
            # return the last pair as a fallback
            return (low_val, high_val)
        
        # Cache relevant columns for efficiency
        impact = sociogram_micro_stats["im"]
        balance = sociogram_micro_stats["bl"]
        prefs_a = sociogram_micro_stats["rp"]
        prefs_b = sociogram_micro_stats["rr"]
        
        # Get best impact quantiles for classification thresholds
        impact_quantile_low, impact_quantile_high = select_best_quantiles(impact)
        
        # Compute impact level boolean series
        impact_low = impact.lt(impact_quantile_low)
        impact_high = impact.gt(impact_quantile_high)
        impact_median = impact.between(impact_quantile_low, impact_quantile_high, inclusive="both")
        
        # Get absolute balance quantiles for relationship type classification
        abs_balance = balance.abs()
        abs_balance_quantile_low, abs_balance_quantile_high = select_best_quantiles(abs_balance)
        abs_balance_high = abs_balance.gt(abs_balance_quantile_high)
        
        # Compute balance type boolean series
        a_prevalent = balance.gt(0) & ~abs_balance_high
        b_prevalent = balance.lt(0) & ~abs_balance_high
        a_dominant = balance.gt(0) & abs_balance_high
        b_dominant = balance.lt(0) & abs_balance_high
        neutral = abs_balance.lt(abs_balance_quantile_low)
        
        # Initialize status series with default values
        status = pd.Series(["-"] * sociogram_micro_stats.shape[0], index=sociogram_micro_stats.index)
        
        # Assign status classifications based on relationship patterns
        status.loc[sociogram_micro_stats.iloc[:, :4].sum(axis=1).eq(0)] = "isolated"
        status.loc[impact_low] = "marginal"
        
        status.loc[a_dominant & impact_high] = "popular"
        status.loc[a_dominant & impact_median] = "popular"
        
        status.loc[a_prevalent & impact_high] = "appreciated"
        status.loc[a_prevalent & impact_median] = "appreciated"
        
        status.loc[b_dominant & impact_high] = "rejected"
        status.loc[b_dominant & impact_median] = "rejected"
        
        status.loc[b_prevalent & impact_high] = "disliked"
        status.loc[b_prevalent & impact_median] = "disliked"
        
        status.loc[balance.eq(0) & impact_median] = "ambitendent"
        status.loc[balance.eq(0) & impact_high] = "controversial"
        status.loc[prefs_a.mul(prefs_b).gt(0) & neutral & impact_median] = "ambitendent"
        status.loc[prefs_a.mul(prefs_b).gt(0) & neutral & impact_high] = "controversial"
        
        # Return status classifications
        return status

    def create_graph(self, coefficient: Literal["ai", "ii"]) -> str:
        """
        Generate a polar visualization of sociogram rankings.
        
        Creates a circular plot showing the distribution of nodes based on their
        scores in the specified centrality coefficient, with nodes arranged in
        concentric circles and grouped by score levels.

        Args:
            coefficient: The centrality coefficient to visualize. Must be either:
                - "ai": Activity index (balance + orientation)
                - "ii": Integration index (received positive + mutual positive)
        
        Returns:
            A base64-encoded SVG string representing the polar sociogram visualization.
            Nodes are plotted as points with labels, arranged in groups by score level
            with applied jitter to reduce overlap.
            
        Raises:
            AttributeError: If micro_stats have not been computed yet.
        """
        if self.sociogram["micro_stats"] is None:
            raise AttributeError("Micro stats must be computed before creating graphs")
            
        # Get values for the specified coefficient
        data = self.sociogram["micro_stats"].loc[:, [coefficient]].copy()
        
        # Normalize values to [0, 1] range and invert for radial display
        plot_data = data.sub(data.min()).div(data.max() - data.min())
        plot_data = plot_data.max() - plot_data
        
        # Create polar plot figure
        fig, ax = plt.subplots(
            constrained_layout=True, 
            figsize=(19 * CM_TO_INCHES, 19 * CM_TO_INCHES),
            subplot_kw={"projection": "polar"}
        )
        
        # Customize plot appearance
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.get_xaxis().set_visible(False)
        ax.set_ylim(0, 1.1)
        ax.grid(color="#bbb", linestyle="--", linewidth=.8)
        
        # Set jitter parameters to reduce point overlap
        theta_jitter_scale = 0.03
        r_jitter_scale = 0.01
        
        # Plot data points grouped by coefficient value
        for idx, (_, group_plot_data) in enumerate(plot_data.groupby(by=coefficient)):
            # Define angular offset for current group
            offset = idx % 2 * -np.pi + idx * 0.25
            
            # Calculate angular spacing for points in this group
            slice_angle = (2 * np.pi) / group_plot_data[coefficient].shape[0]

            # Reset index to get node labels
            group_plot_data = group_plot_data.reset_index(names="node_labels")

            # Set polar coordinates
            r = group_plot_data[coefficient]
            theta = pd.Series(group_plot_data[coefficient].index.values).mul(slice_angle).add(offset)
            
            # Apply reproducible jitter
            np.random.seed(42 + idx)
            theta_jitter = np.random.normal(0, theta_jitter_scale, len(theta))
            r_jitter = np.random.normal(0, r_jitter_scale, len(r))
            
            # Apply jitter with bounds checking
            theta_jittered = theta + theta_jitter
            r_jittered = np.clip(r + r_jitter, 0, 1.1)
            
            # Plot data points
            ax.scatter(theta_jittered, r_jittered, c="#bbb", s=20)

            # Add node labels
            for i, txt in enumerate(group_plot_data["node_labels"]):
                ax.annotate(txt, (theta_jittered.iloc[i], r_jittered.iloc[i]), 
                          color="blue", fontsize=12)

        # Return base64-encoded SVG
        return figure_to_base64_svg(fig)
