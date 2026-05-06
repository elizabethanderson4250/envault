"""CLI command: envault status — show vault status summary."""

import click

from envault.status import format_status, get_status


@click.group("status")
def status_group() -> None:  # pragma: no cover
    """Vault status commands."""


@status_group.command("show")
@click.option(
    "--vault-dir",
    default=".",
    show_default=True,
    help="Path to the vault directory.",
)
def status_show(vault_dir: str) -> None:
    """Display the current status of the vault."""
    try:
        s = get_status(vault_dir)
        click.echo(format_status(s))
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
