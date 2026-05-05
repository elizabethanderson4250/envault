"""Command-line interface for envault."""

import sys
import click

from envault.vault import Vault
from envault.crypto import GPGError, list_secret_keys


@click.group()
@click.option(
    "--vault-dir",
    default=".",
    show_default=True,
    help="Directory containing the .envault metadata.",
)
@click.pass_context
def cli(ctx: click.Context, vault_dir: str) -> None:
    """envault — manage and encrypt per-project .env files."""
    ctx.ensure_object(dict)
    ctx.obj["vault_dir"] = vault_dir


@cli.command("add-recipient")
@click.argument("fingerprint")
@click.pass_context
def add_recipient(ctx: click.Context, fingerprint: str) -> None:
    """Add a GPG FINGERPRINT to the recipient list."""
    vault = Vault(ctx.obj["vault_dir"])
    vault.add_recipient(fingerprint)
    click.echo(f"Recipient {fingerprint} added.")


@cli.command("remove-recipient")
@click.argument("fingerprint")
@click.pass_context
def remove_recipient(ctx: click.Context, fingerprint: str) -> None:
    """Remove a GPG FINGERPRINT from the recipient list."""
    vault = Vault(ctx.obj["vault_dir"])
    vault.remove_recipient(fingerprint)
    click.echo(f"Recipient {fingerprint} removed.")


@cli.command("list-recipients")
@click.pass_context
def list_recipients(ctx: click.Context) -> None:
    """List all current recipients."""
    vault = Vault(ctx.obj["vault_dir"])
    recipients = vault.get_recipients()
    if not recipients:
        click.echo("No recipients configured.")
    else:
        for fp in recipients:
            click.echo(fp)


@cli.command("lock")
@click.option("--env-file", default=".env", show_default=True, help="Path to .env file to encrypt.")
@click.pass_context
def lock(ctx: click.Context, env_file: str) -> None:
    """Encrypt the .env file for all recipients."""
    vault = Vault(ctx.obj["vault_dir"])
    try:
        vault.lock(env_file)
        click.echo("Vault locked successfully.")
    except (GPGError, ValueError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@cli.command("unlock")
@click.option("--env-file", default=".env", show_default=True, help="Destination path for decrypted .env.")
@click.pass_context
def unlock(ctx: click.Context, env_file: str) -> None:
    """Decrypt the vault file to a .env file."""
    vault = Vault(ctx.obj["vault_dir"])
    try:
        vault.unlock(env_file)
        click.echo(f"Vault unlocked to {env_file}.")
    except (GPGError, FileNotFoundError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


@cli.command("list-keys")
def list_keys() -> None:
    """List GPG secret keys available on this machine."""
    try:
        keys = list_secret_keys()
        if not keys:
            click.echo("No secret keys found.")
        else:
            for key in keys:
                click.echo(key)
    except GPGError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
