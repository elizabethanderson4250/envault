"""Tests for envault.watch and envault.cli_watch."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from envault.watch import WatchError, WatchEvent, _current_hash, _sha256_file, watch
from envault.cli_watch import watch_group


# ---------------------------------------------------------------------------
# Unit tests for watch module
# ---------------------------------------------------------------------------


def test_sha256_file_returns_hex_string(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("KEY=value")
    result = _sha256_file(f)
    assert len(result) == 64
    assert all(c in "0123456789abcdef" for c in result)


def test_sha256_file_changes_on_content_change(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("KEY=value")
    h1 = _sha256_file(f)
    f.write_text("KEY=other")
    h2 = _sha256_file(f)
    assert h1 != h2


def test_current_hash_none_when_missing(tmp_path: Path) -> None:
    assert _current_hash(tmp_path / "nonexistent.env") is None


def test_current_hash_returns_string_when_present(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("A=1")
    assert isinstance(_current_hash(f), str)


def test_watch_raises_when_parent_missing(tmp_path: Path) -> None:
    missing = tmp_path / "no_such_dir" / ".env"
    with pytest.raises(WatchError, match="Parent directory"):
        watch(missing, lambda e: None, interval=0.01, max_iterations=1)


def test_watch_calls_on_change_when_file_created(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    events: list[WatchEvent] = []

    # File does not exist yet; create it after the watcher starts via a
    # side-effect on time.sleep.
    original_sleep = time.sleep

    def _fake_sleep(secs: float) -> None:  # noqa: ARG001
        env.write_text("KEY=1")
        original_sleep(0)

    with patch("envault.watch.time.sleep", side_effect=_fake_sleep):
        watch(env, events.append, interval=0.01, max_iterations=1)

    assert len(events) == 1
    assert events[0].old_hash is None
    assert events[0].new_hash != ""


def test_watch_no_change_does_not_call_callback(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("KEY=stable")
    events: list[WatchEvent] = []

    with patch("envault.watch.time.sleep", return_value=None):
        watch(env, events.append, interval=0.01, max_iterations=3)

    assert events == []


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    meta = tmp_path / ".vault_meta.json"
    meta.write_text('{"recipients": ["ABCD1234"]}')
    return tmp_path


def test_watch_start_missing_parent(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(
        watch_group,
        ["start", str(tmp_path / "no_dir"), "--interval", "0.01"],
    )
    assert result.exit_code != 0
    assert "Error" in result.output or "does not exist" in result.output


def test_watch_start_detects_change_and_relocks(runner: CliRunner, vault_dir: Path) -> None:
    env = vault_dir / ".env"
    env.write_text("A=1")

    with patch("envault.cli_watch.watch") as mock_watch, \
         patch("envault.cli_watch.record_event") as mock_record:

        def _fake_watch(path, callback, *, interval, max_iterations=None):  # noqa: ARG001
            # Simulate one change event
            callback(WatchEvent(path=path, old_hash="aaa", new_hash="bbb", timestamp=0.0))

        mock_watch.side_effect = _fake_watch

        with patch("envault.cli_watch.Vault") as MockVault:
            instance = MockVault.return_value
            instance.get_recipients.return_value = ["ABCD1234"]
            instance.lock = MagicMock()

            result = runner.invoke(
                watch_group,
                ["start", str(vault_dir), "--interval", "0.01"],
            )

        assert result.exit_code == 0
        assert "Change detected" in result.output
        mock_record.assert_called_once()
