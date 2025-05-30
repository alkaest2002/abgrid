"""
Filename: abgrid_network.py
Description: Provides functionality to analyze directed networks (graphs) for a given set of edges.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import io
from xmlrpc.client import Boolean
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import networkx as nx

from typing import Any, Literal, List, Dict, Tuple
from base64 import b64encode
from functools import reduce
from scipy.spatial import ConvexHull, Delaunay

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
        self.sociogram = pd.DataFrame()

    def compute_networks(self, with_sociogram: Boolean = False):
        """
        Compute and store graphs, statistics, and visualization layouts for two networks.

        Args:
            sociogram (bool): A flag indicating whether to generate sociograms for the networks.
                          Defaults to False.
        """
        
        # Create network A and B
        network_a = nx.DiGraph(self.edges_a)
        network_b = nx.DiGraph(self.edges_b)

        # Loop through networks
        for network, nodes in [(network_a, self.nodes_a), (network_b, self.nodes_b)]:  
            # Add isolated nodes to current network
            isolated_nodes = set(list(network)).symmetric_difference(set(nodes))
            network.add_nodes_from(isolated_nodes)
           
        # Generate layout for network A and B
        loc_a = nx.kamada_kawai_layout(network_a)
        loc_b = nx.kamada_kawai_layout(network_b)

        # Try to push isolated nodes (if any) away from other nodes
        self.handle_isolated_nodes(network_a, self.nodes_a, loc_a)
        self.handle_isolated_nodes(network_b, self.nodes_b, loc_b)
                    
        # Store network A and B statistics and plots
        self.macro_stats_a = self.get_network_macro_stats(network_a)
        self.macro_stats_b = self.get_network_macro_stats(network_b)
        self.micro_stats_a = self.get_network_micro_stats(network_a)
        self.micro_stats_b = self.get_network_micro_stats(network_b)
        self.nodes_a_rankings = self.get_nodes_rankings(self.micro_stats_a)
        self.nodes_b_rankings = self.get_nodes_rankings(self.micro_stats_b)
        self.edges_a_types = self.get_edges_types(network_a, self.edges_a, network_b)
        self.edges_b_types = self.get_edges_types(network_b, self.edges_b, network_a)
        self.components_a = self.get_network_components(network_a)
        self.components_b = self.get_network_components(network_b)
        self.graph_a = self.get_network_graph(network_a, loc_a, "A")
        self.graph_b = self.get_network_graph(network_b, loc_b, "B")

        # Add sociogram if requested
        if with_sociogram:
            self.sociogram = self.get_sociogram(network_a, network_b)

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
    
    def get_network_macro_stats(self, network: nx.DiGraph) -> Dict[str, Any]:
        """
        Calculate and return macro-level statistics for a directed network.

        This method computes several statistics about the structure of the given
        network , including the number of nodes, the number of edges, 
        density, centralization, transitivity, and reciprocity.

        Args:
            network (nx.DiGraph): A directed graph represented using NetworkX's DiGraph class.

        Returns:
            Dict[str, Any]: A dictionary containing the following macro-level statistics:
                - "network_nodes": int, the total number of nodes in the network.
                - "network_edges": int, the total number of edges in the network.
                - "density": float, the density of the network rounded to three decimal places.
                - "network_centralization": float, the centralization of the undirected version of the network.
                - "network_transitivity": float, the transitivity of the network rounded to three decimal places.
                - "network_reciprocity": float, the reciprocity of the network rounded to three decimal places.
        """
        # Compute macro-level statistics
        network_nodes = network.number_of_nodes()
        network_edges = network.number_of_edges()
        network_density = round(nx.density(network), 3)
        network_centralization = self.get_network_centralization(network.to_undirected())
        network_transitivity = round(nx.transitivity(network), 3)
        network_reciprocity = round(nx.overall_reciprocity(network), 3)
        
        # Return macro-level statistics
        return {
            "network_nodes": network_nodes,
            "network_edges": network_edges,
            "network_density": network_density,
            "network_centralization": network_centralization,
            "network_transitivity": network_transitivity,
            "network_reciprocity": network_reciprocity,
        }
    
    def get_network_micro_stats(self, network: nx.DiGraph) -> pd.DataFrame:
        """
        Calculate and return micro-level statistics for each node in a directed network graph.

        This method computes several node-specific centrality metrics for a given NetworkX directed
        graph and organizes them into a pandas DataFrame. Additionally, it identifies nodes
        without incoming or outgoing connections and calculates relative ranks and percentiles for each
        centrality measure.

        Args:
            network (nx.DiGraph): A directed graph represented using NetworkX's DiGraph class.

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
            pd.Series(nx.to_pandas_adjacency(network).apply(lambda x: ", ".join(x[x > 0].index.values), axis=1), name="lns"),
            pd.Series(nx.in_degree_centrality(network), name="ic"),
            pd.Series(nx.pagerank(network, max_iter=1000), name="pr"),
            pd.Series(nx.betweenness_centrality(network), name="bt"),
            pd.Series(nx.closeness_centrality(network), name="cl"),
            pd.Series(nx.hits(network)[0], name="hu").abs(),

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
        
    def get_edges_types(self, network: nx.DiGraph, edges: List[Tuple[str, str]], network_ref: nx.DiGraph) -> Dict[str, List[Tuple[str, str]]]:
        """
        Classify edges in a directed network graph into various types based on their relationships
        within the network and with respect to a reference network.

        This method computes and classifies edges into five types:
        - Type I: Non-reciprocal edges, where if node A is connected to node B, node B is not connected to node A in the same network.
        - Type II: Reciprocal edges, where node A is connected to node B and node B is also connected to node A in the same network.
        - Type III: Half-symmetrical edges, where if node A is connected to node B in the original network, node A is also connected to node B in the reference network.
        - Type IV: Half-reversed symmetrical edges, where if node A is connected to node B in the original network, node B is connected to node A in the reference network.
        - Type V: Fully symmetrical edges, where node A and node B are reciprocally connected in both the original and reference networks.

        Args:
            network (nx.DiGraph): The main directed graph containing the edges to be classified.
            edges (List[Tuple[str, str]]): A list of edges (tuples) in the graph `network` to be classified.
            network_ref (nx.DiGraph): A reference directed graph used for comparison in classification.

        Returns:
            Dict[str, List[Tuple[str, str]]]: A dictionary classifying edges into five categories:
                - "type_i": List of type I edges (non-reciprocal).
                - "type_ii": List of type II edges (reciprocal).
                - "type_iii": List of type III edges (half-symmetrical, non-fully symmetrical).
                - "type_iv": List of type IV edges (half-reversed symmetrical, non-fully symmetrical).
                - "type_v": List of type V edges (fully symmetrical).
        """
        # Compute ordered adjacency list for both networks
        adj_df = nx.to_pandas_adjacency(network, nodelist=sorted(network.nodes))
        adj_ref_df = nx.to_pandas_adjacency(network_ref, nodelist=sorted(network.nodes))

        # Compute type I edges, non reciprocal
        # i.e. same network: A -> B and not B -> A
        type_i = [ edge for edge in edges if edge[::-1] not in edges ]

        # Compute type II edges, reciprocal
        # i.e. same network: A -> B and B -> A
        type_ii = (
            pd.DataFrame(np.triu(adj_df) * np.tril(adj_df).T, index=adj_df.index, columns=adj_df.columns)
                .stack().loc[lambda x: x == 1].index.tolist()
        )

        # Compute type III edges, half simmetrical
        # i.e. A -> B in network network and A -> B in network G_ref
        type_iii = (
            pd.DataFrame(np.triu(adj_df) * np.triu(adj_ref_df), index=adj_df.index, columns=adj_df.columns)
                .stack().loc[lambda x: x == 1].index.tolist()
        )

        # Compute type IV edges, half reversed simmetrical
        # i.e. A -> B in network network and B -> A in network G_ref
        type_iv = (
            pd.DataFrame(np.triu(adj_df) * np.tril(adj_ref_df).T, index=adj_df.index, columns=adj_df.columns)
                .stack().loc[lambda x: x == 1].index.tolist()
        )

        # Compute type V edges, full simmetrical
        # i.e. A -> B, B -> A in network network and A -> B, B -> A in network G_ref
        type_v = [ edge for edge in type_ii if edge in type_iii and edge in type_iv]

        # Return edges types
        return {
            "type_i": type_i,
            "type_ii": type_ii,
            "type_iii": [ edge for edge in type_iii if edge not in type_v],
            "type_iv": [ edge for edge in type_iv if edge not in type_v],
            "type_v": type_v
        }
    
    def get_network_components(self, network: nx.DiGraph) -> List[str]:
        """
        Identify and return the unique and significant components of a directed graph as strings.

        This method calculates and returns components of the given NetworkX directed graph, including:
        - Strongly connected components: Subsets in which each node is reachable from any other node respecting edges direction.
        - Weakly connected components: Subsets connected without considering the direction of edges.
        - Cliques (from the undirected version of the graph): Subsets where each node is directly connected to every other node in the subset.

        Components of each type are filtered to include only those with more than two nodes. 
        The nodes in each component are concatenated into a single string after being 
        sorted. The function returns a unique list of these strings, sorted by their length in descending order.

        Args:
            network (nx.DiGraph): A directed graph represented using NetworkX's DiGraph class.

        Returns:
            List[str]: A list of strings, where each string represents a unique component with its nodes concatenated
            in sorted order. The list is sorted in descending order of string length.
        """
        components = [
            *["".join(sorted(list(c))) for c in sorted(nx.kosaraju_strongly_connected_components(network), key=len, reverse=True) if len(c) > 2],
            *["".join(sorted(list(c))) for c in sorted(nx.weakly_connected_components(network), key=len, reverse=True) if len(c) > 2],
            *["".join(sorted(list(c))) for c in sorted(nx.find_cliques(network.to_undirected()), key=len, reverse=True) if len(c) > 2]
        ]
        
        # Ensure unique components and sort by length in descending order
        return sorted(list(set(components)), key=len, reverse=True)

    def get_network_graph(self, network: nx.DiGraph, loc: Dict[str, Tuple[float, float]], graphType: Literal["A","B"] = "A") -> str:
        """
        Generate a graphical representation of a network and return it encoded in base64 SVG format.

        Args:
            network (nx.DiGraph): The directed graph to plot.
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
            if network.number_of_nodes() <= 10 else (17 * CM_TO_INCHES, 19 * CM_TO_INCHES)
        
        # Create a matplotlib figure
        fig, ax = plt.subplots(constrained_layout=True, figsize=fig_size)
        
        # Hide axis
        ax.axis('off')  
        
        # Draw nodes
        nx.draw_networkx_nodes(network, loc, node_color=color, edgecolors=color, ax=ax)
        nx.draw_networkx_nodes(nx.isolates(network), loc, node_color="#000", edgecolors="#000", ax=ax)

        # Draw nodes labels
        nx.draw_networkx_labels(network, loc, font_color="#FFF", font_weight="normal", font_size=10, ax=ax)
        
        # Draw reciprocal edges with specific style
        reciprocal_edges = [e for e in network.edges if e[::-1] in network.edges]
        nx.draw_networkx_edges(network, loc, edgelist=reciprocal_edges, edge_color=color, arrowstyle='-', width=3, ax=ax)
                
        # Draw non reciprocal edges with specific style
        non_reciprocal_edges = [e for e in network.edges if e not in reciprocal_edges]
        nx.draw_networkx_edges(network, loc, edgelist=non_reciprocal_edges, edge_color=color, style="--", arrowstyle='-|>', arrowsize=15, ax=ax)
        
        # Save figure to the buffer in SVG format then close it
        fig.savefig(buffer, format="svg", bbox_inches='tight', transparent=True, pad_inches=0.05)
        plt.close(fig) 
        
        # Encode the buffer contents to a base64 string
        base64_econded_string = b64encode(buffer.getvalue()).decode()
        
        # Return the data URI for the SVG
        return f"data:image/svg+xml;base64,{base64_econded_string}"
    
    def handle_isolated_nodes(self, network: nx.DiGraph, nodes: Any, loc: Dict[Any, np.ndarray]):
        """
        Add isolated nodes to the network and adjust their positions to appear marginal.

        This function first identifies isolated nodes by comparing the network nodes 
        to a provided list of node identifiers. It adds these isolated nodes to the 
        network. Then, for visualization purposes, it adjusts the positions of these 
        isolated nodes to appear outside the convex hull of the main node cluster 
        so that they are perceptually distant and marginal.

        Args:
            network (nx.DiGraph): The directed graph where isolated nodes are managed.
            nodes (Any): A collection of node identifiers that should be present in the network.
            loc (Dict[Any, np.ndarray]): A dictionary representing the layout of nodes.

        """
        # Identify and add isolated nodes
        isolated_nodes = set(network).symmetric_difference(set(nodes))
        network.add_nodes_from(isolated_nodes)

        # Adjust layout by pushing isolated nodes away from network
        for isolate in list(nx.isolates(network)):
            
            # Convert current loc coordinates to dataframe
            coordinates = pd.DataFrame(loc).T
            # Compute convex hull
            hull = ConvexHull(coordinates)
            # Compute centroid of convex hull
            centroid = np.mean(coordinates, axis=0)
            # Compute delauny triangulation
            delauny = Delaunay(coordinates)
            
            # try to find candidate position for isolated (max 10 attempts)
            for _ in range(5): 
                # Choose a random hull vertex
                rand_vertex = coordinates.iloc[np.random.choice(hull.vertices)]
                # Create a unit vector pointing outward from the hull centroid
                direction = rand_vertex - centroid
                direction /= np.linalg.norm(direction)
                # Define scaling factore to move outward a bit
                scale = np.random.uniform(0.15, 0.15)
                # Compute candidate position
                candidate_pos = rand_vertex + direction * scale
                # Check if candidate position is outside the convex hull
                if delauny.find_simplex(candidate_pos) == -1:
                    # Update isolate position and exit loop
                    loc[isolate] = candidate_pos
                    break

    def get_network_centralization(self, network: nx.Graph) -> float:
        """
        Calculate the centralization of a network.

        The centralization measure indicates how concentrated the network is around its most central node.
        It compares the current network structure to an ideal star network structure.

        Args:
            network (nx.Graph): The graph for which the centralization is calculated.

        Returns:
            float: The centralization value of the network, rounded to three decimal places, or
        """
        
        # Get number of nodes
        number_of_nodes = network.number_of_nodes()
        
        # Compute node centralities
        node_centralities = pd.Series(dict(nx.degree(network)))

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
    
    def get_sociogram(self, network_a: nx.DiGraph, network_b: nx.DiGraph) -> pd.DataFrame:
        """
        Computes a sociogram DataFrame based on two directed graphs representing 
        social network data for preferences and rejections.

        Parameters:
        - network_a (nx.DiGraph): A directed graph where edges represent preferences given.
        - network_b (nx.DiGraph): A directed graph where edges represent rejections given.

        Returns:
        - pd.DataFrame: A DataFrame with sociometric indices for each node
        """
        
        # Compute basic data for sociogram
        out_preferences = pd.Series(dict(network_a.out_degree()), name="given_preferences")
        out_rejects = pd.Series(dict(network_b.out_degree()), name="given_rejections")
        in_preferences = pd.Series(dict(network_a.in_degree()), name="received_preferences")
        in_rejects = pd.Series(dict(network_b.in_degree()), name="received_rejections")
        
        # Assemble sociogram dataframe
        socio_df = pd.concat([in_preferences, in_rejects, out_preferences, out_rejects], axis=1)
        
        # Add mutual preferences
        socio_df["mutual_preferences"] = pd.Series(
            [ sum([ network_a.has_edge(x,n) for x in network_a.successors(n) ]) 
                for n in network_a.nodes() ], index=network_a.nodes()
        )

        # Add mutual rejections
        socio_df["mutual_rejections"] = pd.Series(
            [ sum([ network_b.has_edge(x,n) for x in network_b.successors(n) ]) 
                for n in network_b.nodes() ], index=network_b.nodes()
        )

        # Add orientation       
        socio_df["orientation"] = (socio_df["given_preferences"]
            .sub(socio_df["given_rejections"])
            .div(socio_df["given_preferences"].add(socio_df["given_rejections"]))
            .fillna(0)
            .round(3)
        )

        # Add impact
        socio_df["impact"] = socio_df["received_preferences"].add(socio_df["received_rejections"])
        
        # Add balance
        socio_df["balance"] = socio_df["received_preferences"].sub(socio_df["received_rejections"])
        
        # Add leadership index
        socio_df["leadership"] = socio_df["received_preferences"].add(socio_df["mutual_preferences"])
        
        # Compute sociogram status
        # Start by computing with z scores of relevat data
        z_impact = socio_df["impact"].sub(socio_df["impact"].mean()).div(socio_df["impact"].std())
        z_balance = socio_df["balance"].sub(socio_df["balance"].mean()).div(socio_df["balance"].std())

        # status is average, unless otherwise specified
        socio_df["status"] = "average"
        socio_df.loc[z_impact < -1, "status"] = "highly negleted"
        socio_df.loc[z_impact.between(-.5, -1), "status"] = "negleted"
        socio_df.loc[np.logical_and(z_impact > 0, z_balance > .5), "status"] = "popular"
        socio_df.loc[np.logical_and(z_impact > 0, z_balance < -.5), "status"] = "rejected"
        socio_df.loc[np.logical_and(z_impact > .5, z_balance.between(-.5, .5)), "status"] = "controversial"
        socio_df.loc[np.logical_and(z_impact > 1, z_balance > 1), "status"] = "highly popular"
        socio_df.loc[np.logical_and(z_impact > 1, z_balance < -1), "status"] = "highly rejected"
        
        # return sociogram dataframe, ordered by node
        return socio_df.sort_index()

