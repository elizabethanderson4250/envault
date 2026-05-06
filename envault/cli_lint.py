"""CLI commands for linting .env files."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from .lint import lint_env, format_lint


@click.group('lint')
def lint_group() -> None:
    """Lint .env files for common issues."""


@lint_group.command('check')
@click.argument('env_file', default='.env', metavar='ENV_FILE')
@click.option('--strict', is_flag=True, default=False,
              help='Exit with non-zero status on warnings as well as errors.')
def lint_check(env_file: str, strict: bool) -> None:
    """Check ENV_FILE for duplicate keys, empty values, and invalid names.

    Exits with status 1 if errors are found, or if --strict and warnings exist.
    """
    path = Path(env_file)
    result = lint_env(path)
    output = format_lint(result)
    click.echo(output)

    if not result.ok:
        errors = [i for i in result.issues if i.code.startswith('E')]
        warnings = [i for i in result.issues if i.code.startswith('W')]
        if errors or (strict and warnings):
            sys.exit(1)
