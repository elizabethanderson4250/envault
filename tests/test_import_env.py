"""Tests for envault.import_env and envault.cli_import."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.import_env import ImportError, merge_env, parse_env_file, write_env_file
from envault.cli_import import import_group


# ---------------------------------------------------------------------------
# parse_env_file
# ---------------------------------------------------------------------------

def test_parse_env_file_basic(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("FOO=bar\nBAZ=qux\n")
    result = parse_env_file(f)
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_file_ignores_comments_and_blanks(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text("# comment\n\nKEY=value\n")
    assert parse_env_file(f) == {"KEY": "value"}


def test_parse_env_file_strips_quotes(tmp_path: Path) -> None:
    f = tmp_path / ".env"
    f.write_text('QUOTED="hello world"\nSINGLE=\'world\'\n')
    result = parse_env_file(f)
    assert result["QUOTED"] == "hello world"
    assert result["SINGLE"] == "world"


def test_parse_env_file_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(ImportError, match="not found"):
        parse_env_file(tmp_path / "nonexistent.env")


# ---------------------------------------------------------------------------
# merge_env
# ---------------------------------------------------------------------------

def test_merge_env_adds_new_keys() -> None:
    merged, added, skipped = merge_env({"A": "1"}, {"B": "2"})
    assert merged == {"A": "1", "B": "2"}
    assert added == ["B"]
    assert skipped == []


def test_merge_env_skips_existing_by_default() -> None:
    merged, added, skipped = merge_env({"A": "1"}, {"A": "99", "B": "2"})
    assert merged["A"] == "1"
    assert "B" in added
    assert "A" in skipped


def test_merge_env_overwrite_flag() -> None:
    merged, added, skipped = merge_env({"A": "1"}, {"A": "99"}, overwrite=True)
    assert merged["A"] == "99"
    assert "A" in added
    assert skipped == []


# ---------------------------------------------------------------------------
# write_env_file
# ---------------------------------------------------------------------------

def test_write_env_file_round_trip(tmp_path: Path) -> None:
    target = tmp_path / ".env"
    write_env_file(target, {"X": "1", "Y": "2"})
    result = parse_env_file(target)
    assert result == {"X": "1", "Y": "2"}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_cli_import_basic(runner: CliRunner, tmp_path: Path) -> None:
    src = tmp_path / "external.env"
    src.write_text("NEW_KEY=hello\n")
    result = runner.invoke(import_group, ["run", str(src), "--vault-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "NEW_KEY" in result.output
    assert (tmp_path / ".env").read_text() == "NEW_KEY=hello\n"


def test_cli_import_dry_run(runner: CliRunner, tmp_path: Path) -> None:
    src = tmp_path / "external.env"
    src.write_text("DRY=run\n")
    result = runner.invoke(
        import_group, ["run", str(src), "--vault-dir", str(tmp_path), "--dry-run"]
    )
    assert result.exit_code == 0
    assert "Would add" in result.output
    assert not (tmp_path / ".env").exists()


def test_cli_import_skip_existing(runner: CliRunner, tmp_path: Path) -> None:
    existing = tmp_path / ".env"
    existing.write_text("KEY=original\n")
    src = tmp_path / "src.env"
    src.write_text("KEY=new\n")
    result = runner.invoke(import_group, ["run", str(src), "--vault-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "Skipped" in result.output
    assert existing.read_text() == "KEY=original\n"
