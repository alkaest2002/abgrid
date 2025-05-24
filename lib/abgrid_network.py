"""
Filename: abgrid_network.py
Description: Provides functionality to analyze directed networks (graphs) for a given set of edges.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import io
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import networkx as nx

from typing import Literal, List, Dict, Tuple, Union
from base64 import b64encode
from functools import reduce

# Customize matplotlib settings
matplotlib.rc('font', **{'size': 8})
matplotlib.use("Agg")


class ABGridNetwork:
    """
    Class to represent and analyze directed networks (graphs) for a given set of edges.
    """

    def __init__(self, edges: Tuple[List[Dict[str, str]], List[Dict[str, str]]]):
        """
        Initialize the network analysis object.

        Args:
            edges (Tuple[List[Dict[str, str]], List[Dict[str, str]]]): 
                Tuple containing two lists of dictionaries, each representing edges for two networks.
        """
        
        # Unpack network nodes and edges
        self.nodes_a, self.edges_a = self.unpack_network_nodes_and_edges(edges[0])
        self.nodes_b, self.edges_b = self.unpack_network_nodes_and_edges(edges[1])

        # Initialize data containers for analysis
        self.macro_a = {}
        self.macro_b = {}
        self.micro_a = pd.DataFrame()
        self.micro_b = pd.DataFrame()
        self.graph_a = ""
        self.graph_b = ""

    def unpack_network_nodes_and_edges(self, packed_edges: List[Dict[str, str]]) -> Tuple[List[str], List[Tuple[str, str]]]:
        """
        Convert a list of edge dictionaries into a list of nodes and edge tuples.

        Args:
            packed_edges (List[Dict[str, str]]): List of dictionaries where each key is a "source" node and the corresponding value is a comma-separated string of "target" nodes.

        Returns:
            Tuple[List[str], List[Tuple[str, str]]]: A tuple containing:
                - A list of nodes (List[str]), sorted and containing unique values.
                - A list of edge tuples (List[Tuple[str, str]]), where each tuple is (source, target).
        """
        # Extract unique nodes and sort them
        nodes = sorted(list(set([
            node for node_edges in packed_edges for node, _ in node_edges.items()
        ])))
            
        # Extract edges as tuples while ensuring no errors with None values and preserving format
        edges = reduce(
            lambda acc, itr: [
                *acc,
                *[
                    (node_from, node_to) 
                    for node_from, edges in itr.items()
                    if edges is not None  # Check if edges is not None
                    for node_to in edges.split(",") if node_to  # Ensure no empty targets are processed
                ]
            ],
            packed_edges,
            []
        )

        # Return nodes list and edges list
        return nodes, edges

    def compute_networks(self):
        """
        Compute and store graphs, statistics, and plots for both networks.
        """
        # Create directed graphs for both networks
        Ga = nx.DiGraph(self.edges_a)
        Gb = nx.DiGraph(self.edges_b)

        # Add nodes without edges
        nodes_a_without_edges = set(list(Ga)).symmetric_difference(set(self.nodes_a))
        Ga.add_nodes_from(nodes_a_without_edges)
        nodes_b_without_edges = set(list(Gb)).symmetric_difference(set(self.nodes_b))
        Gb.add_nodes_from(nodes_b_without_edges)
        
        # Generate layout positions for network plotting
        k_a = .5 if len(nodes_a_without_edges) == 0 else 2
        loca = nx.spring_layout(Ga, k=k_a , seed=42)
        k_b = .5 if len(nodes_b_without_edges) == 0 else 2
        locb = nx.spring_layout(Gb, k=k_b, seed=42)
        
        # Store network statistics and plots
        self.macro_a, self.micro_a = self.get_network_stats(Ga)
        self.macro_b, self.micro_b = self.get_network_stats(Gb)
        self.graph_a = self.get_network_graph(Ga, loca, graphType="A")
        self.graph_b = self.get_network_graph(Gb, locb, graphType="B")

    def get_network_graph(self, G: nx.DiGraph, loc: Dict[str, Tuple[float, float]], graphType: Literal["A","B"] = "A") -> str:
        """
        Generate a graphical representation of a network and return it encoded in base64 SVG format.

        Args:
            G (nx.DiGraph): The directed graph to plot.
            loc (Dict[str, Tuple[float, float]]): Node positions for layout.
            graphType (str): Type of the network ('A' or 'B'), used to determine node colors.

        Returns:
            str: The SVG data URI of the network plot.
        """
        # Conversion factor from inches to centimeters
        CM_TO_INCHES = 1 / 2.54

        # Set color based on graph type (A or B)
        color = "#0000FF" if graphType == "A" else "#FF0000"
        
        # Initialize an in-memory buffer
        buffer = io.BytesIO()
        
        # Create a matplotlib figure
        fig, ax = plt.subplots(constrained_layout=True, figsize=(9 * CM_TO_INCHES, 9 * CM_TO_INCHES))
        
        # Hide axis
        ax.axis('off')  
        
        # Draw nodes
        nx.draw_networkx_nodes(G, loc, node_color=color, edgecolors=color, ax=ax)
        
        # Draw node labels
        nx.draw_networkx_labels(G, loc, font_color="#FFF", font_weight="normal", font_size=13, ax=ax)
        
        # Determine mutual and non-mutual edges
        mutual_edges = [e for e in G.edges if e[::-1] in G.edges]
        non_mutual_edges = [e for e in G.edges if e not in mutual_edges]
        
        # Draw mutual edges with specic styles
        nx.draw_networkx_edges(G, loc, edgelist=mutual_edges, edge_color=color, arrowstyle='-', width=3, ax=ax)
        
        # Draw non-mutual edges with specic styles
        nx.draw_networkx_edges(G, loc, edgelist=non_mutual_edges, edge_color=color, style="--", arrowstyle='-|>', arrowsize=15, ax=ax)
        
        # Save figure to the buffer in SVG format then close it
        fig.savefig(buffer, format="svg", bbox_inches='tight', transparent=True, pad_inches=0.05)
        plt.close(fig) 
        
        # Encode the buffer contents to a base64 string
        base64_econded_string = b64encode(buffer.getvalue()).decode()
        
        # Return the data URI for the SVG
        return f"data:image/svg+xml;base64,{base64_econded_string}"

    def get_network_centralization(self, G: nx.Graph) -> float:
        """
        Calculate the centralization of a network.

        The centralization measure indicates how concentrated the network is around its most central node.
        It compares the current network structure to an ideal star network structure.

        Args:
            G (nx.Graph): The graph for which the centralization is calculated.

        Returns:
            float: The centralization value of the network, rounded to three decimal places, or
            np.nan if the computation is not applicable (e.g., for graphs with fewer than three nodes).
        """
        
        # Get number of nodes
        number_of_nodes = G.number_of_nodes()
        
        # Compute node centralities
        node_centralities = pd.Series(dict(nx.degree(G)))

        # Compute Max centrality
        max_centrality = node_centralities.max()
        
        # Compute network centralization
        network_centralization = (
            node_centralities
                .rsub(max_centrality)
                .sum()
                / ((number_of_nodes - 1) * (number_of_nodes - 2))
        )
        
        # Return network centralization
        return round(network_centralization, 3)


    def get_network_stats(self, G: nx.DiGraph) -> Tuple[Dict[str, Union[float, int]], pd.DataFrame]:
        """
        Generate macro-level and micro-level statistics for a graph.

        Args:
            G (nx.DiGraph): The directed graph to analyze.

        Returns:
            Tuple[Dict[str, Union[float, int]], pd.DataFrame]: A dictionary with macro-level stats and a DataFrame with micro-level stats for each node.
        """

        # Create a DataFrame with various network centralities and metrics for each node
        micro_level_stats = pd.concat([
            pd.Series(nx.to_pandas_adjacency(G).apply(lambda x: ", ".join(x[x > 0].index.values), axis=1), name="lns"),
            pd.Series(nx.in_degree_centrality(G), name="ic"),
            pd.Series(nx.pagerank(G, max_iter=1000), name="pr"),
            pd.Series(nx.betweenness_centrality(G), name="bc"),
            pd.Series(nx.closeness_centrality(G), name="cc"),
            pd.Series(nx.hits(G)[0], name="hu"),
        ], axis=1)
        
        # Identify nodes with no in-degree and/or out-degree
        # 0 = mode has in and out-degree, 1 = node does not have in-degre, 
        # 2 = node does not have out-degree, 3 = node does not have either in or out-degree
        micro_level_stats["ni"] = 0
        micro_level_stats["ni"] += (micro_level_stats["ic"] == 0).astype(int)
        micro_level_stats["ni"] += (micro_level_stats["lns"].str.len() == 0).astype(int)*2

        
        # Rank node-specific metrics
        micro_level_stats_ranks = (
            micro_level_stats.iloc[:, 1:-1]
                .apply(lambda x: x.rank(method="dense", ascending=False))
                .add_suffix("_r", axis=1)
            )
        
        # Finalize the micro-level stats DataFrame
        micro_level_stats = (
            pd.concat([micro_level_stats, micro_level_stats_ranks], axis=1)
                .sort_index()
                .round(3)
                .rename_axis(index="letter")
        )
        
        # Calculate network-wide (macro-level) statistics
        Gu = G.to_undirected()
        network_nodes = G.number_of_nodes()
        network_edges = G.number_of_edges()
        network_max_k_clique = max([v for _, v in nx.node_clique_number(Gu).items()])
        network_centralization = self.get_network_centralization(Gu)
        network_transitivity = round(nx.transitivity(G), 3)
        network_reciprocity = round(nx.overall_reciprocity(G), 3)
        
        # Create macro-level stats object
        macro_level_stats = {
            "network_nodes": network_nodes,
            "network_edges": network_edges,
            "network_max_k_clique": network_max_k_clique,
            "network_centralization": network_centralization,
            "network_transitivity": network_transitivity,
            "network_reciprocity": network_reciprocity
        }
        
        # Return both macro-level and micro-level statistics
        return macro_level_stats, micro_level_stats