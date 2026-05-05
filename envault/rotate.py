"""Key rotation support: re-encrypt vault secrets for a new set of recipients."""

from __future__ import annotations

from pathlib import Path
from typing import List

from envault.crypto import decrypt, encrypt
from envault.vault import Vault
from envault.audit import record_event


class RotationError(Exception):
    """Raised when key rotation fails."""


def rotate_keys(
    vault: Vault,
    secret_key_fingerprint: str,
    new_recipients: List[str] | None = None,
) -> Path:
    """Re-encrypt the vault's .env file for the current (or provided) recipients.

    Steps:
      1. Decrypt the existing vault file using *secret_key_fingerprint*.
      2. Optionally replace the recipient list with *new_recipients*.
      3. Re-encrypt the plaintext for the (updated) recipients.
      4. Overwrite the vault file in place.
      5. Record an audit event.

    Returns the path to the re-encrypted vault file.
    """
    vault_file = vault.vault_dir / "secrets.env.gpg"
    if not vault_file.exists():
        raise RotationError(f"Vault file not found: {vault_file}")

    # --- decrypt current ciphertext ---
    ciphertext = vault_file.read_bytes()
    try:
        plaintext = decrypt(ciphertext, secret_key_fingerprint)
    except Exception as exc:
        raise RotationError(f"Decryption failed during rotation: {exc}") from exc

    # --- update recipients if requested ---
    if new_recipients is not None:
        for fp in new_recipients:
            vault.add_recipient(fp)
        # Remove recipients that are no longer in the new list
        for fp in list(vault.get_recipients()):
            if fp not in new_recipients:
                vault.remove_recipient(fp)

    recipients = vault.get_recipients()
    if not recipients:
        raise RotationError("No recipients configured — cannot re-encrypt.")

    # --- re-encrypt for current recipients ---
    try:
        new_ciphertext = encrypt(plaintext, recipients)
    except Exception as exc:
        raise RotationError(f"Re-encryption failed during rotation: {exc}") from exc

    vault_file.write_bytes(new_ciphertext)

    record_event(
        vault.vault_dir,
        "rotate",
        {
            "rotated_by": secret_key_fingerprint,
            "recipients": list(recipients),
        },
    )

    return vault_file
