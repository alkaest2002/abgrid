"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import asyncio
import io
from base64 import b64encode

import pandas as pd
from matplotlib import pyplot as plt


def figure_to_base64_svg(fig: plt.Figure) -> str:
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

async def run_in_executor(func, *args):
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
