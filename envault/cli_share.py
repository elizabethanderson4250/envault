"""CLI commands for bundle export/import (team sharing)."""

from __future__ import annotations

from pathlib import Path

import click

from envault.vault import Vault
from envault.share import export_bundle, import_bundle, ShareError


@click.group("share")
def share_group():
    """Export and import encrypted .env bundles for team sharing."""


@share_group.command("export")
@click.option(
    "--vault-dir",
    default=".",
    show_default=True,
    help="Directory containing the vault.",
    type=click.Path(file_okay=False),
)
@click.option(
    "--output",
    "-o",
    default="envault-bundle.json",
    show_default=True,
    help="Output bundle file path.",
    type=click.Path(dir_okay=False),
)
@click.option("--actor", default="cli", hidden=True)
def export_cmd(vault_dir: str, output: str, actor: str) -> None:
    """Encrypt the project .env and write a shareable bundle."""
    vault = Vault(Path(vault_dir))
    out_path = Path(output)
    try:
        result = export_bundle(vault, out_path, actor=actor)
        click.echo(f"Bundle written to {result}")
    except ShareError as exc:
        raise click.ClickException(str(exc)) from exc


@share_group.command("import")
@click.argument("bundle", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--vault-dir",
    default=".",
    show_default=True,
    help="Directory containing the vault.",
    type=click.Path(file_okay=False),
)
@click.option("--actor", default="cli", hidden=True)
def import_cmd(bundle: str, vault_dir: str, actor: str) -> None:
    """Decrypt a bundle and restore the .env file."""
    vault = Vault(Path(vault_dir))
    try:
        result = import_bundle(vault, Path(bundle), actor=actor)
        click.echo(f".env written to {result}")
    except ShareError as exc:
        raise click.ClickException(str(exc)) from exc
