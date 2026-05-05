"""Tests for the envault CLI."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envault.cli import cli
from envault.crypto import GPGError


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_dir(tmp_path):
    """Return a temp directory with a minimal .envault/meta.json."""
    meta_dir = tmp_path / ".envault"
    meta_dir.mkdir()
    (meta_dir / "meta.json").write_text(json.dumps({"recipients": []}))
    return str(tmp_path)


def test_add_recipient_cli(runner, vault_dir):
    result = runner.invoke(cli, ["--vault-dir", vault_dir, "add-recipient", "AABBCCDD"])
    assert result.exit_code == 0
    assert "AABBCCDD" in result.output


def test_list_recipients_empty(runner, vault_dir):
    result = runner.invoke(cli, ["--vault-dir", vault_dir, "list-recipients"])
    assert result.exit_code == 0
    assert "No recipients" in result.output


def test_list_recipients_shows_fingerprints(runner, vault_dir):
    runner.invoke(cli, ["--vault-dir", vault_dir, "add-recipient", "DEADBEEF"])
    result = runner.invoke(cli, ["--vault-dir", vault_dir, "list-recipients"])
    assert "DEADBEEF" in result.output


def test_remove_recipient_cli(runner, vault_dir):
    runner.invoke(cli, ["--vault-dir", vault_dir, "add-recipient", "DEADBEEF"])
    result = runner.invoke(cli, ["--vault-dir", vault_dir, "remove-recipient", "DEADBEEF"])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_lock_success(runner, vault_dir):
    env_path = Path(vault_dir) / ".env"
    env_path.write_text("SECRET=hello")
    with patch("envault.cli.Vault") as MockVault:
        instance = MockVault.return_value
        instance.lock.return_value = None
        result = runner.invoke(cli, ["--vault-dir", vault_dir, "lock", "--env-file", str(env_path)])
    assert result.exit_code == 0
    assert "locked" in result.output


def test_lock_gpg_error(runner, vault_dir):
    with patch("envault.cli.Vault") as MockVault:
        instance = MockVault.return_value
        instance.lock.side_effect = GPGError("gpg failed")
        result = runner.invoke(cli, ["--vault-dir", vault_dir, "lock"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_unlock_success(runner, vault_dir):
    with patch("envault.cli.Vault") as MockVault:
        instance = MockVault.return_value
        instance.unlock.return_value = None
        result = runner.invoke(cli, ["--vault-dir", vault_dir, "unlock"])
    assert result.exit_code == 0
    assert "unlocked" in result.output


def test_list_keys_command(runner):
    with patch("envault.cli.list_secret_keys", return_value=["KEY1", "KEY2"]):
        result = runner.invoke(cli, ["list-keys"])
    assert result.exit_code == 0
    assert "KEY1" in result.output
    assert "KEY2" in result.output


def test_list_keys_empty(runner):
    with patch("envault.cli.list_secret_keys", return_value=[]):
        result = runner.invoke(cli, ["list-keys"])
    assert "No secret keys" in result.output
