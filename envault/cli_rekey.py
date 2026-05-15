"""CLI commands for re-keying an encrypted vault."""

from __future__ import annotations

from pathlib import Path

import click

from envault.rekey import rekey, RekeyError


@click.group("rekey")
def rekey_group() -> None:
    """Re-encrypt the vault for a new set of recipients."""


@rekey_group.command("run")
@click.option(
    "--vault-dir",
    default=".",
    show_default=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Directory containing the vault.",
)
@click.option(
    "--recipient",
    "-r",
    "recipients",
    multiple=True,
    required=True,
    help="GPG fingerprint of a new recipient (repeatable).",
)
@click.option(
    "--passphrase",
    default=None,
    help="Passphrase for the existing encrypted file (if required).",
)
def rekey_cmd(
    vault_dir: Path,
    recipients: tuple[str, ...],
    passphrase: str | None,
) -> None:
    """Re-encrypt the vault for RECIPIENTS.

    The vault is decrypted using the current key(s) and immediately
    re-encrypted for the supplied recipient fingerprints.  The
    recipient list stored in vault metadata is updated accordingly.
    """
    try:
        out = rekey(
            vault_dir,
            list(recipients),
            old_passphrase=passphrase,
        )
        click.echo(f"Vault re-keyed successfully: {out}")
        click.echo(f"New recipients ({len(recipients)}):")
        for fp in recipients:
            click.echo(f"  {fp}")
    except RekeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1) from exc
