"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import asyncio
import re
from typing import Any, Literal

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull

from lib.core import A_COLOR, B_COLOR, CM_TO_INCHES
from lib.core.core_schemas import ABGridSNASchema
from lib.core.core_utils import (
    compute_descriptives,
    figure_to_base64_svg,
    run_in_executor,
    unpack_network_edges,
    unpack_network_nodes,
)


class CoreSna:
    """
    A class for comprehensive social network analysis on directed graphs.

    Provides functionality to analyze two directed networks (A and B) simultaneously,
    computing various network metrics, statistics, and visualizations. Supports comparative
    analysis between the two networks, generating reports on network structure,
    centrality measures, and graph properties.

    Attributes:
        sna (SNADict): Dictionary containing all computed network analysis data for both networks.
    """

    def __init__(self,
            packed_edges_a: list[dict[str, str | None]],
            packed_edges_b: list[dict[str, str | None]]) -> None:
        """
        Initialize the social network analysis object.

        Sets up an internal dictionary for storing SNA data
        for both networks A and B, with all values initially set to None.

        Args:
            packed_edges_a: List of packed edges for group A
            packed_edges_b: List of packed edges for group B
        """
        # Store packed edges for later use
        self.packed_edges_a = packed_edges_a
        self.packed_edges_b = packed_edges_b

        # Initialize SNA dict with all possible keys
        self.sna: dict[str, Any] = {}

    def get(self) -> dict[str, Any]:
        """
        Synchronous wrapper for the async get_async method.

        Compute and store comprehensive network analysis for two directed networks.

        Returns:
            A dictionary containing all network analysis results including nodes, edges,
            adjacency matrices, statistics, rankings, components, and visualization data
            for both networks.
        """
        # Get data
        data = asyncio.run(self._get_async())

        # Validate data
        validated_data = ABGridSNASchema(**data)

        return validated_data.model_dump()

    def _get_sync(self) -> dict[str, Any] :
        """
        Synchronous wrapper for the async get_async method.

        Compute and store comprehensive network analysis for two directed networks.

        Returns:
            A dictionary containing all network analysis results including nodes, edges,
            adjacency matrices, statistics, rankings, components, and visualization data
            for both networks.
        """
        self._create_networks()

        # Store edge types, components, macro stats, micro stats, descriptives, rankings and graphs
        for network_type in ("a", "b"):
            self.sna[f"edges_types_{network_type}"] = self._compute_edges_types(network_type)
            self.sna[f"components_{network_type}"] = self._compute_components(network_type)
            self.sna[f"macro_stats_{network_type}"] = self._compute_macro_stats(network_type)
            self.sna[f"micro_stats_{network_type}"] = self._compute_micro_stats(network_type)
            self.sna[f"descriptives_{network_type}"] = self._compute_descriptives(network_type)
            self.sna[f"rankings_{network_type}"] = self._compute_rankings(network_type)
            self.sna[f"graph_{network_type}"] = self._create_graph(network_type)

        # Store rankings comparison between networks
        self.sna["rankings_ab"] = self._compute_rankings_ab()

        # Store relevant nodes analysis
        self.sna["relevant_nodes"] = self._compute_relevant_nodes()

        return self.sna


    async def _get_async(self) -> dict[str, Any]:
        """
        Asynchronously compute and store comprehensive network analysis for two directed networks.

        Performs a complete social network analysis on input networks using concurrent execution
        where possible, including graph construction, statistical analysis, centrality measures,
        component detection, and visualization generation.

        Returns:
            A dictionary containing all network analysis results including nodes, edges,
            adjacency matrices, statistics, rankings, components, and visualization data
            for both networks.
        """
        # STEP 1: Create networks (must happen first)
        await run_in_executor(self._create_networks)

        # STEP 2: Concurrent computation using TaskGroups

        # Batch 1: Independent computations that only depend on Step 1
        async with asyncio.TaskGroup() as tg:
            # Store tasks with their result keys for later retrieval
            tasks = {}
            for network_type in ("a", "b"):
                tasks[f"edges_types_{network_type}"] = tg.create_task(
                    run_in_executor(self._compute_edges_types, network_type)
                )
                tasks[f"components_{network_type}"] = tg.create_task(
                    run_in_executor(self._compute_components, network_type)
                )
                tasks[f"graph_{network_type}"] = tg.create_task(
                    run_in_executor(self._create_graph, network_type)
                )

        # Store batch 1 results
        for key, task in tasks.items():
            self.sna[key] = task.result()

        # Batch 2: Computations that depend on edges_types
        async with asyncio.TaskGroup() as tg:
            tasks = {}
            for network_type in ("a", "b"):
                tasks[f"macro_stats_{network_type}"] = tg.create_task(
                    run_in_executor(self._compute_macro_stats, network_type)
                )
                tasks[f"micro_stats_{network_type}"] = tg.create_task(
                    run_in_executor(self._compute_micro_stats, network_type)
                )

        # Store batch 2 results
        for key, task in tasks.items():
            self.sna[key] = task.result()

        # Batch 3: Computations that depend on micro_stats
        async with asyncio.TaskGroup() as tg:
            tasks = {}
            for network_type in ("a", "b"):
                tasks[f"descriptives_{network_type}"] = tg.create_task(
                    run_in_executor(self._compute_descriptives, network_type)
                )
                tasks[f"rankings_{network_type}"] = tg.create_task(
                    run_in_executor(self._compute_rankings, network_type)
                )

        # Store batch 3 results
        for key, task in tasks.items():
            self.sna[key] = task.result()

        # Final batch: Cross-network comparisons
        async with asyncio.TaskGroup() as tg:
            rankings_ab_task = tg.create_task(
                run_in_executor(self._compute_rankings_ab)
            )
            relevant_nodes_task = tg.create_task(
                run_in_executor(self._compute_relevant_nodes)
            )

        self.sna["rankings_ab"] = rankings_ab_task.result()
        self.sna["relevant_nodes"] = relevant_nodes_task.result()

        return self.sna

    def _create_networks(self) -> None:
        """
        Synchronously create networks with nodes, edges, and adjacency lists.

        This performs the actual work of network creation.

        """
        # Set network data
        network_edges: list[tuple[Literal["a", "b"], Any]] = [
            ("a", self.packed_edges_a),
            ("b", self.packed_edges_b)
        ]

        # Store network A and B nodes and edges
        for network_type, packed_edges in network_edges:
            self.sna[f"nodes_{network_type}"] = unpack_network_nodes(packed_edges)
            self.sna[f"edges_{network_type}"] = unpack_network_edges(packed_edges)
            self.sna[f"network_{network_type}"] = nx.DiGraph(self.sna[f"edges_{network_type}"])

        # Add isolated nodes to networks A and B, and store nodes layout locations
        network_data: list[tuple[Literal["a", "b"], Any, Any]] = [
            ("a", self.sna["network_a"], self.sna["nodes_a"]),
            ("b", self.sna["network_b"], self.sna["nodes_b"])
        ]

        for network_type, network, nodes in network_data:
            # Find isolated nodes
            isolated_nodes: set[str] = set(network).symmetric_difference(set(nodes))

            # Add isolated nodes to current network
            network.add_nodes_from(isolated_nodes)

            # Generate layout locations (loc) for current network
            loc: dict[str, np.ndarray] = nx.kamada_kawai_layout(network)

            # Update loc to push isolated nodes away from other nodes
            updated_loc: dict[str, np.ndarray] = self._handle_isolated_nodes(network, loc)

            # Store current network layout locations
            self.sna[f"loc_{network_type}"] = updated_loc

            # Store current network adjacency matrix
            self.sna[f"adjacency_{network_type}"] = nx.to_pandas_adjacency(network, nodelist=nodes)

    def _compute_macro_stats(self, network_type: Literal["a", "b"]) -> pd.Series:
        """
        Calculate macro-level network statistics.

        Computes network-wide metrics including structural properties, centralization,
        and relationship patterns for the specified network.

        Args:
            network_type: Network identifier ('a' or 'b') for selecting the target network.

        Returns:
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
            error_message = f"Network data for type '{network_type}' is not available."
            raise ValueError(error_message)

        if self.sna[f"edges_types_{network_type}"] is None:
            error_message = f"Edge types data for network '{network_type}' is not available."
            raise ValueError(error_message)

        # Get network
        network: nx.DiGraph = self.sna[f"network_{network_type}"] # type: ignore[type-arg]

        # Get network edges types
        edges_types: dict[str, pd.Index] = self.sna[f"edges_types_{network_type}"]

        # Compute macro-level statistics
        network_nodes: int = network.number_of_nodes()
        network_edges: int = network.number_of_edges()
        network_edges_reciprocal: int = edges_types["type_ii"].shape[0]
        network_density: float = nx.density(network) # type: ignore[no-untyped-call]
        network_centralization: float = self._compute_network_centralization(network.to_undirected())
        network_transitivity: float = nx.transitivity(network)
        network_reciprocity: float = nx.overall_reciprocity(network)

        return pd.Series({
            "network_nodes": network_nodes,
            "network_edges": network_edges,
            "network_edges_reciprocal": network_edges_reciprocal,
            "network_density": network_density,
            "network_centralization": network_centralization,
            "network_transitivity": network_transitivity,
            "network_reciprocity": network_reciprocity,
        })

    def _compute_micro_stats(self, network_type: Literal["a", "b"]) -> pd.DataFrame:
        """
        Calculate node-level (micro) statistics for the specified network.

        Computes various centrality measures and node properties for each node
        in the network, including degree-based and path-based centralities.

        Args:
            network_type: Network identifier ('a' or 'b') for selecting the target network.

        Returns:
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
            error_message = f"Network data for type '{network_type}' is not available."
            raise ValueError(error_message)

        if self.sna[f"adjacency_{network_type}"] is None:
            error_message = f"Adjacency matrix for network '{network_type}' is not available."
            raise ValueError(error_message)

        # Get network and adjacency
        network = self.sna[f"network_{network_type}"]
        adjacency: pd.DataFrame = self.sna[f"adjacency_{network_type}"]

        # Create a DataFrame with micro-level statistics
        micro_level_stats: pd.DataFrame = pd.concat([
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

        # Ensure that isolated nodes have no centrality metric data
        numeric_metrics_colums: list[str] = [c for c in micro_level_stats.select_dtypes("number").columns if c != "nd"]
        micro_level_stats.loc[micro_level_stats["nd"].eq(3), numeric_metrics_colums] = 0

        # Compute node ranks relative to each network centrality metric
        micro_level_stats_ranks: pd.DataFrame = (
            micro_level_stats.iloc[:, 1:-1]  # omit first column (LNS) and last column (ND)
                .rank(method="dense", ascending=False)
                .add_suffix("_rank")
        )

        # Combine metrics and metrics ranks and return
        return (
            pd.concat(
                [
                    micro_level_stats,
                    micro_level_stats_ranks,
                ], axis=1)
                .sort_index()
        )

    def _compute_descriptives(self, network_type: Literal["a", "b"]) -> pd.DataFrame:
        """
        Compute descriptive statistics for centrality measures.

        Generates summary statistics (mean, std, min, max, etc.) for the main
        centrality measures of the specified network.

        Args:
            network_type: Network identifier ('a' or 'b') for selecting the target network.

        Returns:
            DataFrame with descriptive statistics for centrality measures.
            Columns correspond to centrality measures (ic, pr, kz, bt, cl, hu).
            Rows contain statistical summaries (count, mean, std, min, max, etc.).

        Raises:
            ValueError: If required micro statistics data is not available.
        """
        # Check if required data is available
        if self.sna[f"micro_stats_{network_type}"] is None:
            error_message = f"Micro statistics for network '{network_type}' are not available."
            raise ValueError(error_message)

        # Select columns to retain for descriptive statistics
        columns_to_retain: list[str] = ["ic", "pr", "kz", "bt", "cl", "hu"]

        # Select numeric columns only
        sna_numeric_columns: pd.DataFrame = self.sna[f"micro_stats_{network_type}"].loc[:, columns_to_retain]

        return compute_descriptives(sna_numeric_columns)

    def _compute_rankings(self, network_type: Literal["a", "b"]) -> dict[str, pd.Series]:
        """
        Generate node rankings based on centrality measures.

        Creates ordered rankings of nodes for each centrality metric, where
        nodes are sorted by their rank scores in ascending order.

        Args:
            network_type: Network identifier ('a' or 'b') for selecting the target network.

        Returns:
            Dictionary mapping centrality metric names (with '_rank' suffix) to
            pandas Series containing nodes ordered by their rank (best to worst).
            Each Series is indexed by node identifiers and contains rank values.

        Raises:
            ValueError: If required micro statistics data is not available.
        """
        # Check if required data is available
        if self.sna[f"micro_stats_{network_type}"] is None:
            error_message = f"Micro statistics for network '{network_type}' are not available."
            raise ValueError(error_message)

        # Get the micro stats DataFrame for the specified network type
        micro_stats_df: pd.DataFrame = self.sna[f"micro_stats_{network_type}"]

        # Filter columns that end with '_rank' to get ranking data
        rank_columns: pd.DataFrame = micro_stats_df.filter(regex=r"_rank$")

        # Convert to dictionary with metric names as keys and Series as values
        rankings: dict[str, pd.Series] = {}
        for metric_name in rank_columns.columns:
            rankings[metric_name] = rank_columns[metric_name].sort_values()

        return rankings

    def _compute_rankings_ab(self) -> dict[str, pd.DataFrame]:
        """
        Compute combined rankings from both networks A and B.

        Merges the rankings from both networks into side-by-side DataFrames
        for easy comparison of node rankings across the two networks.

        Returns:
            Dictionary where each key corresponds to a ranking metric (e.g., 'ic_rank', 'pr_rank'),
            and the value is a DataFrame with two columns:
            - Column ending with '_a': Rankings from network A
            - Column ending with '_b': Rankings from network B

        Raises:
            ValueError: If the rankings for network 'a' or 'b' are not available.
        """
        # Check if required data is available
        if self.sna["rankings_a"] is None or self.sna["rankings_b"] is None:
            error_message = "Rankings for network a and b are not available."
            raise ValueError(error_message)

        # Get the rankings from network A and B
        rankings_a: dict[str, pd.Series] = self.sna["rankings_a"]
        rankings_b: dict[str, pd.Series] = self.sna["rankings_b"]

        # Combine them into side-by-side DataFrames
        rankings_ab: dict[str, pd.DataFrame] = {}
        for metric, series_a in rankings_a.items():
            series_a_copy = series_a.copy()
            series_b_copy = rankings_b[metric].copy()
            series_a_copy.name = str(series_a_copy.name) + "_a"
            series_b_copy.name = str(series_b_copy.name) + "_b"
            rankings_ab[metric] = pd.concat([series_a_copy, series_b_copy], axis=1)

        return rankings_ab

    def _compute_relevant_nodes(self, threshold: float = 0.05) -> dict[str, pd.DataFrame]:
        """
        Finds nodes that rank highly (indicated by low rank values) for both network A and network B.

        Args:
            threshold: Percentile threshold for selecting top nodes (default: 0.05 for top 5%)

        Returns:
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
        if self.sna["rankings_a"] is None or self.sna["rankings_b"] is None\
                or self.sna["micro_stats_a"] is None or self.sna["micro_stats_b"] is None:
            error_message = "SNA micro stats and rankings for both networks a and b are required."
            raise ValueError(error_message)

        # Init dict with empty sub-dicts for storing relevant nodes
        relevant_nodes: dict[str, pd.DataFrame] = {"a": pd.DataFrame(), "b": pd.DataFrame()}

        # Process both positive (a) and negative (b) relevance directions
        for valence_type in ["a", "b"]:

            # Select micro_stats and rankings to use
            micro_stats: pd.DataFrame =  self.sna["micro_stats_a"] if valence_type == "a" else self.sna["micro_stats_b"]
            rankings: dict[str, pd.Series] = self.sna["rankings_a"] if valence_type == "a" else self.sna["rankings_b"]

            # Loop through metrics and associated ranks
            for metric_rank_name, ranks_series in rankings.items():

                # Clean metric name
                metric_name: str = re.sub("_rank", "", metric_rank_name)

                # Get threshold value for this metric
                threshold_value: float = ranks_series.quantile(threshold)

                # Filter top nodes (assuming lower rank = better)
                current_relevant_ranks: pd.Series = ranks_series[ranks_series.le(threshold_value)]

                # Compute relevant nodes data
                current_relevant_nodes: pd.DataFrame = (
                    current_relevant_ranks
                        .to_frame()
                        .assign(
                            metric=metric_name,
                            recomputed_rank=current_relevant_ranks.rank(method="dense", ascending=True),
                            value=micro_stats.loc[current_relevant_ranks.index, metric_name],
                            weight=lambda x: x["recomputed_rank"].pow(.8).rdiv(10),
                            evidence_type="sna"
                        )
                        .reset_index(drop=False, names="node_id")
                        .rename(columns={
                            metric_rank_name: "original_rank"
                        })
                )

                # Add relevant nodes to dataframe
                relevant_nodes[valence_type] = pd.concat([
                    relevant_nodes[valence_type],
                    current_relevant_nodes
                ], ignore_index=True)

        return relevant_nodes

    def _compute_edges_types(self, network_type: Literal["a", "b"]) -> Any:
        """
        Classify edges into five types based on reciprocity and cross-network relationships.

        Analyzes edge patterns within the specified network and compares them with
        the reference network to classify edges into five distinct types.

        Args:
            network_type: Network identifier ('a' or 'b') for selecting the target network.
                The other network serves as the reference for comparison.

        Returns:
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
            error_message = "Adjacency matrix for network 'a' is not available."
            raise ValueError(error_message)
        if self.sna["adjacency_b"] is None:
            error_message = "Adjacency matrix for network 'b' is not available."
            raise ValueError(error_message)

        # Get the adjacency DataFrames for the specified network type and reference
        if network_type == "a":
            adj_df: pd.DataFrame = self.sna["adjacency_a"]
            adj_ref_df: pd.DataFrame = self.sna["adjacency_b"]
        else:
            adj_df = self.sna["adjacency_b"]
            adj_ref_df = self.sna["adjacency_a"]

        # Define a function for filtering edges
        fn = lambda x: x == 1 # noqa: E731

        # Compute type I edges, non-reciprocal
        # i.e. same network: A -> B and not B -> A
        type_i_df: pd.DataFrame = adj_df - (adj_df * adj_df.T)
        type_i: pd.Index = type_i_df.stack().loc[fn].index

        # Compute type II edges, reciprocal
        # i.e. same network: A -> B and B -> A
        type_ii_df: pd.DataFrame = pd.DataFrame(np.triu(adj_df) * np.tril(adj_df).T, index=adj_df.index, columns=adj_df.columns)
        type_ii: pd.Index = type_ii_df.stack().loc[fn].index

        # Compute type V edges, fully symmetrical
        # i.e. A -> B, B -> A in network and A -> B, B -> A in reference network
        type_v_df: pd.DataFrame = type_ii_df * pd.DataFrame(np.triu(adj_ref_df) * np.tril(adj_ref_df).T, index=adj_df.index, columns=adj_df.columns)
        type_v: pd.Index = type_v_df.stack().loc[fn].index

        # Compute type III edges, half symmetrical
        # i.e. A -> B in network and A -> B in reference network
        type_iii_df: pd.DataFrame = pd.DataFrame(np.triu(adj_df) * np.triu(adj_ref_df), index=adj_df.index, columns=adj_df.columns)
        type_iii: pd.Index = type_iii_df.sub(type_v_df).stack().loc[fn].index

        # Compute type IV edges, half reversed symmetrical
        # i.e. A -> B in network and B -> A in reference network
        type_iv_df: pd.DataFrame = (
            pd.DataFrame(np.triu(adj_df) * np.tril(adj_ref_df).T, index=adj_df.index, columns=adj_df.columns)
            + pd.DataFrame(np.tril(adj_df) * np.triu(adj_ref_df).T, index=adj_df.index, columns=adj_df.columns)
        )
        type_iv: pd.Index = type_iv_df.sub(type_v_df).stack().loc[fn].index

        return {
            "type_i": type_i,
            "type_ii": type_ii,
            "type_iii": type_iii,
            "type_iv": type_iv,
            "type_v": type_v
        }

    def _compute_components(self, network_type: Literal["a", "b"]) -> dict[str, pd.Series]:
        """
        Identify and extract significant network components.

        Finds various types of network components (cliques, strongly connected components,
        weakly connected components) and returns them as concatenated node strings.
        Only components with more than 2 nodes are included.

        Args:
            network_type: Network identifier ('a' or 'b') for selecting the target network.

        Returns:
            Dictionary containing three types of components:
            - cliques: Maximal cliques in the undirected version of the graph
            - strongly_connected: Strongly connected components in the directed graph
            - weakly_connected: Weakly connected components in the directed graph

            Each Series contains components as concatenated strings of sorted node identifiers.
            Components are sorted by size (largest first).

        Raises:
            ValueError: If required network data is not available.
        """
        # Check if required data is available
        if self.sna[f"network_{network_type}"] is None:
            error_message = f"Network data for type '{network_type}' is not available."
            raise ValueError(error_message)

        # Set minimum size for components
        component_min_size: int = 3

        # Get network
        network = self.sna[f"network_{network_type}"]

        # Get cliques with min length of 3, ordered by size
        cliques: pd.Series = pd.Series(
            [ "".join(sorted(c)) for c in sorted(nx.find_cliques(network.to_undirected()), key=len, reverse=True) if len(c) >= component_min_size ])

        # Get strongly connected components with min length of 3, ordered by size
        strongly_connected: pd.Series = pd.Series(
            [ "".join(sorted(c)) for c in sorted(nx.strongly_connected_components(network), key=len, reverse=True) if len(c) >= component_min_size ])

        # Get weakly connected components with min length of 3, ordered by size
        weakly_connected: pd.Series =  pd.Series(
            [ "".join(sorted(c)) for c in sorted(nx.weakly_connected_components(network), key=len, reverse=True) if len(c) >= component_min_size ])

        # Exclude strongly connected components from weakly connected components
        weakly_connected = weakly_connected.loc[~weakly_connected.isin(strongly_connected)]

        # Cobine components
        components: dict[str, pd.Series] = {
            "cliques": cliques,
            "strongly_connected": strongly_connected,
            "weakly_connected": weakly_connected,
        }

        return components

    def _compute_network_centralization(self, network: nx.Graph) -> float:  # type: ignore[type-arg]
        """
        Calculate the degree centralization of an undirected network.

        Centralization measures how concentrated the network structure is around
        its most central node, comparing the actual network to a perfect star network.
        Values range from 0 (evenly distributed) to 1 (perfectly centralized).

        Args:
            network: Undirected graph for which to calculate centralization.
                Should typically be the undirected version of a directed graph.

        Returns:
            Network centralization value between 0 and 1, where:
            - 0 indicates an evenly distributed network (all nodes have equal degree)
            - 1 indicates a perfectly centralized network (star topology)
            - Higher values suggest more centralized structure

        Note:
            This implementation uses degree centrality as the basis for centralization.
            The network should have at least 3 nodes for meaningful centralization values.

        Raises:
            ZeroDivisionError: If the network has fewer than 3 nodes.
            nx.NetworkXError: If the network is empty or invalid.
        """
        # Get number of nodes
        number_of_nodes: int = network.number_of_nodes()

        # Compute node centralities (degree values)
        node_centralities: pd.Series = pd.Series(dict(nx.degree(network)))  # type: ignore[no-untyped-call]

        # Compute Max centrality
        max_centrality: int = node_centralities.max()

        # Compute network centralization
        network_centralization: float = (
            node_centralities
                .rsub(max_centrality)
                .sum()
                / ((number_of_nodes - 1) * (number_of_nodes - 2))
        )

        return network_centralization

    def _create_graph(self, network_type: Literal["a","b"]) -> str:
        """
        Generate an SVG visualization of the specified network.

        Creates a matplotlib-based network visualization with nodes, edges, and labels,
        then converts it to a base64-encoded SVG string for web display.

        Args:
            network_type: Network identifier ('a' or 'b') for selecting which network to visualize.

        Returns:
            Base64-encoded SVG data URI of the network visualization.
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
        network: nx.DiGraph = self.sna[f"network_{network_type}"] # type: ignore[type-arg]

        # Get network layout locations
        loc: dict[str, np.ndarray] = self.sna[f"loc_{network_type}"]

        # Set color based on graph type (a or b)
        color: str = A_COLOR if network_type == "a" else B_COLOR

        # Set dimensions of matplotlib graph
        fig_size: tuple[float, float] = (17 * CM_TO_INCHES, 19 * CM_TO_INCHES)

        # Create a matplotlib figure
        fig, ax = plt.subplots(constrained_layout=True, figsize=fig_size)

        # Hide axis
        ax.axis("off")

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
        reciprocal_edges: list[tuple[str, str]] = [e for e in network.edges if e[::-1] in network.edges]
        nx.draw_networkx_edges(
            network, loc, edgelist=reciprocal_edges,
            edge_color=color, arrowstyle="-", width=4, min_target_margin=0,
            ax=ax
        )

        # Draw non-reciprocal edges with specific style (directed arrows)
        non_reciprocal_edges: list[tuple[str, str]] = [e for e in network.edges if e not in reciprocal_edges]
        nx.draw_networkx_edges(
            network, loc, edgelist=non_reciprocal_edges,
            edge_color=color, arrowstyle="->", width=.4, min_target_margin=10,
            ax=ax
        )

        return figure_to_base64_svg(fig)

    def _handle_isolated_nodes(self, network: nx.DiGraph, loc: dict[str, np.ndarray]) -> dict[str, np.ndarray]: # type: ignore[type-arg]
        """
        Position isolated nodes at the periphery of the network layout.

        Adjusts the positions of isolated nodes to appear outside the convex hull
        of connected nodes, making them visually distinct and marginal in the layout.

        Args:
            network: The directed graph containing both connected and isolated nodes.
            loc: Dictionary mapping node identifiers to their 2D coordinate positions.

        Returns:
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
        isolates: list[str] = list(nx.isolates(network))

        # If there are no isolated nodes, just return original layout
        if not isolates:
            return loc

        # Convert current loc coordinates to dataframe
        coordinates: pd.DataFrame = pd.DataFrame(loc).T

        # Compute centroid of coordinates
        coordinates_centroid: np.ndarray = np.mean(coordinates, axis=0)

        # Compute convex hull around coordinates
        hull: ConvexHull = ConvexHull(coordinates)

        # Get hull vertices
        hull_vertices: np.ndarray = coordinates.iloc[hull.vertices].values

        # Create an iterator from isolated nodes list
        isolate_iter = iter(isolates)

        # Keep track of loop rounds
        round_num: int = 1

        # Loop until all isolated nodes are placed
        try:
            while True:

                # Loop through hull vertices in current round
                for vertex in hull_vertices:

                    # Get next isolated node
                    isolate: str = next(isolate_iter)

                    # Create direction vector from coordinates centroid to current hull vertex
                    direction: np.ndarray = (vertex - coordinates_centroid).to_numpy()
                    direction /= np.linalg.norm(direction)

                    # Set distance multiplier (increases with each round)
                    distance_multiplier: float = 0.15 * round_num

                    # Add some randomness to position
                    random_offset: np.ndarray = np.random.uniform(-0.05, 0.05, size=2)

                    # Compute final position
                    candidate_pos: np.ndarray = vertex + direction * distance_multiplier + random_offset

                    # Update isolated node position
                    loc[isolate] = candidate_pos

                # Move to next round, as hull vertices have been fully exploited
                # but other isolated nodes need to be placed
                round_num += 1

        # All isolated nodes have been placed
        except StopIteration:
            return loc
