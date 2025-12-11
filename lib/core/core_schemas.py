"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
import networkx as nx
import numpy as np
import pandas as pd
from pydantic import BaseModel


class ABGridRelevantNodesSchema(BaseModel):
    """Schema for relevant nodes analysis results.

    Attributes:
        a: Relevant nodes from network A.
        b: Relevant nodes from network B.
    """
    a: pd.DataFrame
    b: pd.DataFrame

    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "forbid"
    }


class ABGridIsolatedNodesSchema(BaseModel):
    """Schema for isolated nodes by network type.

    Attributes:
        a: Isolated nodes from network A.
        b: Isolated nodes from network B.
    """
    a: pd.Index
    b: pd.Index

    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "forbid"
    }


class ABGridSNASchema(BaseModel):
    """Pydantic model for SNA dictionary containing network analysis results.

    Attributes:
        nodes_a: List of node identifiers for network A.
        nodes_b: List of node identifiers for network B.
        edges_a: List of edge tuples for network A.
        edges_b: List of edge tuples for network B.
        adjacency_a: Adjacency matrix for network A.
        adjacency_b: Adjacency matrix for network B.
        network_a: NetworkX directed graph for network A.
        network_b: NetworkX directed graph for network B.
        loc_a: Node position coordinates for network A.
        loc_b: Node position coordinates for network B.
        macro_stats_a: Macro-level statistics for network A.
        macro_stats_b: Macro-level statistics for network B.
        micro_stats_a: Micro-level statistics for network A.
        micro_stats_b: Micro-level statistics for network B.
        descriptives_a: Descriptive statistics for network A.
        descriptives_b: Descriptive statistics for network B.
        rankings_a: Node rankings by various metrics for network A.
        rankings_b: Node rankings by various metrics for network B.
        edges_types_a: Edge type classifications for network A.
        edges_types_b: Edge type classifications for network B.
        components_a: Network component analysis for network A.
        components_b: Network component analysis for network B.
        isolated_nodes_a: Isolated nodes in network A.
        isolated_nodes_b: Isolated nodes in network B.
        relevant_nodes_a: Relevant nodes analysis for network A.
        relevant_nodes_b: Relevant nodes analysis for network B.
        graph_a: String representation of network A graph.
        graph_b: String representation of network B graph.
    """
    nodes_a: list[str]
    nodes_b: list[str]
    edges_a: list[tuple[str, str]]
    edges_b: list[tuple[str, str]]
    adjacency_a: pd.DataFrame
    adjacency_b: pd.DataFrame
    network_a: nx.DiGraph
    network_b: nx.DiGraph
    loc_a: dict[str, np.ndarray]
    loc_b: dict[str, np.ndarray]
    macro_stats_a: pd.Series
    macro_stats_b: pd.Series
    micro_stats_a: pd.DataFrame
    micro_stats_b: pd.DataFrame
    descriptives_a: pd.DataFrame
    descriptives_b: pd.DataFrame
    rankings_a: dict[str, pd.Series]
    rankings_b: dict[str, pd.Series]
    edges_types_a: dict[str, pd.Index]
    edges_types_b: dict[str, pd.Index]
    components_a: dict[str, pd.Series]
    components_b: dict[str, pd.Series]
    isolated_nodes_a: pd.Index
    isolated_nodes_b: pd.Index
    relevant_nodes_a: pd.DataFrame
    relevant_nodes_b: pd.DataFrame
    graph_a: str
    graph_b: str

    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "forbid"
    }


class ABGridSociogramSchema(BaseModel):
    """Pydantic model for storing sociogram analysis results.

    Attributes:
        macro_stats: Macro-level statistics for the sociogram.
        micro_stats: Micro-level statistics for the sociogram.
        descriptives: Descriptive statistics for the sociogram.
        rankings: Node rankings by various metrics.
        relevant_nodes: Dictionary containing relevant nodes analysis.
        graph_ii: String representation of the ii graph.
        graph_ai: String representation of the ai graph.
    """
    macro_stats: pd.Series
    micro_stats: pd.DataFrame
    descriptives: pd.DataFrame
    rankings: dict[str, pd.Series]
    relevant_nodes: dict[str, pd.DataFrame]
    graph_ii: str
    graph_ai: str

    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "forbid"
    }
