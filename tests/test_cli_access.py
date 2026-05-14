"""Tests for envault.cli_access."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_access import access_group

FP = "ABCDEF1234567890ABCDEF1234567890ABCDEF12"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def _run(runner, vault_dir, *args):
    return runner.invoke(access_group, [*args, "--vault-dir", str(vault_dir)])


def test_grant_success(runner, vault_dir):
    result = _run(runner, vault_dir, "grant", FP, "read")
    assert result.exit_code == 0
    assert "Granted read" in result.output


def test_grant_invalid_level(runner, vault_dir):
    result = _run(runner, vault_dir, "grant", FP, "superuser")
    assert result.exit_code != 0


def test_revoke_existing(runner, vault_dir):
    _run(runner, vault_dir, "grant", FP, "write")
    result = _run(runner, vault_dir, "revoke", FP)
    assert result.exit_code == 0
    assert "revoked" in result.output


def test_revoke_absent(runner, vault_dir):
    result = _run(runner, vault_dir, "revoke", FP)
    assert result.exit_code == 0
    assert "No entry" in result.output


def test_show_no_entry(runner, vault_dir):
    result = _run(runner, vault_dir, "show", FP)
    assert result.exit_code == 0
    assert "no access" in result.output


def test_show_entry(runner, vault_dir):
    _run(runner, vault_dir, "grant", FP, "admin")
    result = _run(runner, vault_dir, "show", FP)
    assert result.exit_code == 0
    assert "admin" in result.output


def test_list_empty(runner, vault_dir):
    result = _run(runner, vault_dir, "list")
    assert result.exit_code == 0
    assert "No access entries" in result.output


def test_list_shows_entries(runner, vault_dir):
    _run(runner, vault_dir, "grant", FP, "write")
    result = _run(runner, vault_dir, "list")
    assert FP in result.output
    assert "write" in result.output


def test_check_passes(runner, vault_dir):
    _run(runner, vault_dir, "grant", FP, "admin")
    result = _run(runner, vault_dir, "check", FP, "write")
    assert result.exit_code == 0
    assert "has write access" in result.output


def test_check_fails(runner, vault_dir):
    _run(runner, vault_dir, "grant", FP, "read")
    result = _run(runner, vault_dir, "check", FP, "admin")
    assert result.exit_code != 0
    assert "does NOT" in result.output
