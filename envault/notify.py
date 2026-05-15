"""Notification hooks for envault events (e.g. post-lock, post-rotate)."""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class NotifyError(Exception):
    """Raised when a notification action fails."""


_VALID_CHANNELS = ("stdout", "exec", "file")


@dataclass
class NotifyConfig:
    channel: str  # 'stdout' | 'exec' | 'file'
    target: str   # command path, file path, or ignored for stdout
    events: List[str] = field(default_factory=list)  # empty = all events


def _config_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault" / "notify.json"


def load_config(vault_dir: Path) -> Optional[NotifyConfig]:
    """Return NotifyConfig if configured, else None."""
    path = _config_path(vault_dir)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise NotifyError(f"Failed to read notify config: {exc}") from exc
    return NotifyConfig(
        channel=data.get("channel", "stdout"),
        target=data.get("target", ""),
        events=data.get("events", []),
    )


def save_config(vault_dir: Path, config: NotifyConfig) -> None:
    """Persist a NotifyConfig to disk."""
    if config.channel not in _VALID_CHANNELS:
        raise NotifyError(f"Invalid channel '{config.channel}'; choose from {_VALID_CHANNELS}")
    path = _config_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "channel": config.channel,
        "target": config.target,
        "events": config.events,
    }, indent=2))


def send_notification(vault_dir: Path, event: str, message: str) -> bool:
    """Send a notification for *event* if configured.  Returns True if sent."""
    config = load_config(vault_dir)
    if config is None:
        return False
    if config.events and event not in config.events:
        return False

    payload = f"[envault:{event}] {message}"

    if config.channel == "stdout":
        print(payload)
    elif config.channel == "file":
        target = Path(config.target)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a") as fh:
            fh.write(payload + "\n")
    elif config.channel == "exec":
        try:
            subprocess.run(
                [config.target, event, message],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as exc:
            raise NotifyError(f"Notification command failed: {exc}") from exc
    return True
