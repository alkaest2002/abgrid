"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
# ruff: noqa: T201

from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar, cast, overload

from lib.core.core_schemas_errors import PydanticValidationError
from lib.core.core_templates import TemplateRenderError


# Type variable for any callable
F = TypeVar("F", bound=Callable[..., Any])

@overload
def logger_decorator() -> Callable[[F], F]:
    ...

@overload
def logger_decorator[F: Callable[..., Any]](func: F) -> F:
    ...


def logger_decorator[F: Callable[..., Any]](func: F | None = None) -> F | Callable[[F], F]:
    """Create a logging decorator that wraps functions with error handling.

    This decorator provides comprehensive error handling for function execution,
    catching common exceptions and formatting them for user-friendly display.

    Usage:
        @logger_decorator
        def my_function(): pass

        # or

        @logger_decorator()
        def my_function(): pass

    Notes:
        - Returns None for handled exceptions (doesn"t re-raise them)
        - Uses print for consistent message formatting
        - Handles different exception types with appropriate formatting
    """

    def _decorator(function: F) -> F:
        """Internal decorator function that applies the error handling wrapper."""

        @wraps(function)
        def _wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: PLR0911
            """Wrapper function that executes the decorated function with error handling.

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

            except RuntimeError as error:
                print(str(error))
                return None

            except TemplateRenderError as error:
                print(str(error))
                return None

            except PydanticValidationError as error:
                print(extract_pydantic_errors(error))
                return None

            except Exception as error:
                print(extract_traceback_info(error))
                return None

        # Cast the wrapper to the original function type
        return cast("F", _wrapper)

    # Handle both @logger_decorator and @logger_decorator() usage patterns
    if func is None:
        # Called as @logger_decorator()
        return _decorator
    # Called as @logger_decorator
    return _decorator(func)


def extract_traceback_info(error: Exception, exclude_files: set[str] | None = None) -> str:
    """Extract and format traceback information from an exception.

    Processes the exception"s traceback to create a readable string representation,
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
    error_header = f"{type(error).__name__}: {error!s}"

    if traceback_lines:
        return "Traceback (most recent call last):\n" + "\n".join(traceback_lines) + f"\n{error_header}"
    return f"Error: {error_header}"

def extract_pydantic_errors(pydantic_validation_exception: PydanticValidationError) -> str:
    """Format Pydantic validation errors into human-readable error messages.

    Converts PydanticValidationError objects into formatted strings that provide
    clear information about field locations and error descriptions.

    Args:
        pydantic_validation_exception: PydanticValidationError containing error details

    Returns:
        Formatted string containing all validation errors
    """
    formatted_errors = [
        "Pydantic validation errors:",
        "=" * 28,
    ]

    for error in pydantic_validation_exception.errors:
        location = error.get("location", "unknown_location")
        error_message = error.get("error_message", "unknown_error")
        formatted_errors.append(f"  {location}: {error_message}")

    return "\n".join(formatted_errors)
