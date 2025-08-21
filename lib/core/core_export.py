"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
import datetime
import json
from typing import Any

import numpy as np
import pandas as pd
from networkx import DiGraph

from lib.core.core_utils import compute_hmac_signature


class CoreExport:
    """Utility class for exporting AB-Grid report data to JSON format."""

    @staticmethod
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

        def _convert_pandas_series(series: pd.Series) -> dict[str, Any]:
            """Convert pandas Series to JSON-serializable format."""
            if series.empty:
                return {}

            # Fill missing values
            series = series.replace([np.inf, -np.inf], np.nan)
            series = series.fillna("-")

            # Convert index keys to strings for JSON compatibility
            return {str(k): v for k, v in series.to_dict().items()}

        def _convert_numpy_array(arr: np.ndarray) -> dict[str, Any]:
            """Convert numpy array to JSON-serializable dict."""
            return _convert_pandas_series(pd.Series(arr))

        def _convert_networkx(graph: DiGraph) -> dict[str, Any]:  # type: ignore[type-arg]
            """Convert NetworkX DiGraph to JSON-serializable format."""
            return {
                "nodes": list(graph.nodes()),
                "edges": list(graph.edges()),
                "number_of_nodes": graph.number_of_nodes(),
                "number_of_edges": graph.number_of_edges()
            }

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
            return {k: CoreExport._to_json_encoders(v) for k, v in value.items()}
        if isinstance(value, list | tuple):
            return [CoreExport._to_json_encoders(item) for item in value]
        # Fallback: try to serialize directly, otherwise convert to string
        try:
            return json.dumps(value)
        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def to_json_group_and_sna(group_data: dict[str, Any], sna_data: dict[str, Any]) -> dict[str, Any]:
        """
        Convert AB-Grid report data to a JSON-serializable format.

        Args:
            group_data: The project data dictionary to convert
            sna_data: The SNA data dictionary to convert

        Returns:
            A JSON-serializable dictionary with the same structure as the input
        """
        # Serialize project data and add signature
        serialized_group_data = CoreExport._to_json_encoders(group_data)
        serialized_group_data["_signature"] = compute_hmac_signature(serialized_group_data)

        # Serialize SNA data and add signature
        serialized_sna_data = CoreExport._to_json_encoders(sna_data)
        serialized_sna_data["_signature"] = compute_hmac_signature(serialized_sna_data)

        # Init dictionary
        json_data: dict[str, Any] = {
            "group":  serialized_group_data,
            "sna": serialized_sna_data
        }

        return json_data

    @staticmethod
    def to_json_sociogram(sociogram_data: dict[str, Any]) -> dict[str, Any]:
        """
        Convert AB-Grid report data to a JSON-serializable format.

        Args:
            sociogram_data: The sociogram data dictionary to convert

        Returns:
            A JSON-serializable dictionary with the same structure as the input
        """
        # Serialize project data and add signature
        serialized_sociogram_data = CoreExport._to_json_encoders(sociogram_data)
        serialized_sociogram_data["sociogram"]["_signature"] = compute_hmac_signature(serialized_sociogram_data["sociogram"])

        # Init dictionary
        json_data: dict[str, Any] = serialized_sociogram_data

        return json_data

    @staticmethod
    def to_json(report_data: dict[str, Any]) -> dict[str, Any]:
        """
        Convert AB-Grid report data to a JSON-serializable format.

        Args:
            report_data: The report data dictionary to convert

        Returns:
            A JSON-serializable dictionary with the same structure as the input
        """
        # Init dictionary
        json_data: dict[str, Any] = {}

        # Handle basic metadata fields with defaults
        json_data["year"] = report_data.get("year")
        json_data["project_title"] = report_data.get("project_title")
        json_data["question_a"] = report_data.get("question_a")
        json_data["question_b"] = report_data.get("question_b")
        json_data["group"] = report_data.get("group")
        json_data["group_size"] = report_data.get("group_size")

        # Handle SNA data (complex nested structure)
        json_data["sna"] = CoreExport._to_json_encoders(report_data.get("sna"))

        # Handle sociogram data (optional, can be None)
        json_data["sociogram"] = CoreExport._to_json_encoders(report_data.get("sociogram"))

        # Handle relevant nodes data (nested DataFrames)
        relevant_nodes = report_data.get("relevant_nodes", {})
        json_data["relevant_nodes"] = {
            "a": CoreExport._to_json_encoders(relevant_nodes.get("a", pd.DataFrame())),
            "b": CoreExport._to_json_encoders(relevant_nodes.get("b", pd.DataFrame()))
        }

        # Handle isolated nodes data (pandas Index objects)
        isolated_nodes = report_data.get("isolated_nodes", {})
        json_data["isolated_nodes"] = {
            "a": CoreExport._to_json_encoders(isolated_nodes.get("a", pd.Index([]))),
            "b": CoreExport._to_json_encoders(isolated_nodes.get("b", pd.Index([])))
        }

        return json_data
