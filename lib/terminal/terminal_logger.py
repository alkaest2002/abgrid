from functools import wraps
from pathlib import Path
import textwrap
from typing import Any, Callable, Dict, List, Optional, Set

def logger_decorator(message) -> Callable:
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
                pretty_print("▶ START EVENT: " + message)
                result = function(*args, **kwargs)
                pretty_print("▶ END EVENT: " + message)
                return result
            except Exception as error:
                error_message = extract_traceback_info(error)
                pretty_print("✗ ERROR: " + error_message)
                raise
        return wrapper
    return decorator

def extract_traceback_info(error: Exception, exclude_files: Optional[Set[str]] = None) -> List[Dict[str, Any]]:
    """
    Extract relevant traceback information from an exception.
    
    Args:
        error: Exception object with traceback
        exclude_files: Set of filenames to exclude from traceback
        
    Returns:
        List of dictionaries containing filename, function name, and line number
    """
    if exclude_files is None:
        exclude_files = {"abgrid_utils.py", "abgrid_logger.py"}
    
    traceback_info = []
    current_traceback = error.__traceback__
    
    while current_traceback is not None:
        frame = current_traceback.tb_frame
        filename = Path(frame.f_code.co_filename).name
        
        if filename not in exclude_files:
            traceback_info.append({
                'filename': filename,
                'function_name': frame.f_code.co_name,
                'line_number': current_traceback.tb_lineno
            })
        
        current_traceback = current_traceback.tb_next
    
    return traceback_info

def pretty_print(text: str, prefix: str = "", width: int = 80) -> None:
        """
         Print text with proper line wrapping and consistent prefix indentation.
        
        Handles text wrapping to ensure lines don't exceed specified width while
        maintaining proper indentation alignment for continuation lines. Gracefully
        handles edge cases including empty text, very long prefixes, and whitespace-only content.
        
        Args:
            text: The text content to print with wrapping applied.
            prefix: Optional prefix string for the first line (e.g., "Error: ", "Info: ").
            width: Maximum line width constraint. Uses instance default if None.
            
        Note:
            Continuation lines are automatically indented to align with the text portion
            of the first line. Ensures minimum width of 1 character even with long prefixes.
            Handles whitespace-only text and empty content gracefully.
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