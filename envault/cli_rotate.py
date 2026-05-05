"""CLI commands for key rotation."""

from __future__ import annotations

import click

from envault.vault import Vault
from envault.rotate import rotate_keys, RotationError


@click.group("rotate")
def rotate_group() -> None:
    """Commands for rotating encryption keys."""


@rotate_group.command("run")
@click.argument("vault_dir")
@click.argument("secret_key_fingerprint")
@click.option(
    "--add-recipient",
    "add_recipients",
    multiple=True,
    metavar="FINGERPRINT",
    help="Add a recipient before re-encrypting (may be repeated).",
)
@click.option(
    "--replace-recipients",
    "replace_recipients",
    multiple=True,
    metavar="FINGERPRINT",
    help="Replace the entire recipient list before re-encrypting.",
)
def rotate_cmd(
    vault_dir: str,
    secret_key_fingerprint: str,
    add_recipients: tuple[str, ...],
    replace_recipients: tuple[str, ...],
) -> None:
    """Re-encrypt VAULT_DIR using SECRET_KEY_FINGERPRINT for decryption.

    The vault is decrypted with SECRET_KEY_FINGERPRINT, then re-encrypted
    for the configured recipients (optionally updated via flags).
    """
    vault = Vault(vault_dir)

    if replace_recipients and add_recipients:
        raise click.UsageError(
            "--add-recipient and --replace-recipients are mutually exclusive."
        )

    new_recipients: list[str] | None = None
    if replace_recipients:
        new_recipients = list(replace_recipients)
    elif add_recipients:
        new_recipients = list(vault.get_recipients()) + list(add_recipients)

    try:
        out_path = rotate_keys(vault, secret_key_fingerprint, new_recipients)
        click.echo(f"Rotation complete. Vault re-encrypted at: {out_path}")
        click.echo("Recipients:")
        for fp in vault.get_recipients():
            click.echo(f"  {fp}")
    except RotationError as exc:
        raise click.ClickException(str(exc)) from exc
