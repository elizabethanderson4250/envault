"""Tests for envault.status."""

import json
import os
from pathlib import Path

import pytest

from envault.status import VaultStatus, format_status, get_status


@pytest.fixture()
def vault_dir(tmp_path: Path) -> str:
    meta = {"recipients": ["AABBCCDD", "11223344"]}
    (tmp_path / ".envault_meta.json").write_text(json.dumps(meta))
    return str(tmp_path)


def test_get_status_no_files(vault_dir: str) -> None:
    status = get_status(vault_dir)
    assert status.is_locked is False
    assert status.env_file_exists is False
    assert status.recipient_count == 2
    assert status.last_event_type is None


def test_get_status_locked(vault_dir: str) -> None:
    Path(vault_dir, ".env.vault").write_text("encrypted")
    status = get_status(vault_dir)
    assert status.is_locked is True


def test_get_status_env_present(vault_dir: str) -> None:
    Path(vault_dir, ".env").write_text("KEY=val")
    status = get_status(vault_dir)
    assert status.env_file_exists is True


def test_get_status_with_audit_event(vault_dir: str) -> None:
    audit_path = Path(vault_dir) / ".envault_audit.jsonl"
    event = {"event": "lock", "timestamp": "2024-01-01T00:00:00Z", "user": "alice"}
    audit_path.write_text(json.dumps(event) + "\n")
    status = get_status(vault_dir)
    assert status.last_event_type == "lock"
    assert status.last_event_time == "2024-01-01T00:00:00Z"
    assert status.last_event_user == "alice"


def test_format_status_no_events(vault_dir: str) -> None:
    status = get_status(vault_dir)
    output = format_status(status)
    assert "Vault directory" in output
    assert "Recipients      : 2" in output
    assert "Last event      : none" in output


def test_format_status_locked_and_event(vault_dir: str) -> None:
    Path(vault_dir, ".env.vault").write_text("enc")
    audit_path = Path(vault_dir) / ".envault_audit.jsonl"
    event = {"event": "rotate", "timestamp": "2024-06-01T12:00:00Z", "user": "bob"}
    audit_path.write_text(json.dumps(event) + "\n")
    status = get_status(vault_dir)
    output = format_status(status)
    assert "Locked          : yes" in output
    assert "rotate" in output
    assert "bob" in output


def test_vault_status_dataclass_fields(vault_dir: str) -> None:
    status = get_status(vault_dir)
    assert hasattr(status, "vault_dir")
    assert hasattr(status, "is_locked")
    assert hasattr(status, "env_file_exists")
    assert hasattr(status, "recipient_count")
