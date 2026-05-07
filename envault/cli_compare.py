"""CLI command group for comparing two encrypted vault files."""

from __future__ import annotations

from pathlib import Path

import click

from envault.compare import compare_vaults, format_compare, CompareError


@click.group("compare")
def compare_group() -> None:
    """Compare two encrypted .env vault files."""


@compare_group.command("show")
@click.argument("left", type=click.Path(exists=True, dir_okay=False))
@click.argument("right", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--passphrase",
    envvar="ENVAULT_PASSPHRASE",
    default=None,
    help="Passphrase for symmetric decryption (or set ENVAULT_PASSPHRASE).",
)
@click.option(
    "--exit-code",
    is_flag=True,
    default=False,
    help="Exit with code 1 when differences are found.",
)
def compare_show(
    left: str,
    right: str,
    passphrase: str | None,
    exit_code: bool,
) -> None:
    """Show differences between two encrypted vault files."""
    try:
        result = compare_vaults(Path(left), Path(right), passphrase=passphrase)
    except CompareError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(format_compare(result))

    if exit_code and result.has_changes:
        raise SystemExit(1)
