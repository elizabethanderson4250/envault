"""Tests for envault.sanitize and envault.cli_sanitize."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.sanitize import (
    SanitizeError,
    SanitizeResult,
    apply_sanitize,
    format_sanitize,
    sanitize_env,
    sanitize_line,
)
from envault.cli_sanitize import sanitize_group


# ---------------------------------------------------------------------------
# sanitize_line
# ---------------------------------------------------------------------------

def test_sanitize_line_clean_returns_unchanged():
    result = sanitize_line("FOO=bar\n")
    assert not result.changed
    assert result.sanitized == "FOO=bar\n"


def test_sanitize_line_strips_whitespace_in_value():
    result = sanitize_line("FOO=  bar  \n")
    assert result.changed
    assert result.sanitized == "FOO=bar\n"
    assert any("whitespace" in c for c in result.changes)


def test_sanitize_line_removes_control_chars():
    result = sanitize_line("FOO=ba\x01r\n")
    assert result.changed
    assert result.sanitized == "FOO=bar\n"
    assert any("control" in c for c in result.changes)


def test_sanitize_line_normalizes_crlf():
    result = sanitize_line("FOO=bar\r\n")
    assert result.changed
    assert "\r" not in result.sanitized


def test_sanitize_line_comment_unchanged():
    result = sanitize_line("# comment\n")
    assert not result.changed


def test_sanitize_line_blank_unchanged():
    result = sanitize_line("\n")
    assert not result.changed


def test_sanitize_line_no_equals_unchanged():
    result = sanitize_line("NOEQUALS\n")
    assert not result.changed


# ---------------------------------------------------------------------------
# sanitize_env / apply_sanitize
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nBAZ=  qux  \n", encoding="utf-8")
    return p


def test_sanitize_env_returns_results(env_file: Path):
    results = sanitize_env(env_file)
    assert len(results) == 2
    assert isinstance(results[0], SanitizeResult)


def test_sanitize_env_missing_file_raises(tmp_path: Path):
    with pytest.raises(SanitizeError, match="not found"):
        sanitize_env(tmp_path / "missing.env")


def test_apply_sanitize_writes_fixed_content(env_file: Path):
    apply_sanitize(env_file)
    content = env_file.read_text(encoding="utf-8")
    assert "  qux  " not in content
    assert "qux" in content


# ---------------------------------------------------------------------------
# format_sanitize
# ---------------------------------------------------------------------------

def test_format_sanitize_clean():
    results = [SanitizeResult(original="FOO=bar\n", sanitized="FOO=bar\n")]
    assert "clean" in format_sanitize(results)


def test_format_sanitize_shows_changes():
    r = SanitizeResult(original="FOO=  bar  \n", sanitized="FOO=bar\n", changes=["stripped surrounding whitespace"])
    out = format_sanitize([r])
    assert "1 line(s)" in out
    assert "whitespace" in out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_check_clean_file(runner, tmp_path):
    p = tmp_path / ".env"
    p.write_text("FOO=bar\n", encoding="utf-8")
    result = runner.invoke(sanitize_group, ["check", str(p)])
    assert result.exit_code == 0
    assert "clean" in result.output


def test_cli_check_dirty_file_exits_nonzero(runner, tmp_path):
    p = tmp_path / ".env"
    p.write_text("FOO=  bar  \n", encoding="utf-8")
    result = runner.invoke(sanitize_group, ["check", str(p)])
    assert result.exit_code != 0


def test_cli_fix_updates_file(runner, tmp_path):
    p = tmp_path / ".env"
    p.write_text("FOO=  bar  \n", encoding="utf-8")
    result = runner.invoke(sanitize_group, ["fix", str(p)])
    assert result.exit_code == 0
    assert "updated" in result.output
    assert p.read_text(encoding="utf-8") == "FOO=bar\n"


def test_cli_fix_quiet_no_output_when_clean(runner, tmp_path):
    p = tmp_path / ".env"
    p.write_text("FOO=bar\n", encoding="utf-8")
    result = runner.invoke(sanitize_group, ["fix", "--quiet", str(p)])
    assert result.exit_code == 0
    assert result.output.strip() == ""
