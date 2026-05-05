"""CLI commands for searching env keys/values inside a locked vault."""

from __future__ import annotations

import click

from envault.vault import Vault
from envault.crypto import decrypt
from envault.search import search_env, format_results, SearchError


@click.group("search")
def search_group() -> None:
    """Search env keys and values within a vault."""


@search_group.command("run")
@click.argument("pattern")
@click.option(
    "--vault-dir",
    default=".",
    show_default=True,
    help="Path to the vault directory.",
)
@click.option(
    "--keys/--no-keys",
    default=True,
    show_default=True,
    help="Search within key names.",
)
@click.option(
    "--values",
    is_flag=True,
    default=False,
    help="Also search within values.",
)
@click.option(
    "--show-values",
    is_flag=True,
    default=False,
    help="Print matched values in output.",
)
@click.option(
    "--case-sensitive",
    is_flag=True,
    default=False,
    help="Use case-sensitive matching.",
)
def search_cmd(
    pattern: str,
    vault_dir: str,
    keys: bool,
    values: bool,
    show_values: bool,
    case_sensitive: bool,
) -> None:
    """Search PATTERN across the decrypted .env contents."""
    vault = Vault(vault_dir)
    vault_file = vault.vault_file

    if not vault_file.exists():
        raise click.ClickException("No locked vault found. Run 'envault lock' first.")

    recipients = vault.get_recipients()
    if not recipients:
        raise click.ClickException("No recipients configured for this vault.")

    try:
        plaintext = decrypt(vault_file.read_bytes())
    except Exception as exc:  # pragma: no cover
        raise click.ClickException(f"Decryption failed: {exc}") from exc

    try:
        results = search_env(
            plaintext,
            pattern,
            search_keys=keys,
            search_values=values,
            case_sensitive=case_sensitive,
        )
    except SearchError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Searching for '{pattern}' — {len(results)} match(es) found.")
    click.echo(format_results(results, show_values=show_values))
