"""Manage plaintext .env snapshots used as a baseline for diffs."""

from __future__ import annotations

import shutil
from pathlib import Path

SNAPSHOT_FILENAME = ".env.snapshot"


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


def snapshot_path(vault_dir: str | Path) -> Path:
    """Return the path to the snapshot file inside *vault_dir*."""
    return Path(vault_dir) / SNAPSHOT_FILENAME


def create_snapshot(env_path: str | Path, vault_dir: str | Path) -> Path:
    """Copy *env_path* to the vault snapshot location.

    Returns the path of the created snapshot.
    Raises *SnapshotError* if the source file does not exist.
    """
    src = Path(env_path)
    if not src.exists():
        raise SnapshotError(f".env file not found: {src}")

    dest = snapshot_path(vault_dir)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return dest


def read_snapshot(vault_dir: str | Path) -> str:
    """Read and return the contents of the snapshot file.

    Raises *SnapshotError* if no snapshot exists.
    """
    path = snapshot_path(vault_dir)
    if not path.exists():
        raise SnapshotError(f"No snapshot found at {path}. Run 'envault snapshot create' first.")
    return path.read_text(encoding="utf-8")


def delete_snapshot(vault_dir: str | Path) -> bool:
    """Remove the snapshot file if it exists. Returns True if deleted."""
    path = snapshot_path(vault_dir)
    if path.exists():
        path.unlink()
        return True
    return False


def snapshot_exists(vault_dir: str | Path) -> bool:
    """Return True if a snapshot file exists in *vault_dir*."""
    return snapshot_path(vault_dir).exists()
