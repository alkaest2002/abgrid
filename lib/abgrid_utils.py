"""
Filename: abgrid_utils.py
Description: Implements a decorator to print notifications for function execution and utility functions for AB-Grid project.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import io
import datetime
import pandas as pd
import numpy as np
import json

from pathlib import Path
from functools import wraps
from base64 import b64encode
from matplotlib import pyplot as plt
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Union
from lib import EVENT_ERROR

def handle_errors_decorator(dispatcher) -> Callable:
    def decorator(function: Callable) -> Callable:
        """
        Decorator that wraps a function with notification capabilities.
        
        Args:
            function (Callable): The function to be decorated.
            
        Returns:
            Callable: The wrapped function with notification capabilities.
        """
        @wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            Wrapper function executed in place of the original function.
            It adds error handling with event emission capabilities.
            
            Args:
                *args (Any): Positional arguments to pass to the original function.
                **kwargs (Any): Keyword arguments to pass to the original function.
                
            Returns:
                Any: The result of the original function execution.
                
            Raises:
                Exception: Re-raises any exception that occurs during function execution
                after emitting error details and traceback information.
            """
            try:
                result = function(*args, **kwargs)
                return result
            except Exception as error:
                error_message = extract_traceback_info(error)
                dispatcher.dispatch(dict(
                    event_type=EVENT_ERROR, 
                    event_message=error_message,
                    exception_type=type(error).__name__,
                    exception_str=str(error)
                ))
                raise
        return wrapper
    return decorator

def extract_traceback_info(error: Exception, exclude_files: Optional[Set[str]] = None) -> List[Dict[str, Any]]:
    """
    Extract relevant traceback information from an exception.
    
    Args:
        error: Exception object with traceback
        exclude_files: Set of filenames to exclude from traceback
        
    Returns:
        List of dictionaries containing filename, function name, and line number
    """
    if exclude_files is None:
        exclude_files = {"abgrid_utils.py", "abgrid_logger.py"}
    
    traceback_info = []
    current_traceback = error.__traceback__
    
    while current_traceback is not None:
        frame = current_traceback.tb_frame
        filename = Path(frame.f_code.co_filename).name
        
        if filename not in exclude_files:
            traceback_info.append({
                'filename': filename,
                'function_name': frame.f_code.co_name,
                'line_number': current_traceback.tb_lineno
            })
        
        current_traceback = current_traceback.tb_next
    
    return traceback_info

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

def figure_to_base64_svg(fig: plt.Figure) -> str:
    """
    Convert a matplotlib figure to a base64-encoded SVG data URI.

    Args:
        fig (plt.Figure): The matplotlib figure to convert.

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
    
    return f"data:image/svg+xml;base64,{base64_encoded_string}"

def compute_descriptives(data) -> pd.DataFrame:
    """
    Compute descriptive statistics for a given DataFrame.

    The function calculates standard descriptive statistics such as mean, std, min, max, quartiles,
    along with additional metrics like the median, coefficient of variation (CV), skewness (sk), 
    and kurtosis (kt) and GINI (gn).

    Args:
        data (pd.DataFrame): The input DataFrame for which descriptive statistics are to be computed.

    Returns:
        pd.DataFrame: A DataFrame containing the computed descriptive statistics, with columns for each statistic.
    """

    # Compute descriptive statistics with pandas descrive
    descriptives = data.describe().T

    # Add other statistics
    descriptives = (descriptives
            .rename(columns={ "50%": "median" })
            .assign(
                cv=descriptives["std"].div(descriptives["mean"]),
                sk=data.skew(),
                kt=data.kurt(),
                gn=data.apply(gini_coefficient)
            )
            # Reorder statistics
            .loc[:, ["count", "min", "max", "median", "mean", "std", "cv", "gn", "sk", "kt", "25%", "75%" ]]
    )
    
    return descriptives

def gini_coefficient(values: Union[Sequence[float], np.ndarray]) -> float:
    """
    The Gini coefficient is a measure of statistical dispersion originally developed 
    to represent income or wealth distribution, but widely applicable to any measure 
    of inequality. It quantifies how unequally distributed values are within a dataset.
    
    This implementation automatically shifts negative values to ensure non-negative 
    input (by subtracting the minimum value), preserving relative differences and 
    inequality structure while enabling proper Gini calculation.

    Parameters:
    values (Union[Sequence[float], np.ndarray]): A 1-dimensional sequence (such as a 
    list, tuple, or numpy array) containing the values for which the Gini 
    coefficient is to be calculated. Values can be negative; they will be 
    automatically shifted to non-negative while preserving relative inequality.

    Returns:
    float: The Gini coefficient, a value between 0 and 1 where:
        - 0 indicates perfect equality (all values identical)
        - 1 indicates maximal inequality (one value holds everything, others have nothing)
        - Values closer to 0 suggest more equal distribution
        - Values closer to 1 suggest more concentrated/unequal distribution

    Raises:
    ValueError: If the input is not a 1-dimensional sequence.

    Example:
    # Sociometric status scores (can include negative values)
    status_scores = [-2.1, -0.5, 0.8, 1.2, 3.4]
    gini = gini_coefficient(status_scores)
    print(f"Status inequality: {gini:.3f}")  # Output: 0.382
    
    # Perfect equality
    equal_values = [5, 5, 5, 5, 5]
    print(f"Equal distribution: {gini_coefficient(equal_values)}")  # Output: 0.0
    """
    # Convert to numpu array (make sure values are positive)
    values = np.array(values, dtype=np.float64) - np.min(values)
    
    # Sort the values
    sorted_values = np.sort(values)
    n = len(sorted_values)
    
    # Calculate mean
    mean_value = np.mean(sorted_values)
    
    # If all values are zero or mean is zero, return 0
    if mean_value == 0:
        return 0.0
    
    # Calculate Gini coefficient using the correct formula
    # G = (2 * sum(i * x_i)) / (n * sum(x_i)) - (n + 1) / n
    index_weighted_sum = np.sum((np.arange(1, n + 1) * sorted_values))
    total_sum = np.sum(sorted_values)
    gini = (2.0 * index_weighted_sum) / (n * total_sum) - (n + 1) / n
    
    return gini
