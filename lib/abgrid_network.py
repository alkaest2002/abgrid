"""
Filename: abgrid_network.py
Description: Provides functionality to analyze directed networks (graphs) for a given set of edges.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import io
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import networkx as nx

from typing import Any, Literal, List, Dict, Tuple
from base64 import b64encode
from functools import reduce

# Customize matplotlib settings
matplotlib.rc('font', **{'size': 8})
matplotlib.use("Agg")


class ABGridNetwork:
    """
    Class to represent and analyze directed networks (graphs) for a given set of edges.
    """

    def __init__(self, packed_edges: Tuple[List[Dict[str, str]], List[Dict[str, str]]]):
        """
        Initialize the network analysis object.

        Args:
            packed_edges (Tuple[List[Dict[str, str]], List[Dict[str, str]]]): 
                Tuple containing two lists of dictionaries, each representing edges for two networks.
        """
        
        # Unpack network nodes and edges
        self.nodes_a = self.unpack_network_nodes(packed_edges[0])
        self.nodes_b = self.unpack_network_nodes(packed_edges[1])
        self.edges_a = self.unpack_network_edges(packed_edges[0])
        self.edges_b = self.unpack_network_edges(packed_edges[1])

        # Initialize data containers for analysis
        self.macro_stats_a = {}
        self.macro_stats_b = {}
        self.micro_stats_a = pd.DataFrame()
        self.micro_stats_b = pd.DataFrame()
        self.nodes_a_rankings = []
        self.edges_a_types = []
        self.nodes_b_rankings = []
        self.edges_b_types = []
        self.graph_a = ""
        self.graph_b = ""

    def compute_networks(self):
        """
        Compute and store graphs, statistics, and plots for both networks.
        """
        
        # Create network A and B
        Ga = nx.DiGraph(self.edges_a)
        Gb = nx.DiGraph(self.edges_b)
        
        # Add nodes without edges to network A
        nodes_a_without_edges = set(list(Ga)).symmetric_difference(set(self.nodes_a))
        Ga.add_nodes_from(nodes_a_without_edges)
        
        # Add nodes without edges to network B
        nodes_b_without_edges = set(list(Gb)).symmetric_difference(set(self.nodes_b))
        Gb.add_nodes_from(nodes_b_without_edges)
        
        # Generate layout positions for network A and B
        loc_a = nx.kamada_kawai_layout(Ga)
        loc_b = nx.kamada_kawai_layout(Gb)
        
        # Store network A and B statistics and plots
        self.macro_stats_a = self.get_network_macro_stats(Ga)
        self.macro_stats_b = self.get_network_macro_stats(Gb)
        self.micro_stats_a = self.get_network_micro_stats(Ga)
        self.micro_stats_b = self.get_network_micro_stats(Gb)
        self.nodes_a_rankings = self.get_nodes_rankings(self.micro_stats_a)
        self.nodes_b_rankings = self.get_nodes_rankings(self.micro_stats_b)
        self.edges_a_types = self.get_edges_types(Ga, self.edges_a, Gb)
        self.edges_b_types = self.get_edges_types(Gb, self.edges_b, Ga)
        self.graph_a = self.get_network_graph(Ga, loc_a, "A")
        self.graph_b = self.get_network_graph(Gb, loc_b, "B")

    def unpack_network_edges(self, packed_edges: List[Dict[str, str]]) -> List[Tuple[str, str]]:
        """
        Unpack a list of packed edge dictionaries into a list of edge tuples.

        Each dictionary in `packed_edges` maps a source node to a comma-separated string of target nodes.
        This function extracts these relationships and converts them into a list of tuples, where each 
        tuple represents a directed edge from a source node to a target node.

        Args:
            packed_edges (List[Dict[str, str]]): A list of dictionaries, where each dictionary has a 
            source node as the key and a string consisting of comma-separated target nodes as the value.
            The value can also be None, indicating no target nodes for that source.

        Returns:
            List[Tuple[str, str]]: A list of edge tuples, where each tuple is of the form 
            (source, target), representing a directed edge from the source node to the target node.
        """
        # Extract edges as tuples while ensuring no errors with None values
        return reduce(
            lambda acc, itr: [
                *acc,
                *[
                    (node_from, node_to) for node_from, edges in itr.items() if edges is not None
                        for node_to in edges.split(",")
                ]
            ],
            packed_edges,
            []
        )
        
    def unpack_network_nodes(self, packed_edges: List[Dict[str, str]]) -> list[str]:
        """
        Extract and return a sorted list of unique source nodes from a list of packed edge dictionaries.

        Each dictionary in `packed_edges` has a source node as the key. This function collects all 
        unique source nodes and returns them in a sorted order.

        Args:
            packed_edges (List[Dict[str, str]]): A list of dictionaries where each dictionary's key 
            represents a "source" node. The values are strings of "target" nodes, which are ignored 
            by this function.

        Returns:
            List[str]: A sorted list of unique source node identifiers.
        """
        # Extract nodes and sort them
        return sorted([
            node for node_edges in packed_edges for node, _ in node_edges.items()
        ])
    
    def get_network_macro_stats(self, G: nx.DiGraph) -> Dict[str, Any]:
        """
        Calculate and return macro-level statistics for a directed network graph.

        This method computes several statistics about the structure and connectivity of the given
        NetworkX directed graph `G`, including the number of nodes, the number of edges, 
        centralization, transitivity, and reciprocity.

        Args:
            G (nx.DiGraph): A directed graph represented using NetworkX's DiGraph class.

        Returns:
            Dict[str, Any]: A dictionary containing the following macro-level statistics:
                - "network_nodes": int, the total number of nodes in the graph.
                - "network_edges": int, the total number of edges in the graph.
                - "network_centralization": float, the centralization of the undirected version of the graph.
                - "network_transitivity": float, the transitivity of the graph rounded to three decimal places.
                - "network_reciprocity": float, the reciprocity of the graph rounded to three decimal places.
        """
        # Compute macro-level statistics
        network_nodes = G.number_of_nodes()
        network_edges = G.number_of_edges()
        network_centralization = self.get_network_centralization(G.to_undirected())
        network_transitivity = round(nx.transitivity(G), 3)
        network_reciprocity = round(nx.overall_reciprocity(G), 3)
        
        # Return macro-level statistics
        return {
            "network_nodes": network_nodes,
            "network_edges": network_edges,
            "network_centralization": network_centralization,
            "network_transitivity": network_transitivity,
            "network_reciprocity": network_reciprocity,
        }
    
    def get_network_micro_stats(self, G: nx.DiGraph) -> pd.DataFrame:
        """
        Calculate and return micro-level statistics for each node in a directed network graph.

        This method computes several node-specific centrality metrics for a given NetworkX directed
        graph `G` and organizes them into a pandas DataFrame. Additionally, it identifies nodes
        without incoming or outgoing connections and calculates relative ranks and percentiles for each
        centrality measure.

        Args:
            G (nx.DiGraph): A directed graph represented using NetworkX's DiGraph class.

        Returns:
            pd.DataFrame: A DataFrame containing micro-level statistics for each node, including:
                - "lns": List of nodes each node links to as a comma-separated string.
                - "ic": In-degree centrality.
                - "pr": PageRank.
                - "bt": Betweenness centrality.
                - "cl": Closeness centrality.
                - "hu": HITS hub score.
                - "nd": Category indicating node degree presence (0: has in and out-degree, 1: lacks in-degree,
                2: lacks out-degree, 3: lacks both in and out-degree).
                - Additional columns for each centrality measure's rank and percentile.

        The DataFrame is sorted by index and rounded to three decimal places for centrality measures and percentiles.
        """
        # Create a DataFrame with micro-level statistics
        micro_level_stats = pd.concat([
            pd.Series(nx.to_pandas_adjacency(G).apply(lambda x: ", ".join(x[x > 0].index.values), axis=1), name="lns"),
            pd.Series(nx.in_degree_centrality(G), name="ic"),
            pd.Series(nx.pagerank(G, max_iter=1000), name="pr"),
            pd.Series(nx.betweenness_centrality(G), name="bt"),
            pd.Series(nx.closeness_centrality(G), name="cl"),
            pd.Series(nx.hits(G)[0], name="hu").abs(),
        ], axis=1)
        
        # Identify nodes with no in-degree and/or out-degree
        micro_level_stats["nd"] = 0
        micro_level_stats["nd"] += (micro_level_stats["ic"] == 0).astype(int)
        micro_level_stats["nd"] += (micro_level_stats["lns"].str.len() == 0).astype(int) * 2

        # Compute node ranks relative to each network centrality metric
        micro_level_stats_ranks = (
            micro_level_stats.iloc[:, 1:-1]  # omit first column (LNS) and last column (ND)
                .apply(lambda x: x.rank(method="dense", ascending=False))
                .add_suffix("_rank")
        )
        
        # Compute node percentiles relative to each network centrality metric
        micro_level_stats_pct = (
            micro_level_stats_ranks
                .apply(lambda x: x.rank(pct=True))
                .add_suffix("_pctile")
        )
        
        # Return micro-level statistics
        return (
            pd.concat([
                micro_level_stats,
                micro_level_stats_ranks,
                micro_level_stats_pct,
            ], axis=1)
                .sort_index()
                .round(3)
        )
        
    def get_nodes_rankings(self, micro_stats: pd.DataFrame) -> Dict[str, Dict[int, int]]:
        """
        Generate and return the order of nodes based on their rank scores for each centrality metric.

        This method processes a DataFrame containing micro-level network statistics with node ranks
        for various centrality metrics. It extracts the ranking columns, orders the nodes according 
        to their rank for each metric, and returns the results as a dictionary.

        Args:
            micro_stats (pd.DataFrame): A DataFrame containing node ranks for various centrality metrics,
            with columns suffixed by "_rank".

        Returns:
            Dict[str, Dict[int, int]]: A dictionary where each key corresponds to a centrality metric rank
            column from the input DataFrame with an "_rank" suffix. The value is another dictionary that 
            maps node identifiers to their rank ordinal within that metric.
            
            The inner dictionary has the following mapping structure:
                - Key: int, node identifier.
                - Value: int, node order (ordinal position) based on rank scores.
        """
        # Initialize dictionary to store ordered node rankings
        nodes_ordered_by_rank = {}

        # Get columns that represent rank data
        ranks = micro_stats.filter(regex=r"_rank$")
        
        # For each metric, nodes will be ordered by their relative rank
        for rank_label, rank_data in ranks.items():
            series = rank_data.to_frame().reset_index().sort_values(by=[rank_label, "index"]).set_index("index").squeeze()
            series.name = f"{rank_label}_ooa"
            series = pd.to_numeric(series, downcast="integer")
            nodes_ordered_by_rank[rank_label] = series.to_dict()
        
        # Return the dictionary of nodes ordered by their rank for each metric
        return nodes_ordered_by_rank

           
    def get_edges_types(self, G: nx.DiGraph, edges: List[Tuple[str, str]], G_ref: nx.DiGraph) -> Dict[str, List[Tuple[str, str]]]:
        """
        Classify edges in a directed network graph into various types based on their relationships
        within the network and with respect to a reference network.

        This method computes and classifies edges into four types:
        - Type I: Edges where if node A is connected to node B, then node B is also connected to node A in the same network.
        - Type II: Edges where if node A is connected to node B, then node B is not connected to node A in the same network.
        - Type III: Edges that exist in both the original network and a reference network in the same direction.
        - Type IV: Edges that exist in the original network but are reversed in the reference network.

        Args:
            G (nx.DiGraph): The main directed graph containing the edges to be classified.
            edges (List[Tuple[str, str]]): A list of edges (tuples) in the graph `G` to be classified.
            G_ref (nx.DiGraph): A reference directed graph used for comparison in classification.

        Returns:
            Dict[str, List[Tuple[str, str]]]: A dictionary classifying edges into four categories:
                - "type_i": List of type I edges.
                - "type_ii": List of type II edges.
                - "type_iii": List of type III edges.
                - "type_iv": List of type IV edges.
        """
        # Compute ordered adjacency list for both networks
        adj_df = nx.to_pandas_adjacency(G, nodelist=sorted(G.nodes))
        adj_ref_df = nx.to_pandas_adjacency(G_ref, nodelist=sorted(G.nodes))

        # Compute type I edges,
        # i.e. same network: A -> B and B -> A
        type_i = (
            pd.DataFrame(np.triu(adj_df) * np.tril(adj_df).T, index=adj_df.index, columns=adj_df.columns)
                .stack().loc[lambda x: x == 1].index.tolist()
        )

        # Compute type II edges,
        # i.e. same network: A -> B and not B -> A
        type_ii = [edge for edge in edges if edge not in type_i]

        # Compute type III edges,
        # i.e. A -> B in network G and A -> B in network G_ref
        type_iii = (
            pd.DataFrame(np.triu(adj_df) * np.triu(adj_ref_df), index=adj_df.index, columns=adj_df.columns)
                .stack().loc[lambda x: x == 1].index.tolist()
        )

        # Compute type IV edges,
        # i.e. A -> B in network G and B -> A in network G_ref
        type_iv = (
            pd.DataFrame(np.triu(adj_df) * np.tril(adj_ref_df).T, index=adj_df.index, columns=adj_df.columns)
                .stack().loc[lambda x: x == 1].index.tolist()
        )

        # Compute type V edges
        # i.e. A -> B, B -> A in network G and A -> B, B -> A in network G_ref
        type_v = [ edge for edge in type_i if edge in type_iii and edge in type_iv]

        # Return edges types
        return {
            "type_i": type_i,
            "type_ii": type_ii,
            "type_iii": [ edge for edge in type_iii if edge not in type_v],
            "type_iv": [ edge for edge in type_iv if edge not in type_v],
            "type_v": type_v
        }

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

        # Determine dimensions of matplotlib graph based upon number of nodes
        fig_size = (8 * CM_TO_INCHES, 8 * CM_TO_INCHES)\
            if G.number_of_nodes() <= 10 else (17 * CM_TO_INCHES, 19 * CM_TO_INCHES)
        
        # Create a matplotlib figure
        fig, ax = plt.subplots(constrained_layout=True, figsize=fig_size)
        
        # Hide axis
        ax.axis('off')  
        
        # Draw nodes and nodes labels
        nx.draw_networkx_nodes(G, loc, node_color=color, edgecolors=color, ax=ax)        
        nx.draw_networkx_labels(G, loc, font_color="#FFF", font_weight="normal", font_size=10, ax=ax)
        
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