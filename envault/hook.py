"""Pre/post hook support for envault operations."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import List, Optional

HOOK_EVENTS = ("pre-lock", "post-lock", "pre-unlock", "post-unlock", "pre-rotate", "post-rotate")


class HookError(Exception):
    """Raised when a hook fails or configuration is invalid."""


def _hook_path(vault_dir: Path) -> Path:
    return vault_dir / ".envault" / "hooks.json"


def _load(vault_dir: Path) -> dict:
    p = _hook_path(vault_dir)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        raise HookError(f"Invalid hooks.json: {exc}") from exc


def _save(vault_dir: Path, data: dict) -> None:
    p = _hook_path(vault_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))


def set_hook(vault_dir: Path, event: str, command: str) -> None:
    """Register *command* to run on *event*."""
    if event not in HOOK_EVENTS:
        raise HookError(f"Unknown event '{event}'. Valid events: {', '.join(HOOK_EVENTS)}")
    data = _load(vault_dir)
    data[event] = command
    _save(vault_dir, data)


def remove_hook(vault_dir: Path, event: str) -> bool:
    """Remove the hook for *event*. Returns True if a hook was removed."""
    data = _load(vault_dir)
    if event not in data:
        return False
    del data[event]
    _save(vault_dir, data)
    return True


def get_hook(vault_dir: Path, event: str) -> Optional[str]:
    """Return the command registered for *event*, or None."""
    return _load(vault_dir).get(event)


def list_hooks(vault_dir: Path) -> dict:
    """Return all registered hooks as {event: command}."""
    return _load(vault_dir)


def run_hook(vault_dir: Path, event: str) -> Optional[int]:
    """Execute the hook for *event* if one is registered.

    Returns the exit code, or None if no hook is configured.
    Raises HookError if the hook exits non-zero.
    """
    command = get_hook(vault_dir, event)
    if command is None:
        return None
    result = subprocess.run(command, shell=True, cwd=str(vault_dir))
    if result.returncode != 0:
        raise HookError(
            f"Hook '{event}' failed with exit code {result.returncode}: {command}"
        )
    return result.returncode
