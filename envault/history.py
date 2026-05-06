"""Track and display the history of lock/unlock operations on a vault."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from envault.audit import read_events, format_event

HISTORY_EVENTS = {"lock", "unlock", "rotate", "add_recipient", "remove_recipient"}


class HistoryError(Exception):
    """Raised when history operations fail."""


def filter_events(
    vault_dir: Path,
    event_types: Optional[List[str]] = None,
    limit: Optional[int] = None,
) -> List[dict]:
    """Return audit events filtered by type, newest-first.

    Args:
        vault_dir: Path to the vault directory.
        event_types: Optional list of event type strings to include.
                     Defaults to all HISTORY_EVENTS.
        limit: Maximum number of events to return.

    Returns:
        List of matching event dicts, newest-first.
    """
    types = set(event_types) if event_types else HISTORY_EVENTS
    events = read_events(vault_dir)
    filtered = [e for e in events if e.get("event") in types]
    # read_events returns oldest-first; reverse for newest-first
    filtered = list(reversed(filtered))
    if limit is not None:
        filtered = filtered[:limit]
    return filtered


def format_history(events: List[dict]) -> str:
    """Format a list of history events into a human-readable string.

    Args:
        events: List of event dicts as returned by filter_events.

    Returns:
        Multi-line string, one event per line, or a placeholder if empty.
    """
    if not events:
        return "No history found."
    return "\n".join(format_event(e) for e in events)
