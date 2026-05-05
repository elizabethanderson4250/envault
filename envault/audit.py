"""Audit log for envault vault operations."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

AUDIT_FILENAME = ".envault_audit.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _audit_path(vault_dir: Path) -> Path:
    return vault_dir / AUDIT_FILENAME


def record_event(
    vault_dir: Path,
    action: str,
    actor: Optional[str] = None,
    details: Optional[dict] = None,
) -> dict:
    """Append an audit event to the vault's audit log.

    Args:
        vault_dir: Path to the vault directory.
        action: Short action name, e.g. 'lock', 'unlock', 'add_recipient'.
        actor: GPG fingerprint or identifier of the user performing the action.
        details: Optional extra key/value pairs to store with the event.

    Returns:
        The newly created event dict.
    """
    path = _audit_path(vault_dir)
    events: List[dict] = []
    if path.exists():
        try:
            events = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            events = []

    event = {
        "timestamp": _now_iso(),
        "action": action,
        "actor": actor,
        "details": details or {},
    }
    events.append(event)
    path.write_text(json.dumps(events, indent=2), encoding="utf-8")
    return event


def read_events(vault_dir: Path) -> List[dict]:
    """Return all recorded audit events for a vault, oldest first."""
    path = _audit_path(vault_dir)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def format_event(event: dict) -> str:
    """Return a human-readable single-line representation of an event."""
    ts = event.get("timestamp", "unknown")
    action = event.get("action", "unknown")
    actor = event.get("actor") or "unknown"
    details = event.get("details", {})
    detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
    base = f"[{ts}] {action} by {actor}"
    return f"{base} ({detail_str})" if detail_str else base
