"""
Filename: abgrid_utils.py
Description: Implements a decorator to print notifications for function execution and utility functions for AB-Grid project.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import datetime
import sys
import pandas as pd
import numpy as np
import json

from typing import Any, List, Optional

def check_python_version():
    """Check if Python version meets minimum requirements."""
    required_version = (3, 10)
    current_version = sys.version_info[:2]
    
    if current_version < required_version:
        print("=" * 60)
        print("PYTHON VERSION ERROR")
        print("=" * 60)
        print(f"This application requires Python {required_version[0]}.{required_version[1]} or higher.")
        print(f"You are currently using Python {current_version[0]}.{current_version[1]}")
        print()
        print("Please upgrade your Python installation:")
        print("- Visit https://www.python.org/downloads/")
        print("- Or use your system's package manager")
        print("- Or use pyenv/conda to install a newer version")
        print("=" * 60)
        sys.exit(1)

def to_json_serializable(
    data: Any,
    keep: Optional[List[str]] = None,
    max_depth: int = 4
) -> Any:
    """
    Converts data into a JSON-serializable format by first filtering to keep only
    specified key paths and their ancestors, then transforming values to JSON-compatible types.

    The function works in two phases:
    1. First prunes the data to keep only specified paths and their ancestors
    2. Then converts all remaining data to JSON-serializable format
    
    Args:
        data (Any): The input data to be serialized, which can be of any type.
        keep (Optional[List[str]]): List of key paths to keep during serialization.
            Each path should be given as a string using dot notation (e.g., "sociogram.descriptives").
            Use "ancestor.*" to keep all children of ancestor (e.g., "sna.*" keeps all children of sna).
            All ancestor paths are automatically kept (e.g., keeping "a.b.c" also keeps "a" and "a.b").
            If None or empty, all keys are kept (no filtering).
        max_depth (int): The maximum depth to which the object hierarchy should be
            serialized. This helps prevent issues with circular references.
    
    Returns:
        Any: A JSON-serializable version of the input data with only specified paths and their ancestors kept.
    
    Note:
        - Ancestor paths are automatically included (keeping "a.b.c" also keeps "a" and "a.b")
        - Use "path.*" wildcard to keep all children of a path
        - If keep is None/empty, all keys are preserved
        - Key paths use dot notation for nested objects
        - Array indices are not currently supported in path notation
    
    Example Usage:
        to_json_serializable(data, keep=["sociogram.descriptives"])  # Exact path only
        to_json_serializable(data, keep=["sna.*"])  # All children of sna
        to_json_serializable(data, keep=["user.profile.name", "settings.*"])  # Mixed exact and wildcard
    """
    keep = keep or []
    
    def _get_all_ancestor_paths(paths: List[str]) -> tuple[set[str], set[str]]:
        """Generate all ancestor paths and identify wildcard prefixes."""
        exact_paths = set()
        wildcard_prefixes = set()
        
        for path in paths:
            if path.endswith('.*'):
                # This is a wildcard path
                prefix = path[:-2]  # Remove '.*'
                wildcard_prefixes.add(prefix)
                
                # Add ancestors of the wildcard prefix
                parts = prefix.split('.')
                for i in range(1, len(parts) + 1):
                    ancestor_path = '.'.join(parts[:i])
                    exact_paths.add(ancestor_path)
            else:
                # This is an exact path
                exact_paths.add(path)
                
                # Add all ancestor paths
                parts = path.split('.')
                for i in range(1, len(parts)):
                    ancestor_path = '.'.join(parts[:i])
                    exact_paths.add(ancestor_path)
        
        return exact_paths, wildcard_prefixes
    
    def _should_keep_key(path_str: str, exact_paths: set[str], wildcard_prefixes: set[str]) -> bool:
        """Check if a key path should be kept based on exact paths and wildcard prefixes."""
        # If no filters are specified, keep all keys
        if not keep:
            return True
        
        # Check if this exact path is in the allowed set
        if path_str in exact_paths:
            return True
        
        # Check if this path is a child of any wildcard prefix
        for prefix in wildcard_prefixes:
            if path_str.startswith(prefix + "."):
                return True
        
        return False
    
    def _prune_keys(obj: Any, path: Optional[List[str]] = None, exact_paths: Optional[set[str]] = None, wildcard_prefixes: Optional[set[str]] = None) -> Any:
        """First phase: Keep only specified paths and their ancestors."""
        path = path or []
        exact_paths = exact_paths or set()
        wildcard_prefixes = wildcard_prefixes or set()
        
        if isinstance(obj, dict):
            result = {}
            for k, v in obj.items():
                current_path = path + [str(k)]
                path_str = ".".join(current_path)
                
                if _should_keep_key(path_str, exact_paths, wildcard_prefixes):
                    result[k] = _prune_keys(v, current_path, exact_paths, wildcard_prefixes)
            return result
        elif isinstance(obj, list):
            # For lists, we keep all items but continue pruning within each item
            return [_prune_keys(item, path, exact_paths, wildcard_prefixes) for item in obj]
        else:
            return obj
    
    def _convert_to_serializable(obj: Any, depth: int = 0) -> Any:
        """Second phase: Convert all data to JSON-serializable format."""
        
        # Limit conversion to max depth
        if depth > max_depth:
            return obj
       
        # Perform conversions
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, pd.DataFrame):
            if obj.index.has_duplicates:
                return obj.reset_index(drop=False, names="index").to_dict("index")
            else:
                return obj.to_dict("index")
        elif isinstance(obj, pd.Series):
            return obj.to_dict()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif hasattr(obj, 'tolist') and hasattr(obj, 'dtype'):
            return obj.tolist()
        elif isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: _convert_to_serializable(v, depth + 1) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [_convert_to_serializable(item, depth + 1) for item in obj]
        elif hasattr(obj, '__dict__') and not isinstance(obj, type):
            return _convert_to_serializable(obj.__dict__, depth + 1)
        else:
            try:
                json.dumps(obj)
                return obj
            except (TypeError, ValueError):
                return str(obj)
    
    # Generate exact paths and wildcard prefixes
    exact_paths, wildcard_prefixes = _get_all_ancestor_paths(keep)
    
    # Phase 1: Prune to keep only specified paths and their ancestors
    pruned_data = _prune_keys(data, exact_paths=exact_paths, wildcard_prefixes=wildcard_prefixes)
    
    # Phase 2: Convert to JSON-serializable format
    serialized_data = _convert_to_serializable(pruned_data)
    return serialized_data
