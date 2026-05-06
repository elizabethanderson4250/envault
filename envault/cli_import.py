"""CLI commands for importing .env values into the vault."""

from __future__ import annotations

from pathlib import Path

import click

from envault.import_env import ImportError, merge_env, parse_env_file, write_env_file


@click.group("import")
def import_group() -> None:
    """Import .env values from an external file."""


@import_group.command("run")
@click.argument("source", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--vault-dir",
    default=".",
    show_default=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Directory containing the vault .env file.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite existing keys with values from SOURCE.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would change without writing anything.",
)
def import_cmd(
    source: Path,
    vault_dir: Path,
    overwrite: bool,
    dry_run: bool,
) -> None:
    """Import key-value pairs from SOURCE into the vault .env file."""
    target = vault_dir / ".env"

    try:
        incoming = parse_env_file(source)
    except ImportError as exc:
        raise click.ClickException(str(exc)) from exc

    existing: dict = {}
    if target.exists():
        try:
            existing = parse_env_file(target)
        except ImportError:
            existing = {}

    merged, added, skipped = merge_env(existing, incoming, overwrite=overwrite)

    if dry_run:
        click.echo(f"Would add/update {len(added)} key(s): {', '.join(added) or 'none'}")
        click.echo(f"Would skip {len(skipped)} key(s): {', '.join(skipped) or 'none'}")
        return

    write_env_file(target, merged)
    click.echo(f"Imported {len(added)} key(s): {', '.join(added) or 'none'}")
    if skipped:
        click.echo(
            f"Skipped {len(skipped)} existing key(s) (use --overwrite to replace): "
            f"{', '.join(skipped)}"
        )
