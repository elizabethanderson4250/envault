"""CLI commands for vault tag management."""
from __future__ import annotations

import click

from envault.vault import Vault
from envault.tag import TagError, add_tag, remove_tag, get_tags, format_tags


@click.group("tag")
def tag_group() -> None:
    """Manage tags attached to the vault."""


@tag_group.command("add")
@click.argument("tag")
@click.option(
    "--vault-dir",
    default=".",
    show_default=True,
    help="Path to the vault directory.",
)
def add_cmd(tag: str, vault_dir: str) -> None:
    """Attach TAG to the vault."""
    vault = Vault(vault_dir)
    try:
        updated = add_tag(vault, tag)
    except TagError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Tag '{tag}' added. Current tags: {format_tags(updated)}")


@tag_group.command("remove")
@click.argument("tag")
@click.option(
    "--vault-dir",
    default=".",
    show_default=True,
    help="Path to the vault directory.",
)
def remove_cmd(tag: str, vault_dir: str) -> None:
    """Remove TAG from the vault."""
    vault = Vault(vault_dir)
    try:
        updated = remove_tag(vault, tag)
    except TagError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Tag '{tag}' removed. Current tags: {format_tags(updated)}")


@tag_group.command("list")
@click.option(
    "--vault-dir",
    default=".",
    show_default=True,
    help="Path to the vault directory.",
)
def list_cmd(vault_dir: str) -> None:
    """List all tags attached to the vault."""
    vault = Vault(vault_dir)
    tags = get_tags(vault)
    click.echo(format_tags(tags))
