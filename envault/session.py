"""Session management: track when a vault was last unlocked and enforce idle timeouts."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional


class SessionError(Exception):
    """Raised when a session operation fails."""


def _session_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault" / "session.json"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def start_session(vault_dir: Path) -> datetime:
    """Record a new session start timestamp and return it."""
    path = _session_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    started_at = _now_utc()
    data = {"started_at": started_at.isoformat()}
    path.write_text(json.dumps(data))
    return started_at


def read_session(vault_dir: Path) -> Optional[datetime]:
    """Return the session start time, or None if no session exists."""
    path = _session_path(vault_dir)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return datetime.fromisoformat(data["started_at"])
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        raise SessionError(f"Corrupt session file: {exc}") from exc


def clear_session(vault_dir: Path) -> None:
    """Remove the active session file."""
    path = _session_path(vault_dir)
    if path.exists():
        path.unlink()


def is_session_valid(vault_dir: Path, idle_minutes: int) -> bool:
    """Return True if a session exists and has not exceeded *idle_minutes*."""
    if idle_minutes <= 0:
        raise SessionError("idle_minutes must be a positive integer")
    started_at = read_session(vault_dir)
    if started_at is None:
        return False
    age = _now_utc() - started_at
    return age <= timedelta(minutes=idle_minutes)


def format_session(started_at: Optional[datetime]) -> str:
    """Return a human-readable session summary."""
    if started_at is None:
        return "No active session."
    return f"Session started at {started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
