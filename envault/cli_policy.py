"""CLI commands for managing vault policy."""

from __future__ import annotations

import click
from pathlib import Path

from envault.policy import (
    PolicyRule,
    PolicyError,
    load_policy,
    save_policy,
    check_policy,
    format_violations,
)
from envault.vault import Vault
from envault.export_env import parse_env_pairs


@click.group("policy")
def policy_group() -> None:
    """Manage .env policy rules."""


@policy_group.command("show")
@click.argument("vault_dir", default=".", type=click.Path())
def show_policy(vault_dir: str) -> None:
    """Show current policy for a vault."""
    try:
        policy = load_policy(Path(vault_dir))
    except PolicyError as exc:
        raise click.ClickException(str(exc))
    click.echo(f"required_keys:    {policy.required_keys or '(none)'}")
    click.echo(f"forbidden_keys:   {policy.forbidden_keys or '(none)'}")
    click.echo(f"max_value_length: {policy.max_value_length or '(unlimited)'}")
    click.echo(f"min_recipients:   {policy.min_recipients}")


@policy_group.command("set")
@click.option("--require", multiple=True, metavar="KEY", help="Add required key.")
@click.option("--forbid", multiple=True, metavar="KEY", help="Add forbidden key.")
@click.option("--max-value-length", type=int, default=None)
@click.option("--min-recipients", type=int, default=1)
@click.argument("vault_dir", default=".", type=click.Path())
def set_policy(
    require: tuple,
    forbid: tuple,
    max_value_length: int | None,
    min_recipients: int,
    vault_dir: str,
) -> None:
    """Create or overwrite the vault policy."""
    policy = PolicyRule(
        required_keys=list(require),
        forbidden_keys=list(forbid),
        max_value_length=max_value_length,
        min_recipients=min_recipients,
    )
    try:
        save_policy(Path(vault_dir), policy)
    except PolicyError as exc:
        raise click.ClickException(str(exc))
    click.echo("Policy saved.")


@policy_group.command("check")
@click.argument("env_file", type=click.Path(exists=True))
@click.argument("vault_dir", default=".", type=click.Path())
def check_cmd(env_file: str, vault_dir: str) -> None:
    """Check an .env file against the vault policy."""
    try:
        policy = load_policy(Path(vault_dir))
        vault = Vault(Path(vault_dir))
        recipients = vault.get_recipients()
        raw = Path(env_file).read_text().splitlines()
        env = parse_env_pairs(raw)
        violations = check_policy(policy, env, recipients)
    except PolicyError as exc:
        raise click.ClickException(str(exc))
    output = format_violations(violations)
    click.echo(output)
    if violations:
        raise SystemExit(1)
