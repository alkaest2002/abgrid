"""
Author: Pierpaolo Calanna

Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import re
import sys
import datetime
import pandas as pd
import numpy as np
import networkx as nx
import json

from typing import Any, Dict, List, Union

from lib.core.core_data import ReportDataDict

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

def to_json(report_data: ReportDataDict) -> Dict[str, Any]:
    """
    Convert ReportDataDict to a JSON-serializable format.
    
    This function handles the specific data types commonly found in AB-Grid report data,
    including pandas DataFrames/Series, NetworkX graphs, numpy arrays, and nested dictionaries.
    
    Args:
        report_data: The report data dictionary to convert
        
    Returns:
        A JSON-serializable dictionary with the same structure as the input
        
    Note:
        - DataFrames are converted to dict format with index preservation
        - NetworkX graphs are converted to node/edge lists
        - Numpy arrays become Python lists
        - Datetime objects become ISO format strings
        - Complex objects are converted to string representation as fallback
    """
    
    def _convert_pandas_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
        """Convert pandas DataFrame to JSON-serializable format."""
        if df.empty:
            return {}
        
        # Fill missing values
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.fillna("-")
        
        # Handle DataFrames with duplicate indices by resetting index
        if df.index.has_duplicates:
            return df.reset_index(drop=False, names="index").to_dict("index")
        else:
            # Convert to dict with index as keys for better readability
            return df.to_dict("index")
    
    def _convert_pandas_series(series: pd.Series) -> Union[Dict[str, Any], List[Any]]:
        """Convert pandas Series to JSON-serializable format."""
        if series.empty:
            return {}
        
        # Fill missing values
        series = series.replace([np.inf, -np.inf], np.nan)
        series = series.fillna("-")
        
        # If series has a meaningful index, convert to dict
        if not isinstance(series.index, pd.RangeIndex):
            return series.to_dict()
        else:
            # For range index, convert to list
            return series.tolist()
    
    def _convert_networkx(graph: nx.DiGraph) -> Dict[str, Any]:
        """Convert NetworkX DiGraph to JSON-serializable format."""
        return {
            "nodes": list(graph.nodes()),
            "edges": list(graph.edges()),
            "number_of_nodes": graph.number_of_nodes(),
            "number_of_edges": graph.number_of_edges()
        }
    
    def _convert_numpy_array(arr: np.ndarray) -> List[Any]:
        """Convert numpy array to JSON-serializable list."""
        return _convert_pandas_series(pd.Series(arr))
    
    def _convert_datetime(dt: datetime.datetime) -> str:
        """Convert datetime to ISO format string."""
        return dt.isoformat()
    
    def _convert_value(value: Any) -> Any:
        """Convert individual values to JSON-serializable format."""
        if value is None:
            return None
        elif isinstance(value, (str, int, float, bool)):
            return value
        elif isinstance(value, pd.DataFrame):
            return _convert_pandas_dataframe(value)
        elif isinstance(value, pd.Series):
            return _convert_pandas_series(value)
        elif isinstance(value, pd.Index):
            return value.tolist()
        elif isinstance(value, nx.DiGraph):
            return _convert_networkx(value)
        elif isinstance(value, np.ndarray):
            return _convert_numpy_array(value)
        elif isinstance(value, (datetime.date, datetime.datetime)):
            return _convert_datetime(value)
        elif isinstance(value, dict):
            return {k: _convert_value(v) for k, v in value.items()}
        elif isinstance(value, (list, tuple)):
            return [_convert_value(item) for item in value]
        else:
            # Fallback: try to serialize directly, otherwise convert to string
            try:
                json.dumps(value)
                return value
            except (TypeError, ValueError):
                return str(value)
    
    # Convert the main report data structure
    json_data: Dict[str, Any] = {}
    
    # Handle basic metadata fields
    json_data["year"] = report_data["year"]
    json_data["project_title"] = report_data["project_title"]
    json_data["question_a"] = report_data["question_a"]
    json_data["question_b"] = report_data["question_b"]
    json_data["group"] = report_data["group"]
    json_data["members_per_group"] = report_data["members_per_group"]
    
    # Handle SNA data (complex nested structure)
    json_data["sna"] = _convert_value(report_data["sna"])
    
    # Handle sociogram data (optional, can be None)
    json_data["sociogram"] = _convert_value(report_data["sociogram"])
    
    # Handle relevant nodes data (nested DataFrames)
    json_data["relevant_nodes_ab"] = {
        "a": _convert_pandas_dataframe(report_data["relevant_nodes_ab"]["a"]),
        "b": _convert_pandas_dataframe(report_data["relevant_nodes_ab"]["b"])
    }
    
    # Handle isolated nodes data (pandas Index objects)
    json_data["isolated_nodes_ab"] = {
        "a": report_data["isolated_nodes_ab"]["a"].tolist(),
        "b": report_data["isolated_nodes_ab"]["b"].tolist()
    }
    
    return json_data

def to_snake_case(text: str) -> str:
    # Replace spaces and other separators with underscores
    text = re.sub(r'[\s\-\.]+', '_', text)
    # Insert underscore before uppercase letters (except at the start)
    text = re.sub(r'(?<!^)(?=[A-Z])', '_', text)
    # Convert to lowercase and clean up multiple underscores
    text = re.sub(r'_+', '_', text.lower())
    # Remove leading/trailing underscores
    return text.strip('_')
