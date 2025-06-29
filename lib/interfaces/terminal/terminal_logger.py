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
from typing import Any, Callable, List, Optional, Set, TypeVar
from lib.core.core_schemas import PydanticValidationException
from lib.core.core_templates import TemplateRenderError

# Type variable for preserving function signatures
F = TypeVar('F', bound=Callable[..., Any])

def logger_decorator(func: Optional[F] = None) -> Callable[[F], F]:
    """
    Create a logging decorator that wraps functions with start/end messages and error handling.
    
    This decorator provides comprehensive error handling and logging for function execution,
    catching common exceptions and formatting them for user-friendly display.
    
    Args:
        func: Optional function to decorate (when used without parentheses)
    
    Returns:
        Decorator function that can be applied to other functions, or the decorated function itself
    
    Notes:
        - Can be used with or without parentheses: @logger_decorator or @logger_decorator()
        - Catches and formats ValueError, AttributeError, TypeError, FileNotFoundError, OSError
        - Re-raises unexpected exceptions after logging traceback information
        - Uses print for consistent message formatting
    """
    def decorator(function: F) -> F:
        """
        Decorator function that wraps the target function with logging and error handling.
        
        Args:
            function: The function to be decorated with logging capabilities
        
        Returns:
            Wrapper function with logging and error handling
        """
        @wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            Wrapper function that executes the decorated function with logging.
            
            Args:
                *args: Positional arguments to pass to the decorated function
                **kwargs: Keyword arguments to pass to the decorated function
            
            Returns:
                Result of the decorated function execution, or None if an exception is caught
            
            Notes:
                - Logs start message before execution
                - Logs end message on successful completion
                - Handles exceptions with appropriate error formatting
                - Returns None for handled exceptions (doesn't re-raise them)
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
            except Exception as error:
                print(extract_traceback_info(error))
                raise
        return wrapper
    
    # Handle both @logger_decorator and @logger_decorator() usage
    if func is None:
        # Called with parentheses: @logger_decorator()
        return decorator
    else:
        # Called without parentheses: @logger_decorator
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
        - Defaults to excluding "abgrid_logger.py" from traceback
        - Formats each frame as "filename:line_number in function_name()"
        - Returns fallback message if no traceback frames are available
    """
    if exclude_files is None:
        exclude_files = {"abgrid_logger.py"}
    
    traceback_lines = []
    current_traceback = error.__traceback__
    
    while current_traceback is not None:
        frame = current_traceback.tb_frame
        filename = Path(frame.f_code.co_filename).name

        if filename not in exclude_files:
            # Format each traceback frame as a readable line
            trace_line = f"{filename}:{current_traceback.tb_lineno} in {frame.f_code.co_name}()"
            traceback_lines.append(f"→ {trace_line}")
        
        current_traceback = current_traceback.tb_next
    
    # Return formatted string or fallback message
    if traceback_lines:
        return "Traceback (most recent call last):\n" + "\n".join(traceback_lines)
    else:
        return "No traceback available"
    
def extract_pydantic_errors(pydantic_validation_exception: PydanticValidationException) -> str:
        """
        Format Pydantic validation errors into human-readable error messages.
        
        Converts ValidationError objects into formatted strings that provide
        clear information about field locations and error descriptions.
        
        Args:
            validation_error: Pydantic ValidationError object containing error details
        
        Returns:
            Formatted string containing all validation errors separated by semicolons
        
        Notes:
            - Builds location paths using dot notation for nested fields
            - Supports optional context prefixes for error categorization
            - Returns empty string if no errors are present
        """
        # Init formatted errors
        formatted_errors: List[str] = [
            "Pydantic validation errors", 
            "==========================",
        ]
        
        # Loop through errors
        for error in pydantic_validation_exception.errors:  
            
            # Get location of error
            location = error.get('location', "Unkown location")
            
            # Get error message
            error_message = error.get('error_message', 'Unknown error')
            
            # Append error to list
            formatted_errors.append(f"{location}: {error_message}")
        
        # Join all errors into a single string
        return "\n".join(formatted_errors)