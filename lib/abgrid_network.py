"""
Filename: abgrid_network.py
Description: Provides functionality to analyze directed networks (graphs) for a given set of edges.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import networkx as nx

from typing import List, Dict
from lib.abgrid_sna import ABGridSna
from lib.abgrid_sociogram import ABGridSociogram

class ABGridNetwork:
    """
    A class to represent and analyze directed networks (graphs) given a set of edges.
    
    This class provides methods to compute social network analysis data and optionally
    sociogram analysis for two networks defined by sets of edges.
    """

    def __init__(self):
        """
        Initialize the ABGridNetwork object.

        Initializes data structures to store network analysis results, including
        separate storage for social network analysis (SNA) and sociograms.
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
            "graph_ic": None,
            "graph_ac": None,
            "supplemental": None
        }

    def compute(self, 
        packed_edges_a: List[Dict[str, str]], 
        packed_edges_b: List[Dict[str, str]], 
        with_sociogram: bool = False
    ):
        """
        Compute and store graphs, statistics, and visualization layouts for network A and B.

        This method processes given edge lists to perform social network analysis.
        If requested, it also computes sociogram analysis for these networks.

        Args:
            packed_edges_a (List[Dict[str, str]]): 
                A list of dictionaries, each representing an edge for network A.
                Each dictionary should have keys that define source and target nodes.
            packed_edges_b (List[Dict[str, str]]): 
                A list of dictionaries, each representing an edge for network B.
                Similar structure to `packed_edges_a`.
            with_sociogram (bool, optional): 
                Boolean flag indicating whether to compute sociograms. Defaults to False.

        Side Effects:
            - Updates the `self.sna` attribute with analysis results for both networks.
            - Updates the `self.sociogram` attribute with sociogram results if `with_sociogram` is True.
        """

        # Init sna class
        abgrid_sna = ABGridSna()

        # Compute sna data
        self.sna = abgrid_sna.compute_sna(packed_edges_a, packed_edges_b)
        
        # if Sociogram is requested
        if with_sociogram:
            
            # Init sociogram class
            abgrid_sociogram = ABGridSociogram()

            # Compute sociogram data
            self.sociogram = abgrid_sociogram.compute_sociogram( self.sna)

       
