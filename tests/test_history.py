"""Tests for envault.history and envault.cli_history."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.audit import record_event
from envault.history import filter_events, format_history
from envault.cli_history import history_group


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_filter_events_empty(vault_dir: Path) -> None:
    assert filter_events(vault_dir) == []


def test_filter_events_returns_matching(vault_dir: Path) -> None:
    record_event(vault_dir, "lock", {"file": ".env"})
    record_event(vault_dir, "unlock", {"file": ".env"})
    record_event(vault_dir, "add_recipient", {"fingerprint": "ABCD"})

    events = filter_events(vault_dir)
    assert len(events) == 3


def test_filter_events_by_type(vault_dir: Path) -> None:
    record_event(vault_dir, "lock", {})
    record_event(vault_dir, "unlock", {})

    events = filter_events(vault_dir, event_types=["lock"])
    assert len(events) == 1
    assert events[0]["event"] == "lock"


def test_filter_events_newest_first(vault_dir: Path) -> None:
    record_event(vault_dir, "lock", {"seq": 1})
    record_event(vault_dir, "lock", {"seq": 2})

    events = filter_events(vault_dir, event_types=["lock"])
    assert events[0]["data"]["seq"] == 2
    assert events[1]["data"]["seq"] == 1


def test_filter_events_limit(vault_dir: Path) -> None:
    for i in range(5):
        record_event(vault_dir, "lock", {"i": i})

    events = filter_events(vault_dir, limit=3)
    assert len(events) == 3


def test_format_history_empty() -> None:
    assert format_history([]) == "No history found."


def test_format_history_non_empty(vault_dir: Path) -> None:
    record_event(vault_dir, "lock", {"file": ".env"})
    events = filter_events(vault_dir)
    output = format_history(events)
    assert "lock" in output


def test_cli_history_show_no_events(vault_dir: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(history_group, ["show", str(vault_dir)])
    assert result.exit_code == 0
    assert "No history found" in result.output


def test_cli_history_show_with_events(vault_dir: Path) -> None:
    record_event(vault_dir, "lock", {"file": ".env"})
    runner = CliRunner()
    result = runner.invoke(history_group, ["show", str(vault_dir)])
    assert result.exit_code == 0
    assert "lock" in result.output


def test_cli_history_show_type_filter(vault_dir: Path) -> None:
    record_event(vault_dir, "lock", {})
    record_event(vault_dir, "unlock", {})
    runner = CliRunner()
    result = runner.invoke(history_group, ["show", str(vault_dir), "--type", "lock"])
    assert result.exit_code == 0
    assert "lock" in result.output


def test_cli_history_show_limit(vault_dir: Path) -> None:
    for i in range(10):
        record_event(vault_dir, "lock", {"i": i})
    runner = CliRunner()
    result = runner.invoke(history_group, ["show", str(vault_dir), "--limit", "3"])
    assert result.exit_code == 0
    assert result.output.count("lock") == 3
