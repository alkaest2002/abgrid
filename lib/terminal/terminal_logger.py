from functools import wraps
from pathlib import Path
import textwrap
from typing import Any, Callable, Dict, List, Optional, Set

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
                pretty_print("▶ " + start_message)
                result = function(*args, **kwargs)
                pretty_print("▶ " + end_message)
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
        exclude_files = {"abgrid_logger.py"}
    
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

def pretty_print(text: str, width: int = 80) -> None:
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
        if len(text) <= width:
            print(text)
            return
        
        # Text needs wrapping
        wrapped_text_lines = textwrap.wrap(
            text,
            width=width,
            break_long_words=True,
            break_on_hyphens=True
        )
        
        # Print wrapped text lines
        print(*wrapped_text_lines, sep='\n')