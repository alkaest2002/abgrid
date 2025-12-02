"""
Author: Pierpaolo Calanna

The code is part of the AB-Grid project and is licensed under the MIT License.
"""
import threading
import time
from pathlib import Path

import orjson


class BlacklistManager:
    """Manages a blacklist of JWT tokens with caching and periodic reloading."""

    def __init__(self, reload_interval_hours: int = 12) -> None:
        """Initialize the blacklist manager.

        Args:
            reload_interval_hours: Hours between automatic reloads (default: 12).

        Attributes:
            _file_path: Path to the JSON file containing blacklisted tokens.
            _blacklisted_tokens: In-memory set of blacklisted tokens.
            _reload_interval_seconds: Interval for automatic reloads in seconds.
            _last_loaded: Timestamp of the last successful load.
            _last_modified: Last modification time of the blacklist file.
            _write_lock: Lock for thread-safe updates to the blacklist.
            _stop_reload: Event to signal stopping the auto-reload thread.
            _reload_thread: Background thread for periodic reloading.
        """
        self._file_path: Path = Path(__file__).parent / "blacklisted_tokens.json"
        self._blacklisted_tokens: set[str] = set()
        self._reload_interval_seconds: float = reload_interval_hours * 3600
        self._last_loaded: float = 0  # Unix timestamp
        self._last_modified: float | None = None
        self._write_lock: threading.Lock = threading.Lock()
        self._stop_reload: threading.Event = threading.Event()
        self._reload_thread: threading.Thread | None = None

    def load_blacklist(self) -> bool:
        """Load blacklisted tokens from JSON file into memory.

        Returns:
            bool: True if loading was successful, False otherwise.
        """
        try:
            # Check if file has changed
            current_mtime = self._file_path.stat().st_mtime
            if self._last_modified == current_mtime:
                return True

            # Read and parse file
            with self._file_path.open("rb") as f:
                new_tokens = set(orjson.loads(f.read()))

            # Atomic swap
            with self._write_lock:
                self._blacklisted_tokens = new_tokens
                self._last_loaded = time.time()
                self._last_modified = current_mtime

        except Exception:
            return False
        else:
            return True


    def is_blacklisted(self, token: str) -> bool:
        """Check if a JWT token is blacklisted (lock-free).

        Args:
            token: The JWT token to check.

        Returns:
            True if blacklisted, False otherwise.
        """
        return token in self._blacklisted_tokens

    def start_auto_reload(self) -> None:
        """Start background thread for automatic periodic reloading."""
        if self._reload_thread and self._reload_thread.is_alive():
            return

        self._stop_reload.clear()
        self._reload_thread = threading.Thread(
            target=self._auto_reload_worker,
            daemon=True,
            name="BlacklistAutoReload"
        )
        self._reload_thread.start()

    def stop_auto_reload(self) -> None:
        """Stop the background auto-reload thread."""
        self._stop_reload.set()
        if self._reload_thread:
            self._reload_thread.join(timeout=5)

    def _auto_reload_worker(self) -> None:
        """Background worker that periodically reloads the blacklist."""
        check_interval = min(3600, max(60, self._reload_interval_seconds / 4))

        while not self._stop_reload.wait(timeout=check_interval):
            if time.time() - self._last_loaded >= self._reload_interval_seconds:
                self.load_blacklist()

    def get_cache_info(self) -> dict:
        """Get information about the current cache state."""
        return {
            "last_loaded_timestamp": self._last_loaded,
            "token_count": len(self._blacklisted_tokens),
            "reload_interval_hours": self._reload_interval_seconds / 3600,
            "seconds_until_next_reload": max(0, self._reload_interval_seconds - (time.time() - self._last_loaded)),
        }


# Singleton instance
blacklist_manager = BlacklistManager(reload_interval_hours=12)


####################################################################
# Convenience functions
####################################################################

def init_blacklist(auto_reload: bool = True) -> bool:
    """Load blacklisted tokens and optionally start auto-reload."""
    success = blacklist_manager.load_blacklist()
    if success and auto_reload:
        blacklist_manager.start_auto_reload()
    return success


def reload_blacklist() -> bool:
    """Manually reload blacklisted tokens."""
    return blacklist_manager.load_blacklist()


def is_blacklisted(token: str) -> bool:
    """Check if a JWT token is blacklisted."""
    return blacklist_manager.is_blacklisted(token)


def stop_auto_reload() -> None:
    """Stop automatic periodic reloading."""
    blacklist_manager.stop_auto_reload()


def get_cache_info() -> dict:
    """Get cache state information."""
    return blacklist_manager.get_cache_info()
