"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
# ruff: noqa: T201

import asyncio
import re
import sys
from collections.abc import Callable
from typing import Any


def check_python_version() -> None:
    """Check if Python version meets minimum requirements."""
    required_version = (3, 12)
    current_version = sys.version_info[:2]

    if current_version < required_version:
        print("=" * 60)
        print("PYTHON VERSION ERROR")
        print("=" * 60)
        print(f"This application requires Python {required_version[0]}.{required_version[1]} or higher.")
        print(f"You are currently using Python {current_version[0]}.{current_version[1]}")
        print()
        print("Please upgrade your Python installation:")
        print("- Visit https://www.python.org/downloads/")
        print("- Or use your system's package manager")
        print("- Or use virtual environments to install a newer version")
        print("=" * 60)
        sys.exit(1)

def to_snake_case(text: str) -> str:
    """Convert text to snake_case.

    This function replaces spaces and other separators with underscores,
    converts the text to lowercase, and removes leading/trailing underscores.

    Args:
        text: The input text to convert.

    Returns:
        The converted text in snake_case.
    """
    # Replace spaces and other separators with underscores
    text = re.sub(r"[\s\-\.]+", "_", text)
    # Insert underscore before uppercase letters (except at the start)
    text = re.sub(r"(?<!^)(?=[A-Z])", "_", text)
    # Convert to lowercase and clean up multiple underscores
    text = re.sub(r"_+", "_", text.lower())
    # Remove leading/trailing underscores
    return text.strip("_")

async def run_in_executor[T](func: Callable[..., T], *args: Any) -> T:
    """Run a synchronous function in a thread pool executor.

    This allows CPU-bound synchronous functions to run without blocking
    the asyncio event loop.

    Args:
        func: The synchronous function to run.
        *args: Arguments to pass to the function.

    Returns:
        The result of the function call.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)
