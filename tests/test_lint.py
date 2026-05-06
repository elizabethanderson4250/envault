"""Tests for envault.lint."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.lint import lint_env, format_lint, LintIssue
from envault.cli_lint import lint_group


@pytest.fixture()
def env_file(tmp_path: Path):
    def _write(content: str) -> Path:
        p = tmp_path / '.env'
        p.write_text(content)
        return p
    return _write


def test_lint_clean_file(env_file):
    p = env_file("DB_HOST=localhost\nDB_PORT=5432\n")
    result = lint_env(p)
    assert result.ok


def test_lint_missing_file(tmp_path):
    result = lint_env(tmp_path / 'missing.env')
    assert not result.ok
    assert result.issues[0].code == 'E001'


def test_lint_missing_equals(env_file):
    p = env_file("BADLINE\n")
    result = lint_env(p)
    codes = [i.code for i in result.issues]
    assert 'E002' in codes


def test_lint_invalid_key_name(env_file):
    p = env_file("1BADKEY=value\n")
    result = lint_env(p)
    codes = [i.code for i in result.issues]
    assert 'E003' in codes


def test_lint_duplicate_key(env_file):
    p = env_file("FOO=bar\nFOO=baz\n")
    result = lint_env(p)
    codes = [i.code for i in result.issues]
    assert 'W001' in codes


def test_lint_empty_value(env_file):
    p = env_file("SECRET=\n")
    result = lint_env(p)
    codes = [i.code for i in result.issues]
    assert 'W002' in codes


def test_lint_ignores_comments_and_blanks(env_file):
    p = env_file("# comment\n\nVALID=yes\n")
    result = lint_env(p)
    assert result.ok


def test_format_lint_ok(env_file):
    p = env_file("OK=1\n")
    result = lint_env(p)
    assert format_lint(result) == 'No issues found.'


def test_format_lint_shows_issues(env_file):
    p = env_file("SECRET=\n")
    result = lint_env(p)
    output = format_lint(result)
    assert 'W002' in output
    assert '1 issue(s) found.' in output


# --- CLI tests ---

@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_lint_clean(runner, tmp_path):
    p = tmp_path / '.env'
    p.write_text("HOST=localhost\n")
    result = runner.invoke(lint_group, ['check', str(p)])
    assert result.exit_code == 0
    assert 'No issues found.' in result.output


def test_cli_lint_error_exits_nonzero(runner, tmp_path):
    p = tmp_path / '.env'
    p.write_text("BADLINE\n")
    result = runner.invoke(lint_group, ['check', str(p)])
    assert result.exit_code == 1


def test_cli_lint_warning_passes_without_strict(runner, tmp_path):
    p = tmp_path / '.env'
    p.write_text("EMPTY=\n")
    result = runner.invoke(lint_group, ['check', str(p)])
    assert result.exit_code == 0


def test_cli_lint_warning_fails_with_strict(runner, tmp_path):
    p = tmp_path / '.env'
    p.write_text("EMPTY=\n")
    result = runner.invoke(lint_group, ['check', '--strict', str(p)])
    assert result.exit_code == 1
