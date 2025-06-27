from functools import wraps
from pathlib import Path
import textwrap
from typing import Any, Callable, Dict, List, Optional, Set

from pydantic_core import ValidationError

def logger_decorator(messages) -> Callable:
    start_message, end_message = messages
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
            It adds error handling with event emission capabilities.
            
            Args:
                *args (Any): Positional arguments to pass to the original function.
                **kwargs (Any): Keyword arguments to pass to the original function.
                
            Returns:
                Any: The result of the original function execution.
                
            Raises:
                Exception: Re-raises any exception that occurs during function execution
                after emitting error details and traceback information.
            """
            try:
                pretty_print(start_message, "▶ ")
                result = function(*args, **kwargs)
                pretty_print(end_message, "▶ ")
                return result
            except ValueError as error:
                pretty_print(str(error), "✗ ")
            except AttributeError as error:
                pretty_print(str(error), "✗ ")
            except TypeError as error:
                pretty_print(str(error), "✗ ")
            except FileNotFoundError as error:
                pretty_print(str(error), "✗ ")
            except OSError as error:
                pretty_print(str(error), "✗ ")
            except Exception as error:
                pretty_print(extract_traceback_info(error))
                raise
        return wrapper
    return decorator

def extract_traceback_info(error: Exception, exclude_files: Optional[Set[str]] = None) -> str:
    """
    Extract and format traceback information from an exception into a readable string.
    
    Creates a formatted traceback message showing the call stack with file names,
    function names, and line numbers. Excludes specified files (like logger files)
    to focus on relevant application code in the traceback.
    
    Args:
        error: Exception object containing traceback information to extract and format.
        exclude_files: Set of filenames to exclude from the traceback output.
                      Defaults to excluding "abgrid_logger.py" to avoid logger noise.
        
    Returns:
        Formatted string containing traceback information with each frame on a new line.
        Returns "No traceback available" if no relevant frames are found.
        
    Note:
        The traceback format follows: "filename:line_number in function_name()"
        Each frame is separated by newlines with arrow prefixes for readability.
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


def pretty_print(text: str, prefix: str = "", width: int = 80) -> None:
        """
        Print text with proper line wrapping and consistent prefix indentation.
        
        Handles text wrapping to ensure lines don't exceed specified width while
        maintaining proper indentation alignment for continuation lines. Gracefully
        handles edge cases including empty text, very long prefixes, and whitespace-only content.
        
        Args:
            text: The text content to print with wrapping applied.
            width: Maximum line width constraint. Default is 80 characters
        """
        # Handle empty text
        if not text:
            return
        
        # Print text directly, if it fits on one line
        if len(full_line := f"{prefix}{text}") <= width:
            print(full_line)
            return
        
        # Text needs wrapping
        [first_line, *rest_of_lines] = textwrap.wrap(
            text,
            width=max(1, width - len(prefix)),
            break_long_words=True,
            break_on_hyphens=True
        )
        
         # Print first line with prefix
        print(f"{prefix}{first_line}")
        
        # Print rest of lines with indentation
        for line in rest_of_lines:
            print(f"{' ' * len(prefix)}{line}")