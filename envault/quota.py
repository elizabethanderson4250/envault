"""Quota management: enforce max number of keys in a .env file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

QUOTA_FILENAME = ".envault_quota.json"
DEFAULT_MAX_KEYS = 100


class QuotaError(Exception):
    """Raised when a quota operation fails."""


class QuotaResult:
    def __init__(self, key_count: int, max_keys: int) -> None:
        self.key_count = key_count
        self.max_keys = max_keys

    @property
    def exceeded(self) -> bool:
        return self.key_count > self.max_keys

    @property
    def remaining(self) -> int:
        return max(0, self.max_keys - self.key_count)


def _quota_path(vault_dir: Path) -> Path:
    return vault_dir / QUOTA_FILENAME


def set_quota(vault_dir: Path, max_keys: int) -> None:
    """Persist a max-keys quota for the given vault directory."""
    if max_keys < 1:
        raise QuotaError("max_keys must be at least 1")
    data = {"max_keys": max_keys}
    _quota_path(vault_dir).write_text(json.dumps(data))


def read_quota(vault_dir: Path) -> int:
    """Return the configured max_keys, or the default if not set."""
    path = _quota_path(vault_dir)
    if not path.exists():
        return DEFAULT_MAX_KEYS
    try:
        data = json.loads(path.read_text())
        return int(data["max_keys"])
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        raise QuotaError(f"Corrupt quota file: {exc}") from exc


def delete_quota(vault_dir: Path) -> bool:
    """Remove the quota file. Returns True if it existed."""
    path = _quota_path(vault_dir)
    if path.exists():
        path.unlink()
        return True
    return False


def _count_keys(env_file: Path) -> int:
    """Count non-blank, non-comment KEY=... lines."""
    if not env_file.exists():
        raise QuotaError(f"Env file not found: {env_file}")
    count = 0
    for line in env_file.read_text().splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            count += 1
    return count


def check_quota(vault_dir: Path, env_file: Path) -> QuotaResult:
    """Check whether the env file exceeds the configured quota."""
    max_keys = read_quota(vault_dir)
    key_count = _count_keys(env_file)
    return QuotaResult(key_count=key_count, max_keys=max_keys)


def format_quota(result: QuotaResult) -> str:
    status = "EXCEEDED" if result.exceeded else "OK"
    return (
        f"Keys: {result.key_count} / {result.max_keys}  "
        f"[{status}]  remaining: {result.remaining}"
    )
