"""CLI commands for session management."""

from __future__ import annotations

from pathlib import Path

import click

from .session import (
    SessionError,
    clear_session,
    format_session,
    is_session_valid,
    read_session,
    start_session,
)


@click.group("session")
def session_group() -> None:
    """Manage vault unlock sessions."""


@session_group.command("start")
@click.argument("vault_dir", default=".", type=click.Path(file_okay=False))
def start_cmd(vault_dir: str) -> None:
    """Start (or refresh) a session for VAULT_DIR."""
    try:
        ts = start_session(Path(vault_dir))
        click.echo(f"Session started at {ts.strftime('%Y-%m-%d %H:%M:%S UTC')}.")
    except SessionError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@session_group.command("show")
@click.argument("vault_dir", default=".", type=click.Path(file_okay=False))
def show_cmd(vault_dir: str) -> None:
    """Show the current session for VAULT_DIR."""
    try:
        ts = read_session(Path(vault_dir))
        click.echo(format_session(ts))
    except SessionError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@session_group.command("check")
@click.option("--idle", default=30, show_default=True, help="Idle timeout in minutes.")
@click.argument("vault_dir", default=".", type=click.Path(file_okay=False))
def check_cmd(idle: int, vault_dir: str) -> None:
    """Exit 0 if session is valid, 1 if expired or absent."""
    try:
        valid = is_session_valid(Path(vault_dir), idle)
    except SessionError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    if valid:
        click.echo("Session is active.")
    else:
        click.echo("Session expired or not found.", err=True)
        raise SystemExit(1)


@session_group.command("clear")
@click.argument("vault_dir", default=".", type=click.Path(file_okay=False))
def clear_cmd(vault_dir: str) -> None:
    """Clear the active session for VAULT_DIR."""
    clear_session(Path(vault_dir))
    click.echo("Session cleared.")
