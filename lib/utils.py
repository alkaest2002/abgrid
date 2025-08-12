"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
# ruff: noqa: T201

import datetime
import json
import re
import sys
from typing import Any

import numpy as np
import pandas as pd
from networkx import DiGraph


def check_python_version() -> None:
    """Check if Python version meets minimum requirements."""
    required_version = (3, 12)
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
        print("- Or use virtual environments to install a newer version")
        print("=" * 60)
        sys.exit(1)

def to_snake_case(text: str) -> str:
    """
    Convert text to snake_case.

    This function replaces spaces and other separators with underscores,
    converts the text to lowercase, and removes leading/trailing underscores.

    Args:
        text: The input text to convert.

    Returns:
        The converted text in snake_case.
    """
    # Replace spaces and other separators with underscores
    text = re.sub(r"[\s\-\.]+", "_", text)
    # Insert underscore before uppercase letters (except at the start)
    text = re.sub(r"(?<!^)(?=[A-Z])", "_", text)
    # Convert to lowercase and clean up multiple underscores
    text = re.sub(r"_+", "_", text.lower())
    # Remove leading/trailing underscores
    return text.strip("_")

def _to_json_encoders(value: Any) -> Any:  # noqa: PLR0911
    """
    Convert various Python/scientific computing types to JSON-serializable format.

    This function provides encoders for common data types used in scientific computing
    and data analysis, including pandas DataFrames/Series, NetworkX graphs, numpy arrays,
    and datetime objects.

    Args:
        value: The value to convert to JSON-serializable format

    Returns:
        A JSON-serializable representation of the input value

    Note:
        - DataFrames are converted to dict format with index preservation
        - NetworkX graphs are converted to node/edge lists
        - Numpy arrays become Python lists
        - Datetime objects become ISO format strings
        - Complex objects are converted to string representation as fallback
    """

    def _convert_pandas_dataframe(df: pd.DataFrame) -> dict[str, Any]:
        """Convert pandas DataFrame to JSON-serializable format."""
        if df.empty:
            return {}

        # Fill missing values
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.fillna("-")

        # Handle DataFrames with duplicate indices by resetting index
        if df.index.has_duplicates:
            # Reset index to ensure no duplicates
            df = df.reset_index(drop=False, names="index")
            # Convert index keys to strings for JSON compatibility
            return {str(k): v for k, v in df.to_dict("index").items()}
        # Convert index keys to strings for JSON compatibility
        return {str(k): v for k, v in df.to_dict("index").items()}

    def _convert_pandas_series(series: pd.Series) -> dict[str, Any] | list[Any]:
        """Convert pandas Series to JSON-serializable format."""
        if series.empty:
            return {}

        # Fill missing values
        series = series.replace([np.inf, -np.inf], np.nan)
        series = series.fillna("-")

        # If series has a meaningful index, convert to dict
        if not isinstance(series.index, pd.RangeIndex):
            return series.to_dict()
        # For range index, convert to list
        return series.tolist()

    def _convert_networkx(graph: DiGraph) -> dict[str, Any]:  # type: ignore[type-arg]
        """Convert NetworkX DiGraph to JSON-serializable format."""
        return {
            "nodes": list(graph.nodes()),
            "edges": list(graph.edges()),
            "number_of_nodes": graph.number_of_nodes(),
            "number_of_edges": graph.number_of_edges()
        }

    def _convert_numpy_array(arr: np.ndarray) -> list[Any]:
        """Convert numpy array to JSON-serializable list."""
        result = _convert_pandas_series(pd.Series(arr))
        if isinstance(result, dict):
            return list(result.values())
        return result

    def _convert_datetime(dt: datetime.datetime) -> str:
        """Convert datetime to ISO format string."""
        return dt.isoformat()

    # Main conversion logic
    if value is None:
        return None
    if isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, pd.DataFrame):
        return _convert_pandas_dataframe(value)
    if isinstance(value, pd.Series):
        return _convert_pandas_series(value)
    if isinstance(value, pd.Index):
        return value.tolist()
    if isinstance(value, DiGraph):
        return _convert_networkx(value)
    if isinstance(value, np.ndarray):
        return _convert_numpy_array(value)
    if isinstance(value, datetime.datetime):
        return _convert_datetime(value)
    if isinstance(value, datetime.date):
        return _convert_datetime(datetime.datetime.combine(value, datetime.time()))
    if isinstance(value, dict):
        return {k: _to_json_encoders(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_to_json_encoders(item) for item in value]

    # Fallback: try to serialize directly, otherwise convert to string
    try:
        return json.dumps(value)
    except (TypeError, ValueError):
        return str(value)


def to_json_report(report_data: dict[str, Any]) -> dict[str, Any]:
    """
    Convert AB-Grid ReportDataDict to a JSON-serializable format.

    This function specifically handles the structure of AB-Grid report data,
    treating all keys as optional and providing appropriate defaults.

    Args:
        report_data: The report data dictionary to convert

    Returns:
        A JSON-serializable dictionary with the same structure as the input

    Note:
        All keys are treated as optional and missing keys will result in None values
        or appropriate empty defaults (empty DataFrames, empty lists, etc.)
    """
    # Convert the main report data structure
    json_data: dict[str, Any] = {}

    # Handle basic metadata fields with defaults
    json_data["year"] = report_data.get("year")
    json_data["project_title"] = report_data.get("project_title")
    json_data["question_a"] = report_data.get("question_a")
    json_data["question_b"] = report_data.get("question_b")
    json_data["group"] = report_data.get("group")
    json_data["group_size"] = report_data.get("group_size")

    # Handle SNA data (complex nested structure)
    json_data["sna"] = _to_json_encoders(report_data.get("sna"))

    # Handle sociogram data (optional, can be None)
    json_data["sociogram"] = _to_json_encoders(report_data.get("sociogram"))

    # Handle relevant nodes data (nested DataFrames)
    relevant_nodes = report_data.get("relevant_nodes_ab", {})
    json_data["relevant_nodes_ab"] = {
        "a": _to_json_encoders(relevant_nodes.get("a", pd.DataFrame())),
        "b": _to_json_encoders(relevant_nodes.get("b", pd.DataFrame()))
    }

    # Handle isolated nodes data (pandas Index objects)
    isolated_nodes = report_data.get("isolated_nodes_ab", {})
    json_data["isolated_nodes_ab"] = {
        "a": _to_json_encoders(isolated_nodes.get("a", pd.Index([]))),
        "b": _to_json_encoders(isolated_nodes.get("b", pd.Index([])))
    }

    return json_data

