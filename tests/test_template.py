"""Tests for envault.template."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.template import (
    TemplateError,
    generate_template,
    parse_env_keys,
    write_template,
)


ENV_TEXT = """# Database config
DB_HOST=localhost
DB_PORT=5432
DB_PASS=supersecret

# App
APP_KEY=abc123
"""


def test_parse_env_keys_basic():
    keys = parse_env_keys(ENV_TEXT)
    assert [k for k, _ in keys] == ["DB_HOST", "DB_PORT", "DB_PASS", "APP_KEY"]


def test_parse_env_keys_ignores_comments_and_blanks():
    text = "# comment\n\nFOO=bar\n"
    keys = parse_env_keys(text)
    assert keys == [("FOO", "")]


def test_parse_env_keys_inline_comment():
    text = "SECRET=value  # keep this safe\n"
    keys = parse_env_keys(text)
    assert keys == [("SECRET", "keep this safe")]


def test_generate_template_replaces_values():
    result = generate_template(ENV_TEXT, placeholder="CHANGE_ME")
    assert "DB_HOST=CHANGE_ME" in result
    assert "DB_PORT=CHANGE_ME" in result
    assert "APP_KEY=CHANGE_ME" in result


def test_generate_template_preserves_comments():
    result = generate_template(ENV_TEXT)
    assert "# Database config" in result
    assert "# App" in result


def test_generate_template_empty_placeholder():
    result = generate_template("FOO=bar\n")
    assert "FOO=" in result
    assert "bar" not in result


def test_write_template_creates_file(tmp_path: Path):
    src = tmp_path / ".env"
    src.write_text("KEY=value\n", encoding="utf-8")
    out = tmp_path / ".env.example"
    returned = write_template(src, out, placeholder="")
    assert returned == out
    assert out.exists()
    assert "KEY=" in out.read_text()


def test_write_template_missing_source_raises(tmp_path: Path):
    with pytest.raises(TemplateError, match="not found"):
        write_template(tmp_path / "missing.env", tmp_path / "out.env")


def test_write_template_creates_parent_dirs(tmp_path: Path):
    src = tmp_path / ".env"
    src.write_text("X=1\n", encoding="utf-8")
    out = tmp_path / "subdir" / "nested" / ".env.example"
    write_template(src, out)
    assert out.exists()
