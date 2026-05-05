"""Tests for envault.rotate — key rotation logic."""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from envault.rotate import rotate_keys, RotationError
from envault.vault import Vault


PLAINTEXT = b"SECRET=hunter2\nAPI_KEY=abc123\n"
CIPHERTEXT = b"<encrypted>"
NEW_CIPHERTEXT = b"<re-encrypted>"
FP_ALICE = "AAAA" * 10
FP_BOB = "BBBB" * 10


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path / ".envault"


@pytest.fixture()
def vault(vault_dir: Path) -> Vault:
    v = Vault(vault_dir)
    v.add_recipient(FP_ALICE)
    return v


@pytest.fixture()
def vault_with_file(vault: Vault) -> Vault:
    vault_file = vault.vault_dir / "secrets.env.gpg"
    vault_file.write_bytes(CIPHERTEXT)
    return vault


def test_rotate_success(vault_with_file: Vault) -> None:
    with (
        patch("envault.rotate.decrypt", return_value=PLAINTEXT) as mock_dec,
        patch("envault.rotate.encrypt", return_value=NEW_CIPHERTEXT) as mock_enc,
        patch("envault.rotate.record_event") as mock_audit,
    ):
        result = rotate_keys(vault_with_file, FP_ALICE)

    assert result == vault_with_file.vault_dir / "secrets.env.gpg"
    assert result.read_bytes() == NEW_CIPHERTEXT
    mock_dec.assert_called_once_with(CIPHERTEXT, FP_ALICE)
    mock_enc.assert_called_once_with(PLAINTEXT, [FP_ALICE])
    mock_audit.assert_called_once()


def test_rotate_updates_recipients(vault_with_file: Vault) -> None:
    with (
        patch("envault.rotate.decrypt", return_value=PLAINTEXT),
        patch("envault.rotate.encrypt", return_value=NEW_CIPHERTEXT),
        patch("envault.rotate.record_event"),
    ):
        rotate_keys(vault_with_file, FP_ALICE, new_recipients=[FP_BOB])

    assert FP_BOB in vault_with_file.get_recipients()
    assert FP_ALICE not in vault_with_file.get_recipients()


def test_rotate_missing_vault_file(vault: Vault) -> None:
    with pytest.raises(RotationError, match="Vault file not found"):
        rotate_keys(vault, FP_ALICE)


def test_rotate_decrypt_error(vault_with_file: Vault) -> None:
    with patch("envault.rotate.decrypt", side_effect=RuntimeError("bad key")):
        with pytest.raises(RotationError, match="Decryption failed"):
            rotate_keys(vault_with_file, FP_ALICE)


def test_rotate_encrypt_error(vault_with_file: Vault) -> None:
    with (
        patch("envault.rotate.decrypt", return_value=PLAINTEXT),
        patch("envault.rotate.encrypt", side_effect=RuntimeError("gpg error")),
    ):
        with pytest.raises(RotationError, match="Re-encryption failed"):
            rotate_keys(vault_with_file, FP_ALICE)


def test_rotate_no_recipients_raises(vault_with_file: Vault) -> None:
    vault_with_file.remove_recipient(FP_ALICE)
    with (
        patch("envault.rotate.decrypt", return_value=PLAINTEXT),
    ):
        with pytest.raises(RotationError, match="No recipients"):
            rotate_keys(vault_with_file, FP_ALICE)
