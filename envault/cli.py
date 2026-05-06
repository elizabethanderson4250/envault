"""Main CLI entry point for envault."""

from __future__ import annotations

import click
from pathlib import Path

from envault.vault import Vault
from envault.crypto import encrypt, decrypt
from envault.cli_share import share_group
from envault.cli_rotate import rotate_group
from envault.cli_diff import diff_group
from envault.cli_search import search_group
from envault.cli_history import history_group
from envault.cli_status import status_group
from envault.cli_lint import lint_group
from envault.cli_template import template_group
from envault.cli_import import import_group
from envault.cli_export import export_group
from envault.cli_tag import tag_group
from envault.cli_pin import pin_group
from envault.cli_policy import policy_group


@click.group()
def cli() -> None:
    """envault — encrypted per-project .env manager."""


@cli.command()
@click.argument("fingerprint")
@click.argument("vault_dir", default=".", type=click.Path())
def add_recipient(fingerprint: str, vault_dir: str) -> None:
    """Add a GPG recipient by fingerprint."""
    vault = Vault(Path(vault_dir))
    vault.add_recipient(fingerprint)
    click.echo(f"Added recipient: {fingerprint}")


@cli.command()
@click.argument("fingerprint")
@click.argument("vault_dir", default=".", type=click.Path())
def remove_recipient(fingerprint: str, vault_dir: str) -> None:
    """Remove a GPG recipient by fingerprint."""
    vault = Vault(Path(vault_dir))
    vault.remove_recipient(fingerprint)
    click.echo(f"Removed recipient: {fingerprint}")


@cli.command("list-recipients")
@click.argument("vault_dir", default=".", type=click.Path())
def list_recipients(vault_dir: str) -> None:
    """List all GPG recipients."""
    vault = Vault(Path(vault_dir))
    recipients = vault.get_recipients()
    if not recipients:
        click.echo("No recipients configured.")
    for fp in recipients:
        click.echo(fp)


@cli.command()
@click.argument("env_file", type=click.Path(exists=True))
@click.argument("vault_dir", default=".", type=click.Path())
def lock(env_file: str, vault_dir: str) -> None:
    """Encrypt .env file into the vault."""
    vault = Vault(Path(vault_dir))
    plaintext = Path(env_file).read_bytes()
    recipients = vault.get_recipients()
    ciphertext = encrypt(plaintext, recipients)
    vault.write_locked(ciphertext)
    click.echo("Vault locked.")


@cli.command()
@click.argument("vault_dir", default=".", type=click.Path())
@click.argument("output", default=".env", type=click.Path())
def unlock(vault_dir: str, output: str) -> None:
    """Decrypt vault into a .env file."""
    vault = Vault(Path(vault_dir))
    ciphertext = vault.read_locked()
    plaintext = decrypt(ciphertext)
    Path(output).write_bytes(plaintext)
    click.echo(f"Vault unlocked to {output}.")


cli.add_command(share_group, "share")
cli.add_command(rotate_group, "rotate")
cli.add_command(diff_group, "diff")
cli.add_command(search_group, "search")
cli.add_command(history_group, "history")
cli.add_command(status_group, "status")
cli.add_command(lint_group, "lint")
cli.add_command(template_group, "template")
cli.add_command(import_group, "import")
cli.add_command(export_group, "export")
cli.add_command(tag_group, "tag")
cli.add_command(pin_group, "pin")
cli.add_command(policy_group, "policy")
