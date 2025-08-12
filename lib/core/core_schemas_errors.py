"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""



from typing import Any


class PydanticValidationError(Exception):
    """Custom exception for structured validation errors.

    Raised when validation fails, containing detailed error information
    for each validation failure.

    Attributes:
        errors: List of error dictionaries with location, value, and message.
    """

    def __init__(self, errors: list[dict[str, Any]]):
        """Initialize exception with validation errors.

        Args:
            errors: List of validation error dictionaries. Each dictionary
                contains 'location', 'value_to_blame', and 'error_message' keys.
        """
        self.errors = errors
        error_message = [f"{error['location']}: {error['error_message']}" for error in errors]
        super().__init__("\n".join(error_message))
