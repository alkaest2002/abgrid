"""
Filename: abgrid_utils.py
Description: Implements a decorator to print notifications for function execution and utility functions for AB-Grid project.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import io
import datetime
import re
import pandas as pd
import numpy as np
import json

from base64 import b64encode
from pathlib import Path
from typing import Callable, Any, List, Optional, Sequence, Union, Pattern
from functools import wraps

from matplotlib import pyplot as plt

def notify_decorator(operation_name: str) -> Callable:
    """
    Decorator factory that creates a decorator to add notification capabilities to functions.
    
    Args:
        operation_name (str): Name of the operation to be displayed in notifications.
        
    Returns:
        Callable: A decorator function that wraps the target function with notifications.
    """
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
            It adds print notifications before and after function execution.
            
            Args:
                *args (Any): Positional arguments to pass to the original function.
                **kwargs (Any): Keyword arguments to pass to the original function.
                
            Returns:
                Any: The result of the original function execution.
                
            Raises:
                Exception: Re-raises any exception that occurs during function execution
                after printing error details and traceback information.
            """
            print(f"Operation '{operation_name}' is being currently executed.")
            
            try:
                result = function(*args, **kwargs)
                print(f"Operation '{operation_name}' was successfully executed.")
                return result
            except Exception as error:
                print(f"Error while executing operation '{operation_name}'.\n{error}")
                
                # Retrieve the traceback object from the exception
                traceback = error.__traceback__
                while traceback is not None:
                    if Path(traceback.tb_frame.f_code.co_filename).name != "abgrid_utils.py":
                        print(
                            "-->",
                            Path(traceback.tb_frame.f_code.co_filename).name,
                            traceback.tb_frame.f_code.co_name,
                            "line code",
                            traceback.tb_lineno,
                            end="\n"
                        )
                    traceback = traceback.tb_next
                
                raise
        
        return wrapper
    
    return decorator

def to_json_serializable(
    data: Any,
    keep: Optional[List[str]] = None,
    max_depth: int = 7
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


def get_robust_threshold(n: float) -> float:
    """
    Calculate a robust threshold used for median/mad computations.

    This threshold ensures a minimum level of robustness for statistical
    calculations based on the number of data points provided.

    Args:
        n (float): The number of data points, typically representing the size of a dataset.

    Returns:
        float: A robust threshold value calculated based on the input size 'n'.
               The result is set to a minimum of 0.6745 or adjusted according to
               the formula (1.5 - (n / 50)), whichever is larger.
    """
    # Define robust threshold for median/mad computations
    return max(0.6745, 1.5 - (n / 50))

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
    
    return (
        descriptives
            .rename(columns={ "50%": "median" })
            .assign(
                cv=descriptives["std"].div(descriptives["mean"]),
                sk=data.skew(),
                kt=data.kurt(),
                gn=data.apply(gini_coefficient)
            )
            .loc[:, ["count", "min", "max", "median", "mean", "std", "cv", "gn", "sk", "kt", "25%", "75%" ]]
            .apply(pd.to_numeric, downcast="integer")
    )

def gini_coefficient(values: Union[Sequence[float], np.ndarray]) -> float:
    """
    Calculate the Gini coefficient of a 1-dimensional sequence of values.

    The Gini coefficient is a measure of statistical dispersion intended to represent 
    the income or wealth distribution of a nation's residents. It is the most 
    commonly used measure of inequality.

    Parameters:
    values (Union[Sequence[float], np.ndarray]): A 1-dimensional sequence (such as a 
    list, tuple, or numpy array) which contains the values for which the Gini 
    coefficient is to be calculated.

    Returns:
    float: The Gini coefficient, a value between 0 and 1 where 0 indicates 
    perfect equality and 1 indicates maximal inequality.

    Raises:
    ValueError: If the input is not a 1-dimensional sequence.

    Example:
    gini = gini_coefficient([40000, 50000, 60000, 75000, 80000, 180000])
    print(gini)  # Output: Gini coefficient as a float
    """
    # Convert to numpu array (make sure values are positive)
    values = np.abs(np.array(values, dtype=np.float64))
    
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
