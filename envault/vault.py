"""Vault: read, write, and manage encrypted .env files."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from envault.crypto import encrypt, decrypt

DEFAULT_VAULT_FILE = ".env.vault"
DEFAULT_META_FILE = ".env.vault.meta"


class Vault:
    """Represents an encrypted .env vault for a project."""

    def __init__(
        self,
        vault_path: Path = Path(DEFAULT_VAULT_FILE),
        meta_path: Path = Path(DEFAULT_META_FILE),
    ) -> None:
        self.vault_path = vault_path
        self.meta_path = meta_path

    # ------------------------------------------------------------------
    # Metadata helpers
    # ------------------------------------------------------------------

    def _load_meta(self) -> Dict:
        if self.meta_path.exists():
            with self.meta_path.open() as fh:
                return json.load(fh)
        return {"recipients": []}

    def _save_meta(self, meta: Dict) -> None:
        with self.meta_path.open("w") as fh:
            json.dump(meta, fh, indent=2)

    def get_recipients(self) -> List[str]:
        """Return the list of GPG recipients stored in the vault metadata."""
        return self._load_meta().get("recipients", [])

    def add_recipient(self, key_id: str) -> None:
        """Add a GPG key ID to the recipient list."""
        meta = self._load_meta()
        if key_id not in meta["recipients"]:
            meta["recipients"].append(key_id)
            self._save_meta(meta)

    def remove_recipient(self, key_id: str) -> None:
        """Remove a GPG key ID from the recipient list."""
        meta = self._load_meta()
        meta["recipients"] = [r for r in meta["recipients"] if r != key_id]
        self._save_meta(meta)

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def lock(self, env_path: Path = Path(".env")) -> None:
        """Encrypt *env_path* and write the ciphertext to the vault file."""
        recipients = self.get_recipients()
        if not recipients:
            raise ValueError(
                "No recipients configured. Add at least one GPG key with `envault add-key`."
            )
        if not env_path.exists():
            raise FileNotFoundError(f"Env file not found: {env_path}")
        plaintext = env_path.read_bytes()
        ciphertext = encrypt(plaintext, recipients)
        self.vault_path.write_bytes(ciphertext)

    def unlock(
        self,
        env_path: Path = Path(".env"),
        passphrase: Optional[str] = None,
        overwrite: bool = False,
    ) -> None:
        """Decrypt the vault file and write the plaintext to *env_path*."""
        if not self.vault_path.exists():
            raise FileNotFoundError(f"Vault file not found: {self.vault_path}")
        if env_path.exists() and not overwrite:
            raise FileExistsError(
                f"{env_path} already exists. Use overwrite=True to replace it."
            )
        ciphertext = self.vault_path.read_bytes()
        plaintext = decrypt(ciphertext, passphrase=passphrase)
        env_path.write_bytes(plaintext)
