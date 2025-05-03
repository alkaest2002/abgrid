"""
Filename: abgrid_utils.py
Description: Implements a decorator to print notifications for function execution.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from typing import Callable, Any

def notify_decorator(argument: str) -> Callable:
    def decorator(function: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            Wrapper function executed in place of the original function.

            It adds print notifications before and after function execution.

            Args:
                *args (Any): Positional arguments to pass to the original function.
                **kwargs (Any): Keyword arguments to pass to the original function.

            Returns:
                Any: The result of the original function execution.

            Exceptions:
                Prints an error message if the original function raises an exception.
            """
            print(f"Operation '{argument}' is being currently executed.")
            try:
                result = function(*args, **kwargs)  # Call the original function
                print(f"Operation '{argument}' was succesfully executed.")
                return result
            except Exception as error:
                print(f"Error while executing operation '{argument}'. Error details: {error}")
        
        return wrapper
    
    return decorator
