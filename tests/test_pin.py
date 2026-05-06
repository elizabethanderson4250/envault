"""Tests for envault.pin and envault.cli_pin."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.pin import (
    PinError,
    create_pin,
    delete_pin,
    format_pin,
    read_pin,
    verify_pin,
)
from envault.cli_pin import pin_group


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    vault_dir = tmp_path / "vault"
    vault_dir.mkdir()
    return vault_dir


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("KEY=value\nFOO=bar\n")
    return f


# --- unit tests ---

def test_create_pin_writes_file(vault_dir, env_file):
    record = create_pin(vault_dir, env_file)
    pin_file = vault_dir / ".envault-pin"
    assert pin_file.exists()
    data = json.loads(pin_file.read_text())
    assert data["sha256"] == record["sha256"]
    assert data["file"] == env_file.name


def test_create_pin_missing_env_raises(vault_dir, tmp_path):
    with pytest.raises(PinError, match="not found"):
        create_pin(vault_dir, tmp_path / "missing.env")


def test_read_pin_returns_none_when_absent(vault_dir):
    assert read_pin(vault_dir) is None


def test_read_pin_returns_record(vault_dir, env_file):
    create_pin(vault_dir, env_file)
    record = read_pin(vault_dir)
    assert record is not None
    assert "sha256" in record


def test_verify_pin_matches(vault_dir, env_file):
    create_pin(vault_dir, env_file)
    assert verify_pin(vault_dir, env_file) is True


def test_verify_pin_mismatch(vault_dir, env_file):
    create_pin(vault_dir, env_file)
    env_file.write_text("CHANGED=1\n")
    assert verify_pin(vault_dir, env_file) is False


def test_verify_pin_no_pin_raises(vault_dir, env_file):
    with pytest.raises(PinError, match="no pin"):
        verify_pin(vault_dir, env_file)


def test_delete_pin_removes_file(vault_dir, env_file):
    create_pin(vault_dir, env_file)
    assert delete_pin(vault_dir) is True
    assert read_pin(vault_dir) is None


def test_delete_pin_no_file(vault_dir):
    assert delete_pin(vault_dir) is False


def test_format_pin_output(vault_dir, env_file):
    record = create_pin(vault_dir, env_file)
    out = format_pin(record)
    assert ".env" in out
    assert record["sha256"] in out


# --- CLI tests ---

@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_set_pin(runner, vault_dir, env_file):
    result = runner.invoke(pin_group, ["set", str(vault_dir), str(env_file)])
    assert result.exit_code == 0
    assert "Pin created" in result.output


def test_cli_verify_ok(runner, vault_dir, env_file):
    runner.invoke(pin_group, ["set", str(vault_dir), str(env_file)])
    result = runner.invoke(pin_group, ["verify", str(vault_dir), str(env_file)])
    assert result.exit_code == 0
    assert "OK" in result.output


def test_cli_verify_mismatch(runner, vault_dir, env_file):
    runner.invoke(pin_group, ["set", str(vault_dir), str(env_file)])
    env_file.write_text("CHANGED=1\n")
    result = runner.invoke(pin_group, ["verify", str(vault_dir), str(env_file)])
    assert result.exit_code != 0


def test_cli_show_no_pin(runner, vault_dir):
    result = runner.invoke(pin_group, ["show", str(vault_dir)])
    assert result.exit_code == 0
    assert "No pin" in result.output


def test_cli_delete_pin(runner, vault_dir, env_file):
    runner.invoke(pin_group, ["set", str(vault_dir), str(env_file)])
    result = runner.invoke(pin_group, ["delete", str(vault_dir)])
    assert result.exit_code == 0
    assert "deleted" in result.output
