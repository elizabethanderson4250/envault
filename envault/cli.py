"""Main CLI entry point for envault."""

from __future__ import annotations

import click

from .vault import Vault
from .crypto import encrypt, decrypt, list_secret_keys, GPGError
from .cli_share import share_group
from .cli_rotate import rotate_group
from .cli_diff import diff_group
from .cli_search import search_group
from .cli_history import history_group
from .cli_status import status_group
from .cli_lint import lint_group
from .cli_template import template_group


@click.group()
def cli() -> None:
    """envault — encrypted .env manager with GPG team sharing."""


@cli.command()
@click.argument("fingerprint")
@click.argument("vault_dir", default=".", type=click.Path(file_okay=False))
def add_recipient(fingerprint: str, vault_dir: str) -> None:
    """Add a GPG recipient to the vault."""
    vault = Vault(vault_dir)
    vault.add_recipient(fingerprint)
    click.echo(f"Added recipient {fingerprint}")


@cli.command()
@click.argument("fingerprint")
@click.argument("vault_dir", default=".", type=click.Path(file_okay=False))
def remove_recipient(fingerprint: str, vault_dir: str) -> None:
    """Remove a GPG recipient from the vault."""
    vault = Vault(vault_dir)
    vault.remove_recipient(fingerprint)
    click.echo(f"Removed recipient {fingerprint}")


@cli.command()
@click.argument("vault_dir", default=".", type=click.Path(file_okay=False))
def list_recipients(vault_dir: str) -> None:
    """List all GPG recipients for the vault."""
    vault = Vault(vault_dir)
    recipients = vault.get_recipients()
    if not recipients:
        click.echo("No recipients configured.")
    else:
        for fp in recipients:
            click.echo(fp)


@cli.command()
@click.argument("vault_dir", default=".", type=click.Path(file_okay=False))
@click.option("--env-file", default=".env", show_default=True)
def lock(vault_dir: str, env_file: str) -> None:
    """Encrypt the .env file into the vault."""
    vault = Vault(vault_dir)
    vault.lock(env_file=env_file)
    click.echo("Vault locked.")


@cli.command()
@click.argument("vault_dir", default=".", type=click.Path(file_okay=False))
@click.option("--env-file", default=".env", show_default=True)
def unlock(vault_dir: str, env_file: str) -> None:
    """Decrypt the vault into a .env file."""
    vault = Vault(vault_dir)
    vault.unlock(env_file=env_file)
    click.echo("Vault unlocked.")


cli.add_command(share_group, name="share")
cli.add_command(rotate_group, name="rotate")
cli.add_command(diff_group, name="diff")
cli.add_command(search_group, name="search")
cli.add_command(history_group, name="history")
cli.add_command(status_group, name="status")
cli.add_command(lint_group, name="lint")
cli.add_command(template_group, name="template")
