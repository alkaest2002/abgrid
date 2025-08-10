"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
class ABGridError(Exception):
    """
    Base exception class for AB-Grid application errors.

    Serves as the parent class for all application-specific exceptions,
    providing a common interface for error handling throughout the application.
    """

class FolderNotFoundError(ABGridError):
    """
    Exception raised when a required directory doesn't exist.

    Used specifically for cases where the application expects to find
    an existing folder but it's missing from the file system.
    """

class FolderAlreadyExistsError(ABGridError):
    """
    Exception raised when attempting to create a project that already exists.

    Prevents accidental overwriting of existing project data by failing
    early when duplicate project names are detected.
    """

class InvalidArgumentError(ABGridError):
    """
    Exception raised when command-line arguments are invalid or malformed.

    Handles validation errors for user input including missing required
    arguments, invalid character sets, and constraint violations.
    """
