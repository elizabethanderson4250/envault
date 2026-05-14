"""Tests for envault.ttl and envault.cli_ttl."""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envault.ttl import (
    TTLError,
    set_ttl,
    read_ttl,
    is_expired,
    clear_ttl,
    remaining_seconds,
)
from envault.cli_ttl import ttl_group


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


# ---------------------------------------------------------------------------
# Unit tests — envault.ttl
# ---------------------------------------------------------------------------

def test_set_ttl_creates_file(vault_dir):
    set_ttl(vault_dir, 60)
    assert (vault_dir / ".envault" / "ttl.json").exists()


def test_set_ttl_returns_future_datetime(vault_dir):
    expires = set_ttl(vault_dir, 120)
    assert expires > datetime.now(timezone.utc)


def test_set_ttl_zero_raises(vault_dir):
    with pytest.raises(TTLError):
        set_ttl(vault_dir, 0)


def test_set_ttl_negative_raises(vault_dir):
    with pytest.raises(TTLError):
        set_ttl(vault_dir, -10)


def test_read_ttl_returns_none_when_absent(vault_dir):
    assert read_ttl(vault_dir) is None


def test_read_ttl_returns_record(vault_dir):
    set_ttl(vault_dir, 30)
    record = read_ttl(vault_dir)
    assert record is not None
    assert record["seconds"] == 30
    assert "expires_at" in record


def test_read_ttl_corrupt_file_raises(vault_dir):
    ttl_file = vault_dir / ".envault" / "ttl.json"
    ttl_file.parent.mkdir(parents=True, exist_ok=True)
    ttl_file.write_text("not-json")
    with pytest.raises(TTLError, match="Corrupt"):
        read_ttl(vault_dir)


def test_is_expired_false_for_future(vault_dir):
    set_ttl(vault_dir, 3600)
    assert is_expired(vault_dir) is False


def test_is_expired_true_for_past(vault_dir):
    past = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    ttl_file = vault_dir / ".envault" / "ttl.json"
    ttl_file.parent.mkdir(parents=True, exist_ok=True)
    ttl_file.write_text(json.dumps({"seconds": 1, "created_at": past, "expires_at": past}))
    assert is_expired(vault_dir) is True


def test_is_expired_false_when_no_record(vault_dir):
    assert is_expired(vault_dir) is False


def test_clear_ttl_removes_file(vault_dir):
    set_ttl(vault_dir, 60)
    assert clear_ttl(vault_dir) is True
    assert not (vault_dir / ".envault" / "ttl.json").exists()


def test_clear_ttl_returns_false_when_absent(vault_dir):
    assert clear_ttl(vault_dir) is False


def test_remaining_seconds_none_when_absent(vault_dir):
    assert remaining_seconds(vault_dir) is None


def test_remaining_seconds_positive(vault_dir):
    set_ttl(vault_dir, 3600)
    secs = remaining_seconds(vault_dir)
    assert secs is not None and secs > 0


# ---------------------------------------------------------------------------
# CLI tests — envault.cli_ttl
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_set_creates_ttl(runner, vault_dir):
    result = runner.invoke(ttl_group, ["set", str(vault_dir), "300"])
    assert result.exit_code == 0
    assert "expires at" in result.output


def test_cli_set_invalid_seconds(runner, vault_dir):
    result = runner.invoke(ttl_group, ["set", str(vault_dir), "0"])
    assert result.exit_code != 0


def test_cli_show_no_ttl(runner, vault_dir):
    result = runner.invoke(ttl_group, ["show", str(vault_dir)])
    assert result.exit_code == 0
    assert "No TTL set" in result.output


def test_cli_show_with_ttl(runner, vault_dir):
    set_ttl(vault_dir, 3600)
    result = runner.invoke(ttl_group, ["show", str(vault_dir)])
    assert result.exit_code == 0
    assert "Expires at" in result.output


def test_cli_check_no_ttl_exits_nonzero(runner, vault_dir):
    result = runner.invoke(ttl_group, ["check", str(vault_dir)])
    assert result.exit_code != 0


def test_cli_check_valid_ttl(runner, vault_dir):
    set_ttl(vault_dir, 3600)
    result = runner.invoke(ttl_group, ["check", str(vault_dir)])
    assert result.exit_code == 0
    assert "valid" in result.output


def test_cli_clear_removes(runner, vault_dir):
    set_ttl(vault_dir, 60)
    result = runner.invoke(ttl_group, ["clear", str(vault_dir)])
    assert result.exit_code == 0
    assert "cleared" in result.output


def test_cli_clear_no_record(runner, vault_dir):
    result = runner.invoke(ttl_group, ["clear", str(vault_dir)])
    assert result.exit_code == 0
    assert "No TTL record" in result.output
