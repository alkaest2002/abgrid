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
        a: Positive relevance nodes from network A.
        b: Negative relevance nodes from network B.
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
    """Pydantic model for SNA dictionary containing network analysis results."""
    nodes_a: list[str]
    nodes_b: list[str]
    edges_a: list[tuple[str, str]]
    edges_b: list[tuple[str, str]]
    adjacency_a: pd.DataFrame
    adjacency_b: pd.DataFrame
    network_a: nx.DiGraph  # type: ignore[type-arg]
    network_b: nx.DiGraph  # type: ignore[type-arg]
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
    graph_a: str
    graph_b: str
    rankings_ab: dict[str, pd.DataFrame]
    relevant_nodes: dict[str, pd.DataFrame]

    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "forbid"
    }


class ABGridSociogramSchema(BaseModel):
    """Pydantic model for storing sociogram analysis results."""
    macro_stats: pd.Series
    micro_stats: pd.DataFrame
    descriptives: pd.DataFrame
    rankings: dict[str, pd.Series]
    graph_ii: str
    graph_ai: str
    relevant_nodes: dict[str, pd.DataFrame]

    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "forbid"
    }
