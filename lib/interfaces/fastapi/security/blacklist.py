"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
from pathlib import Path

import orjson


class BlacklistManager:
    """Manages a blacklist of JWT tokens."""

    def __init__(self) -> None:
        """Manages a blacklist of JWT tokens.

        Attributes:
            _blacklisted_tokens: Set of blacklisted JWT tokens for O(1) lookup.
            _file_path: Path to the json file containing blacklisted tokens

        Returns:
            None.
        """
        # Initialize file path and blacklisted tokens set
        self._file_path: Path = Path(__file__).parent / "blacklisted_tokens.json"
        self._blacklisted_tokens: set[str] = set()

    def load_blacklist(self) -> bool:
        """Init blacklisted tokens from JSON file into memory.

        Returns:
            bool: True if loading was successful, False otherwise.
        """
        try:
            # If file path is not set or file does not exist
            if not self._file_path.exists():
                return False

            # Open JSON
            with self._file_path.open("rb") as f:
                # Parse JSON data
                data = orjson.loads(f.read())
                # Store tokens in a set for O(1) lookup
                self._blacklisted_tokens = set(data)

        # JSON parsing error
        except orjson.JSONDecodeError:
            return False
        else:
            return True

    def is_blacklisted(self, token: str) -> bool:
        """Check if a JWT token is blacklisted.

        Args:
            token: The JWT token to check.

        Returns:
            True if blacklisted, False otherwise.
        """
        return token in self._blacklisted_tokens

# Create a singleton instance
blacklist_manager = BlacklistManager()

####################################################################
# Convenience functions that use the singleton
####################################################################

def init_blacklist() -> bool:
    """Load blacklisted tokens from JSON file into memory."""
    return blacklist_manager.load_blacklist()

def reload_blacklist() -> bool:
    """Reload blacklisted tokens from JSON file into memory."""
    return blacklist_manager.load_blacklist()

def is_blacklisted(token: str) -> bool:
    """Check if a JWT token is blacklisted."""
    return blacklist_manager.is_blacklisted(token)
