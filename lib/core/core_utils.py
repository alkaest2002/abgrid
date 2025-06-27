
import io
import numpy as np
import pandas as pd

from typing import Sequence, Union
from base64 import b64encode
from matplotlib import pyplot as plt


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
