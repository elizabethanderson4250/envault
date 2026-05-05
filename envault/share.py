"""Team sharing helpers: export/import encrypted env bundles."""

from __future__ import annotations

import json
import base64
from pathlib import Path
from typing import List, Optional

from envault.crypto import encrypt, decrypt, GPGError
from envault.vault import Vault
from envault.audit import record_event


class ShareError(Exception):
    """Raised when a share/import operation fails."""


def export_bundle(
    vault: Vault,
    output_path: Path,
    recipients: Optional[List[str]] = None,
    actor: str = "unknown",
) -> Path:
    """Encrypt the vault's .env file and write a shareable bundle JSON.

    The bundle contains the base64-encoded GPG ciphertext plus metadata
    so a teammate can import it with ``import_bundle``.
    """
    env_file = vault.vault_dir / ".env"
    if not env_file.exists():
        raise ShareError(f".env file not found in {vault.vault_dir}")

    plaintext = env_file.read_bytes()
    if recipients is None:
        recipients = vault.get_recipients()
    if not recipients:
        raise ShareError("No recipients configured — add recipients before exporting.")

    ciphertext = encrypt(plaintext, recipients)
    bundle = {
        "version": 1,
        "recipients": recipients,
        "ciphertext": base64.b64encode(ciphertext).decode(),
    }
    output_path.write_text(json.dumps(bundle, indent=2))
    record_event(vault.vault_dir, "export", actor=actor, details={"output": str(output_path)})
    return output_path


def import_bundle(vault: Vault, bundle_path: Path, actor: str = "unknown") -> Path:
    """Decrypt a bundle produced by ``export_bundle`` and write .env.

    Returns the path to the written .env file.
    """
    if not bundle_path.exists():
        raise ShareError(f"Bundle file not found: {bundle_path}")

    try:
        bundle = json.loads(bundle_path.read_text())
    except json.JSONDecodeError as exc:
        raise ShareError(f"Invalid bundle JSON: {exc}") from exc

    if bundle.get("version") != 1:
        raise ShareError("Unsupported bundle version.")

    try:
        ciphertext = base64.b64decode(bundle["ciphertext"])
    except (KeyError, ValueError) as exc:
        raise ShareError(f"Malformed bundle ciphertext: {exc}") from exc

    try:
        plaintext = decrypt(ciphertext)
    except GPGError as exc:
        raise ShareError(f"Decryption failed: {exc}") from exc

    env_file = vault.vault_dir / ".env"
    env_file.write_bytes(plaintext)
    record_event(vault.vault_dir, "import", actor=actor, details={"source": str(bundle_path)})
    return env_file
