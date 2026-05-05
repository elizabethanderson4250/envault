"""Tests for envault.share — export/import bundle feature."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envault.share import export_bundle, import_bundle, ShareError
from envault.vault import Vault


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    d = tmp_path / "myproject"
    d.mkdir()
    return d


@pytest.fixture()
def vault(vault_dir: Path) -> Vault:
    v = Vault(vault_dir)
    v.add_recipient("AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555")
    return v


@pytest.fixture()
def env_file(vault_dir: Path) -> Path:
    f = vault_dir / ".env"
    f.write_text("SECRET=hello\nDB_PASS=world\n")
    return f


def _fake_encrypt(plaintext: bytes, recipients):
    return b"ENCRYPTED:" + plaintext


def _fake_decrypt(ciphertext: bytes):
    assert ciphertext.startswith(b"ENCRYPTED:")
    return ciphertext[len(b"ENCRYPTED:"):]


class TestExportBundle:
    def test_creates_bundle_file(self, vault, env_file, tmp_path):
        out = tmp_path / "bundle.json"
        with patch("envault.share.encrypt", side_effect=_fake_encrypt):
            result = export_bundle(vault, out)
        assert result == out
        assert out.exists()

    def test_bundle_contains_expected_keys(self, vault, env_file, tmp_path):
        out = tmp_path / "bundle.json"
        with patch("envault.share.encrypt", side_effect=_fake_encrypt):
            export_bundle(vault, out)
        data = json.loads(out.read_text())
        assert data["version"] == 1
        assert "ciphertext" in data
        assert "recipients" in data

    def test_raises_when_no_env_file(self, vault, tmp_path):
        out = tmp_path / "bundle.json"
        with pytest.raises(ShareError, match=".env file not found"):
            export_bundle(vault, out)

    def test_raises_when_no_recipients(self, vault_dir, env_file, tmp_path):
        empty_vault = Vault(vault_dir)
        out = tmp_path / "bundle.json"
        with pytest.raises(ShareError, match="No recipients"):
            export_bundle(empty_vault, out)


class TestImportBundle:
    def _make_bundle(self, tmp_path, plaintext=b"KEY=val\n"):
        ciphertext = b"ENCRYPTED:" + plaintext
        bundle = {
            "version": 1,
            "recipients": ["AAAA1111"],
            "ciphertext": base64.b64encode(ciphertext).decode(),
        }
        p = tmp_path / "bundle.json"
        p.write_text(json.dumps(bundle))
        return p

    def test_writes_env_file(self, vault, tmp_path):
        bundle = self._make_bundle(tmp_path)
        with patch("envault.share.decrypt", side_effect=_fake_decrypt):
            result = import_bundle(vault, bundle)
        assert result.name == ".env"
        assert result.read_text() == "KEY=val\n"

    def test_raises_on_missing_bundle(self, vault, tmp_path):
        with pytest.raises(ShareError, match="Bundle file not found"):
            import_bundle(vault, tmp_path / "ghost.json")

    def test_raises_on_bad_json(self, vault, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("not-json")
        with pytest.raises(ShareError, match="Invalid bundle JSON"):
            import_bundle(vault, bad)

    def test_raises_on_wrong_version(self, vault, tmp_path):
        p = tmp_path / "b.json"
        p.write_text(json.dumps({"version": 99, "ciphertext": "x", "recipients": []}))
        with pytest.raises(ShareError, match="Unsupported bundle version"):
            import_bundle(vault, p)
