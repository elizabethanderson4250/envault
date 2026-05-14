"""CLI commands for sanitizing .env files."""

from __future__ import annotations

from pathlib import Path

import click

from .sanitize import SanitizeError, apply_sanitize, format_sanitize, sanitize_env


@click.group("sanitize")
def sanitize_group() -> None:
    """Sanitize .env file values."""


@sanitize_group.command("check")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
def check_cmd(env_file: str) -> None:
    """Check an env file for sanitization issues without modifying it."""
    path = Path(env_file)
    try:
        results = sanitize_env(path)
    except SanitizeError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    changed = [r for r in results if r.changed]
    summary = format_sanitize(results)
    click.echo(summary)
    if changed:
        raise SystemExit(1)


@sanitize_group.command("fix")
@click.argument("env_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--quiet", "-q", is_flag=True, help="Suppress output when no changes are made.")
def fix_cmd(env_file: str, quiet: bool) -> None:
    """Sanitize an env file in-place, fixing any issues found."""
    path = Path(env_file)
    try:
        results = apply_sanitize(path)
    except SanitizeError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    summary = format_sanitize(results)
    changed = [r for r in results if r.changed]
    if changed or not quiet:
        click.echo(summary)
    if changed:
        click.echo(f"File updated: {path}")
