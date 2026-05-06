"""Tests for the 'envault export run' CLI command."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from envault.cli_export import export_group

SAMPLE_ENV = "DB_HOST=localhost\nDB_PORT=5432\nSECRET=abc\n"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_dir(tmp_path):
    (tmp_path / "vault.env.gpg").write_bytes(b"encrypted")
    (tmp_path / ".envault_meta.json").write_text('{"recipients": []}', encoding="utf-8")
    return tmp_path


def _patch_decrypt(return_value=SAMPLE_ENV):
    return patch("envault.cli_export.decrypt", return_value=return_value)


def test_export_stdout_dotenv(runner, vault_dir):
    with _patch_decrypt():
        result = runner.invoke(export_group, ["run", str(vault_dir), "--format", "dotenv"])
    assert result.exit_code == 0
    assert 'DB_HOST="localhost"' in result.output


def test_export_stdout_json(runner, vault_dir):
    with _patch_decrypt():
        result = runner.invoke(export_group, ["run", str(vault_dir), "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["DB_HOST"] == "localhost"


def test_export_stdout_shell(runner, vault_dir):
    with _patch_decrypt():
        result = runner.invoke(export_group, ["run", str(vault_dir), "--format", "shell"])
    assert result.exit_code == 0
    assert "export DB_HOST=" in result.output


def test_export_to_file(runner, vault_dir, tmp_path):
    out_file = tmp_path / "out.json"
    with _patch_decrypt():
        result = runner.invoke(
            export_group,
            ["run", str(vault_dir), "--format", "json", "--output", str(out_file)],
        )
    assert result.exit_code == 0
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert data["DB_HOST"] == "localhost"


def test_export_missing_vault_file(runner, tmp_path):
    (tmp_path / ".envault_meta.json").write_text('{"recipients": []}', encoding="utf-8")
    result = runner.invoke(export_group, ["run", str(tmp_path)])
    assert result.exit_code != 0
    assert "vault file not found" in result.output


def test_export_gpg_error(runner, vault_dir):
    from envault.crypto import GPGError
    with patch("envault.cli_export.decrypt", side_effect=GPGError("bad key")):
        result = runner.invoke(export_group, ["run", str(vault_dir)])
    assert result.exit_code != 0
    assert "Decryption failed" in result.output


def test_export_records_audit_event(runner, vault_dir):
    from envault.audit import read_events
    with _patch_decrypt():
        runner.invoke(export_group, ["run", str(vault_dir), "--format", "json"])
    events = read_events(vault_dir)
    assert any(e["event"] == "export" for e in events)
