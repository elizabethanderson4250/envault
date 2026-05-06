"""Tests for envault.export_env."""
from __future__ import annotations

import json
import pytest

from envault.export_env import (
    ExportError,
    parse_env_pairs,
    export_dotenv,
    export_json,
    export_shell,
    export_env,
)

SAMPLE = """# comment\nDB_HOST=localhost\nDB_PORT=5432\nSECRET='my secret'\n"""


def test_parse_env_pairs_basic():
    pairs = parse_env_pairs(SAMPLE)
    assert pairs == [("DB_HOST", "localhost"), ("DB_PORT", "5432"), ("SECRET", "my secret")]


def test_parse_env_pairs_ignores_blank_and_comments():
    text = "\n# ignore\n\nKEY=val\n"
    assert parse_env_pairs(text) == [("KEY", "val")]


def test_parse_env_pairs_no_equals_skipped():
    text = "BADLINE\nGOOD=ok\n"
    assert parse_env_pairs(text) == [("GOOD", "ok")]


def test_export_dotenv_format():
    pairs = [("A", "1"), ("B", "hello world")]
    out = export_dotenv(pairs)
    assert 'A="1"' in out
    assert 'B="hello world"' in out
    assert out.endswith("\n")


def test_export_json_format():
    pairs = [("A", "1"), ("B", "two")]
    out = export_json(pairs)
    data = json.loads(out)
    assert data == {"A": "1", "B": "two"}


def test_export_shell_format():
    pairs = [("PATH_VAR", "/usr/bin")]
    out = export_shell(pairs)
    assert 'export PATH_VAR="/usr/bin"' in out


def test_export_env_dotenv():
    result = export_env(SAMPLE, "dotenv")
    assert 'DB_HOST="localhost"' in result


def test_export_env_json():
    result = export_env(SAMPLE, "json")
    data = json.loads(result)
    assert data["DB_HOST"] == "localhost"
    assert data["SECRET"] == "my secret"


def test_export_env_shell():
    result = export_env(SAMPLE, "shell")
    assert "export DB_HOST=" in result


def test_export_env_invalid_format_raises():
    with pytest.raises(ExportError, match="Unsupported format"):
        export_env(SAMPLE, "xml")


def test_export_env_empty_input():
    result = export_env("", "json")
    assert json.loads(result) == {}
