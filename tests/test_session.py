"""Tests for envault.session and envault.cli_session."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envault.session import (
    SessionError,
    _session_path,
    clear_session,
    format_session,
    is_session_valid,
    read_session,
    start_session,
)
from envault.cli_session import session_group


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

def test_start_session_creates_file(vault_dir):
    ts = start_session(vault_dir)
    assert _session_path(vault_dir).exists()
    assert isinstance(ts, datetime)


def test_read_session_returns_none_when_absent(vault_dir):
    assert read_session(vault_dir) is None


def test_start_and_read_roundtrip(vault_dir):
    ts = start_session(vault_dir)
    recovered = read_session(vault_dir)
    assert recovered is not None
    assert abs((recovered - ts).total_seconds()) < 1


def test_read_session_corrupt_raises(vault_dir):
    path = _session_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not valid json")
    with pytest.raises(SessionError):
        read_session(vault_dir)


def test_clear_session_removes_file(vault_dir):
    start_session(vault_dir)
    clear_session(vault_dir)
    assert not _session_path(vault_dir).exists()


def test_clear_session_noop_when_absent(vault_dir):
    clear_session(vault_dir)  # should not raise


def test_is_session_valid_fresh(vault_dir):
    start_session(vault_dir)
    assert is_session_valid(vault_dir, idle_minutes=30) is True


def test_is_session_valid_expired(vault_dir):
    old_time = datetime.now(timezone.utc) - timedelta(minutes=60)
    path = _session_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"started_at": old_time.isoformat()}))
    assert is_session_valid(vault_dir, idle_minutes=30) is False


def test_is_session_valid_no_session(vault_dir):
    assert is_session_valid(vault_dir, idle_minutes=10) is False


def test_is_session_valid_zero_minutes_raises(vault_dir):
    with pytest.raises(SessionError):
        is_session_valid(vault_dir, idle_minutes=0)


def test_format_session_none():
    assert format_session(None) == "No active session."


def test_format_session_datetime():
    ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = format_session(ts)
    assert "2024-06-01" in result


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_start(runner, vault_dir):
    result = runner.invoke(session_group, ["start", str(vault_dir)])
    assert result.exit_code == 0
    assert "Session started" in result.output


def test_cli_show_no_session(runner, vault_dir):
    result = runner.invoke(session_group, ["show", str(vault_dir)])
    assert result.exit_code == 0
    assert "No active session" in result.output


def test_cli_check_valid(runner, vault_dir):
    start_session(vault_dir)
    result = runner.invoke(session_group, ["check", "--idle", "30", str(vault_dir)])
    assert result.exit_code == 0
    assert "active" in result.output


def test_cli_check_expired(runner, vault_dir):
    old_time = datetime.now(timezone.utc) - timedelta(hours=2)
    path = _session_path(vault_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"started_at": old_time.isoformat()}))
    result = runner.invoke(session_group, ["check", "--idle", "30", str(vault_dir)])
    assert result.exit_code == 1


def test_cli_clear(runner, vault_dir):
    start_session(vault_dir)
    result = runner.invoke(session_group, ["clear", str(vault_dir)])
    assert result.exit_code == 0
    assert "cleared" in result.output
    assert read_session(vault_dir) is None
