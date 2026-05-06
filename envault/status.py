"""Vault status reporting: summarizes lock state, recipients, and last audit event."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from envault.audit import read_events
from envault.vault import Vault


@dataclass
class VaultStatus:
    vault_dir: str
    is_locked: bool
    env_file_exists: bool
    recipient_count: int
    last_event_type: Optional[str]
    last_event_time: Optional[str]
    last_event_user: Optional[str]


def get_status(vault_dir: str) -> VaultStatus:
    """Return a VaultStatus snapshot for the given vault directory."""
    vault = Vault(vault_dir)
    vault_path = Path(vault_dir)

    locked_file = vault_path / ".env.vault"
    env_file = vault_path / ".env"

    is_locked = locked_file.exists()
    env_file_exists = env_file.exists()
    recipients = vault.get_recipients()

    events = read_events(vault_dir)
    last_event: Optional[dict] = events[0] if events else None

    return VaultStatus(
        vault_dir=vault_dir,
        is_locked=is_locked,
        env_file_exists=env_file_exists,
        recipient_count=len(recipients),
        last_event_type=last_event.get("event") if last_event else None,
        last_event_time=last_event.get("timestamp") if last_event else None,
        last_event_user=last_event.get("user") if last_event else None,
    )


def format_status(status: VaultStatus) -> str:
    """Return a human-readable summary of the vault status."""
    lines = [
        f"Vault directory : {status.vault_dir}",
        f"Locked          : {'yes' if status.is_locked else 'no'}",
        f".env present    : {'yes' if status.env_file_exists else 'no'}",
        f"Recipients      : {status.recipient_count}",
    ]
    if status.last_event_type:
        lines.append(f"Last event      : {status.last_event_type} at {status.last_event_time} by {status.last_event_user}")
    else:
        lines.append("Last event      : none")
    return "\n".join(lines)
