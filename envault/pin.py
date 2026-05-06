"""Pin management: lock a vault to a specific .env file checksum."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Optional

PIN_FILENAME = ".envault-pin"


class PinError(Exception):
    """Raised when a pin operation fails."""


def _pin_path(vault_dir: Path) -> Path:
    return vault_dir / PIN_FILENAME


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def create_pin(vault_dir: Path, env_file: Path) -> dict:
    """Create a pin for *env_file* inside *vault_dir*.

    Returns the pin record that was written.
    """
    if not env_file.exists():
        raise PinError(f"env file not found: {env_file}")

    checksum = _sha256_file(env_file)
    record = {
        "file": env_file.name,
        "sha256": checksum,
    }
    _pin_path(vault_dir).write_text(json.dumps(record, indent=2))
    return record


def read_pin(vault_dir: Path) -> Optional[dict]:
    """Return the stored pin record, or *None* if no pin exists."""
    p = _pin_path(vault_dir)
    if not p.exists():
        return None
    return json.loads(p.read_text())


def verify_pin(vault_dir: Path, env_file: Path) -> bool:
    """Return *True* if *env_file* matches the stored pin checksum."""
    record = read_pin(vault_dir)
    if record is None:
        raise PinError("no pin found in vault directory")
    if not env_file.exists():
        raise PinError(f"env file not found: {env_file}")
    return _sha256_file(env_file) == record["sha256"]


def delete_pin(vault_dir: Path) -> bool:
    """Remove the pin file.  Returns *True* if a file was deleted."""
    p = _pin_path(vault_dir)
    if p.exists():
        p.unlink()
        return True
    return False


def format_pin(record: dict) -> str:
    """Return a human-readable summary of a pin record."""
    return f"Pinned file : {record['file']}\nSHA-256     : {record['sha256']}"
