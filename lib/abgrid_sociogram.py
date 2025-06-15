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

from typing import Any, Literal, Dict, Optional, TypedDict, Union
from lib import CM_TO_INCHES
from lib.abgrid_utils import figure_to_base64_svg

class SociogramDict(TypedDict):
    macro_stats: Optional[Dict[str, Union[int, float]]]
    micro_stats: Optional[pd.DataFrame]
    descriptives: Optional[pd.DataFrame]
    rankings: Optional[Dict[str, pd.Series]]
    graph_ii: Optional[str]
    graph_ai: Optional[str]

class ABGridSociogram:
    """
    Analyzes and visualizes social networks by constructing components like macro/micro statistics,
    rankings, and graphical representations of sociograms.
    """

    def __init__(self) -> None:
        """
        Initialize the internal dictionary for storing sociogram data.
        """
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
            sna (Dict[str, Any]): A dictionary containing the social network analysis data.

        Returns:
            SociogramDict: A dictionary containing detailed sociogram data, structured as follows:
                - "macro_stats": Dictionary of network-level statistics.
                - "micro_stats": DataFrame of individual-level statistics.
                - "descriptives": DataFrame with macro-level descriptive statistics.
                - "rankings": Dictionary with rankings of nodes based on different centrality metrics.
                - "graph_ii" and "graph_ai": Strings of base64-encoded SVGs representing graph visualizations.

        Side Effects:
            Updates the `self.sociogram` attribute with the computed sociogram data.
        """
        # Store sna data
        self.sna = sna

        # Compute micro and macro statistics
        sociogram_macro_stats = self.compute_macro_stats()
        sociogram_micro_stats = self.compute_micro_stats()
        sociogram_descriptives = self.compute_descriptives(sociogram_micro_stats)

        # Compute rankings
        rankings = self.compute_rankings(sociogram_micro_stats)

        # Store sociogram data
        self.sociogram = {
            "macro_stats": sociogram_macro_stats,
            "micro_stats": sociogram_micro_stats,
            "descriptives": sociogram_descriptives,
            "rankings": rankings,
        }

        # Create graphs
        self.sociogram["graph_ai"] = self.create_graph("ii")
        self.sociogram["graph_ii"] = self.create_graph("ai")

        # Return sociogram data
        return self.sociogram

    def compute_macro_stats(self) -> pd.Series:
        """
        Compute macro-level sociogram statistics.

        Returns:
            pd.Series: Series containing cohesion and conflict indices for the network.
        """
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
        Compute micro-level sociogram statistics for individual nodes based on social network data.

        Returns:
            pd.DataFrame: DataFrame with micro-level statistics for each node, including metrics like rp, rr, gp, gr, etc.
        """
        
        # Define robust threshold for median/mad computations
        ROBUST_THRESHOLD = max(0.6745, 1.5 - (len(self.sna["nodes_a"]) / 50))

        # Retrieve network and adjacency matrices
        network_a = self.sna["network_a"]
        network_b = self.sna["network_b"]
        adjacency_a = self.sna["adjacency_a"]
        adjacency_b = self.sna["adjacency_b"]
        
        # Init sociogram micro df
        sociogram_micro_stats = pd.concat([
            pd.Series(dict(network_a.in_degree()), name="rp"), 
            pd.Series(dict(network_b.in_degree()), name="rr"),
            pd.Series(dict(network_a.out_degree()), name="gp"), 
            pd.Series(dict(network_b.out_degree()), name="gr"), 
        ], axis=1)

        # Add relevant metrics
        sociogram_micro_stats["mp"] = (adjacency_a * adjacency_a.T).sum(axis=1).astype(int)
        sociogram_micro_stats["mr"] = (adjacency_b * adjacency_b.T).sum(axis=1).astype(int)
        sociogram_micro_stats["bl"] = sociogram_micro_stats["rp"].sub(sociogram_micro_stats["rr"])
        sociogram_micro_stats["or"] = sociogram_micro_stats["gp"].sub(sociogram_micro_stats["gr"])
        sociogram_micro_stats["im"] = sociogram_micro_stats["rp"].add(sociogram_micro_stats["rr"])
        sociogram_micro_stats["ai"] = sociogram_micro_stats["bl"].add(sociogram_micro_stats["or"])
        sociogram_micro_stats["ii"] = sociogram_micro_stats["rp"].add(sociogram_micro_stats["mp"])
        
        # Compute robust z-scores for affiliation index (ai)
        affiliation = sociogram_micro_stats["ai"]
        affiliation_median = affiliation.median()
        affiliation_mad = max(affiliation.sub(affiliation_median).abs().median(), 1e-6)
        sociogram_micro_stats["ai_robust_z"] = (
            affiliation
                .sub(affiliation_median)
                .div(affiliation_mad)
                .mul(ROBUST_THRESHOLD * 10)
                .add(100)
                .astype(int)
                .clip(lower=0, upper=200)
        )

        # Compute robust z-scores for influence index (ii)
        influence = sociogram_micro_stats["ii"]
        influence_median = influence.median()
        influence_mad = max(influence.sub(influence_median).abs().median(), 1e-6)
        sociogram_micro_stats["ii_robust_z"] = (
            influence
                .sub(influence_median)
                .div(influence_mad)
                .mul(ROBUST_THRESHOLD * 10)
                .add(100)
                .astype(int)
                .clip(lower=0, upper=200)
        )

        # Compute status interpretation
        sociogram_micro_stats["st"] = (
            self.compute_status(sociogram_micro_stats)
        )

        # Return sociogram micro statistics
        return sociogram_micro_stats.sort_index()

    def compute_descriptives(self, sociogram_micro_stats: pd.DataFrame) -> pd.DataFrame:
        """
        Compute macro-level descriptive statistics based on micro-level statistics.

        Args:
            sociogram_micro_stats (pd.DataFrame): DataFrame containing micro-level statistics.

        Returns:
            pd.DataFrame: DataFrame with macro-level descriptive statistics including median, IQR, and total sum.
        """
        # Select numeric columns only
        sociogram_numeric_columns = sociogram_micro_stats.select_dtypes(np.number)
        
        # Compute median, IQR and total sum
        median = sociogram_numeric_columns.median()
        iqr = sociogram_numeric_columns.quantile([.75, .25]).apply(lambda x: x.iat[0] - x.iat[1])
        sum_tot = sociogram_numeric_columns.sum(axis=0)
        
        # Get descriptive statistics from pandas describe function
        sociogram_macro_df = sociogram_numeric_columns.describe().T

        # Add median, IQR and total sum statistics
        sociogram_macro_df.insert(1, "median", median)
        sociogram_macro_df.insert(2, "iqr", iqr)
        sociogram_macro_df.insert(1, "sum_tot", sum_tot)

        # Drop unused metrics
        sociogram_macro_df = sociogram_macro_df.drop(["ai_robust_z", "ii_robust_z"])

        # Return sociogram macro statistics
        return sociogram_macro_df.apply(pd.to_numeric, downcast="integer")

    def compute_status(self, sociogram_micro_stats: pd.DataFrame) -> pd.Series:
        """
        Determine sociometric status for each node based on sociogram statistics.
        
        Args:
            sociogram_micro_stats (pd.DataFrame): DataFrame containing micro-level statistics.
            
        Returns:
            pd.Series: Series with sociometric status for each node, indicating states such as isolated, marginal, etc.
        """
        def select_best_quantiles(series: pd.Series, quantile_pairs: list, epsilon: float) -> tuple:
            """
            Select the first quantile pair that matches theoretical proportions within epsilon tolerance.
            
            Args:
                series (pd.Series): The data series to analyze
                quantile_pairs (list): List of (low, high) quantile pairs to test
                epsilon (float): Tolerance for proportion matching
                
            Returns:
                tuple: (low_value, high_value) for the first reasonable match
            """
            n = len(series)
            
            for low_q, high_q in quantile_pairs:
                # Calculate quantile values
                low_val = series.quantile(low_q)
                high_val = series.quantile(high_q)
                
                # Calculate actual proportions
                actual_low_prop = (series < low_val).sum() / n
                actual_high_prop = (series > high_val).sum() / n
                
                # Calculate deviations from theoretical proportions
                low_deviation = abs(actual_low_prop - low_q)
                high_deviation = abs(actual_high_prop - (1 - high_q))

                # Return first quantile pair within epsilon tolerance
                if low_deviation <= epsilon and high_deviation <= epsilon:
                    return (low_val, high_val)
            
            # If no quantiles within epsilon, return the last pair as a fallback
            low_q, high_q = quantile_pairs[-1]
            low_val = series.quantile(low_q)
            high_val = series.quantile(high_q)
            return (low_val, high_val)
        
        # Define quantile pairs to test
        quantile_pairs = [(0.25, 0.75), (0.2, 0.8), (0.15, 0.85), (0.10, 0.90), (0.05, 0.95)]
        
        # Cache relevant columns
        impact = sociogram_micro_stats["im"]
        balance = sociogram_micro_stats["bl"]
        prefs_a = sociogram_micro_stats["rp"]
        prefs_b = sociogram_micro_stats["rr"]
        
        # Get best impact quantiles
        impact_quantile_low, impact_quantile_high = select_best_quantiles(impact, quantile_pairs, 0.05)
        
        # Compute impact boolean series
        impact_low = impact.lt(impact_quantile_low)
        impact_high = impact.gt(impact_quantile_high)
        impact_median = impact.between(impact_quantile_low, impact_quantile_high, inclusive="both")
        
        # Get absolute balance quantiles
        abs_balance = balance.abs()
        abs_balance_quantile_low, abs_balance_quantile_high = select_best_quantiles(abs_balance, quantile_pairs, 0.05)
        abs_balance_high = abs_balance.gt(abs_balance_quantile_high)
        
        # Compute balance boolean series
        a_prevalent = balance.gt(0) & ~abs_balance_high
        b_prevalent = balance.lt(0) & ~abs_balance_high
        a_dominant = balance.gt(0) & abs_balance_high
        b_dominant = balance.lt(0) & abs_balance_high
        neutral = abs_balance.lt(abs_balance_quantile_low)
        
        # Init status as a pandas Series with default value of "-"
        status = pd.Series(["-"] * sociogram_micro_stats.shape[0], index=sociogram_micro_stats.index)
        
        # Compute statuses
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
        
        # Return status
        return status

    def compute_rankings(self, sociogram_micro_stats: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Generate and return the order of nodes based on their rank scores for each specified centrality metric.
        Args:
            sociogram_micro_stats (pd.DataFrame): A DataFrame containing micro-level statistics for nodes
                                            indexed by node identifiers with columns representing metrics.

        Returns:
            Dict[str, pd.Series]: A dictionary where each key corresponds to a metric from the input DataFrame.
                                The value is a pandas Series mapping node identifiers to their rank order
                                (ordinal position) based on the metric scores.
        """
        # Define metrics to rank
        CENTRALITY_METRICS = ["bl", "im", "ai", "ii"]
        
        # Define status ordering (from highest to lowest social status)
        STATUS_ORDER = [
            "popular", "appreciated", "ambitendent", "marginal",
            "controversial", "disliked", "rejected", "isolated"
        ]
        
        # Init dicts
        rankings = {}
        
        # Rank centrality metrics (higher scores get better ranks)
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

    def create_graph(self, coefficient: Literal["ai", "ii"]) -> str:
        """
        Generate a graphical representation of sociogram rankings and return it encoded in base64 SVG format.

        Args:
            coefficient (Literal["ai", "ii"]): The coefficient to be used for plotting the sociogram.
        
        Returns:
            str: A base64-encoded SVG string representing the sociogram plot.
        """
        # Get values
        data = self.sociogram["micro_stats"].loc[:, [coefficient]].copy()
        
        # Normalize values
        plot_data = data.sub(data.min()).div(data.max() - data.min())
        plot_data = plot_data.max() - plot_data
        
        # Create plot figure
        fig, ax = plt.subplots(
            constrained_layout=True, 
            figsize=(19 * CM_TO_INCHES, 19 * CM_TO_INCHES),
            subplot_kw={"projection": "polar"}
        )
        
        # Customize plot figure
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.get_xaxis().set_visible(False)
        ax.set_ylim(0, 1.1)
        ax.grid(color="#bbb", linestyle="--", linewidth=.8)
        
        # Set jitter parameters
        theta_jitter_scale = 0.03
        r_jitter_scale = 0.01
        
        # Plot data points for each group
        for idx, (_, group_plot_data) in enumerate(plot_data.groupby(by=coefficient)):
            # Define starting offset for the current bunch of data points
            offset = idx % 2 * -np.pi + idx * 0.25
            
            # Divide the 360 degree pie into equal size slices 
            # based on the number of dots to be plotted
            slice_angle = (2 * np.pi) / group_plot_data[coefficient].shape[0]

            # Reset index
            group_plot_data = group_plot_data.reset_index(names="node_labels")

            # Set r and theta data for the polar plot
            r = group_plot_data[coefficient]
            theta = pd.Series(group_plot_data[coefficient].index.values).mul(slice_angle).add(offset)
            
            # Seed random state for reproducibility
            np.random.seed(42 + idx)

            # Generate jitter
            theta_jitter = np.random.normal(0, theta_jitter_scale, len(theta))
            r_jitter = np.random.normal(0, r_jitter_scale, len(r))
            
            # Apply jitter with bounds checking
            theta_jittered = theta + theta_jitter
            r_jittered = np.clip(r + r_jitter, 0, 1.1)
            
            # Plot data points
            ax.scatter(theta_jittered, r_jittered, c="#bbb", s=20)

            # Annotate point labels
            for i, txt in enumerate(group_plot_data["node_labels"]):
                ax.annotate(txt, (theta_jittered.iloc[i], r_jittered.iloc[i]), color="blue", fontsize=12)

        # Return figure
        return figure_to_base64_svg(fig)
