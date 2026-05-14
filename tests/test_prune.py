"""Tests for envault.prune."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_prune import prune_group
from envault.prune import PruneError, format_prune, prune_keys


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "# comment\nDB_HOST=localhost\nDB_PASS=secret\nAPP_KEY=abc123\n",
        encoding="utf-8",
    )
    return p


def test_prune_removes_single_key(env_file: Path) -> None:
    result = prune_keys(env_file, ["DB_PASS"])
    assert result.removed == ["DB_PASS"]
    assert "DB_PASS" not in env_file.read_text()
    assert "DB_HOST" in env_file.read_text()


def test_prune_removes_multiple_keys(env_file: Path) -> None:
    result = prune_keys(env_file, ["DB_HOST", "APP_KEY"])
    assert set(result.removed) == {"DB_HOST", "APP_KEY"}
    text = env_file.read_text()
    assert "DB_HOST" not in text
    assert "APP_KEY" not in text
    assert "DB_PASS" in text


def test_prune_preserves_comments(env_file: Path) -> None:
    prune_keys(env_file, ["DB_HOST"])
    assert "# comment" in env_file.read_text()


def test_prune_key_not_present_is_not_in_removed(env_file: Path) -> None:
    result = prune_keys(env_file, ["NONEXISTENT"])
    assert result.removed == []
    assert not result.changed


def test_prune_dry_run_does_not_modify_file(env_file: Path) -> None:
    original = env_file.read_text()
    result = prune_keys(env_file, ["DB_PASS"], dry_run=True)
    assert result.removed == ["DB_PASS"]
    assert env_file.read_text() == original


def test_prune_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(PruneError, match="not found"):
        prune_keys(tmp_path / "missing.env", ["KEY"])


def test_prune_empty_keys_list_raises(env_file: Path) -> None:
    with pytest.raises(PruneError, match="must not be empty"):
        prune_keys(env_file, [])


def test_format_prune_no_changes() -> None:
    from envault.prune import PruneResult
    assert format_prune(PruneResult()) == "Nothing pruned."


def test_format_prune_with_removals() -> None:
    from envault.prune import PruneResult
    r = PruneResult(removed=["A", "B"])
    out = format_prune(r)
    assert "2 key(s)" in out
    assert "- A" in out
    assert "- B" in out


# --- CLI ---

@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


def test_cli_prune_removes_key(runner: CliRunner, env_file: Path) -> None:
    result = runner.invoke(prune_group, ["run", str(env_file), "DB_PASS"])
    assert result.exit_code == 0
    assert "DB_PASS" not in env_file.read_text()


def test_cli_prune_dry_run(runner: CliRunner, env_file: Path) -> None:
    original = env_file.read_text()
    result = runner.invoke(prune_group, ["run", "--dry-run", str(env_file), "DB_PASS"])
    assert result.exit_code == 0
    assert "[dry-run]" in result.output
    assert env_file.read_text() == original


def test_cli_prune_missing_file(runner: CliRunner, tmp_path: Path) -> None:
    result = runner.invoke(prune_group, ["run", str(tmp_path / "nope.env"), "KEY"])
    assert result.exit_code != 0
