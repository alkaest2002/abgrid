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
        """Convert various Python/scientific computing types to JSON-serializable format.

        This function provides encoders for common data types used in scientific computing
        and data analysis, including pandas DataFrames/Series, NetworkX graphs, numpy arrays,
        and datetime objects.

        Args:
            value: The value to convert to JSON-serializable format.

        Returns:
            A JSON-serializable representation of the input value.

        Notes:
            - DataFrames are converted to dict format with index preservation.
            - NetworkX graphs are converted to node/edge lists.
            - Numpy arrays become Python lists.
            - Datetime objects become ISO format strings.
            - Complex objects are converted to string representation as fallback.
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
        try:
            return json.dumps(value)
        except (TypeError, ValueError):
            return str(value)

    #########################################################################################
    #   SINGLE STEP REPORT GENERATION
    #########################################################################################

    @staticmethod
    def to_json(data: dict[str, Any]) -> dict[str, Any]:
        """Convert complete AB-Grid report data to a JSON-serializable format with HMAC signature.

        Handles the full AB-Grid report structure including metadata (year, project title,
        questions), Group information, SNA analysis results, Sociogram data, Relevant nodes
        analysis, and Isolated nodes identification.

        Args:
            data: The data dictionary to convert and sign.

        Returns:
            A JSON-serializable dictionary with the same structure as the input,
            with all pandas/numpy/networkx objects converted to JSON-compatible formats.

        Notes:
            this encoding process ensures that all data is properly serialized
            and ready for JSON output when single step report generation is used.
        """
        # Initialize dictionary
        json_data: dict[str, Any] = {}

        # Add following data 'as is' to json data (no need to serialize)
        json_data["year"] = data.get("year")
        json_data["project_title"] = data.get("project_title")
        json_data["question_a"] = data.get("question_a")
        json_data["question_b"] = data.get("question_b")
        json_data["group"] = data.get("group")
        json_data["group_size"] = data.get("group_size")

        # Get, serialize and add SNA data to json_data
        sna = data.get("sna")
        json_data["sna"] = CoreExport._to_json_encoders(sna)

        # Get, serialize and add  Sociogram data
        sociogram = data.get("sociogram")
        json_data["sociogram"] = CoreExport._to_json_encoders(sociogram)

        # Get, serialize and add isolated nodes data to json_data
        isolated_nodes = data.get("isolated_nodes", {})
        json_data["isolated_nodes"] = {
            "a": CoreExport._to_json_encoders(isolated_nodes.get("a", pd.Index([]))),
            "b": CoreExport._to_json_encoders(isolated_nodes.get("b", pd.Index([])))
        }

        # Get, serialize and add relevant nodes data to json_data
        relevant_nodes = data.get("relevant_nodes", {})
        json_data["relevant_nodes"] = {
            "a": CoreExport._to_json_encoders(relevant_nodes.get("a", pd.DataFrame())),
            "b": CoreExport._to_json_encoders(relevant_nodes.get("b", pd.DataFrame()))
        }

        return json_data


    #########################################################################################
    #   MULTI STEP REPORT GENERATION
    #########################################################################################

    @staticmethod
    def to_json_report_step_1(data: dict[str, Any]) -> dict[str, Any]:
        """Convert AB-Grid step 1 data to a JSON-serializable format with HMAC signature.

        Serializes data, combines them into a single dictionary structure,
        and adds HMAC signature for data integrity verification.

        Args:
            data: The data dictionary to convert and sign.

        Returns:
            A JSON-serializable dictionary containing both group and SNA data with signature.

        Notes:
            this encoding process ensures that all data is properly serialized
            and ready for JSON output when multi-step report generation is used.
        """
        # Initialize dictionary
        json_data: dict[str, Any] = {}

        # Get, serialize and add Group data to json_data
        group_data = data.get("group_data")
        json_data["group_data"] = CoreExport._to_json_encoders(group_data)

        # Get, serialize and add SNA data to json_data
        sna_data = data.get("sna_data")
        json_data["sna_data"] = CoreExport._to_json_encoders(sna_data)

        # Create data to sign
        data_to_sign = json.dumps(json_data, sort_keys=True, separators=(",", ":"))

        # Base encode data
        encoded_data = data_to_sign

        # Add signature to data
        signature = compute_hmac_signature(encoded_data)

        return {
            "encoded_data": encoded_data,
            "signature": signature
        }

    @staticmethod
    def to_json_report_step_2(data: dict[str, Any]) -> dict[str, Any]:
        """Convert AB-Grid step 2 data to a JSON-serializable format with HMAC signature.

        Serializes data, combines them into a single dictionary structure,
        and adds HMAC signature for data integrity verification.

        Args:
            data: The data dictionary to convert and sign.

        Returns:
            A JSON-serializable dictionary containing both group and SNA data with signatures.

        Notes:
            this encoding process ensures that all data is properly serialized
            and ready for JSON output when multi-step report generation is used.
        """
        # Initialize dictionary
        json_data: dict[str, Any] = {}

        # Add following data 'as is' to json data
        # (either no need to serialize or already JSON-serialized in step 1)
        json_data["year"] = data.get("year")
        json_data["project_title"] = data.get("project_title")
        json_data["question_a"] = data.get("question_a")
        json_data["question_b"] = data.get("question_b")
        json_data["group"] = data.get("group")
        json_data["group_size"] = data.get("group_size")
        json_data["sna"] = data.get("sna")

        # Get, serialize and add Sociogram data to json_data
        sociogram = data.get("sociogram")
        json_data["sociogram"] = CoreExport._to_json_encoders(sociogram)

        # Get, serialize and add Isolated nodes data to json_data
        isolated_nodes = data.get("isolated_nodes", {})
        json_data["isolated_nodes"] = {
            "a": CoreExport._to_json_encoders(isolated_nodes.get("a", pd.Index([]))),
            "b": CoreExport._to_json_encoders(isolated_nodes.get("b", pd.Index([])))
        }

        # Get, serialize and add Relevant nodes data to json_data
        relevant_nodes = data.get("relevant_nodes", {})
        json_data["relevant_nodes"] = {
            "a": CoreExport._to_json_encoders(relevant_nodes.get("a", pd.DataFrame())),
            "b": CoreExport._to_json_encoders(relevant_nodes.get("b", pd.DataFrame()))
        }

        # Create data to sign
        data_to_sign = json.dumps(json_data, sort_keys=True, separators=(",", ":"))

        # Base encode data
        encoded_data = data_to_sign

        # Add signature to json data
        signature = compute_hmac_signature(encoded_data)

        return {
            "encoded_data": encoded_data,
            "signature": signature
        }

