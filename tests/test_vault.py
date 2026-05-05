"""Unit tests for envault.vault (Vault class)."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from envault.vault import Vault


SAMPLE_PLAINTEXT = b"DB_URL=postgres://localhost/dev\n"
SAMPLE_CIPHERTEXT = b"-----BEGIN PGP MESSAGE-----\nfake\n-----END PGP MESSAGE-----\n"


@pytest.fixture()
def tmp_vault(tmp_path):
    vault_file = tmp_path / ".env.vault"
    meta_file = tmp_path / ".env.vault.meta"
    return Vault(vault_path=vault_file, meta_path=meta_file)


def test_add_and_get_recipients(tmp_vault):
    tmp_vault.add_recipient("alice@example.com")
    tmp_vault.add_recipient("bob@example.com")
    recipients = tmp_vault.get_recipients()
    assert "alice@example.com" in recipients
    assert "bob@example.com" in recipients


def test_add_recipient_no_duplicates(tmp_vault):
    tmp_vault.add_recipient("alice@example.com")
    tmp_vault.add_recipient("alice@example.com")
    assert tmp_vault.get_recipients().count("alice@example.com") == 1


def test_remove_recipient(tmp_vault):
    tmp_vault.add_recipient("alice@example.com")
    tmp_vault.remove_recipient("alice@example.com")
    assert "alice@example.com" not in tmp_vault.get_recipients()


@patch("envault.vault.encrypt", return_value=SAMPLE_CIPHERTEXT)
def test_lock_writes_vault_file(mock_encrypt, tmp_vault, tmp_path):
    tmp_vault.add_recipient("alice@example.com")
    env_file = tmp_path / ".env"
    env_file.write_bytes(SAMPLE_PLAINTEXT)

    tmp_vault.lock(env_path=env_file)

    assert tmp_vault.vault_path.read_bytes() == SAMPLE_CIPHERTEXT
    mock_encrypt.assert_called_once_with(SAMPLE_PLAINTEXT, ["alice@example.com"])


def test_lock_no_recipients_raises(tmp_vault, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_bytes(SAMPLE_PLAINTEXT)
    with pytest.raises(ValueError, match="No recipients"):
        tmp_vault.lock(env_path=env_file)


@patch("envault.vault.decrypt", return_value=SAMPLE_PLAINTEXT)
def test_unlock_writes_env_file(mock_decrypt, tmp_vault, tmp_path):
    tmp_vault.vault_path.write_bytes(SAMPLE_CIPHERTEXT)
    env_file = tmp_path / ".env"

    tmp_vault.unlock(env_path=env_file)

    assert env_file.read_bytes() == SAMPLE_PLAINTEXT


@patch("envault.vault.decrypt", return_value=SAMPLE_PLAINTEXT)
def test_unlock_refuses_overwrite_by_default(mock_decrypt, tmp_vault, tmp_path):
    tmp_vault.vault_path.write_bytes(SAMPLE_CIPHERTEXT)
    env_file = tmp_path / ".env"
    env_file.write_bytes(b"existing content")

    with pytest.raises(FileExistsError):
        tmp_vault.unlock(env_path=env_file)


def test_unlock_missing_vault_raises(tmp_vault, tmp_path):
    env_file = tmp_path / ".env"
    with pytest.raises(FileNotFoundError):
        tmp_vault.unlock(env_path=env_file)
