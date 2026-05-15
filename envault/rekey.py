"""Re-encrypt the vault file for a new set of recipients."""

from __future__ import annotations

from pathlib import Path
from typing import List

from envault.crypto import decrypt, encrypt, GPGError
from envault.vault import Vault
from envault.audit import record_event


class RekeyError(Exception):
    """Raised when re-encryption fails."""


def rekey(
    vault_dir: Path,
    new_recipients: List[str],
    *,
    old_passphrase: str | None = None,
) -> Path:
    """Re-encrypt the locked vault file for *new_recipients*.

    Parameters
    ----------
    vault_dir:
        Directory that contains the vault metadata and encrypted file.
    new_recipients:
        GPG fingerprints of the new recipient set.
    old_passphrase:
        Optional passphrase forwarded to :func:`~envault.crypto.decrypt`.

    Returns
    -------
    Path
        The path to the newly written encrypted file.
    """
    if not new_recipients:
        raise RekeyError("new_recipients must not be empty")

    vault = Vault(vault_dir)
    vault_file = vault_dir / "vault.env.gpg"

    if not vault_file.exists():
        raise RekeyError(f"Encrypted vault file not found: {vault_file}")

    # Decrypt with the existing recipients / key.
    try:
        plaintext: bytes = decrypt(vault_file, passphrase=old_passphrase)
    except GPGError as exc:
        raise RekeyError(f"Failed to decrypt vault for re-keying: {exc}") from exc

    # Re-encrypt for the new recipients.
    try:
        ciphertext: bytes = encrypt(plaintext, recipients=new_recipients)
    except GPGError as exc:
        raise RekeyError(f"Failed to re-encrypt vault: {exc}") from exc

    vault_file.write_bytes(ciphertext)

    # Update stored recipients in metadata.
    vault.set_recipients(new_recipients)

    record_event(
        vault_dir,
        "rekey",
        {"new_recipients": new_recipients},
    )

    return vault_file
