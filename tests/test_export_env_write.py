"""Tests for write_export helper in envault.export_env."""
from __future__ import annotations

from pathlib import Path

import pytest

from envault.export_env import write_export


def test_write_export_creates_file(tmp_path):
    out = tmp_path / "result.env"
    write_export('KEY="value"\n', out)
    assert out.exists()
    assert out.read_text() == 'KEY="value"\n'


def test_write_export_overwrites_existing(tmp_path):
    out = tmp_path / "result.env"
    out.write_text("old content", encoding="utf-8")
    write_export("new content\n", out)
    assert out.read_text() == "new content\n"


def test_write_export_creates_nested_path(tmp_path):
    out = tmp_path / "subdir" / "out.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_export('{"A": "1"}\n', out)
    assert out.read_text() == '{"A": "1"}\n'


def test_write_export_empty_content(tmp_path):
    out = tmp_path / "empty.env"
    write_export("", out)
    assert out.read_text() == ""
