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
        self._blacklisted_tokens: set[str] = set()
        self._file_path: Path | None = None

    def load_blacklist(self, file_path: Path) -> None:
        """
        Load blacklisted tokens from JSON file into memory.

        Args:
            file_path: Path to the JSON file containing blacklisted tokens.

        Returns:
            None.
        """
        # Store file path for reload
        self._file_path = file_path

        # If file doen not exist
        if not file_path.exists():
            # Set _blacklisted_tokens to empty set
            self._blacklisted_tokens = set()
            return

        try:
            # Read JSON file and store tokens in a set for O(1) lookup
            with file_path.open("rb") as f:
                data = orjson.loads(f.read())
                self._blacklisted_tokens = set(data)

        # If file is malformed
        except orjson.JSONDecodeError:
            # Set _blacklisted_tokens to empty set
            self._blacklisted_tokens = set()

    def reload_blacklist(self) -> bool:
        """Reload blacklist from the stored file path.

        Returns:
            bool: True if reload was successful, False otherwise.
        """
        # Ensure file path is set
        if not self._file_path:
            return False

        try:
            # Reload from the stored file path
            self.load_blacklist(self._file_path)
        except Exception:
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

def load_blacklist(file_path: Path) -> None:
    """Load blacklisted tokens from JSON file into memory."""
    blacklist_manager.load_blacklist(file_path)

def reload_blacklist() -> bool:
    """Reload blacklisted tokens from JSON file into memory."""
    return blacklist_manager.reload_blacklist()

def is_blacklisted(token: str) -> bool:
    """Check if a JWT token is blacklisted."""
    return blacklist_manager.is_blacklisted(token)
