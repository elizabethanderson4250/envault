"""CLI commands for diffing .env file versions."""

from __future__ import annotations

import click

from envault.diff import diff_env, format_diff, unified_diff
from envault.vault import Vault


@click.group("diff")
def diff_group() -> None:
    """Show differences between .env versions."""


@diff_group.command("show")
@click.argument("vault_dir", default=".", type=click.Path(exists=True, file_okay=False))
@click.option("--unified", "-u", is_flag=True, help="Output a unified diff instead of summary.")
@click.option("--reveal", is_flag=True, help="Show actual values instead of masking them.")
@click.option(
    "--from-file",
    "from_file",
    default=None,
    help="Path to the 'old' .env file. Defaults to the last committed snapshot.",
    type=click.Path(exists=True, dir_okay=False),
)
@click.option(
    "--to-file",
    "to_file",
    default=None,
    help="Path to the 'new' .env file. Defaults to the working .env.",
    type=click.Path(exists=True, dir_okay=False),
)
def diff_show(
    vault_dir: str,
    unified: bool,
    reveal: bool,
    from_file: str | None,
    to_file: str | None,
) -> None:
    """Compare two .env files and display the differences."""
    vault = Vault(vault_dir)

    # Resolve files: fall back to vault snapshot vs working .env
    snapshot_path = vault.snapshot_path
    working_path = vault.env_path

    old_path = from_file or (str(snapshot_path) if snapshot_path.exists() else None)
    new_path = to_file or (str(working_path) if working_path.exists() else None)

    if old_path is None:
        raise click.ClickException("No 'old' file found. Use --from-file or create a snapshot.")
    if new_path is None:
        raise click.ClickException("No 'new' file found. Use --to-file or ensure .env exists.")

    old_text = click.open_file(old_path).read()
    new_text = click.open_file(new_path).read()

    if unified:
        result = unified_diff(old_text, new_text, fromfile=old_path, tofile=new_path)
        click.echo(result or "(no changes)")
    else:
        d = diff_env(old_text, new_text)
        for line in format_diff(d, mask_values=not reveal):
            click.echo(line)
