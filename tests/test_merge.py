"""Tests for envault.merge."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.merge import (
    ConflictStrategy,
    MergeError,
    MergeResult,
    format_merge_result,
    merge_env,
    write_merged,
)
from envault.cli_merge import merge_group


@pytest.fixture()
def tmp_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


# --- merge_env ---

def test_merge_env_no_conflicts(tmp_dir: Path) -> None:
    base = _write(tmp_dir / "base.env", "A=1\nB=2\n")
    incoming = _write(tmp_dir / "inc.env", "C=3\n")
    result = merge_env(base, incoming)
    assert result.merged == {"A": "1", "B": "2", "C": "3"}
    assert not result.has_conflicts
    assert result.added == ["C"]


def test_merge_env_detects_conflict(tmp_dir: Path) -> None:
    base = _write(tmp_dir / "base.env", "A=1\n")
    incoming = _write(tmp_dir / "inc.env", "A=99\n")
    result = merge_env(base, incoming, strategy=ConflictStrategy.OURS)
    assert result.has_conflicts
    assert result.conflicts[0].key == "A"
    assert result.conflicts[0].base_value == "1"
    assert result.conflicts[0].incoming_value == "99"
    # OURS keeps base value
    assert result.merged["A"] == "1"


def test_merge_env_strategy_theirs(tmp_dir: Path) -> None:
    base = _write(tmp_dir / "base.env", "A=1\n")
    incoming = _write(tmp_dir / "inc.env", "A=99\n")
    result = merge_env(base, incoming, strategy=ConflictStrategy.THEIRS)
    assert result.merged["A"] == "99"


def test_merge_env_removed_keys(tmp_dir: Path) -> None:
    base = _write(tmp_dir / "base.env", "A=1\nB=2\n")
    incoming = _write(tmp_dir / "inc.env", "A=1\n")
    result = merge_env(base, incoming)
    assert "B" in result.removed
    assert "B" in result.merged  # removed keys stay in merged (base wins)


def test_merge_env_missing_file_raises(tmp_dir: Path) -> None:
    base = tmp_dir / "missing.env"
    incoming = _write(tmp_dir / "inc.env", "A=1\n")
    with pytest.raises(MergeError, match="not found"):
        merge_env(base, incoming)


def test_write_merged(tmp_dir: Path) -> None:
    result = MergeResult(merged={"X": "hello", "Y": "world"})
    out = tmp_dir / "out.env"
    write_merged(result, out)
    content = out.read_text()
    assert "X=hello" in content
    assert "Y=world" in content


def test_format_merge_result_no_changes() -> None:
    result = MergeResult()
    assert format_merge_result(result) == "No changes."


# --- CLI ---

@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_cli_merge_dry_run(runner: CliRunner, tmp_dir: Path) -> None:
    base = _write(tmp_dir / "base.env", "A=1\n")
    incoming = _write(tmp_dir / "inc.env", "B=2\n")
    result = runner.invoke(merge_group, ["run", str(base), str(incoming), "--dry-run"])
    assert result.exit_code == 0
    assert "dry-run" in result.output
    # base file must NOT be modified
    assert base.read_text() == "A=1\n"


def test_cli_merge_writes_output(runner: CliRunner, tmp_dir: Path) -> None:
    base = _write(tmp_dir / "base.env", "A=1\n")
    incoming = _write(tmp_dir / "inc.env", "B=2\n")
    out = tmp_dir / "merged.env"
    result = runner.invoke(
        merge_group, ["run", str(base), str(incoming), "--output", str(out)]
    )
    assert result.exit_code == 0
    assert out.exists()
    assert "B=2" in out.read_text()


def test_cli_merge_conflict_reported(runner: CliRunner, tmp_dir: Path) -> None:
    base = _write(tmp_dir / "base.env", "A=1\n")
    incoming = _write(tmp_dir / "inc.env", "A=99\n")
    result = runner.invoke(
        merge_group, ["run", str(base), str(incoming), "--dry-run", "--strategy", "theirs"]
    )
    assert result.exit_code == 0
    assert "conflict" in result.output.lower()
