"""CLI-level tests for the share export/import commands."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from envault.cli_share import share_group
from envault.vault import Vault


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    d = tmp_path / "proj"
    d.mkdir()
    v = Vault(d)
    v.add_recipient("DEADBEEFDEADBEEFDEADBEEFDEADBEEFDEADBEEF")
    (d / ".env").write_text("API_KEY=secret\n")
    return d


def _fake_encrypt(plaintext, recipients):
    return b"ENC:" + plaintext


def _fake_decrypt(ciphertext):
    return ciphertext[4:]


class TestExportCmd:
    def test_creates_bundle(self, runner, vault_dir, tmp_path):
        out = str(tmp_path / "out.json")
        with patch("envault.share.encrypt", side_effect=_fake_encrypt):
            result = runner.invoke(
                share_group,
                ["export", "--vault-dir", str(vault_dir), "--output", out],
            )
        assert result.exit_code == 0, result.output
        assert "Bundle written to" in result.output
        assert Path(out).exists()

    def test_fails_without_env_file(self, runner, tmp_path):
        d = tmp_path / "empty"
        d.mkdir()
        Vault(d).add_recipient("AAAA" * 10)
        result = runner.invoke(
            share_group, ["export", "--vault-dir", str(d)]
        )
        assert result.exit_code != 0
        assert ".env file not found" in result.output


class TestImportCmd:
    def _write_bundle(self, path: Path, plaintext: bytes = b"X=1\n") -> Path:
        ciphertext = b"ENC:" + plaintext
        bundle = {
            "version": 1,
            "recipients": ["DEADBEEF"],
            "ciphertext": base64.b64encode(ciphertext).decode(),
        }
        path.write_text(json.dumps(bundle))
        return path

    def test_import_writes_env(self, runner, vault_dir, tmp_path):
        bundle = self._write_bundle(tmp_path / "b.json")
        with patch("envault.share.decrypt", side_effect=_fake_decrypt):
            result = runner.invoke(
                share_group,
                ["import", str(bundle), "--vault-dir", str(vault_dir)],
            )
        assert result.exit_code == 0, result.output
        assert ".env written to" in result.output
        assert (vault_dir / ".env").read_text() == "X=1\n"

    def test_import_bad_version(self, runner, vault_dir, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps({"version": 2, "ciphertext": "x", "recipients": []}))
        result = runner.invoke(
            share_group,
            ["import", str(bad), "--vault-dir", str(vault_dir)],
        )
        assert result.exit_code != 0
        assert "Unsupported bundle version" in result.output
