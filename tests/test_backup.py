"""Tests for envault.backup and envault.cli_backup."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.backup import (
    BACKUP_DIR,
    BackupError,
    create_backup,
    delete_backup,
    list_backups,
    restore_backup,
)
from envault.cli_backup import backup_group

_VAULT_FILE = "vault.env.gpg"
_META_FILE = ".vault-meta.json"


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def vault_with_files(vault_dir: Path) -> Path:
    (vault_dir / _VAULT_FILE).write_bytes(b"encrypted")
    (vault_dir / _META_FILE).write_text('{"recipients": []}', encoding="utf-8")
    return vault_dir


# --- unit tests ---

def test_create_backup_returns_path(vault_with_files: Path) -> None:
    dest = create_backup(vault_with_files)
    assert dest.is_dir()
    assert (dest / _VAULT_FILE).exists()


def test_create_backup_copies_meta(vault_with_files: Path) -> None:
    dest = create_backup(vault_with_files)
    assert (dest / _META_FILE).exists()


def test_create_backup_no_vault_raises(vault_dir: Path) -> None:
    with pytest.raises(BackupError, match="No vault file"):
        create_backup(vault_dir)


def test_list_backups_empty(vault_dir: Path) -> None:
    assert list_backups(vault_dir) == []


def test_list_backups_newest_first(vault_with_files: Path) -> None:
    create_backup(vault_with_files)
    import time; time.sleep(0.01)
    create_backup(vault_with_files)
    backups = list_backups(vault_with_files)
    assert len(backups) == 2
    assert backups[0].name > backups[1].name


def test_restore_backup_overwrites(vault_with_files: Path) -> None:
    dest = create_backup(vault_with_files)
    (vault_with_files / _VAULT_FILE).write_bytes(b"changed")
    restore_backup(vault_with_files, dest)
    assert (vault_with_files / _VAULT_FILE).read_bytes() == b"encrypted"


def test_restore_backup_missing_raises(vault_dir: Path, tmp_path: Path) -> None:
    empty = tmp_path / "ghost"
    empty.mkdir()
    with pytest.raises(BackupError, match="no vault file"):
        restore_backup(vault_dir, empty)


def test_delete_backup_removes_dir(vault_with_files: Path) -> None:
    dest = create_backup(vault_with_files)
    delete_backup(dest)
    assert not dest.exists()


def test_delete_backup_missing_raises(vault_dir: Path) -> None:
    with pytest.raises(BackupError, match="not found"):
        delete_backup(vault_dir / "ghost")


# --- CLI tests ---

@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_cli_create_success(runner: CliRunner, vault_with_files: Path) -> None:
    result = runner.invoke(backup_group, ["create", str(vault_with_files)])
    assert result.exit_code == 0
    assert "Backup created" in result.output


def test_cli_create_no_vault(runner: CliRunner, vault_dir: Path) -> None:
    result = runner.invoke(backup_group, ["create", str(vault_dir)])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_cli_list_empty(runner: CliRunner, vault_dir: Path) -> None:
    result = runner.invoke(backup_group, ["list", str(vault_dir)])
    assert result.exit_code == 0
    assert "No backups" in result.output


def test_cli_list_shows_entries(runner: CliRunner, vault_with_files: Path) -> None:
    create_backup(vault_with_files)
    result = runner.invoke(backup_group, ["list", str(vault_with_files)])
    assert result.exit_code == 0
    assert len(result.output.strip().splitlines()) == 1


def test_cli_restore_success(runner: CliRunner, vault_with_files: Path) -> None:
    dest = create_backup(vault_with_files)
    result = runner.invoke(
        backup_group, ["restore", str(vault_with_files), dest.name]
    )
    assert result.exit_code == 0
    assert "Restored" in result.output
