"""
Filename: abgrid_utils.py
Description: Implements a decorator to print notifications for function execution.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import io
import datetime
import pandas as pd
import json

from base64 import b64encode
from pathlib import Path
from typing import Callable, Any, Dict, List, Optional, Set
from functools import wraps

from matplotlib import pyplot as plt
import pandas as pd

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
            
            # Start notification
            print(f"Operation '{operation_name}' is being currently executed.")
            
            # Try to run the function
            try:
                
                # Run the original function
                result = function(*args, **kwargs)

                # Everything run smoothly. Notify succes
                print(f"Operation '{operation_name}' was successfully executed.")
                
                # Return result
                return result
            
            except Exception as error:
                
                # Notify error
                print(f"Error while executing operation '{operation_name}'.\n{error}")
                
                # Retrieve the traceback object from the exception
                traceback = error.__traceback__

                # Walk through each step in the traceback chain
                while traceback is not None:
                    # Skip 
                    if Path(traceback.tb_frame.f_code.co_filename).name != "abgrid_utils.py":
                    
                        # Print the current traceback step with information about file, function, and line
                        print(
                            "-->",
                            Path(traceback.tb_frame.f_code.co_filename).name,
                            traceback.tb_frame.f_code.co_name,
                            "line code",
                            traceback.tb_lineno,
                            end="\n"
                        )
                    # Proceed to the next traceback step
                    traceback = traceback.tb_next
                
        return wrapper
    
    return decorator

def to_json_serializable(
    data: Any,
    keys_to_omit: Optional[List[str]] = None,
    max_depth: int = 100
) -> Any:
    """
    Converts data into a JSON-serializable format, supporting nested objects and
    omitting specified keys or exceeding a certain depth in the object hierarchy.

    Args:
        data: The input data to be serialized, which can be of any type.
        keys_to_omit: Optional list of keys or paths to omit from serialization.
                      Each key should be given as a string representing the complete
                      path in dot notation to the key you want to omit.
        max_depth: The maximum depth to which the object hierarchy should be
                   serialized. This helps prevent issues with circular references.

    Returns:
        A JSON-serializable version of the input data.
    """
    keys_to_omit = keys_to_omit or []

    def _serialize(obj, path=None, depth=0):
        
        # Avoid circular reference
        if depth > max_depth:
            return f"<Max depth {max_depth} exceeded>"
        
        # Default path is empty list
        path = path or []
        
        # Run several serialization scenarios
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
            return {
                k: _serialize(v, path + [str(k)], depth + 1)
                for k, v in obj.items()
                    if ".".join(path + [str(k)]) not in keys_to_omit
            }
        elif isinstance(obj, (list, tuple)):
            return [
                _serialize(item, path + [f"[{i}]"], depth + 1)
                for i, item in enumerate(obj)
            ]
        elif hasattr(obj, '__dict__') and not isinstance(obj, type):
            return _serialize(obj.__dict__, path, depth + 1)
        else:
            try:
                json.dumps(obj)
                return obj
            except (TypeError, ValueError):
                return str(obj)
    
    return _serialize(data)


def figure_to_base64_svg(fig: plt.Figure) -> str:
        """
        Convert a matplotlib figure to a base64-encoded SVG data URI.

        Args:
            fig: plt.Figure
                The matplotlib figure to convert.

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
        
        # Return the data URI for the SVG
        return f"data:image/svg+xml;base64,{base64_encoded_string}"