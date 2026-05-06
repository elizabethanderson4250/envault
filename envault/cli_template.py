"""CLI commands for template generation."""

from __future__ import annotations

from pathlib import Path

import click

from .template import TemplateError, write_template


@click.group("template")
def template_group() -> None:
    """Generate .env.example templates from your vault."""


@template_group.command("generate")
@click.argument("vault_dir", default=".", type=click.Path(file_okay=False))
@click.option(
    "--env-file",
    default=".env",
    show_default=True,
    help="Name of the plaintext env file inside VAULT_DIR.",
)
@click.option(
    "--output",
    default=".env.example",
    show_default=True,
    help="Output file path (relative to VAULT_DIR or absolute).",
)
@click.option(
    "--placeholder",
    default="",
    show_default=True,
    help="Value to substitute for every key.",
)
def generate_cmd(
    vault_dir: str,
    env_file: str,
    output: str,
    placeholder: str,
) -> None:
    """Generate a .env.example from the plaintext env file."""
    base = Path(vault_dir)
    src = base / env_file
    out = Path(output) if Path(output).is_absolute() else base / output
    try:
        dest = write_template(src, out, placeholder=placeholder)
        click.echo(f"Template written to {dest}")
    except TemplateError as exc:
        raise click.ClickException(str(exc)) from exc
