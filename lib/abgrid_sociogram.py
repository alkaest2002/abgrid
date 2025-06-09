"""
Filename: abgrid_network.py
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

class SociogramDict(TypedDict, total=False):
    macro_stats: Optional[Dict[str, Union[int, float]]]
    micro_stats: Optional[pd.DataFrame]
    supplemental: Optional[Dict[str, float]]
    graph_ic: Optional[str]
    graph_ac: Optional[str]

class ABGridSociogram:

    def __init__(self):
        """
        This initialization sets up the internal dictionary for storing sociogram data.
        """

        # init sociogram dict
        self.sociogram: SociogramDict = {
            "macro_stats": None,
            "micro_stats": None,
            "supplemental": None,
            "graph_ic": None,
            "graph_ac": None,
        }

    def get(self, sna: dict):
        """
        Compute and store sociogram-related data from the provided social network analysis (SNA) data.

        Args:
            sna (dict): A dictionary containing the social network analysis data. This should include.

        Returns:
            dict: A dictionary containing detailed sociogram data, structured as follows:
                - "micro_stats": DataFrame of individual-level statistics.
                - "macro_stats": DataFrame of network-level statistics.
                - "rankings": A dictionary mapping metrics to node rank orders.
                - "supplemental": Dictionary with cohesion and conflict indices.
                - "graph_ic" and "graph_ac": Strings of base64-encoded SVGs representing graph visualizations.

        Side Effects:
            - The `self.sociogram` attribute is updated with the computed sociogram data based on the input
            SNA data, encapsulating both statistical and visual components.
        """           
        # Get sna data to be used for sociogram analysis
        network_a = sna["network_a"]
        network_b = sna["network_b"]
        
        # Compute micro and macro statistics
        sociogram_micro_df = self.compute_micro_stats(sna)
        sociogram_macro_df = self.compute_macro_stats(sociogram_micro_df)

        # Compute rankings
        rankings = self.compute_rankings(sociogram_micro_df)

        # Add cohesion indices
        cohesion_index_type_i = (len(sna["edges_types_a"]["type_ii"]) *2) / len(network_a.edges())
        cohesion_index_type_ii = len(sna["edges_types_a"]["type_ii"]) / len(network_a)

        # Add conflict indices
        conflict_index_type_i = (len(sna["edges_types_b"]["type_ii"]) *2) / len(network_b.edges())
        conflict_index_type_ii = len(sna["edges_types_b"]["type_ii"]) / len(network_b)

        # Compute sociogram data
        self.sociogram =  {
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
    
        # Add sociogram graphs
        self.sociogram["graph_ic"] = self.create_graph("ic_raw")
        self.sociogram["graph_ac"] = self.create_graph("ac_raw")

        # return sociogram data
        return self.sociogram
        
    def compute_macro_stats(self, sociogram_micro_df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes macro-level sociogram statistics based on micro-level statistics.

        Args:
            sociogram_micro_df (pd.DataFrame): DataFrame containing micro-level statistics

        Returns:
            pd.DataFrame: DataFrame with macro-level descriptive statistics
        """
        # Compute sociogram macro stats
        sociogram_numeric_columns = sociogram_micro_df.select_dtypes(np.number)
        median = sociogram_numeric_columns.median()
        iqr = sociogram_numeric_columns.quantile([.75, .25]).apply(lambda x: x.iat[0] - x.iat[1])
        sociogram_macro_df = sociogram_numeric_columns.describe().T
        sociogram_macro_df.insert(1, "median", median)
        sociogram_macro_df.insert(2, "iqr", iqr)
        
        # Return sociogram macro stats
        return sociogram_macro_df.apply(pd.to_numeric, downcast="integer")
    
    def compute_micro_stats(self, sna: dict) -> pd.DataFrame:
        """
        Computes micro-level sociogram statistics for individual nodes based on 
        social network data for preferences and rejections.

        Args:
            sna (dict): Dictionary containing network data with keys:
                - network_a: NetworkX graph for preferences
                - network_b: NetworkX graph for rejections  
                - adjacency_a: Adjacency matrix for preferences
                - adjacency_b: Adjacency matrix for rejections

        Returns:
            pd.DataFrame: DataFrame with micro-level statistics for each node
        """
        # Get sna data to be used for sociogram analysis
        network_a = sna["network_a"]
        network_b = sna["network_b"]
        adjacency_a = sna["adjacency_a"]
        adjacency_b = sna["adjacency_b"]
        
        # Init sociogram micro stats dataframe
        sociogram_micro_df = pd.concat([
            pd.Series(dict(network_a.in_degree()), name="rp"), 
            pd.Series(dict(network_b.in_degree()), name="rr"),
            pd.Series(dict(network_a.out_degree()), name="gp"), 
            pd.Series(dict(network_b.out_degree()), name="gr"), 
            ], axis=1
        )

        # Compute threshold for calculations relating to median and mad
        ROBUST_THRESHOLD = max(0.6745, 1.5 - (sociogram_micro_df.shape[0] / 50))

        # Add mutual preferences
        sociogram_micro_df["mp"] = (adjacency_a * adjacency_a.T).sum(axis=1).astype(int)

        # Add mutual rejections
        sociogram_micro_df["mr"] = (adjacency_b * adjacency_b.T).sum(axis=1).astype(int)

        # Add balance: received preferences - received rejections
        sociogram_micro_df["bl"] = (
            sociogram_micro_df["rp"]
                .sub(sociogram_micro_df["rr"])
        )

        # Add orientation: give preferences - given rejections       
        sociogram_micro_df["or"] = (
            sociogram_micro_df["gp"]
                .sub(sociogram_micro_df["gr"])
        )

        # Add impact: received preferences + received rejections
        sociogram_micro_df["im"] = (
            sociogram_micro_df["rp"]
                .add(sociogram_micro_df["rr"])
        )

        # Add affiliation coefficient raw: balance + orientation
        sociogram_micro_df["ac_raw"] = (
            sociogram_micro_df["bl"]
                .add(sociogram_micro_df["or"])
        )

        # Add affiliation coefficient
        affiliation_coeff = sociogram_micro_df["ac_raw"]
        median_affiliation_coeff = affiliation_coeff.median()
        mad_affiliation_coeff = (
            max(affiliation_coeff.sub(median_affiliation_coeff).abs().median(), 1e-6) # ensure no zero division
        )
        sociogram_micro_df["ac"] = (
            affiliation_coeff
                .sub(median_affiliation_coeff)
                .div(mad_affiliation_coeff)
                .mul(ROBUST_THRESHOLD)
                .mul(10)
                .add(100)
                .astype(int)
        )

        # Add influence coefficient raw: received preferences + mutual preferences
        sociogram_micro_df["ic_raw"] = (
            sociogram_micro_df["rp"]
                .add(sociogram_micro_df["mp"])
        )

        # Add influence coefficient
        influence_coeff = sociogram_micro_df["ic_raw"]
        median_influence_coeff = influence_coeff.median()
        mad_influence_coeff = (
            max(influence_coeff.sub(median_influence_coeff).abs().median(), 1e-6) # ensure no zero division
        )
        sociogram_micro_df["ic"] = (
            influence_coeff
                .sub(median_influence_coeff)
                .div(mad_influence_coeff)
                .mul(ROBUST_THRESHOLD)
                .mul(10)
                .add(100)
                .astype(int)
        )

        # Cache relevant columns to be used in following calculations
        received_preferences = sociogram_micro_df["rp"]
        received_rejections = sociogram_micro_df["rr"]
        impact = sociogram_micro_df["im"]
        balance = sociogram_micro_df["bl"]
        
        # Compute robust z score for impact 
        median_impact = impact.median()
        mad_impact = impact.sub(median_impact).abs().median()
        mad_impact = max(mad_impact, 1e-6) # ensure no zero division
        robust_z_impact = impact.sub(median_impact).div(mad_impact).mul(ROBUST_THRESHOLD)

        # Compute balance related data
        # (i.e., received preference - received rejections)
        abs_balance = balance.abs()
        median_rprr = received_preferences.add(received_rejections).median()

        # Define positive, negative and neutral evaluations
        positive_eval = np.logical_and(balance > 0, abs_balance > median_rprr)
        negative_eval = np.logical_and(balance < 0, abs_balance >  median_rprr)
        neutral_eval = np.logical_and(
            received_preferences.mul(received_rejections).gt(0),
            abs_balance.between(1, abs_balance.median())
        )

        # Define status: default is "-", unless otherwise specified
        sociogram_micro_df["st"] = "-"
        sociogram_micro_df.loc[sociogram_micro_df.iloc[:, :4].sum(axis=1).eq(0), "st"] = "isolated"
        sociogram_micro_df.loc[robust_z_impact < -1, "st"] = "marginal"
        sociogram_micro_df.loc[np.logical_and(positive_eval, robust_z_impact.between(-1, 1)), "st"] = "appreciated"
        sociogram_micro_df.loc[np.logical_and(negative_eval, robust_z_impact.between(-1, 1)), "st"] = "disliked"
        sociogram_micro_df.loc[np.logical_and(neutral_eval, robust_z_impact.between(-1, 1)), "st"] = "ambivalent"
        sociogram_micro_df.loc[np.logical_and(positive_eval, robust_z_impact > 1), "st"] = "popular"
        sociogram_micro_df.loc[np.logical_and(negative_eval, robust_z_impact > 1), "st"] = "rejected"
        sociogram_micro_df.loc[np.logical_and(neutral_eval, robust_z_impact > 1), "st"] = "controversial"
        
        # Return sociogram micro stats
        return sociogram_micro_df.sort_index()

    def compute_rankings(self, micro_stats: pd.DataFrame) -> Dict[str, Dict[Any, int]]:
        """
        Generate and return the order of nodes based on their rank scores for each specified centrality metric.

        Args:
            micro_stats (pd.DataFrame): A DataFrame containing micro-level statistics for nodes
                indexed by node identifiers with columns representing metrics.

        Returns:
            Dict[str, Dict[Any, int]]: A dictionary where each key corresponds to a metric from the input DataFrame.
                The value is another dictionary mapping node identifiers to their rank order
                (ordinal position) based on the metric scores.
        """

        # Initialize dictionary to store ordered node rankings
        nodes_ordered_by_rank = {}

        # Get columns that represent rank data
        metrics = micro_stats.loc[:, [ "rp", "rr", "gp", "gr", "bl", "im", "ac_raw", "ic_raw" ]]
        
        # For each metric, nodes will be ordered by their relative rank
        for metric_label, metric_data in metrics.items():
            series = (
                metric_data
                    .rank(method="dense", ascending=False)
                    .to_frame()
                    .reset_index()
                    .sort_values(by=[metric_label, "index"])
                    .set_index("index").squeeze()
            )
            series = pd.to_numeric(series, downcast="integer")
            nodes_ordered_by_rank[metric_label] = series.to_dict()
        
        # Return the dictionary of nodes ordered by their rank for each metric
        return nodes_ordered_by_rank
    
    def create_graph(self, coeffient: Literal["ac_raw", "ic_raw"]) -> str:
        """
        Generate a graphical representation of sociogram rankings and return it encoded in base64 SVG format.


        Returns:
            str: A base64-encoded SVG string representing the sociogram plot.
        """

        # Create matplotlib plot
        fig = self.create_fig(coeffient)
        
        # Convert matplotlib plot to base64 SVG string
        return figure_to_base64_svg(fig)  
    
    def create_fig(self, coeffient: Literal["ac_raw", "ic_raw"]):
        """
        Create a polar plot of sociogram data normalized to [0, 1].
        Args:
            coefficient (Literal["ac_raw", "ic_raw"]): The coefficient to be used for plotting.
            Must be one of "ac_raw" or "ic_raw", indicating which micro-level metric to visualize.
        Returns:
            plt.Figure: A matplotlib Figure object containing the plot.
        """
        # Get values
        data = self.sociogram["micro_stats"].loc[:, [coeffient]].copy()
        
        # Normalize values
        plot_data = data.sub(data.min()).div(data.max() - data.min())
        plot_data = plot_data.max() - plot_data
        
        # Create plot figure
        fig, ax = plt.subplots(
            figsize=(25 * CM_TO_INCHES, 25 * CM_TO_INCHES),
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
        for idx, (_, group_plot_data) in enumerate(plot_data.groupby(by=coeffient)):
            
            # Define starting offset for the current bunch of data points
            offset = idx % 2 * -np.pi + idx * .25
            
            # Divide the 360 degree pie into equal size slices based on the number of dots
            # to be plotted
            slice_angle = (2 * np.pi) / group_plot_data[coeffient].shape[0]
            
            # Reset index
            group_plot_data = group_plot_data.reset_index(names="node_labels")
            
            # Set r and theta data for the polar plot
            r = group_plot_data[coeffient]
            theta = pd.Series(group_plot_data[coeffient].index.values).mul(slice_angle).add(offset)
            
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

            # Alternative way to avoid text collision, with no dependencies
            for i, txt in enumerate(group_plot_data["node_labels"]):
                ax.annotate(
                    txt, 
                    (theta_jittered.iloc[i], r_jittered.iloc[i]), 
                    color="blue",
                    fontsize=12
                )

        # Return figure
        return fig