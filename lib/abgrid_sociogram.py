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
    rankings: Optional[pd.DataFrame]
    supplemental: Optional[Dict[str, float]]
    graph_ic: Optional[str]
    graph_ac: Optional[str]

class ABGridSociogram:
    """
    Analyzes and visualizes social networks by constructing components like macro/micro statistics,
    rankings, and graphical representations of sociograms.
    """

    def __init__(self) -> None:
        """
        Initialize internal dictionary for storing sociogram data.
        """
        self.sociogram: SociogramDict = {
            "macro_stats": None,
            "micro_stats": None,
            "rankings": None,
            "supplemental": None,
            "graph_ic": None,
            "graph_ac": None,
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
                - "rankings": DataFrame of metrics to node rank orders.
                - "supplemental": Dictionary with cohesion and conflict indices.
                - "graph_ic" and "graph_ac": Strings of base64-encoded SVGs representing graph visualizations.

        Side Effects:
            Updates the `self.sociogram` attribute with the computed sociogram data.
        """
        # Retrieve SNA data
        network_a = sna["network_a"]
        network_b = sna["network_b"]

        # Compute robust threshold (needed for some media/mad related computations)
        robust_threshold = max(0.6745, 1.5 - (len(sna["nodes_a"]) / 50))
        
        # Compute micro and macro statistics
        sociogram_micro_df = self.compute_micro_stats(sna, robust_threshold)
        sociogram_macro_df = self.compute_macro_stats(sociogram_micro_df)

        # Compute rankings
        rankings = self.compute_rankings(sociogram_micro_df)

        # Calculate cohesion and conflict indices
        cohesion_index_type_i = (len(sna["edges_types_a"]["type_ii"]) * 2) / len(network_a.edges())
        cohesion_index_type_ii = len(sna["edges_types_a"]["type_ii"]) / len(network_a)
        conflict_index_type_i = (len(sna["edges_types_b"]["type_ii"]) * 2) / len(network_b.edges())
        conflict_index_type_ii = len(sna["edges_types_b"]["type_ii"]) / len(network_b)

        # Store sociogram data
        self.sociogram = {
            "micro_stats": sociogram_micro_df,
            "macro_stats": sociogram_macro_df,
            "rankings": rankings,
            "supplemental": {
                "ui_i": cohesion_index_type_i,
                "ui_ii": cohesion_index_type_ii,
                "wi_i": conflict_index_type_i,
                "wi_ii": conflict_index_type_ii
            },
        }
        
        # Generate sociogram graphs
        self.sociogram["graph_ic"] = self.create_graph("ii")
        self.sociogram["graph_ac"] = self.create_graph("ai")

        return self.sociogram

    def compute_macro_stats(self, sociogram_micro_df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute macro-level sociogram statistics based on micro-level statistics.

        Args:
            sociogram_micro_df (pd.DataFrame): DataFrame containing micro-level statistics.

        Returns:
            pd.DataFrame: DataFrame with macro-level descriptive statistics including median, IQR, and total sum.
        """
        # Select numeric columns only
        sociogram_numeric_columns = sociogram_micro_df.select_dtypes(np.number)
        
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
    
    def compute_micro_stats(self, sna: Dict[str, Any], robust_threshold: float) -> pd.DataFrame:
        """
        Compute micro-level sociogram statistics for individual nodes based on social network data.

        Args:
            sna (Dict[str, Any]): Dictionary containing network data with relevant keys.

        Returns:
            pd.DataFrame: DataFrame with micro-level statistics for each node, including metrics like rp, rr, gp, gr, etc.
        """
        # Retrieve network and adjacency matrices
        network_a = sna["network_a"]
        network_b = sna["network_b"]
        adjacency_a = sna["adjacency_a"]
        adjacency_b = sna["adjacency_b"]
        
        # Init sociogram micro df
        sociogram_micro_df = pd.concat([
            pd.Series(dict(network_a.in_degree()), name="rp"), 
            pd.Series(dict(network_b.in_degree()), name="rr"),
            pd.Series(dict(network_a.out_degree()), name="gp"), 
            pd.Series(dict(network_b.out_degree()), name="gr"), 
        ], axis=1)

        # Add relevant metrics
        sociogram_micro_df["mp"] = (adjacency_a * adjacency_a.T).sum(axis=1).astype(int)
        sociogram_micro_df["mr"] = (adjacency_b * adjacency_b.T).sum(axis=1).astype(int)
        sociogram_micro_df["bl"] = sociogram_micro_df["rp"].sub(sociogram_micro_df["rr"])
        sociogram_micro_df["or"] = sociogram_micro_df["gp"].sub(sociogram_micro_df["gr"])
        sociogram_micro_df["im"] = sociogram_micro_df["rp"].add(sociogram_micro_df["rr"])
        sociogram_micro_df["ai"] = sociogram_micro_df["bl"].add(sociogram_micro_df["or"])
        
        # Compute robust z-scores for affiliation index (ai)
        affiliation_idx = sociogram_micro_df["ai"]
        median_affiliation_coeff = affiliation_idx.median()
        mad_affiliation_coeff = max(affiliation_idx.sub(median_affiliation_coeff).abs().median(), 1e-6)
        sociogram_micro_df["ai_robust_z"] = (
            affiliation_idx
                .sub(median_affiliation_coeff)
                .div(mad_affiliation_coeff)
                .mul(robust_threshold * 10)
                .add(100)
                .astype(int)
        )

        # Compute robust z-scores for influence index (ii)
        sociogram_micro_df["ii"] = sociogram_micro_df["rp"].add(sociogram_micro_df["mp"])
        influence_idx = sociogram_micro_df["ii"]
        median_influence_coeff = influence_idx.median()
        mad_influence_coeff = max(influence_idx.sub(median_influence_coeff).abs().median(), 1e-6)
        sociogram_micro_df["ii_robust_z"] = (
            influence_idx
                .sub(median_influence_coeff)
                .div(mad_influence_coeff)
                .mul(robust_threshold * 10)
                .add(100)
                .astype(int)
        )

        sociogram_micro_df["st"] = self.compute_status_interpretation(sociogram_micro_df, robust_threshold)
        return sociogram_micro_df.sort_index()

    def compute_status_interpretation(self, sociogram_micro_df: pd.DataFrame, robust_threshold: float) -> pd.Series:
        """
        Determine sociometric status for each node based on sociogram statistics.

        Args:
            sociogram_micro_df (pd.DataFrame): DataFrame containing micro-level statistics.
            robust_threshold (float): The robustness threshold used for calculating certain metrics.

        Returns:
            pd.Series: Series with sociometric status for each node, indicating states such as isolated, marginal, etc.
        """
        # Cache relevant columns
        received_preferences = sociogram_micro_df["rp"]
        received_rejections = sociogram_micro_df["rr"]
        impact = sociogram_micro_df["im"]
        balance = sociogram_micro_df["bl"]
        
        # Compute robust impact
        median_impact = impact.median()
        mad_impact = max(impact.sub(median_impact).abs().median(), 1e-6)
        robust_z_impact = (
            impact
                .sub(median_impact)
                .div(mad_impact)
                .mul(robust_threshold)
        )

        # Compute absolute balance
        abs_balance = balance.abs()

        # Compute positive, neutral, and negative evaluations
        positive_eval = np.logical_and(balance > 0, abs_balance > median_impact)
        negative_eval = np.logical_and(balance < 0, abs_balance > median_impact)
        neutral_eval = np.logical_and(
            received_preferences
                .mul(received_rejections).gt(0), abs_balance.between(1, abs_balance.median())
        )

        # Compute status
        status = pd.Series(["-"] * sociogram_micro_df.shape[0], index=sociogram_micro_df.index)
        status.loc[sociogram_micro_df.iloc[:, :4].sum(axis=1).eq(0)] = "isolated"
        status.loc[robust_z_impact < -1] = "marginal"
        status.loc[np.logical_and(positive_eval, robust_z_impact.between(-1, 1))] = "appreciated"
        status.loc[np.logical_and(negative_eval, robust_z_impact.between(-1, 1))] = "disliked"
        status.loc[np.logical_and(neutral_eval, robust_z_impact.between(-1, 1))] = "ambivalent"
        status.loc[np.logical_and(positive_eval, robust_z_impact > 1)] = "popular"
        status.loc[np.logical_and(negative_eval, robust_z_impact > 1)] = "rejected"
        status.loc[np.logical_and(neutral_eval, robust_z_impact > 1)] = "controversial"

        # Return status
        return status

    def compute_rankings(self, micro_stats: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        Generate and return the order of nodes based on their rank scores for each specified centrality metric.

        Args:
            micro_stats (pd.DataFrame): A DataFrame containing micro-level statistics for nodes
                indexed by node identifiers with columns representing metrics.

        Returns:
            Dict[str, pd.Series]: A dictionary where each key corresponds to a metric from the input DataFrame.
                The value is a pandas Series mapping node identifiers to their rank order
                (ordinal position) based on the metric scores.
        """
        # Select metrics
        metrics = micro_stats.loc[:, ["rp", "rr", "gp", "gr", "bl", "im", "ai", "ii"]]

        # Compute and return rankings
        return metrics.rank(method="dense", ascending=False)

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
