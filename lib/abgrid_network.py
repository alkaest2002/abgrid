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

from typing import Any, Literal, List, Dict, Tuple, Union
from base64 import b64encode
from functools import reduce
from scipy.spatial import ConvexHull

# Customize matplotlib settings
matplotlib.rc('font', **{'size': 8})
matplotlib.use("Agg")

# Conversion factor from inches to centimeters
CM_TO_INCHES = 1 / 2.54
A_COLOR = "#0000FF"
B_COLOR = "#FF0000"

class ABGridNetwork:
    """
    Class to represent and analyze directed networks (graphs) given a set of edges.
    """

    def __init__(self):
        """
        Initialize the network analysis object.
        This initialization sets up the internal dictionaries for storing
        network structure, statistics, and potentially sociograms.
        """
        
        # Init sna dict
        self.sna = {
            "nodes_a": None,
            "nodes_b": None,
            "edges_a": None,
            "edges_b": None,
            "adjacency_a": None,
            "adjacency_b": None,
            "network_a": None,
            "network_b": None,
            "macro_stats_a": None,
            "macro_stats_b": None,
            "micro_stats_a": None,
            "micro_stats_b": None,
            "rankings_a": None,
            "rankings_b": None,
            "edges_types_a": None,
            "edges_types_b": None,
            "graph_a": None,
            "graph_b": None
        }

        # init sociogram dict
        self.sociogram = {
            "micro_stats": None,
            "macro_stats": None,
            "supplemental": None
        }

    def compute_networks(self, 
        packed_edges_a: List[Dict[str, str]], 
        packed_edges_b: List[Dict[str, str]], 
        with_sociogram: Boolean = False
    ):
        """
        Compute and store graphs, statistics, and visualization layouts for network a and b.

        Args:
            packed_edges_a: List[Dict[str, str]]
                List of dictionaries, each representing edges for network_a.
            packed_edges_b: List[Dict[str, str]]
                List of dictionaries, each representing edges for network_b.
            with_sociogram: bool, optional (default is False)
                Flag indicating whether to generate sociograms for the networks.
        """

        # Crete netowork a and b
        for network_type, packed_edges in [("a", packed_edges_a), ("b", packed_edges_b)]:
            self.sna[f"nodes_{network_type}"] = self.unpack_network_nodes(packed_edges)
            self.sna[f"edges_{network_type}"] = self.unpack_network_edges(packed_edges)
            self.sna[f"network_{network_type}"] = nx.DiGraph(self.sna[f"edges_{network_type}"])

        # Add isolated nodes to network a and b
        for network_type, network, nodes in [
            ("a", self.sna["network_a"], self.sna["nodes_a"]), 
            ("b", self.sna["network_b"], self.sna["nodes_b"])
        ]:  
            # Add isolated nodes to current network
            isolated_nodes = set(list(network)).symmetric_difference(set(nodes))
            network.add_nodes_from(isolated_nodes)
            
            # Generate layout for current network
            loc = nx.kamada_kawai_layout(network)
            
            # Update loc so to push isolated nodes away from other nodes
            updated_loc = self.handle_isolated_nodes(network, loc)

            # Add loc to current network
            self.sna[f"loc_{network_type}"] = updated_loc

            # add adiacency list of current network
            self.sna[f"adjacency_{network_type}"] = nx.to_pandas_adjacency(network, nodelist=nodes)
                    
        # Store sna data
        for network_type in ("a", "b"):
            self.sna[f"macro_stats_{network_type}"] = self.get_sna_macro_stats(network_type)
            self.sna[f"micro_stats_{network_type}"] = self.get_sna_micro_stats(network_type)
            self.sna[f"rankings_{network_type}"] = self.get_sna_rankings(network_type)
            self.sna[f"edges_types_{network_type}"] = self.get_sna_edges_types(network_type)
            self.sna[f"components_{network_type}"] = self.get_sna_components(network_type)
            self.sna[f"graph_{network_type}"] = self.get_sna_graph(network_type)

        # Add sociogram if requested
        if with_sociogram:
            self.sociogram = self.get_sociogram_data()

    def unpack_network_edges(self, packed_edges: List[Dict[str, str]]) -> List[Tuple[str, str]]:
        """
        Unpack a list of packed edge dictionaries into a list of edge tuples.

        Args:
            packed_edges: List[Dict[str, str]]
                A list of dictionaries, each with a source node as the key and a 
                comma-separated string of target nodes as the value.

        Returns:
            List[Tuple[str, str]]:
                A list of edge tuples (source, target) representing directed edges.
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

        Args:
            packed_edges: List[Dict[str, str]]
                A list of dictionaries where each dictionary's key represents a "source" node.

        Returns:
            List[str]: A sorted list of unique source node identifiers.
        """
        # Extract nodes and sort them
        return sorted([
            node for node_edges in packed_edges for node, _ in node_edges.items()
        ])
    
    def get_sna_macro_stats(self, network_type: Literal["a", "b"]) -> Dict[str, Union[int, float]]:
        """
        Calculate and return macro-level statistics for a directed network.

        Args:
            network_type: Literal["a", "b"]
                The type identifier for selecting the specific network.

        Returns:
            Dict[str, Union[int, float]]:
                A dictionary containing macro-level statistics such as number of nodes,
                number of edges, network density, centralization, transitivity, and reciprocity.
        """
        # Get netwrok
        network = self.sna[f"network_{network_type}"]
        
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
    
    def get_sna_micro_stats(self, network_type: Literal["a", "b"]) -> pd.DataFrame:
        """
        Calculate and return micro-level statistics for each node in a directed network graph.

        Args:
            network_type: Literal["a", "b"]
                The type identifier for selecting the specific network.

        Returns:
            pd.DataFrame: A DataFrame with micro-level statistics for each node, including
                metrics like in-degree centrality, PageRank, betweenness, closeness centrality,
                hubs score, and nodes rankings.
        """
        # Get network
        network = self.sna[f"network_{network_type}"]

        # Create a DataFrame with micro-level statistics
        micro_level_stats = pd.concat([
            pd.Series(nx.to_pandas_adjacency(network).apply(lambda x: ", ".join(x[x > 0].index.values), axis=1), name="lns"),
            pd.Series(nx.in_degree_centrality(network), name="ic_raw"),
            pd.Series(nx.pagerank(network, max_iter=1000), name="pr_raw"),
            pd.Series(nx.betweenness_centrality(network), name="bt_raw"),
            pd.Series(nx.closeness_centrality(network), name="cl_raw"),
            pd.Series(nx.hits(network)[0], name="hu_raw").abs(),
        ], axis=1)
        
        # Identify nodes with no in-degree and/or out-degree
        micro_level_stats["nd"] = 0
        micro_level_stats["nd"] += (micro_level_stats["ic_raw"] == 0).astype(int)
        micro_level_stats["nd"] += (micro_level_stats["lns"].str.len() == 0).astype(int) * 2

        # Compute node ranks relative to each network centrality metric
        micro_level_stats_ranks = (
            micro_level_stats.iloc[:, 1:-1]  # omit first column (LNS) and last column (ND)
                .rename(columns=lambda x: x.replace("_raw", ""))
                .apply(lambda x: x.rank(method="dense", ascending=False))
                .add_suffix("_rank")
        )
        
        # Compute node percentiles relative to each network centrality metric
        micro_level_stats_pct = (
            micro_level_stats.iloc[:, 1:-1]
                .rename(columns=lambda x: x.replace("_raw", ""))
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
        
    def get_sna_rankings(self, network_type: Literal["a", "b"]) -> Dict[str, Dict[int, int]]:
        """
        Generate and return the order of nodes based on their rank scores for each centrality metric.

        Args:
            network_type: Literal["a", "b"]
                The type identifier for selecting the specific network.

        Returns:
            Dict[str, Dict[int, int]]:
                A dictionary mapping centrality metric names to dictionaries of nodes sorted by rank.
        """
        # Get network
        micro_stats = self.sna[f"micro_stats_{network_type}"]

        # Initialize dictionary to store ordered node rankings
        nodes_ordered_by_rank = {}

        # Get columns that represent rank data
        ranks = micro_stats.filter(regex=r"_rank$")
        
        # For each metric, nodes will be ordered by their relative rank
        for rank_label, rank_data in ranks.items():
            series = rank_data.to_frame().reset_index().sort_values(by=[rank_label, "index"]).set_index("index").squeeze()
            series.name = rank_label
            series = pd.to_numeric(series, downcast="integer")
            nodes_ordered_by_rank[rank_label] = series.to_dict()
        
        # Return the dictionary of nodes ordered by their rank for each metric
        return nodes_ordered_by_rank
        
    def get_sna_edges_types(self, network_type: Literal["a", "b"]) -> Dict[str, List[Tuple[str, str]]]:
        """
        Classify edges in a directed network graph into various types based on relationships within
        the same network and a reference network.

        Args:
            network_type: Literal["a", "b"]
                The type identifier for selecting the specific network.

        Returns:
            Dict[str, List[Tuple[str, str]]]:
                A dictionary classifying edges into five types: I, II, III, IV, and V.
        """
        # Get adiacency dataframes
        if network_type == "a":
            adj_df = self.sna["adjacency_a"]
            adj_ref_df = self.sna["adjacency_b"]
        else:
            adj_df = self.sna["adjacency_b"]
            adj_ref_df = self.sna["adjacency_a"]

        # Compute type I edges, non reciprocal
        # i.e. same network: A -> B and not B -> A
        type_i_df = adj_df - (adj_df * adj_df.T)
        type_i = type_i_df.stack().loc[lambda x: x == 1].index.tolist()

        # Compute type II edges, reciprocal
        # i.e. same network: A -> B and B -> A
        type_ii_df = pd.DataFrame(np.triu(adj_df) * np.tril(adj_df).T, index=adj_df.index, columns=adj_df.columns)
        type_ii = type_ii_df.stack().loc[lambda x: x == 1].index.tolist()

        # Compute type V edges, full simmetrical
        # i.e. A -> B, B -> A in network network and A -> B, B -> A in network G_ref
        type_v_df = type_ii_df * pd.DataFrame(np.triu(adj_ref_df) * np.tril(adj_ref_df).T, index=adj_df.index, columns=adj_df.columns)
        type_v = type_v_df.stack().loc[lambda x: x == 1].index.tolist()
        
        # Compute type III edges, half simmetrical
        # i.e. A -> B in network network and A -> B in network G_ref
        type_iii_df = pd.DataFrame(np.triu(adj_df) * np.triu(adj_ref_df), index=adj_df.index, columns=adj_df.columns)
        type_iii = type_iii_df.sub(type_v_df).stack().loc[lambda x: x == 1].index.tolist()
        
        # Compute type IV edges, half reversed simmetrical
        # i.e. A -> B in network network and B -> A in network G_ref
        type_iv_df = (
            pd.DataFrame(np.triu(adj_df) * np.tril(adj_ref_df).T, index=adj_df.index, columns=adj_df.columns)
            + pd.DataFrame(np.tril(adj_df) * np.triu(adj_ref_df).T, index=adj_df.index, columns=adj_df.columns)
        )
        type_iv = type_iv_df.sub(type_v_df).stack().loc[lambda x: x == 1].index.tolist()
        
        # Return edges types
        return {
            "type_i": type_i,
            "type_ii": type_ii,
            "type_iii": type_iii,
            "type_iv": type_iv,
            "type_v": type_v
        }
    
    def get_sna_components(self, network_type: Literal["a", "b"]) -> List[str]:
        """
        Identify and return the unique and significant components of a directed graph as strings.

        Args:
            network_type: Literal["a", "b"]
                The type identifier for selecting the specific network.

        Returns:
            List[str]: 
                A list of strings, each representing a unique component with its nodes concatenated.
        """
        # Get netwrok
        network = self.sna[f"network_{network_type}"]
        
        # Compute network components
        components = [
            *["".join(sorted(list(c))) for c in sorted(nx.kosaraju_strongly_connected_components(network), key=len, reverse=True) if len(c) > 2],
            *["".join(sorted(list(c))) for c in sorted(nx.weakly_connected_components(network), key=len, reverse=True) if len(c) > 2],
            *["".join(sorted(list(c))) for c in sorted(nx.find_cliques(network.to_undirected()), key=len, reverse=True) if len(c) > 2]
        ]
        
        # Ensure unique components and sort by length in descending order
        return sorted(list(set(components)), key=len, reverse=True)

    def create_sna_plot(self, network: nx.DiGraph, loc: Dict[str, Tuple[float, float]], network_type: Literal["a","b"]) -> plt.Figure:
        """
        Create a matplotlib plot of a network graph.

        Args:
            network: nx.DiGraph
                The directed graph to plot.
            loc: Dict[str, Tuple[float, float]]
                Node positions for layout.
            network_type: Literal["a", "b"]
                Type of the network ('a' or 'b'), used to determine node colors.

        Returns:
            plt.Figure: 
                The matplotlib figure containing the network plot.
        """
        
        # Set color based on graph type (A or B)
        color = A_COLOR if network_type == "a" else B_COLOR
        
        # Determine dimensions of matplotlib graph based upon number of nodes
        fig_size = (8 * CM_TO_INCHES, 8 * CM_TO_INCHES) \
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
        nx.draw_networkx_edges(network, loc, edgelist=reciprocal_edges, edge_color=color, 
                            arrowstyle='-', width=3, ax=ax)
        
        # Draw non reciprocal edges with specific style
        non_reciprocal_edges = [e for e in network.edges if e not in reciprocal_edges]
        nx.draw_networkx_edges(network, loc, edgelist=non_reciprocal_edges, edge_color=color, 
                            style="--", arrowstyle='-|>', arrowsize=15, ax=ax)
        # Return figure
        return fig

    def figure_to_base64_svg(self, fig: plt.Figure) -> str:
        """
        Convert a matplotlib figure to a base64-encoded SVG data URI.

        Args:
            fig: plt.Figure
                The matplotlib figure to convert.

        Returns:
            str: The SVG data URI of the figure.
        """
        # Initialize an in-memory buffer
        buffer = io.BytesIO()
        
        # Save figure to the buffer in SVG format then close it
        fig.savefig(buffer, format="svg", bbox_inches='tight', transparent=True, pad_inches=0.05)
        plt.close(fig)
        
        # Encode the buffer contents to a base64 string
        base64_encoded_string = b64encode(buffer.getvalue()).decode()
        
        # Return the data URI for the SVG
        return f"data:image/svg+xml;base64,{base64_encoded_string}"

    def get_sna_graph(self, network_type: Literal["a","b"]) -> str:
        """
        Generate a graphical representation of a network and return it encoded in base64 SVG format.

        Args:
            network_type: Literal["a", "b"]
                Type of the network ('a' or 'b') used to select which graph to create the plot for.

        Returns:
            str: The SVG data URI of the network plot.
        """

        # Get network
        network = self.sna[f"network_{network_type}"]

        # Get network locations
        loc = self.sna[f"loc_{network_type}"]

        # Create the matplotlib plot
        fig = self.create_sna_plot(network, loc, network_type)
        
        # Convert to base64 SVG string
        return self.figure_to_base64_svg(fig)
    
    def handle_isolated_nodes(self, network: nx.DiGraph, loc: Dict[Any, np.ndarray]) -> Dict[Any, np.ndarray]:
        """"
        Add isolated nodes to the network and adjust their positions to appear marginal.

        Adjust the positions of isolated nodes to appear outside the convex hull of the main node
        cluster so that they are perceptually distant and marginal.

        Args:
            network: nx.DiGraph
                The directed graph where isolated nodes are managed.
            loc: Dict[Any, np.ndarray]
                A dictionary representing the layout of nodes.

        Returns:
            Dict[Any, np.ndarray]: Updated node layout including isolated nodes.
        """
        # Get isolated nodes, if any
        isolates = list(nx.isolates(network))
        
        # If there are no isolated nodes, just return loc
        if not isolates:
            return loc
        
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
            return loc

    def get_network_centralization(self, network: nx.Graph) -> float:
        """
        Calculate the centralization of a network.

        Centralization indicates how concentrated the network is around its most central node, 
        comparing the current network structure to an ideal star network structure.

        Args:
            network: nx.Graph
                The graph for which the centralization is calculated.

        Returns:
            float: The centralization value of the network, rounded to three decimal places.
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
    
    def get_sociogram_data(self) -> Dict[str, Union[pd.DataFrame, Dict[str, float]]]:
        """
        Computes a sociogram DataFrame based on two directed graphs representing 
        social network data for preferences and rejections.

        Returns:
            Dict[str, Union[pd.DataFrame, Dict[str, float]]]:
                A dictionary containing sociogram micro and macro statistics and supplemental indices.
        """

        network_a = self.sna["network_a"]
        matrix_a = self.sna["adjacency_a"]

        network_b = self.sna["network_b"]
        matrix_b = self.sna["adjacency_b"]
        
        # Compute basic data for sociogram micro stats
        out_preferences = pd.Series(dict(network_a.out_degree()), name="gp")
        out_rejects = pd.Series(dict(network_b.out_degree()), name="gr")
        in_preferences = pd.Series(dict(network_a.in_degree()), name="rp")
        in_rejects = pd.Series(dict(network_b.in_degree()), name="rr")
        
        # Init sociogram micro stats dataframe
        sociogram_micro_df = pd.concat([in_preferences, in_rejects, out_preferences, out_rejects], axis=1)
        

        # Add mutual preferences
        sociogram_micro_df["mp"] = (matrix_a * matrix_a.T).dot(np.ones(matrix_a.shape[0])).astype(int)

        # Add mutual rejections
        sociogram_micro_df["mr"] = (matrix_b * matrix_b.T).dot(np.ones(matrix_b.shape[0])).astype(int)

        # Add balance
        sociogram_micro_df["bl"] = (
            sociogram_micro_df["rp"]
                .sub(sociogram_micro_df["rr"])
        )

        # Add orientation       
        sociogram_micro_df["or"] = (
            sociogram_micro_df["gp"]
                .sub(sociogram_micro_df["gr"])
        )

        # Add impact
        sociogram_micro_df["im"] = (
            sociogram_micro_df["rp"]
                .add(sociogram_micro_df["rr"])
        )
        
        # Add affiliation coefficient raw
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

        # Add influence coefficient raw
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
        sociogram_micro_df.loc[np.logical_and(z_impact.between(.5, 1), z_balance > 1), "status"] = "appreciated"
        sociogram_micro_df.loc[np.logical_and(z_impact > 1, z_balance > 1), "st"] = "popular"
        sociogram_micro_df.loc[np.logical_and(z_impact > -.5, z_balance < -1), "st"] = "rejected"
        sociogram_micro_df.loc[np.logical_and(z_impact > 0, z_balance.between(-.5, .5)), "st"] = "controversial"
        
        # Compute sociogram macro stats
        sociogram_numeric_columns = sociogram_micro_df.select_dtypes(np.number)
        median = sociogram_numeric_columns.median()
        sociogram_macro_df = sociogram_numeric_columns.describe().T
        sociogram_macro_df.insert(1, "median", median)

        # Add cohesion index
        cohesion_index_type_i = (len(self.sna["edges_types_a"]["type_ii"]) *2) / len(network_a.edges())
        cohesion_index_type_ii = len(self.sna["edges_types_a"]["type_ii"]) / len(network_a)

        # Add conflict index
        conflict_index_type_i = (len(self.sna["edges_types_b"]["type_ii"]) *2) / len(network_b.edges())
        conflict_index_type_ii = len(self.sna["edges_types_b"]["type_ii"]) / len(network_b)

        # Return sociogram dataframe, ordered by node
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
    
    def get_sociogram_rankings(self, micro_stats: pd.DataFrame):

        # Initialize dictionary to store ordered node rankings
        nodes_ordered_by_rank = {}

        # Get columns that represent rank data
        metrics = micro_stats.loc[:, [ "rp", "rr", "bl", "im", "ac_raw", "ic_raw"]]
        
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
            series.name = metric_label
            series = pd.to_numeric(series, downcast="integer")
            nodes_ordered_by_rank[metric_label] = series.to_dict()
        
        # Return the dictionary of nodes ordered by their rank for each metric
        return nodes_ordered_by_rank
