"""Access control: per-recipient read/write permissions for a vault."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

ACCESS_FILENAME = ".envault_access.json"

VALID_LEVELS = ("read", "write", "admin")


class AccessError(Exception):
    """Raised when an access-control operation fails."""


def _access_path(vault_dir: Path) -> Path:
    return vault_dir / ACCESS_FILENAME


def _load(vault_dir: Path) -> Dict[str, str]:
    path = _access_path(vault_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise AccessError(f"Corrupt access file: {exc}") from exc
    if not isinstance(data, dict):
        raise AccessError("Access file must contain a JSON object.")
    return data


def _save(vault_dir: Path, mapping: Dict[str, str]) -> None:
    _access_path(vault_dir).write_text(json.dumps(mapping, indent=2))


def set_access(vault_dir: Path, fingerprint: str, level: str) -> None:
    """Grant *fingerprint* the given access *level* (read/write/admin)."""
    if level not in VALID_LEVELS:
        raise AccessError(f"Invalid level {level!r}. Choose from: {VALID_LEVELS}")
    fp = fingerprint.upper().replace(" ", "")
    mapping = _load(vault_dir)
    mapping[fp] = level
    _save(vault_dir, mapping)


def get_access(vault_dir: Path, fingerprint: str) -> Optional[str]:
    """Return the access level for *fingerprint*, or None if not set."""
    fp = fingerprint.upper().replace(" ", "")
    return _load(vault_dir).get(fp)


def revoke_access(vault_dir: Path, fingerprint: str) -> bool:
    """Remove *fingerprint* from the access list. Returns True if it existed."""
    fp = fingerprint.upper().replace(" ", "")
    mapping = _load(vault_dir)
    if fp not in mapping:
        return False
    del mapping[fp]
    _save(vault_dir, mapping)
    return True


def list_access(vault_dir: Path) -> List[Dict[str, str]]:
    """Return all fingerprint/level pairs sorted by fingerprint."""
    mapping = _load(vault_dir)
    return [
        {"fingerprint": fp, "level": lvl}
        for fp, lvl in sorted(mapping.items())
    ]


def check_access(vault_dir: Path, fingerprint: str, required: str) -> bool:
    """Return True if *fingerprint* has at least *required* level."""
    order = {lvl: i for i, lvl in enumerate(VALID_LEVELS)}
    if required not in order:
        raise AccessError(f"Unknown required level: {required!r}")
    fp = fingerprint.upper().replace(" ", "")
    current = _load(vault_dir).get(fp)
    if current is None:
        return False
    return order[current] >= order[required]
