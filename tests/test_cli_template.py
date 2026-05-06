"""Tests for envault.cli_template."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_template import template_group


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text("DB_URL=postgres://localhost/db\nSECRET=abc\n", encoding="utf-8")
    return tmp_path


def test_generate_creates_example_file(runner: CliRunner, vault_dir: Path):
    result = runner.invoke(
        template_group,
        ["generate", str(vault_dir)],
    )
    assert result.exit_code == 0, result.output
    example = vault_dir / ".env.example"
    assert example.exists()
    content = example.read_text()
    assert "DB_URL=" in content
    assert "SECRET=" in content
    assert "postgres" not in content


def test_generate_with_placeholder(runner: CliRunner, vault_dir: Path):
    result = runner.invoke(
        template_group,
        ["generate", str(vault_dir), "--placeholder", "CHANGE_ME"],
    )
    assert result.exit_code == 0
    content = (vault_dir / ".env.example").read_text()
    assert "DB_URL=CHANGE_ME" in content


def test_generate_custom_output(runner: CliRunner, vault_dir: Path):
    out = vault_dir / "custom.example"
    result = runner.invoke(
        template_group,
        ["generate", str(vault_dir), "--output", str(out)],
    )
    assert result.exit_code == 0
    assert out.exists()


def test_generate_missing_env_file_fails(runner: CliRunner, tmp_path: Path):
    result = runner.invoke(
        template_group,
        ["generate", str(tmp_path)],
    )
    assert result.exit_code != 0
    assert "Error" in result.output


def test_generate_prints_destination(runner: CliRunner, vault_dir: Path):
    result = runner.invoke(
        template_group,
        ["generate", str(vault_dir)],
    )
    assert "Template written to" in result.output
