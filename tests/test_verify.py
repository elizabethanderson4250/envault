"""Tests for envault.verify."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.vault import Vault
from envault.verify import VerifyResult, format_verify, verify_vault


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def vault(vault_dir: Path) -> Vault:
    return Vault(vault_dir)


# ---------------------------------------------------------------------------
# verify_vault tests
# ---------------------------------------------------------------------------


def test_verify_fails_when_no_files(vault: Vault) -> None:
    result = verify_vault(vault)
    assert result.ok is False
    assert result.vault_file_present is False
    assert result.meta_present is False


def test_verify_fails_when_only_vault_file(vault: Vault, vault_dir: Path) -> None:
    (vault_dir / "vault.env.gpg").write_bytes(b"encrypted")
    result = verify_vault(vault)
    assert result.ok is False
    assert result.vault_file_present is True
    assert result.meta_present is False


def test_verify_fails_when_only_meta(vault: Vault, vault_dir: Path) -> None:
    vault.add_recipient("AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555")
    result = verify_vault(vault)
    assert result.ok is False
    assert result.vault_file_present is False
    assert result.meta_present is True


def test_verify_passes_with_both_files(vault: Vault, vault_dir: Path) -> None:
    vault.add_recipient("AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555")
    (vault_dir / "vault.env.gpg").write_bytes(b"encrypted-data")
    result = verify_vault(vault)
    assert result.ok is True
    assert result.vault_file_present is True
    assert result.meta_present is True
    assert result.recipients_match is True
    assert result.sha256 is not None
    assert len(result.sha256) == 64  # hex SHA-256


def test_verify_sha256_is_correct(vault: Vault, vault_dir: Path) -> None:
    import hashlib

    data = b"some encrypted bytes"
    vault.add_recipient("AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555")
    gpg_file = vault_dir / "vault.env.gpg"
    gpg_file.write_bytes(data)
    result = verify_vault(vault)
    expected = hashlib.sha256(data).hexdigest()
    assert result.sha256 == expected


def test_verify_no_errors_on_success(vault: Vault, vault_dir: Path) -> None:
    vault.add_recipient("AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555")
    (vault_dir / "vault.env.gpg").write_bytes(b"x")
    result = verify_vault(vault)
    assert result.errors == []


# ---------------------------------------------------------------------------
# format_verify tests
# ---------------------------------------------------------------------------


def test_format_verify_pass(vault: Vault, vault_dir: Path) -> None:
    vault.add_recipient("AAAA1111BBBB2222CCCC3333DDDD4444EEEE5555")
    (vault_dir / "vault.env.gpg").write_bytes(b"data")
    result = verify_vault(vault)
    output = format_verify(result)
    assert "PASS" in output
    assert "SHA-256" in output


def test_format_verify_fail_shows_errors(vault: Vault) -> None:
    result = verify_vault(vault)
    output = format_verify(result)
    assert "FAIL" in output
    assert "ERROR" in output
