"""Watch a .env file for changes and trigger re-lock automatically."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional


class WatchError(Exception):
    """Raised when the watcher encounters an unrecoverable error."""


@dataclass
class WatchEvent:
    path: Path
    old_hash: Optional[str]
    new_hash: str
    timestamp: float


def _sha256_file(path: Path) -> str:
    """Return the SHA-256 hex digest of *path*."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _current_hash(path: Path) -> Optional[str]:
    """Return file hash, or None if the file does not exist."""
    if not path.exists():
        return None
    return _sha256_file(path)


def watch(
    env_path: Path,
    on_change: Callable[[WatchEvent], None],
    *,
    interval: float = 1.0,
    max_iterations: Optional[int] = None,
) -> None:
    """Poll *env_path* every *interval* seconds.

    Calls *on_change* with a :class:`WatchEvent` whenever the file content
    changes (including creation and deletion).  Raises :class:`WatchError` if
    *env_path* is not inside a directory that exists.

    Parameters
    ----------
    env_path:
        Path to the ``.env`` file to watch.
    on_change:
        Callback invoked on each detected change.
    interval:
        Polling interval in seconds.
    max_iterations:
        Stop after this many poll cycles (useful for testing; ``None`` means
        run forever).
    """
    if not env_path.parent.exists():
        raise WatchError(f"Parent directory does not exist: {env_path.parent}")

    last_hash: Optional[str] = _current_hash(env_path)
    iterations = 0

    while max_iterations is None or iterations < max_iterations:
        time.sleep(interval)
        current = _current_hash(env_path)
        if current != last_hash:
            event = WatchEvent(
                path=env_path,
                old_hash=last_hash,
                new_hash=current or "",
                timestamp=time.time(),
            )
            on_change(event)
            last_hash = current
        iterations += 1
