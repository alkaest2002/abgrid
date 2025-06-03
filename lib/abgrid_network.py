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
        self.sociogram = {
            "micro_stats": pd.DataFrame(),
            "macro_stats": pd.DataFrame(),
            "supplemental": {}
        }

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
        self.handle_isolated_nodes(network_a, loc_a)
        self.handle_isolated_nodes(network_b, loc_b)
                    
        # Store network A and B statistics and plots
        self.macro_stats_a = self.get_network_macro_stats(network_a)
        self.macro_stats_b = self.get_network_macro_stats(network_b)
        self.micro_stats_a = self.get_network_micro_stats(network_a)
        self.micro_stats_b = self.get_network_micro_stats(network_b)
        self.nodes_a_rankings = self.get_nodes_rankings(self.micro_stats_a)
        self.nodes_b_rankings = self.get_nodes_rankings(self.micro_stats_b)
        self.edges_a_types = self.get_edges_types(network_a, self.edges_a, network_b, self.edges_b)
        self.edges_b_types = self.get_edges_types(network_b, self.edges_b, network_a, self.edges_a)
        self.components_a = self.get_network_components(network_a)
        self.components_b = self.get_network_components(network_b)
        self.graph_a = self.get_network_graph(network_a, loc_a, "A")
        self.graph_b = self.get_network_graph(network_b, loc_b, "B")

        # Add sociogram if requested
        if with_sociogram:
            self.sociogram = self.get_sociogram_data(network_a, network_b)

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
        network_density = nx.density(network)
        network_centralization = self.get_network_centralization(network.to_undirected())
        network_transitivity = nx.transitivity(network)
        network_reciprocity = nx.overall_reciprocity(network)
        
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
        
    def get_edges_types(self, network: nx.DiGraph, edges: List[Tuple[str, str]], network_ref: nx.DiGraph, edges_ref: List[Tuple[str, str]]) -> Dict[str, List[Tuple[str, str]]]:
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
            edges (List[Tuple[str, str]]): A list ozf edges (tuples) in the graph `network` to be classified.
            network_ref (nx.DiGraph): A reference directed graph used for comparison in classification.
            edges_ref (List[Tuple[str, str]]): A list of edges (tuples) in the graph used for comparison in classification.

        Returns:
            Dict[str, List[Tuple[str, str]]]: A dictionary classifying edges into the five categories:
        """
        # Compute ordered adjacency list for both networks
        adj_df = nx.to_pandas_adjacency(network, nodelist=sorted(network.nodes))
        adj_ref_df = nx.to_pandas_adjacency(network_ref, nodelist=sorted(network.nodes))

        # Compute type I edges, non reciprocal
        # i.e. same network: A -> B and not B -> A
        type_i = [ edge for edge in edges if edge[::-1] not in edges ]

        # Compute type II edges, reciprocal
        # i.e. same network: A -> B and B -> A
        type_ii_df = pd.DataFrame(np.triu(adj_df) * np.tril(adj_df).T, index=adj_df.index, columns=adj_df.columns)
        type_ii = type_ii_df.stack().loc[lambda x: x == 1].index.tolist()
        
        # Compute type III edges, half simmetrical
        # i.e. A -> B in network network and A -> B in network G_ref
        type_iii_df = pd.DataFrame(np.triu(adj_df) * np.triu(adj_ref_df), index=adj_df.index, columns=adj_df.columns)
        type_iii = type_iii_df.stack().loc[lambda x: x == 1].index.tolist()
        
        # Compute type IV edges, half reversed simmetrical
        # i.e. A -> B in network network and B -> A in network G_ref
        type_iv_df = (
            pd.DataFrame(np.triu(adj_df) * np.tril(adj_ref_df).T, index=adj_df.index, columns=adj_df.columns)
            + pd.DataFrame(np.tril(adj_df) * np.triu(adj_ref_df).T, index=adj_df.index, columns=adj_df.columns)
        )
        type_iv = type_iv_df.stack().loc[lambda x: x == 1].index.tolist()
        
        # Compute type V edges, full simmetrical
        # i.e. A -> B, B -> A in network network and A -> B, B -> A in network G_ref
        type_v_df = pd.DataFrame(np.triu(type_ii_df) * np.triu(type_iii_df * type_iv_df), index=adj_df.index, columns=adj_df.columns)
        type_v = type_v_df.stack().loc[lambda x: x == 1].index.tolist()

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
    
    def handle_isolated_nodes(self, network: nx.DiGraph, loc: Dict[Any, np.ndarray]):
        """
        Add isolated nodes to the network and adjust their positions to appear marginal.
        This function adjusts the positions of isolated nodes to appear outside the convex hull
        of the main node cluster so that they are perceptually distant and marginal.
        
        Args:
            network (nx.DiGraph): The directed graph where isolated nodes are managed.
            loc (Dict[Any, np.ndarray]): A dictionary representing the layout of nodes.
        """
        # Get isolated nodes, if any
        isolates = list(nx.isolates(network))
        if not isolates:
            return
        
        # Convert current loc coordinates to dataframe
        coordinates = pd.DataFrame(loc).T
        
        # Compute convex hull
        hull = ConvexHull(coordinates)
        
        # Compute centroid of coordinates
        centroid = np.mean(coordinates, axis=0)
        
        # Get hull vertices
        hull_vertices = coordinates.iloc[hull.vertices].values
        
        # Create an iterator from isolated nodes list
        isolate_iter = iter(isolates)

        # Keep track of loop rounds
        # as isolated nodes may be greater than hull vertices
        round_num = 1
        
        # Loop through rounds until all isolated nodes are placed
        try:
            while True:
                # Loop through hull vertices in current round
                for vertex in hull_vertices:
                    
                    # Get next isolated node
                    isolate = next(isolate_iter)
                    
                    # Create direction vector from centroid to hull vertex
                    direction = vertex - centroid
                    direction /= np.linalg.norm(direction)
                    
                    # Distance multiplier increases with each round
                    distance_multiplier = 0.15 * round_num
                    
                    # Add some randomness to position
                    random_offset = np.random.uniform(-0.05, 0.05, size=2)
                    
                    # Calculate final position
                    candidate_pos = vertex + direction * distance_multiplier + random_offset
                    
                    # Place the isolated node
                    loc[isolate] = candidate_pos
                
                # Move to next round with increased distance
                round_num += 1
        
        # All isolated nodes have been placed
        except StopIteration:
            pass

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
        return network_centralization
    
    def get_sociogram_data(self, network_a: nx.DiGraph, network_b: nx.DiGraph) -> dict[str, pd.DataFrame | dict]:
        """
        Computes a sociogram DataFrame based on two directed graphs representing 
        social network data for preferences and rejections.

        Parameters:
        - network_a (nx.DiGraph): A directed graph where edges represent preferences given.
        - network_b (nx.DiGraph): A directed graph where edges represent rejections given.

        Returns:
        - dict[str, pd.DataFrame | dict]: a dict containing sociogram macro and micro stats
        """
        
        # Compute basic data for sociogram micro stats
        out_preferences = pd.Series(dict(network_a.out_degree()), name="given_preferences")
        out_rejects = pd.Series(dict(network_b.out_degree()), name="given_rejections")
        in_preferences = pd.Series(dict(network_a.in_degree()), name="received_preferences")
        in_rejects = pd.Series(dict(network_b.in_degree()), name="received_rejections")
        
        # Init sociogram micro stats dataframe
        sociogram_micro_df = pd.concat([in_preferences, in_rejects, out_preferences, out_rejects], axis=1)
        
        # Add mutual preferences
        sociogram_micro_df["mutual_preferences"] = pd.Series(
            [ sum([ network_a.has_edge(x,n) for x in network_a.successors(n) ]) 
                for n in network_a.nodes() ], index=network_a.nodes()
        )

        # Add mutual rejections
        sociogram_micro_df["mutual_rejections"] = pd.Series(
            [ sum([ network_b.has_edge(x,n) for x in network_b.successors(n) ]) 
                for n in network_b.nodes() ], index=network_b.nodes()
        )

        # Add balance
        sociogram_micro_df["balance"] = (
            sociogram_micro_df["received_preferences"]
                .sub(sociogram_micro_df["received_rejections"])
        )

        # Add orientation       
        sociogram_micro_df["orientation"] = (
            sociogram_micro_df["given_preferences"]
                .sub(sociogram_micro_df["given_rejections"])
        )

        # Add impact
        sociogram_micro_df["impact"] = (
            sociogram_micro_df["received_preferences"]
                .add(sociogram_micro_df["received_rejections"])
        )
        
        # Add affiliation coefficient
        affiliation = (
            sociogram_micro_df["balance"]
                .add(sociogram_micro_df["mutual_preferences"])
                .add(sociogram_micro_df["orientation"])
        )
        sociogram_micro_df["affiliation_coeff"] = (
            affiliation
                .sub(affiliation.mean())
                .div(affiliation.std())
                .mul(10)
                .add(100)
        )

        # Add influence coefficient
        influence = (
            sociogram_micro_df["received_preferences"]
                .add(sociogram_micro_df["mutual_preferences"])
        )
        sociogram_micro_df["influence_coeff"] = (
            influence
                .sub(influence.mean())
                .div(influence.std())
                .mul(10)
                .add(100)
        )
        
        # Add sociogram status
        # 1. Start by computing with z scores of relevat data
        impact = sociogram_micro_df["impact"]
        z_impact = impact.sub(impact.mean()).div(impact.std())
        balance = sociogram_micro_df["balance"]
        z_balance = balance.sub(balance.mean()).div(balance.std())

        # 2. Update status: default is "-", unless otherwise specified
        sociogram_micro_df["status"] = "-"
        sociogram_micro_df.loc[sociogram_micro_df.iloc[:, :4].sum(axis=1).eq(0), "status"] = "isolated"
        sociogram_micro_df.loc[z_impact < -1, "status"] = "neglected"
        sociogram_micro_df.loc[z_impact.between(-1, -.5), "status"] = "underrated"
        sociogram_micro_df.loc[np.logical_and(z_impact.between(.5, 1), z_balance > 1), "status"] = "appreciated"
        sociogram_micro_df.loc[np.logical_and(z_impact > 1, z_balance > 1), "status"] = "popular"
        sociogram_micro_df.loc[np.logical_and(z_impact > -.5, z_balance < -1), "status"] = "rejected"
        sociogram_micro_df.loc[np.logical_and(z_impact > 0, z_balance.between(-.5, .5)), "status"] = "controversial"
        
        # Compute sociogram macro stats
        sociogram_numeric_columns = sociogram_micro_df.select_dtypes(np.number)
        median = sociogram_numeric_columns.median()
        sociogram_macro_df = sociogram_numeric_columns.describe().T
        sociogram_macro_df.insert(1, "median", median)

        # Add cohesion index
        coehsion_index = (sociogram_micro_df.loc[:, "mutual_preferences"].sum() / 2) / len(network_a)

        # Return sociogram dataframe, ordered by node
        return {
           "micro_stats": sociogram_micro_df.sort_index(),
           "macro_stats": sociogram_macro_df.apply(pd.to_numeric, downcast="integer"),
           "supplemental": {
               "coehsion_index": coehsion_index
           }
        }

