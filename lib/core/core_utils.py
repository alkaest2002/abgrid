"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import asyncio
import hashlib
import hmac
import io
import json
from base64 import b64encode
from collections.abc import Callable
from functools import reduce
from typing import Any, TypeVar

import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.figure import Figure

from lib.interfaces.fastapi.settings import Settings


settings = Settings.load()

# Type variable for the return type of the function
T = TypeVar("T")

async def run_in_executor[T](func: Callable[..., T], *args: Any) -> T:
    """
    Run a synchronous function in a thread pool executor.

    This allows CPU-bound synchronous functions to run without blocking
    the asyncio event loop.

    Args:
        func: The synchronous function to run
        *args: Arguments to pass to the function

    Returns:
        The result of the function call
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)


def unpack_network_edges(packed_edges: list[dict[str, str | None]]) -> list[tuple[str, str]]:
        """
        Unpack edge dictionaries into a list of directed edge tuples.

        Takes a list of dictionaries where each dictionary represents outgoing edges
        from source nodes, and converts them into a flat list of (source, target) tuples.

        Args:
            packed_edges: List of dictionaries where keys are source nodes and values are
                comma-separated strings of target nodes. None values are safely handled.

        Returns:
            Flat list of directed edge tuples (source, target).
        """
        return reduce(
            lambda acc, itr: [
                *acc,
                *[
                    (node_from, node_to) for node_from, edges in itr.items() if edges is not None
                        for node_to in edges.split(",")
                ]
            ],
            packed_edges,
            []
        )


def unpack_network_nodes(packed_edges: list[dict[str, str | None]]) -> list[str]:
    """
    Extract unique source nodes from packed edge dictionaries.

    Args:
        packed_edges: List of dictionaries where keys represent source nodes.

    Returns:
        Sorted list of unique source node identifiers.
    """
    return sorted([node for node_edges in packed_edges for node in node_edges])


def figure_to_base64_svg(fig: Figure) -> str:
    """
    Convert a matplotlib figure to a base64-encoded SVG string for web embedding.

    Takes a matplotlib figure object and converts it to a base64-encoded SVG format
    suitable for embedding in HTML documents or web applications. The figure is
    automatically closed after conversion to free memory.

    Args:
        fig: Matplotlib figure object to convert

    Returns:
        Base64-encoded SVG string with data URI prefix for direct HTML embedding

    Notes:
        - Uses SVG format for scalable vector graphics
        - Applies tight bounding box to minimize whitespace
        - Sets transparent background for flexible styling
        - Automatically closes the figure to prevent memory leaks
    """
    # Initialize an in-memory buffer
    buffer = io.BytesIO()

    # Save figure to the buffer in SVG format then close it
    fig.savefig(buffer, format="svg", bbox_inches="tight", transparent=True, pad_inches=0.05)

    # Close figure
    plt.close(fig)

    # Encode the buffer contents to a base64 string
    base64_encoded_string = b64encode(buffer.getvalue()).decode()

    return f"data:image/svg+xml;base64,{base64_encoded_string}"


def compute_descriptives(data: pd.DataFrame) -> pd.DataFrame:
    """
    Compute comprehensive descriptive statistics for numerical data.

    Calculates a wide range of descriptive statistics including central tendency,
    dispersion, distribution shape, and inequality measures. Extends pandas'
    basic describe() function with additional metrics useful for social network analysis.

    Args:
        data: DataFrame containing numerical data for statistical analysis

    Returns:
        DataFrame with comprehensive descriptive statistics for each column

    Notes:
        - Includes standard statistics: count, min, max, mean, std, quartiles
        - Adds coefficient of variation (cv) for relative variability
        - Calculates skewness (sk) and kurtosis (kt) for distribution shape
        - Computes Gini coefficient (gn) for inequality measurement
        - Reorders columns for logical statistical interpretation
    """
    # Compute descriptive statistics with pandas descrive
    descriptives = data.describe().T

    # Add other statistics
    return (descriptives
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


def gini_coefficient(values: pd.Series) -> float:
    """
    Calculate the Gini coefficient for measuring inequality in a distribution.

    Computes the Gini coefficient, a measure of inequality ranging from 0 (perfect equality)
    to 1 (maximum inequality). The calculation uses the standard formula adjusted for
    non-negative values by subtracting the minimum value from all observations.

    Args:
        values: Sequence of numerical values to analyze for inequality

    Returns:
        Gini coefficient as a float between 0 and 1

    Notes:
        - Returns 0.0 for distributions with zero variance (perfect equality)
        - Automatically handles negative values by shifting to non-negative range
        - Uses the standard Gini formula: G = (2 * Σ(i * x_i)) / (n * Σ(x_i)) - (n + 1) / n
        - Commonly used in social network analysis for measuring centralization
    """
    # Convert to non-negative values by subtracting minimum
    pos_values: pd.Series = values.sub(values.min())

    # Sort the values
    sorted_values: pd.Series = pos_values.sort_values(ignore_index=True)
    n: int = len(sorted_values)

    # Calculate mean
    mean_value: float = sorted_values.mean()

    # If all values are zero or mean is zero, return 0
    if mean_value == 0:
        return 0.0

    # Create index series (1 to n)
    index_series: pd.Series = pd.Series(range(1, n + 1), index=sorted_values.index)

    # Calculate Gini coefficient using the correct formula
    # Formula is G = (2 * sum(i * x_i)) / (n * sum(x_i)) - (n + 1) / n
    index_weighted_sum: float = sorted_values.mul(index_series).sum()
    total_sum: float = sorted_values.sum()
    gini: float = (2.0 * index_weighted_sum) / (n * total_sum) - (n + 1) / n

    return gini

def compute_hmac_signature(json_data: dict[str, Any]) -> str:
    """
    Compute an HMAC signature of the JSON data for cryptographic integrity and authentication.

    Uses HMAC-SHA256 which provides:
    - Cryptographic integrity (tamper detection)
    - Authentication (proves the data came from someone with the secret key)
    - Collision resistance
    - Platform independence

    Args:
        json_data: The JSON data dictionary to sign (excluding signature keys)

    Returns:
        A hexadecimal string representation of the HMAC signature
    """
    # Convert to JSON string with sorted keys for consistent signing
    json_string = json.dumps(json_data, sort_keys=True, separators=(",", ":"))

    # Compute HMAC-SHA256
    return hmac.new(
        settings.auth_secret.encode("utf-8"),
        json_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

def verify_hmac_signature(json_data: dict[str, Any]) -> bool:
    """
    Verify the HMAC signature of JSON data.

    Args:
        json_data: The complete JSON data dictionary including the "_signature" key

    Returns:
        True if signature is valid, False otherwise

    Raises:
        KeyError: If the "_signature" key is missing from json_data
    """
    if "_signature" not in json_data:
        error_message = "no_signature_key_in_json_data"
        raise KeyError(error_message)

    # Extract the signature and create data without signature for verification
    provided_signature = json_data["_signature"]
    data_without_signature = {k: v for k, v in json_data.items() if k != "_signature"}

    # Compute expected signature
    expected_signature = compute_hmac_signature(data_without_signature)

    # Use hmac.compare_digest for timing-attack resistance
    return hmac.compare_digest(provided_signature, expected_signature)
