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
from adjustText import adjust_text

class SociogramDict(TypedDict, total=False):
    micro_stats: Optional[pd.DataFrame]
    macro_stats: Optional[Dict[str, Union[int, float]]]
    graph_ic: Optional[str]
    graph_ac: Optional[str]
    supplemental: Optional[Dict[str, float]]

class ABGridSociogram:

    def __init__(self):
        """
        This initialization sets up the internal dictionary for storing sociogram data.
        """

        # init sociogram dict
        self.sociogram: SociogramDict = {
            "micro_stats": None,
            "macro_stats": None,
            "graph_ic": None,
            "graph_ac": None,
            "supplemental": None
        }

    def compute(self, sna: dict):
        """
        Compute sociogram data from the given structural network analysis (SNA) data.

        This method uses the provided SNA data to generate sociogram-related information,
        which includes graph representations and statistical data.

        Args:
            sna (dict): A dictionary containing social network analysis data. 
                        It includes various metrics computed for networks 
                        which are required for generating sociograms.

        Returns:
            dict: A dictionary containing the computed sociogram data. Its keys include:
                - "graph_ic": The in-component graph representation.
                - "graph_ac": The all-component graph representation.
                Additional keys provide further sociogram-related data and statistics.

        Side Effects:
            - Modifies the `self.sociogram` attribute by populating it with computed
            sociogram data derived from the input SNA data.
        """
        # Compute sociogram data

        self.sociogram = self.get_sociogram_data(sna)
        self.sociogram["graph_ic"] = self.get_sociogram_graph("ic_raw")
        self.sociogram["graph_ac"] = self.get_sociogram_graph("ac_raw")

        # Return sociogram data
        return self.sociogram
    
    def get_sociogram_data(self, sna: dict) -> Dict[str, Union[pd.DataFrame, Dict[str, float]]]:
        """
        Computes a sociogram DataFrame based on two directed graphs representing 
        social network data for preferences and rejections.

        Returns:
            Dict[str, Union[pd.DataFrame, Dict[str, float]]]:
                A dictionary containing sociogram micro and macro statistics and supplemental indices.
        """

        # Get sna data to be used for sociogram analysis
        network_a = sna["network_a"]
        network_b = sna["network_b"]
        adjacency_a = sna["adjacency_a"]
        adjacency_b = sna["adjacency_b"]
 
        # Compute basic data for sociogram micro stats
        out_preferences = pd.Series(dict(network_a.out_degree()), name="gp")
        out_rejects = pd.Series(dict(network_b.out_degree()), name="gr")
        in_preferences = pd.Series(dict(network_a.in_degree()), name="rp")
        in_rejects = pd.Series(dict(network_b.in_degree()), name="rr")
        
        # Init sociogram micro stats dataframe
        sociogram_micro_df = pd.concat([in_preferences, in_rejects, out_preferences, out_rejects], axis=1)

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
        sociogram_micro_df["ac"] = (
            sociogram_micro_df["ac_raw"]
                .sub(sociogram_micro_df["ac_raw"].mean())
                .div(sociogram_micro_df["ac_raw"].std())
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
        sociogram_micro_df["ic"] = (
            sociogram_micro_df["ic_raw"]
                .sub(sociogram_micro_df["ic_raw"].mean())
                .div(sociogram_micro_df["ic_raw"].std())
                .mul(10)
                .add(100)
                .astype(int)
        )
        
        # Add sociogram status
        # 1. Start by computing with z scores of relevat data
        impact = sociogram_micro_df["im"]
        z_impact = impact.sub(impact.mean()).div(impact.std())
        balance = sociogram_micro_df["bl"]
        z_balance = balance.sub(balance.mean()).div(balance.std())

        # 2. Update status: default is "-", unless otherwise specified
        sociogram_micro_df["st"] = "-"
        sociogram_micro_df.loc[sociogram_micro_df.iloc[:, :4].sum(axis=1).eq(0), "st"] = "isolated"
        sociogram_micro_df.loc[z_impact < -1, "st"] = "neglected"
        sociogram_micro_df.loc[z_impact.between(-1, -.5), "st"] = "underrated"
        sociogram_micro_df.loc[np.logical_and(z_impact.between(.5, 1), z_balance > 1), "st"] = "appreciated"
        sociogram_micro_df.loc[np.logical_and(z_impact > 1, z_balance > 1), "st"] = "popular"
        sociogram_micro_df.loc[np.logical_and(z_impact > -.5, z_balance < -1), "st"] = "rejected"
        sociogram_micro_df.loc[np.logical_and(z_impact > 0, z_balance.between(-.5, .5)), "st"] = "controversial"
        
        # Compute sociogram macro stats
        sociogram_numeric_columns = sociogram_micro_df.select_dtypes(np.number)
        median = sociogram_numeric_columns.median()
        sociogram_macro_df = sociogram_numeric_columns.describe().T
        sociogram_macro_df.insert(1, "median", median)

        # Add cohesion indices
        cohesion_index_type_i = (len(sna["edges_types_a"]["type_ii"]) *2) / len(network_a.edges())
        cohesion_index_type_ii = len(sna["edges_types_a"]["type_ii"]) / len(network_a)

        # Add conflict indices
        conflict_index_type_i = (len(sna["edges_types_b"]["type_ii"]) *2) / len(network_b.edges())
        conflict_index_type_ii = len(sna["edges_types_b"]["type_ii"]) / len(network_b)

        # Return sociogram data
        return {
           "micro_stats": sociogram_micro_df.sort_index(),
           "macro_stats": sociogram_macro_df.apply(pd.to_numeric, downcast="integer"),
           "rankings": self.get_sociogram_rankings(sociogram_micro_df),
           "supplemental": {
               "ui_i": cohesion_index_type_i,
               "ui_ii": cohesion_index_type_ii,
               "wi_i": conflict_index_type_i,
               "wi_ii": conflict_index_type_ii
           }
        }
    
    def get_sociogram_rankings(self, micro_stats: pd.DataFrame) -> Dict[str, Dict[Any, int]]:
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
    
    def get_sociogram_graph(self, coeffient: Literal["ac_raw", "ic_raw"]) -> str:
        """
        Generate a graphical representation of sociogram rankings and return it encoded in base64 SVG format.


        Returns:
            str: A base64-encoded SVG string representing the sociogram plot.
        """

        # Create matplotlib plot
        fig = self.create_sociogram_plot(coeffient)
        
        # Convert matplotlib plot to base64 SVG string
        return figure_to_base64_svg(fig)  
    
    def create_sociogram_plot(self, coeffient: Literal["ac_raw", "ic_raw"]):
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
        theta_jitter_scale = 0.05
        r_jitter_scale = 0.02
        
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
            ax.scatter(theta_jittered, r_jittered, alpha=0.6, color="#999", s=20)

            # Alternative way to avoid text collision, with no dependencies
            # for i, txt in enumerate(group_plot_data["node_labels"]):
            #     ax.annotate(
            #         txt, 
            #         (theta_jittered.iloc[i], r_jittered.iloc[i]), 
            #         color="blue",
            #         fontsize=12
            #     )
            
            texts = [ 
                ax.text(
                    theta_jittered[i], 
                    r_jittered[i], 
                    group_plot_data["node_labels"].iat[i], 
                    ha="center", 
                    va="center", 
                    color="blue",
                    fontsize=12, 
                ) for i in range(len(theta_jittered)) 
            ]
            adjust_text(texts)
        
        # Return figure
        return fig