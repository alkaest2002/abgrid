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
    keys_to_omit: Optional[List[str]] = None,
    keys_regex_to_omit: Optional[Union[List[str], List[Pattern[str]]]] = None,
    max_depth: int = 3
) -> Any:
    """
    Converts data into a JSON-serializable format, supporting nested objects and
    omitting specified keys or exceeding a certain depth in the object hierarchy.

    The function works in two phases:
    1. First converts all data to JSON-serializable format
    2. Then prunes unwanted keys based on the omit patterns
    
    Args:
        data (Any): The input data to be serialized, which can be of any type.
        keys_to_omit (Optional[List[str]]): List of exact key paths to omit from serialization.
            Each key should be given as a string representing the complete path in dot notation (e.g., "user.password").
        keys_regex_to_omit (Optional[Union[List[str], List[Pattern[str]]]]): List of regex patterns to match key paths for omission.
        max_depth (int): The maximum depth to which the object hierarchy should be
            serialized. This helps prevent issues with circular references.
    
    Returns:
        Any: A JSON-serializable version of the input data with specified keys omitted.
    
    Example Usage:
        to_json_serializable(data, keys_to_omit=["user.password"], keys_regex_to_omit=[r'.*secret.*'])
    """
    keys_to_omit = keys_to_omit or []
    keys_regex_to_omit = keys_regex_to_omit or []
    
    def _convert_to_serializable(obj: Any, depth: int = 0) -> Any:
        """First phase: Convert all data to JSON-serializable format."""
        
        # Limit conversion to max depth
        if depth > max_depth:
            return obj
        
        # Perform conversions
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict("index")
        elif isinstance(obj, pd.Series):
            return obj.to_dict()
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
    
    def _should_omit_key(path_str: str) -> bool:
        """Check if a key path should be omitted based on exact matches or regex patterns."""
        if path_str in keys_to_omit:
            return True
        
        for regex_pattern in keys_regex_to_omit:
            if re.search(regex_pattern, path_str):
                return True
        
        return False
    
    def _prune_keys(obj: Any, path: Optional[List[str]] = None) -> Any:
        """Second phase: Remove unwanted keys from the serialized data."""
        path = path or []
        
        if isinstance(obj, dict):
            result = {}
            for k, v in obj.items():
                current_path = path + [str(k)]
                path_str = ".".join(current_path)
                
                if not _should_omit_key(path_str):
                    result[k] = _prune_keys(v, current_path)
            return result
        elif isinstance(obj, list):
            return [_prune_keys(item, path + [f"[{i}]"]) for i, item in enumerate(obj)]
        else:
            return obj
    
    serialized_data = _convert_to_serializable(data)
    pruned_data = _prune_keys(serialized_data)
    
    return pruned_data


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
    # Convert to numpu array
    values = np.abs(np.array(values, dtype=np.float64))
    
    # Sort the values
    sorted_values = np.sort(values)
    n = len(sorted_values)
    
    # Handle edge cases
    if n == 0:
        return 0.0
    
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
