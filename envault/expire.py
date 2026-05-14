"""Expiry management for vault secrets — set and check TTL on .env files."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

EXPIRY_FILENAME = ".expiry.json"


class ExpiryError(Exception):
    """Raised when expiry operations fail."""


def _expiry_path(vault_dir: Path) -> Path:
    return vault_dir / EXPIRY_FILENAME


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def set_expiry(vault_dir: Path, days: int) -> datetime:
    """Set an expiry date *days* from now. Returns the expiry datetime."""
    if days <= 0:
        raise ExpiryError("days must be a positive integer")
    expires_at = _now_utc().replace(microsecond=0)
    from datetime import timedelta
    expires_at = expires_at + timedelta(days=days)
    data = {"expires_at": expires_at.isoformat()}
    _expiry_path(vault_dir).write_text(json.dumps(data))
    return expires_at


def read_expiry(vault_dir: Path) -> Optional[datetime]:
    """Return the stored expiry datetime, or None if not set."""
    path = _expiry_path(vault_dir)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return datetime.fromisoformat(data["expires_at"])
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        raise ExpiryError(f"Corrupt expiry file: {exc}") from exc


def delete_expiry(vault_dir: Path) -> bool:
    """Remove the expiry file. Returns True if it existed."""
    path = _expiry_path(vault_dir)
    if path.exists():
        path.unlink()
        return True
    return False


def is_expired(vault_dir: Path) -> bool:
    """Return True if an expiry is set and has passed."""
    expiry = read_expiry(vault_dir)
    if expiry is None:
        return False
    return _now_utc() >= expiry


def format_expiry(vault_dir: Path) -> str:
    """Return a human-readable expiry status string."""
    expiry = read_expiry(vault_dir)
    if expiry is None:
        return "No expiry set."
    now = _now_utc()
    if now >= expiry:
        return f"EXPIRED on {expiry.strftime('%Y-%m-%d %H:%M:%S UTC')}"
    delta = expiry - now
    days = delta.days
    return f"Expires on {expiry.strftime('%Y-%m-%d %H:%M:%S UTC')} (in {days} day(s))"
