"""Backup and restore support for encrypted vault files."""

from __future__ import annotations

import shutil
import time
from pathlib import Path

BACKUP_DIR = ".envault_backups"
_VAULT_FILE = "vault.env.gpg"
_META_FILE = ".vault-meta.json"


class BackupError(Exception):
    """Raised when a backup or restore operation fails."""


def _backup_dir(vault_dir: Path) -> Path:
    return vault_dir / BACKUP_DIR


def _timestamp() -> str:
    return time.strftime("%Y%m%dT%H%M%S")


def create_backup(vault_dir: Path) -> Path:
    """Copy vault files into a timestamped backup directory.

    Returns the path to the created backup directory.
    Raises BackupError if no vault file exists to back up.
    """
    vault_file = vault_dir / _VAULT_FILE
    if not vault_file.exists():
        raise BackupError(f"No vault file found at {vault_file}")

    stamp = _timestamp()
    dest = _backup_dir(vault_dir) / stamp
    dest.mkdir(parents=True, exist_ok=True)

    shutil.copy2(vault_file, dest / _VAULT_FILE)

    meta_file = vault_dir / _META_FILE
    if meta_file.exists():
        shutil.copy2(meta_file, dest / _META_FILE)

    return dest


def list_backups(vault_dir: Path) -> list[Path]:
    """Return backup directories sorted newest-first."""
    bdir = _backup_dir(vault_dir)
    if not bdir.exists():
        return []
    entries = sorted(bdir.iterdir(), reverse=True)
    return [e for e in entries if e.is_dir()]


def restore_backup(vault_dir: Path, backup_path: Path) -> None:
    """Restore vault files from *backup_path* into *vault_dir*.

    Raises BackupError if the backup directory or vault file is missing.
    """
    src_vault = backup_path / _VAULT_FILE
    if not src_vault.exists():
        raise BackupError(f"Backup at {backup_path} contains no vault file")

    shutil.copy2(src_vault, vault_dir / _VAULT_FILE)

    src_meta = backup_path / _META_FILE
    if src_meta.exists():
        shutil.copy2(src_meta, vault_dir / _META_FILE)


def delete_backup(backup_path: Path) -> None:
    """Remove a backup directory entirely.

    Raises BackupError if the path does not exist.
    """
    if not backup_path.exists():
        raise BackupError(f"Backup not found: {backup_path}")
    shutil.rmtree(backup_path)
