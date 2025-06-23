"""
Filename: abgrid_sna.py
Description: Provides functionality to analyze directed networks (graphs) for a given set of edges.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

from typing import Literal, List, Dict, Optional, Tuple, TypedDict, Union
from functools import reduce
from scipy.spatial import ConvexHull

from lib import A_COLOR, B_COLOR, CM_TO_INCHES
from lib.abgrid_utils import compute_descriptives, figure_to_base64_svg

class SNADict(TypedDict):
    """Type definition for the SNA dictionary containing network analysis results."""
    nodes_a: Optional[List[str]]
    nodes_b: Optional[List[str]]
    edges_a: Optional[List[Tuple[str, str]]]
    edges_b: Optional[List[Tuple[str, str]]]
    adjacency_a: Optional[pd.DataFrame]
    adjacency_b: Optional[pd.DataFrame]
    network_a: Optional[nx.DiGraph]
    network_b: Optional[nx.DiGraph]
    loc_a: Optional[Dict[str, np.ndarray]]
    loc_b: Optional[Dict[str, np.ndarray]]
    macro_stats_a: Optional[pd.Series]
    macro_stats_b: Optional[pd.Series]
    micro_stats_a: Optional[pd.DataFrame]
    micro_stats_b: Optional[pd.DataFrame]
    descriptives_a: Optional[pd.DataFrame]
    descriptives_b: Optional[pd.DataFrame]
    rankings_a: Optional[Dict[str, pd.Series]]
    rankings_b: Optional[Dict[str, pd.Series]]
    edges_types_a: Optional[Dict[str, pd.Index]]
    edges_types_b: Optional[Dict[str, pd.Index]]
    components_a: Optional[Dict[str, pd.Series]]
    components_b: Optional[Dict[str, pd.Series]]
    graph_a: Optional[str]
    graph_b: Optional[str]
    rankings_ab: Optional[Dict[str, pd.DataFrame]]
    relevant_nodes_ab: Optional[Dict[str, pd.DataFrame]]

class ABGridSna:
    """
    A class for comprehensive social network analysis on directed graphs.
    
    Provides functionality to analyze two directed networks (A and B) simultaneously,
    computing various network metrics, statistics, and visualizations. Supports comparative
    analysis between the two networks, generating reports on network structure,
    centrality measures, and graph properties.
    
    Attributes:
        sna (SNADict): Dictionary containing all computed network analysis data for both networks.
    """

    def __init__(self) -> None:
        """
        Initialize the social network analysis object.
        
        Sets up an internal dictionary for storing SNA data
        for both networks A and B, with all values initially set to None.
        """
        
        # Initialize SNA dict with all possible keys
        self.sna: SNADict = {
            "nodes_a": None,
            "nodes_b": None,
            "edges_a": None,
            "edges_b": None,
            "edges_types_a": None,
            "edges_types_b": None,
            "adjacency_a": None,
            "adjacency_b": None,
            "network_a": None,
            "network_b": None,
            "loc_a": None,
            "loc_b": None,
            "macro_stats_a": None,
            "macro_stats_b": None,
            "micro_stats_a": None,
            "micro_stats_b": None,
            "descriptives_a": None,
            "descriptives_b": None,
            "rankings_a": None,
            "rankings_b": None,
            "components_a": None,
            "components_b": None,
            "graph_a": None,
            "graph_b": None,
            "rankings_ab": None,
            "relevant_nodes_ab": None
        }

    def get(self, 
            packed_edges_a: List[Dict[str, str]], 
            packed_edges_b: List[Dict[str, str]], 
    ) -> SNADict:
        """
        Compute and store comprehensive network analysis for two directed networks.

        Performs a complete social network analysis on input networks,
        including graph construction, statistical analysis, centrality measures, 
        component detection, and visualization generation.

        Args:
            packed_edges_a (List[Dict[str, str]]): 
                Edge data for network A. Each dictionary represents edges from a source node,
                with keys as source nodes and values as comma-separated target nodes.
            packed_edges_b (List[Dict[str, str]]): 
                Edge data for network B. Structure mirrors `packed_edges_a`.

        Returns:
            SNADict: A dictionary containing all network analysis results
                     including nodes, edges, adjacency matrices, statistics, rankings,
                     components, and visualization data for both networks.

        Side Effects:
            - Creates NetworkX DiGraph objects for both networks
            - Computes and stores macro/micro statistics for each network
            - Generates node layout information with isolated node handling
            - Updates all fields in the internal `self.sna` dictionary
            - Creates SVG visualizations of both networks
        """
        
        # Store network A and B nodes and edges
        for network_type, packed_edges in [("a", packed_edges_a), ("b", packed_edges_b)]:
            self.sna[f"nodes_{network_type}"] = self._unpack_network_nodes(packed_edges)
            self.sna[f"edges_{network_type}"] = self._unpack_network_edges(packed_edges)
            self.sna[f"network_{network_type}"] = nx.DiGraph(self.sna[f"edges_{network_type}"])

        # Add isolated nodes to networks A and B and 
        # store nodes layout locations
        for network_type, network, nodes in [
            ("a", self.sna["network_a"], self.sna["nodes_a"]), 
            ("b", self.sna["network_b"], self.sna["nodes_b"])
        ]:  
            # Add isolated nodes to current network
            isolated_nodes = set(list(network)).symmetric_difference(set(nodes))
            network.add_nodes_from(isolated_nodes)
            
            # Generate layout locations (loc) for current network
            loc = nx.kamada_kawai_layout(network)
            
            # Update loc to push isolated nodes away from other nodes
            updated_loc = self._handle_isolated_nodes(network, loc)

            # Store current network layout locations
            self.sna[f"loc_{network_type}"] = updated_loc

            # Add current network adjacency matrix
            self.sna[f"adjacency_{network_type}"] = nx.to_pandas_adjacency(network, nodelist=nodes)
                    
        # Store edge types, components, macro stats, micro stats, descriptives, rankings and graphs
        for network_type in ("a", "b"):
            self.sna[f"edges_types_{network_type}"] = self.compute_edges_types(network_type)
            self.sna[f"components_{network_type}"] = self.compute_components(network_type)
            self.sna[f"macro_stats_{network_type}"] = self.compute_macro_stats(network_type)
            self.sna[f"micro_stats_{network_type}"] = self.compute_micro_stats(network_type)
            self.sna[f"descriptives_{network_type}"] = self.compute_descriptives(network_type)
            self.sna[f"rankings_{network_type}"] = self.compute_rankings(network_type)
            self.sna[f"graph_{network_type}"] = self.create_graph(network_type)

        # Store rankings comparison between networks
        self.sna["rankings_ab"] = self.compute_rankings_ab()

        # Store relevant nodes analysis
        self.sna["relevant_nodes_ab"] = self.compute_relevant_nodes_ab()

        return self.sna
    
    def compute_macro_stats(self, network_type: Literal["a", "b"]) -> pd.Series:
        """
        Calculate macro-level network statistics.

        Computes network-wide metrics including structural properties, centralization,
        and relationship patterns for the specified network.

        Args:
            network_type (Literal["a", "b"]):
                Network identifier ('a' or 'b') for selecting the target network.

        Returns:
            pd.Series:
                Series containing macro-level statistics with the following metrics:
                - network_nodes: Total number of nodes
                - network_edges: Total number of edges  
                - network_edges_reciprocal: Number of reciprocal edge pairs
                - network_density: Edge density (0-1 scale)
                - network_centralization: Degree centralization measure
                - network_transitivity: Global clustering coefficient
                - network_reciprocity: Overall reciprocity measure

        Raises:
            ValueError: If required data is not available.
        """
        # Check if required data is available
        if self.sna[f"network_{network_type}"] is None:
            raise ValueError(f"Network data for type '{network_type}' is not available.")
        
        if self.sna[f"edges_types_{network_type}"] is None:
            raise ValueError(f"Edge types data for network '{network_type}' is not available.")
    
        # Get network
        network = self.sna[f"network_{network_type}"]

        # Get network edges types
        edges_types = self.sna[f"edges_types_{network_type}"]
        
        # Compute macro-level statistics
        network_nodes = network.number_of_nodes()
        network_edges = network.number_of_edges()
        network_edges_reciprocal = edges_types["type_ii"].shape[0]
        network_density = nx.density(network)
        network_centralization = self._compute_network_centralization(network.to_undirected())
        network_transitivity = nx.transitivity(network)
        network_reciprocity = nx.overall_reciprocity(network)
        
        return pd.Series({
            "network_nodes": network_nodes,
            "network_edges": network_edges,
            "network_edges_reciprocal": network_edges_reciprocal,
            "network_density": network_density,
            "network_centralization": network_centralization,
            "network_transitivity": network_transitivity,
            "network_reciprocity": network_reciprocity,
        })
    
    def compute_micro_stats(self, network_type: Literal["a", "b"]) -> pd.DataFrame:
        """
        Calculate node-level (micro) statistics for the specified network.

        Computes various centrality measures and node properties for each node
        in the network, including degree-based and path-based centralities.

        Args:
            network_type (Literal["a", "b"]):
                Network identifier ('a' or 'b') for selecting the target network.

        Returns:
            pd.DataFrame: 
                DataFrame indexed by node identifiers with the following columns:
                - lns: Comma-separated list of neighbor nodes (out-neighbors)
                - ic: In-degree centrality
                - kz: Katz centrality
                - pr: PageRank score
                - bt: Betweenness centrality
                - cl: Closeness centrality  
                - hu: Hubs score (absolute value)
                - nd: Node degree status (0=normal, 1=no in-degree, 2=no out-degree, 3=isolated)
                - *_rank: Rank columns for each centrality measure (ic_rank, kz_rank, etc.)

        Raises:
            ValueError: If required network data is not available.
            nx.NetworkXError: If centrality computations fail to converge.
        """
        # Check if required data is available
        if self.sna[f"network_{network_type}"] is None:
            raise ValueError(f"Network data for type '{network_type}' is not available.")
        
        if self.sna[f"adjacency_{network_type}"] is None:
            raise ValueError(f"Adjacency matrix for network '{network_type}' is not available.")
   
        # Get network and adjacency
        network = self.sna[f"network_{network_type}"]
        adjacency = self.sna[f"adjacency_{network_type}"]

        # Create a DataFrame with micro-level statistics
        micro_level_stats = pd.concat([
            pd.Series(adjacency.apply(lambda x: ", ".join(x[x > 0].index.values), axis=1), name="lns"),
            pd.Series(nx.in_degree_centrality(network), name="ic"),
            pd.Series(nx.katz_centrality(network), name="kz"),
            pd.Series(nx.pagerank(network), name="pr"),
            pd.Series(nx.betweenness_centrality(network), name="bt"),
            pd.Series(nx.closeness_centrality(network), name="cl"),
            pd.Series(nx.hits(network)[0], name="hu").abs(),
        ], axis=1)
        
        # Identify nodes with no in-degree and/or out-degree
        # 3 -> no in or out degree, 2 -> no out-degree, 1 -> no in-degree, 0 -> normal
        micro_level_stats["nd"] = 0
        micro_level_stats["nd"] += (micro_level_stats["ic"] == 0).astype(int)
        micro_level_stats["nd"] += (micro_level_stats["lns"].str.len() == 0).astype(int) * 2

        # Compute node ranks relative to each network centrality metric
        micro_level_stats_ranks = (
            micro_level_stats.iloc[:, 1:-1]  # omit first column (LNS) and last column (ND)
                .rank(method="dense", ascending=False)
                .add_suffix("_rank")
        )

        return (
            pd.concat([
                micro_level_stats,
                micro_level_stats_ranks,
            ], axis=1)
                .sort_index()
        )

    def compute_descriptives(self, network_type: Literal["a", "b"]) -> pd.DataFrame:
        """
        Compute descriptive statistics for centrality measures.

        Generates summary statistics (mean, std, min, max, etc.) for the main
        centrality measures of the specified network.

        Args:
            network_type (Literal["a", "b"]):
                Network identifier ('a' or 'b') for selecting the target network.

        Returns:
            pd.DataFrame: 
                DataFrame with descriptive statistics for centrality measures.
                Columns correspond to centrality measures (ic, pr, kz, bt, cl, hu).
                Rows contain statistical summaries (count, mean, std, min, max, etc.).

        Raises:
            ValueError: If required micro statistics data is not available.
        """
        # Check if required data is available
        if self.sna[f"micro_stats_{network_type}"] is None:
            raise ValueError(f"Micro statistics for network '{network_type}' are not available.")
   
        # Select columns to retain for descriptive statistics
        columns_to_retain = ["ic", "pr", "kz", "bt", "cl", "hu"]

        # Select numeric columns only
        sna_numeric_columns = self.sna[f"micro_stats_{network_type}"].loc[:, columns_to_retain]
        
        return compute_descriptives(sna_numeric_columns)

    def compute_rankings(self, network_type: Literal["a", "b"]) -> Dict[str, pd.Series]:
        """
        Generate node rankings based on centrality measures.
        
        Creates ordered rankings of nodes for each centrality metric, where
        nodes are sorted by their rank scores in ascending order.
        
        Args:
            network_type (Literal["a", "b"]): 
                Network identifier ('a' or 'b') for selecting the target network.
        
        Returns:
            Dict[str, pd.Series]: 
                Dictionary mapping centrality metric names (with '_rank' suffix) to
                pandas Series containing nodes ordered by their rank (best to worst).
                Each Series is indexed by node identifiers and contains rank values.

        Example:
            >>> rankings = compute_rankings("a")
            >>> rankings["ic_rank"]  # Returns nodes ordered by in-degree centrality rank
            node_A    1.0
            node_C    2.0  
            node_B    3.0
            dtype: float64

        Raises:
            ValueError: If required micro statistics data is not available.
        """
        # Check if required data is available
        if self.sna[f"micro_stats_{network_type}"] is None:
            raise ValueError(f"Micro statistics for network '{network_type}' are not available.")
    
        # Get the micro stats DataFrame for the specified network type
        micro_stats_df = self.sna[f"micro_stats_{network_type}"]
        
        # Filter columns that end with '_rank' to get ranking data
        rank_columns = micro_stats_df.filter(regex=r"_rank$").astype(int)
        
        # Convert to dictionary with metric names as keys and Series as values
        rankings = {}
        for metric_name in rank_columns.columns:
            rankings[metric_name] = rank_columns[metric_name].sort_values()
        
        return rankings

    def compute_rankings_ab(self) -> Dict[str, pd.DataFrame]:
        """
        Compute combined rankings from both networks A and B.

        Merges the rankings from both networks into side-by-side DataFrames
        for easy comparison of node rankings across the two networks.

        Returns:
            Dict[str, pd.DataFrame]: A dictionary where each key corresponds to a ranking metric
            (e.g., 'ic_rank', 'pr_rank'), and the value is a DataFrame with two columns:
            - Column ending with '_a': Rankings from network A
            - Column ending with '_b': Rankings from network B

        Raises:
            ValueError: If the rankings for network 'a' or 'b' are not available.
        """
        
        # Check if required data is available
        if self.sna["rankings_a"] is None or self.sna["rankings_b"] is None:
            raise ValueError("Rankings for network a and b are not available.")
        
        # Get the rankings from network A and B
        rankings_a = self.sna["rankings_a"]
        rankings_b = self.sna["rankings_b"]

        # Combine them into side-by-side DataFrames
        rankings_ab = {}
        for k in rankings_a.keys():
            series_a = rankings_a[k]
            series_a.name = series_a.name + "_a"  # Rename to include network identifier
            series_b = rankings_b[k]
            series_b.name = series_a.name + "_b"  # Rename to include network identifier
            rankings_ab[k] = pd.concat([series_a, series_b], axis=1) 

        return rankings_ab
    
    def compute_relevant_nodes_ab(self, threshold: float = 0.05) -> Dict[str, pd.DataFrame]:
        """   
        Finds nodes that rank highly (low rank values) in various centrality measures
        for both network A and network B.
        
        Args:
            threshold (float): Percentile threshold for selecting top nodes (default: 0.05 for top 5%)
            
        Returns:
            Dict[str, pd.DataFrame]: 
                Dictionary with keys 'a' and 'b', each containing a DataFrame of relevant nodes.
                Each DataFrame has columns:
                - 'node_id': node identifier
                - 'metric': metric name without '_rank' suffix
                - 'rank': re-computed dense rank position
                - 'value': original metric value from micro_stats
                - 'weight': computed weight using formula 10 / (rank ** 0.8)
                - 'evidence_type': always 'sna'

        Note:
            - Lower rank values indicate higher centrality (rank 1 = most central)
            - Weight calculation uses formula: 10.0 / (rank ** 0.8)
            - Only nodes ranking in the top threshold percentile are included
            - Processes all ranking columns ending with '_rank' from rankings data

        Raises:
            ValueError: If rankings or micro_stats for both networks are not available.
        """
        # Make sure data is available
        if self.sna["rankings_a"] is None or self.sna["rankings_b"] is None or self.sna["micro_stats_a"] is None or self.sna["micro_stats_b"] is None:
            raise ValueError("SNA micro stats and rankings for both networks a and b are required.")
        
        # Init dict with empty sub-dicts for storing relevant nodes
        relevant_nodes_ab = {"a": pd.DataFrame(), "b": pd.DataFrame()}
        
        # Process both positive (a) and negative (b) relevance directions
        for valence_type in relevant_nodes_ab.keys():

            # Select micro_stats abd rankings to use
            micro_stats =  self.sna["micro_stats_a"] if valence_type == "a" else self.sna["micro_stats_b"]
            rankings = self.sna["rankings_a"] if valence_type == "a" else self.sna["rankings_b"]

            # Loop through metrics and associated ranks
            for metric_rank_name, ranks_series in rankings.items():
                
                # Clean metric name
                metric_name = re.sub("_rank", "", metric_rank_name)
               
                # Get threshold value for this metric
                threshold_value = ranks_series.quantile(threshold)
                
                # Filter top nodes (assuming lower rank = better)
                relevant_ranks = ranks_series[ranks_series.le(threshold_value)]

                # Compute relevant nodes data
                relevant_nodes = (
                    relevant_ranks
                        .to_frame()
                        .assign(
                            metric=metric_name,
                            rank=relevant_ranks.rank(method="dense", ascending=True),
                            value=micro_stats.loc[relevant_ranks.index, metric_name],
                            weight=lambda x: x["rank"].pow(.8).rdiv(10),
                            evidence_type="sna"
                        )
                        .reset_index(drop=False, names="node_id")
                )
                
                # Add relevant nodes to dataframe
                relevant_nodes_ab[valence_type] = pd.concat([
                    relevant_nodes_ab[valence_type],
                    relevant_nodes
                ], ignore_index=True)
                
        return relevant_nodes_ab

    def compute_edges_types(self, network_type: Literal["a", "b"]) -> Dict[str, pd.Index]:
        """
        Classify edges into five types based on reciprocity and cross-network relationships.

        Analyzes edge patterns within the specified network and compares them with
        the reference network to classify edges into five distinct types.

        Args:
            network_type (Literal["a", "b"]):
                Network identifier ('a' or 'b') for selecting the target network.
                The other network serves as the reference for comparison.

        Returns:
            Dict[str, pd.Index]:
                Dictionary containing five edge classifications:
                - type_i: Non-reciprocal edges (A→B but not B→A in same network)
                - type_ii: Reciprocal edges (A↔B in same network)  
                - type_iii: Half symmetrical (A→B in both networks, but not B→A)
                - type_iv: Half reversed symmetrical (A→B in one, B→A in other)
                - type_v: Fully symmetrical (A↔B in both networks)

        Note:
            Edge classification uses upper triangular matrices to avoid double-counting
            reciprocal relationships. The reference network is determined automatically
            (network 'b' is reference for 'a', and vice versa).

        Raises:
            ValueError: If required adjacency matrix data is not available.
        """
        # Check if required data is available
        if self.sna["adjacency_a"] is None:
                raise ValueError("Adjacency matrix for network 'a' is not available.")
        if self.sna["adjacency_b"] is None:
            raise ValueError("Adjacency matrix for network 'b' is not available.")
        
        # Get the adjacency DataFrames for the specified network type and reference
        if network_type == "a":
            adj_df = self.sna["adjacency_a"]
            adj_ref_df = self.sna["adjacency_b"]
        else:
            adj_df = self.sna["adjacency_b"]
            adj_ref_df = self.sna["adjacency_a"]

        # Compute type I edges, non-reciprocal
        # i.e. same network: A -> B and not B -> A
        type_i_df = adj_df - (adj_df * adj_df.T)
        type_i = type_i_df.stack().loc[lambda x: x == 1].index

        # Compute type II edges, reciprocal
        # i.e. same network: A -> B and B -> A
        type_ii_df = pd.DataFrame(np.triu(adj_df) * np.tril(adj_df).T, index=adj_df.index, columns=adj_df.columns)
        type_ii = type_ii_df.stack().loc[lambda x: x == 1].index

        # Compute type V edges, fully symmetrical
        # i.e. A -> B, B -> A in network and A -> B, B -> A in reference network
        type_v_df = type_ii_df * pd.DataFrame(np.triu(adj_ref_df) * np.tril(adj_ref_df).T, index=adj_df.index, columns=adj_df.columns)
        type_v = type_v_df.stack().loc[lambda x: x == 1].index
        
        # Compute type III edges, half symmetrical
        # i.e. A -> B in network and A -> B in reference network
        type_iii_df = pd.DataFrame(np.triu(adj_df) * np.triu(adj_ref_df), index=adj_df.index, columns=adj_df.columns)
        type_iii = type_iii_df.sub(type_v_df).stack().loc[lambda x: x == 1].index
        
        # Compute type IV edges, half reversed symmetrical
        # i.e. A -> B in network and B -> A in reference network
        type_iv_df = (
            pd.DataFrame(np.triu(adj_df) * np.tril(adj_ref_df).T, index=adj_df.index, columns=adj_df.columns)
            + pd.DataFrame(np.tril(adj_df) * np.triu(adj_ref_df).T, index=adj_df.index, columns=adj_df.columns)
        )
        type_iv = type_iv_df.sub(type_v_df).stack().loc[lambda x: x == 1].index
        
        return {
            "type_i": type_i,
            "type_ii": type_ii,
            "type_iii": type_iii,
            "type_iv": type_iv,
            "type_v": type_v
        }
    
    def compute_components(self, network_type: Literal["a", "b"]) -> Dict[str, pd.Series]:
        """
        Identify and extract significant network components.

        Finds various types of network components (cliques, strongly connected components,
        weakly connected components) and returns them as concatenated node strings.
        Only components with more than 2 nodes are included.

        Args:
            network_type (Literal["a", "b"]):
                Network identifier ('a' or 'b') for selecting the target network.

        Returns:
            Dict[str, pd.Series]: 
                Dictionary containing three types of components:
                - cliques: Maximal cliques in the undirected version of the graph
                - strongly_connected: Strongly connected components in the directed graph
                - weakly_connected: Weakly connected components in the directed graph
                
                Each Series contains components as concatenated, sorted node strings.
                Components are sorted by size (largest first).

        Example:
            >>> components = compute_components("a")
            >>> components["cliques"]
            0    ABC
            1    BCD
            dtype: object

        Raises:
            ValueError: If required network data is not available.
        """
        # Check if required data is available
        if self.sna[f"network_{network_type}"] is None:
            raise ValueError(f"Network data for type '{network_type}' is not available.")
    
        # Get network
        network = self.sna[f"network_{network_type}"]
        
        # Compute network components
        components = {
            "cliques": pd.Series([ "".join(sorted(list(c))) for c in sorted(nx.find_cliques(network.to_undirected()), key=len, reverse=True) if len(c) > 2 ]),
            "strongly_connected": pd.Series([ "".join(sorted(list(c))) for c in sorted(nx.strongly_connected_components(network), key=len, reverse=True) if len(c) > 2 ]),
            "weakly_connected": pd.Series([ "".join(sorted(list(c))) for c in sorted(nx.weakly_connected_components(network), key=len, reverse=True) if len(c) > 2 ]),
        }

        # Return components
        return components

    def create_graph(self, network_type: Literal["a","b"]) -> str:
        """
        Generate an SVG visualization of the specified network.

        Creates a matplotlib-based network visualization with nodes, edges, and labels,
        then converts it to a base64-encoded SVG string for web display.

        Args:
            network_type (Literal["a", "b"]):
                Network identifier ('a' or 'b') for selecting which network to visualize.

        Returns:
            str: Base64-encoded SVG data URI of the network visualization.
                 The visualization includes:
                 - Colored nodes (different colors for networks A and B)
                 - Black nodes for isolated vertices
                 - Reciprocal edges shown as undirected lines
                 - Non-reciprocal edges shown as directed arrows
                 - Node labels with white text

        Note:
            - Uses Kamada-Kawai layout with special handling for isolated nodes
            - Network A uses A_COLOR, Network B uses B_COLOR (from lib constants)
            - Figure size is set to 17cm x 19cm
            - Isolated nodes are positioned at the periphery using convex hull positioning

        Raises:
            KeyError: If the specified network_type is not found in self.sna.
            ValueError: If the network layout computation fails.
        """

        # Get network
        network = self.sna[f"network_{network_type}"]

        # Get network layout locations
        loc = self.sna[f"loc_{network_type}"]

        # Set color based on graph type (a or b)
        color = A_COLOR if network_type == "a" else B_COLOR
        
        # Set dimensions of matplotlib graph
        fig_size = (17 * CM_TO_INCHES, 19 * CM_TO_INCHES)
        
        # Create a matplotlib figure
        fig, ax = plt.subplots(constrained_layout=True, figsize=fig_size)
        
        # Hide axis
        ax.axis('off')
        
        # Draw nodes
        nx.draw_networkx_nodes(
            network, loc, 
            node_color=color, edgecolors=color, ax=ax
        )
        
        # Draw isolated nodes in black
        nx.draw_networkx_nodes(nx.isolates(network), loc, node_color="#000", edgecolors="#000", ax=ax)
        
        # Draw nodes labels
        nx.draw_networkx_labels(network, loc, font_family="Times New Roman", font_color="#FFF", font_weight="normal", font_size=10, ax=ax)
        
        # Draw reciprocal edges with specific style (undirected lines)
        reciprocal_edges = [e for e in network.edges if e[::-1] in network.edges]
        nx.draw_networkx_edges(
            network, loc, edgelist=reciprocal_edges, 
            edge_color=color, arrowstyle='-', width=4, min_target_margin=0, 
            ax=ax
        )
        
        # Draw non-reciprocal edges with specific style (directed arrows)
        non_reciprocal_edges = [e for e in network.edges if e not in reciprocal_edges]
        nx.draw_networkx_edges(
            network, loc, edgelist=non_reciprocal_edges, 
            edge_color=color, arrowstyle="->", width=.4, min_target_margin=10,
            ax=ax 
        )
        
        return figure_to_base64_svg(fig)

    def _unpack_network_edges(self, packed_edges: List[Dict[str, str]]) -> List[Tuple[str, str]]:
        """
        Unpack edge dictionaries into a list of directed edge tuples.

        Takes a list of dictionaries where each dictionary represents outgoing edges
        from source nodes, and converts them into a flat list of (source, target) tuples.

        Args:
            packed_edges (List[Dict[str, str]]): 
                List of dictionaries where keys are source nodes and values are
                comma-separated strings of target nodes. None values are safely handled.

        Returns:
            List[Tuple[str, str]]: 
                Flat list of directed edge tuples (source, target).

        Example:
            >>> packed_edges = [{"A": "B,C"}, {"B": "C"}]
            >>> _unpack_network_edges(packed_edges)
            [("A", "B"), ("A", "C"), ("B", "C")]
        """
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
        
    def _unpack_network_nodes(self, packed_edges: List[Dict[str, str]]) -> List[str]:
        """
        Extract unique source nodes from packed edge dictionaries.

        Args:
            packed_edges (List[Dict[str, str]]): 
                List of dictionaries where keys represent source nodes.

        Returns:
            List[str]: 
                Sorted list of unique source node identifiers.

        Example:
            >>> packed_edges = [{"A": "B,C"}, {"B": "C"}]
            >>> _unpack_network_nodes(packed_edges)
            ["A", "B"]
        """
        return sorted([node for node_edges in packed_edges for node in node_edges.keys()])

    def _handle_isolated_nodes(self, network: nx.DiGraph, loc: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """
        Position isolated nodes at the periphery of the network layout.

        Adjusts the positions of isolated nodes to appear outside the convex hull
        of connected nodes, making them visually distinct and marginal in the layout.

        Args:
            network (nx.DiGraph):
                The directed graph containing both connected and isolated nodes.
            loc (Dict[str, np.ndarray]):
                Dictionary mapping node identifiers to their 2D coordinate positions.

        Returns:
            Dict[str, np.ndarray]: 
                Updated node layout dictionary with isolated nodes repositioned
                at the periphery. Connected nodes retain their original positions.

        Algorithm:
            1. Identifies isolated nodes using NetworkX
            2. Computes convex hull around connected nodes
            3. Places isolated nodes outside the hull in multiple rounds
            4. Each round places nodes further from the center
            5. Adds random offset to prevent overlapping

        Note:
            - If no isolated nodes exist, returns the original layout unchanged
            - Uses multiple rounds to handle cases with more isolated nodes than hull vertices
            - Distance multiplier increases with each round (0.15 * round_number)
            - Random offset range: ±0.05 in both x and y directions

        Raises:
            ValueError: If convex hull computation fails (e.g., with < 3 connected nodes).
        """
        # Get isolated nodes
        isolates = list(nx.isolates(network))
        
        # If there are no isolated nodes, just return original layout
        if not isolates:
            return loc
        
        # Convert current loc coordinates to dataframe
        coordinates = pd.DataFrame(loc).T
        
        # Compute centroid of coordinates
        coordinates_centroid = np.mean(coordinates, axis=0)
        
        # Compute convex hull around coordinates
        hull = ConvexHull(coordinates)
        
        # Get hull vertices
        hull_vertices = coordinates.iloc[hull.vertices].values
        
        # Create an iterator from isolated nodes list
        isolate_iter = iter(isolates)

        # Keep track of loop rounds
        round_num = 1
        
        # Loop until all isolated nodes are placed
        try:
            while True:
                
                # Loop through hull vertices in current round
                for vertex in hull_vertices:
                    
                    # Get next isolated node
                    isolate = next(isolate_iter)
                    
                    # Create direction vector from coordinates centroid to current hull vertex
                    direction = vertex - coordinates_centroid
                    direction /= np.linalg.norm(direction)
                    
                    # Set distance multiplier (increases with each round)
                    distance_multiplier = 0.15 * round_num
                    
                    # Add some randomness to position
                    random_offset = np.random.uniform(-0.05, 0.05, size=2)
                    
                    # Calculate final position
                    candidate_pos = vertex + direction * distance_multiplier + random_offset
                    
                    # Update isolated node position
                    loc[isolate] = candidate_pos
                
                # Move to next round, as hull vertices have been fully exploited
                # but other isolated nodes need to be placed
                round_num += 1
        
        # All isolated nodes have been placed
        except StopIteration:
            return loc
        
    def _compute_network_centralization(self, network: nx.Graph) -> float:
        """
        Calculate the degree centralization of an undirected network.

        Centralization measures how concentrated the network structure is around
        its most central node, comparing the actual network to a perfect star network.
        Values range from 0 (completely decentralized) to 1 (perfectly centralized).

        Args:
            network (nx.Graph):
                Undirected graph for which to calculate centralization.
                Should typically be the undirected version of a directed graph.

        Returns:
            float: 
                Network centralization value between 0 and 1, where:
                - 0 indicates a completely decentralized network (all nodes have equal degree)
                - 1 indicates a perfectly centralized network (star topology)
                - Higher values suggest more centralized structure

        Formula:
            Centralization = Σ(max_centrality - node_centrality) / ((n-1)(n-2))
            where n is the number of nodes.

        Note:
            This implementation uses degree centrality as the basis for centralization.
            The network should have at least 3 nodes for meaningful centralization values.

        Raises:
            ZeroDivisionError: If the network has fewer than 3 nodes.
            nx.NetworkXError: If the network is empty or invalid.
        """
        
        # Get number of nodes
        number_of_nodes = network.number_of_nodes()
        
        # Compute node centralities (degree values)
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
        
        return network_centralization
