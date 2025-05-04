"""
Filename: abgrid_utils.py
Description: Implements a decorator to print notifications for function execution.

Author: Pierpaolo Calanna
Date Created: May 3, 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

from pathlib import Path
from typing import Callable, Any
from functools import wraps

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
                print(f"Error while executing operation '{operation_name}'. Error details: {error}")
                
                # Retrieve the traceback object from the exception
                traceback = error.__traceback__
                
                # Walk through each step in the traceback chain
                while traceback is not None:
                    
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