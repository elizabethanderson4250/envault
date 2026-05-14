"""TTL (time-to-live) enforcement for decrypted .env files.

After unlocking a vault, a TTL record can be written so that the
plaintext .env is considered stale after a configurable number of
seconds.  The CLI can then warn or auto-remove the file.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional


class TTLError(Exception):
    """Raised for TTL-related failures."""


def _ttl_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault" / "ttl.json"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def set_ttl(vault_dir: Path, seconds: int) -> datetime:
    """Record a TTL starting from now.  Returns the expiry datetime."""
    if seconds <= 0:
        raise TTLError("TTL must be a positive number of seconds.")
    ttl_file = _ttl_path(vault_dir)
    ttl_file.parent.mkdir(parents=True, exist_ok=True)
    expires_at = _now_utc() + timedelta(seconds=seconds)
    data = {
        "seconds": seconds,
        "created_at": _now_utc().isoformat(),
        "expires_at": expires_at.isoformat(),
    }
    ttl_file.write_text(json.dumps(data, indent=2))
    return expires_at


def read_ttl(vault_dir: Path) -> Optional[dict]:
    """Return the stored TTL record, or None if absent."""
    ttl_file = _ttl_path(vault_dir)
    if not ttl_file.exists():
        return None
    try:
        return json.loads(ttl_file.read_text())
    except json.JSONDecodeError as exc:
        raise TTLError(f"Corrupt TTL file: {exc}") from exc


def is_expired(vault_dir: Path) -> bool:
    """Return True if a TTL record exists and has passed."""
    record = read_ttl(vault_dir)
    if record is None:
        return False
    expires_at = datetime.fromisoformat(record["expires_at"])
    return _now_utc() >= expires_at


def clear_ttl(vault_dir: Path) -> bool:
    """Remove the TTL record.  Returns True if a file was deleted."""
    ttl_file = _ttl_path(vault_dir)
    if ttl_file.exists():
        ttl_file.unlink()
        return True
    return False


def remaining_seconds(vault_dir: Path) -> Optional[float]:
    """Return seconds until expiry, or None if no TTL is set.
    Returns a negative value if already expired.
    """
    record = read_ttl(vault_dir)
    if record is None:
        return None
    expires_at = datetime.fromisoformat(record["expires_at"])
    delta = (expires_at - _now_utc()).total_seconds()
    return delta
