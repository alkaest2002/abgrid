"""
Terminal logging utilities for the AB-Grid project.

This module provides logging functionality with decorators for function execution tracking,
error handling, and formatted output. It includes traceback extraction and pretty printing
capabilities for enhanced debugging and user feedback.

Author: Pierpaolo Calanna
Date Created: Wed Jun 25 2025

The code is part of the AB-Grid project and is licensed under the MIT License.
"""

import textwrap
from functools import wraps
from pathlib import Path
from typing import Any, Callable, List, Optional, Set, TypeVar, Union
from lib.core.core_schemas import PydanticValidationException
from lib.core.core_templates import TemplateRenderError

# Type variable for preserving function signatures
F = TypeVar('F', bound=Callable[..., Any])

def logger_decorator(func: Optional[F] = None) -> Union[Callable[[F], F], F]:
    """
    Create a logging decorator that wraps functions with error handling.
    
    This decorator provides comprehensive error handling for function execution,
    catching common exceptions and formatting them for user-friendly display.
    
    Args:
        func: Optional function to decorate (when used without parentheses)
    
    Returns:
        Decorator function or the decorated function itself
    
    Usage:
        @logger_decorator
        def my_function(): pass
        
        # or
        
        @logger_decorator()
        def my_function(): pass
    
    Notes:
        - Returns None for handled exceptions (doesn't re-raise them)
        - Uses print for consistent message formatting
        - Handles different exception types with appropriate formatting
    """
    def decorator(function: F) -> F:
        """
        Decorator function that wraps the target function with error handling.
        
        Args:
            function: The function to be decorated
        
        Returns:
            Wrapper function with error handling
        """
        @wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            Wrapper function that executes the decorated function with error handling.
            
            Returns:
                Result of the decorated function execution, or None if an exception occurs
            """
            try:
                return function(*args, **kwargs)
            except ValueError as error:
                print(str(error))
                return None
            except AttributeError as error:
                print(str(error))
                return None
            except TypeError as error:
                print(str(error))
                return None
            except FileNotFoundError as error:
                print(str(error))
                return None
            except OSError as error:
                print(str(error))
                return None
            except TemplateRenderError as error:
                print(str(error))
                return None
            except PydanticValidationException as error:
                print(extract_pydantic_errors(error))
                return None
            except Exception as error:
                print(extract_traceback_info(error))
                return None
        return wrapper
    
    # Handle both @logger_decorator and @logger_decorator() usage
    if func is None:
        return decorator
    else:
        return decorator(func)


def extract_traceback_info(error: Exception, exclude_files: Optional[Set[str]] = None) -> str:
    """
    Extract and format traceback information from an exception.
    
    Processes the exception's traceback to create a readable string representation,
    filtering out specified files to focus on relevant code locations.
    
    Args:
        error: Exception object containing traceback information
        exclude_files: Set of filenames to exclude from traceback output
    
    Returns:
        Formatted string containing traceback information
    
    Notes:
        - Defaults to excluding "terminal_logger.py" from traceback
        - Formats each frame as "filename:line_number in function_name()"
        - Includes the original error message
    """
    if exclude_files is None:
        exclude_files = {"terminal_logger.py"}
    
    traceback_lines = []
    current_traceback = error.__traceback__
    
    while current_traceback is not None:
        frame = current_traceback.tb_frame
        filename = Path(frame.f_code.co_filename).name

        if filename not in exclude_files:
            trace_line = f"{filename}:{current_traceback.tb_lineno} in {frame.f_code.co_name}()"
            traceback_lines.append(f"→ {trace_line}")
        
        current_traceback = current_traceback.tb_next
    
    # Include the error type and message
    error_header = f"{type(error).__name__}: {str(error)}"
    
    if traceback_lines:
        return f"Traceback (most recent call last):\n" + "\n".join(traceback_lines) + f"\n{error_header}"
    else:
        return f"Error: {error_header}"
    

def extract_pydantic_errors(pydantic_validation_exception: PydanticValidationException) -> str:
    """
    Format Pydantic validation errors into human-readable error messages.
    
    Converts PydanticValidationException objects into formatted strings that provide
    clear information about field locations and error descriptions.
    
    Args:
        pydantic_validation_exception: PydanticValidationException containing error details
    
    Returns:
        Formatted string containing all validation errors
    """
    formatted_errors = [
        "Pydantic validation errors:",
        "=" * 28,
    ]
    
    for error in pydantic_validation_exception.errors:
        location = error.get('location', "Unknown location")
        error_message = error.get('error_message', 'Unknown error')
        formatted_errors.append(f"  {location}: {error_message}")
    
    return "\n".join(formatted_errors)
