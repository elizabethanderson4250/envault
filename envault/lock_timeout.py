"""Lock timeout: auto-lock a vault after a configurable idle period."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional


class LockTimeoutError(Exception):
    """Raised when lock-timeout operations fail."""


def _timeout_path(vault_dir: Path) -> Path:
    return vault_dir / ".lock_timeout.json"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def set_timeout(vault_dir: Path, minutes: int) -> datetime:
    """Record a lock-timeout of *minutes* minutes from now.

    Returns the datetime at which the vault should be locked.
    """
    if minutes <= 0:
        raise LockTimeoutError("timeout minutes must be a positive integer")

    expires_at = _now_utc() + timedelta(minutes=minutes)
    data = {
        "minutes": minutes,
        "expires_at": expires_at.isoformat(),
    }
    _timeout_path(vault_dir).write_text(json.dumps(data))
    return expires_at


def read_timeout(vault_dir: Path) -> Optional[dict]:
    """Return the stored timeout dict, or None if not set."""
    path = _timeout_path(vault_dir)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise LockTimeoutError(f"corrupt timeout file: {exc}") from exc


def is_expired(vault_dir: Path) -> bool:
    """Return True if the lock timeout has passed."""
    data = read_timeout(vault_dir)
    if data is None:
        return False
    expires_at = datetime.fromisoformat(data["expires_at"])
    return _now_utc() >= expires_at


def clear_timeout(vault_dir: Path) -> bool:
    """Remove the timeout file.  Returns True if a file was removed."""
    path = _timeout_path(vault_dir)
    if path.exists():
        path.unlink()
        return True
    return False


def format_timeout(data: dict) -> str:
    """Human-readable description of a timeout record."""
    expires_at = datetime.fromisoformat(data["expires_at"])
    now = _now_utc()
    if now >= expires_at:
        return f"EXPIRED  (was {data['minutes']} min, expired {expires_at.isoformat()})"
    remaining = int((expires_at - now).total_seconds() // 60)
    return f"active   ({data['minutes']} min, ~{remaining} min remaining, expires {expires_at.isoformat()})"
