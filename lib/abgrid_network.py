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
        
        # Unpack network edges for both networks A (choices) and B (refusals)
        # i.e., from {"A": "B, C"} to [(A,B), (A,C)]
        self.edges_a = self.unpack_network_edges(edges[0])
        self.edges_b = self.unpack_network_edges(edges[1])
        
        # Extract nodes for both networks
        self.nodes_a = sorted(set([n[0] for n in self.edges_a]))
        self.nodes_b = sorted(set([n[0] for n in self.edges_b]))

        # Initialize data containers for analysis
        self.macro_a = {}
        self.macro_b = {}
        self.micro_a = pd.DataFrame()
        self.micro_b = pd.DataFrame()
        self.graph_a = ""
        self.graph_b = ""

    def unpack_network_edges(self, packed_edges: List[Dict[str, str]]) -> List[Tuple[str, str]]:
        """
        Convert a list of edge dictionaries into a list of edge tuples.

        Args:
            packed_edges (List[Dict[str, str]]): List of dictionaries representing edges with comma-separated targets.

        Returns:
            List[Tuple[str, str]]: List of edge tuples (source, target).
        """
        return reduce(
            lambda acc, itr: [*acc, *[(node_from, node_to) for node_from, edges in itr.items() for node_to in edges.split(",")]],
            packed_edges,
            []
        )

    def compute_networks(self):
        """
        Compute and store graphs, statistics, and plots for both networks.
        """
        # Create directed graphs for both networks
        Ga = nx.DiGraph(self.edges_a)
        Gb = nx.DiGraph(self.edges_b)
        
        # Generate layout positions for network plotting
        loca = nx.spring_layout(Ga, k=.5, seed=42)
        locb = nx.spring_layout(Gb, k=.3, seed=42)
        
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

    def get_network_centralization(self, G: nx.Graph, number_of_nodes: int) -> float:
        """
        Calculate the centralization of a network.

        The centralization measure indicates how concentrated the network is around its most central node.
        It compares the current network structure to an ideal star network structure.

        Args:
            G (nx.Graph): The graph for which the centralization is calculated.
            number_of_nodes (int): The number of nodes in the graph.

        Returns:
            float: The centralization value of the network, rounded to three decimal places, or
            np.nan if the computation is not applicable (e.g., for graphs with fewer than three nodes).
        """
        
        # Compute node centralities
        node_centralities = pd.Series(dict(nx.degree(G)))
        
        # Compute network centralization
        network_centralization = (
            node_centralities
                .rsub(node_centralities.max())
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
            pd.Series({node: nx.local_reaching_centrality(G, node) for node in G.nodes()}, name="or"),
        ], axis=1)
        
        # Identify nodes with zero in-degree and add to micro-level stats DataFrame
        micro_level_stats = micro_level_stats.assign(ni=(lambda x: (x['ic'] == 0).astype(int)))
        
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
        network_centralization = self.get_network_centralization(Gu, network_nodes)
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