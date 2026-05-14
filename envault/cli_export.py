"""CLI commands for exporting decrypted .env files to various formats."""
from __future__ import annotations

import sys
from pathlib import Path

import click

from .export_env import ExportError, SUPPORTED_FORMATS, export_env, write_export
from .vault import Vault
from .crypto import decrypt, GPGError
from .audit import record_event


@click.group("export")
def export_group() -> None:
    """Export decrypted .env to dotenv / JSON / shell format."""


@export_group.command("run")
@click.argument("vault_dir", default=".", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--format", "fmt",
    default="dotenv",
    show_default=True,
    type=click.Choice(SUPPORTED_FORMATS, case_sensitive=False),
    help="Output format.",
)
@click.option(
    "--output", "-o",
    default=None,
    type=click.Path(dir_okay=False),
    help="Write output to FILE instead of stdout.",
)
def export_cmd(vault_dir: str, fmt: str, output: str | None) -> None:
    """Decrypt the vault and export its .env in the chosen format."""
    vdir = Path(vault_dir)
    vault = Vault(vdir)

    vault_file = vdir / "vault.env.gpg"
    if not vault_file.exists():
        click.echo("Error: vault file not found. Run 'envault lock' first.", err=True)
        sys.exit(1)

    try:
        env_text = decrypt(vault_file)
    except GPGError as exc:
        click.echo(f"Decryption failed: {exc}", err=True)
        sys.exit(1)

    try:
        result = export_env(env_text, fmt)
    except ExportError as exc:
        click.echo(f"Export error: {exc}", err=True)
        sys.exit(1)

    record_event(vdir, "export", {"format": fmt, "output": output or "<stdout>"})

    if output:
        output_path = Path(output)
        if output_path.exists():
            click.confirm(
                f"File '{output}' already exists. Overwrite?",
                abort=True,
            )
        write_export(result, output_path)
        click.echo(f"Exported to {output} [{fmt}]")
    else:
        click.echo(result, nl=False)
