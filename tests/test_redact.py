"""Tests for envault.redact."""

import pytest
from envault.redact import (
    _is_sensitive_key,
    _mask_value,
    redact_line,
    redact_env,
    format_redact_summary,
    RedactedLine,
)


# --- _is_sensitive_key ---

def test_is_sensitive_key_detects_password():
    assert _is_sensitive_key("DB_PASSWORD") is True


def test_is_sensitive_key_detects_token():
    assert _is_sensitive_key("GITHUB_TOKEN") is True


def test_is_sensitive_key_detects_api_key():
    assert _is_sensitive_key("STRIPE_API_KEY") is True


def test_is_sensitive_key_safe_key():
    assert _is_sensitive_key("APP_NAME") is False


def test_is_sensitive_key_case_insensitive():
    assert _is_sensitive_key("db_secret") is True


# --- _mask_value ---

def test_mask_value_no_show():
    assert _mask_value("supersecret") == "***REDACTED***"


def test_mask_value_with_show_chars():
    result = _mask_value("supersecret", show_chars=3)
    assert result.startswith("sup")
    assert "***REDACTED***" in result


def test_mask_value_empty_string():
    assert _mask_value("") == ""


def test_mask_value_show_chars_exceeds_length():
    assert _mask_value("hi", show_chars=10) == "***REDACTED***"


# --- redact_line ---

def test_redact_line_sensitive_key():
    rl = redact_line("DB_PASSWORD=hunter2\n")
    assert rl.was_redacted is True
    assert "hunter2" not in rl.redacted
    assert "***REDACTED***" in rl.redacted


def test_redact_line_safe_key():
    rl = redact_line("APP_NAME=myapp\n")
    assert rl.was_redacted is False
    assert "myapp" in rl.redacted


def test_redact_line_comment_unchanged():
    rl = redact_line("# this is a comment\n")
    assert rl.was_redacted is False
    assert rl.redacted == rl.original


def test_redact_line_blank_unchanged():
    rl = redact_line("\n")
    assert rl.was_redacted is False


# --- redact_env ---

def test_redact_env_redacts_sensitive():
    content = "APP_NAME=myapp\nDB_PASSWORD=secret123\nDEBUG=true\n"
    result, keys = redact_env(content)
    assert "secret123" not in result
    assert "DB_PASSWORD" in keys
    assert "APP_NAME" not in keys


def test_redact_env_no_sensitive_keys():
    content = "APP_NAME=myapp\nDEBUG=true\n"
    result, keys = redact_env(content)
    assert keys == []
    assert "myapp" in result


def test_redact_env_with_show_chars():
    content = "API_KEY=abcdef1234\n"
    result, keys = redact_env(content, show_chars=3)
    assert "abc" in result
    assert "def1234" not in result


# --- format_redact_summary ---

def test_format_redact_summary_no_keys():
    assert format_redact_summary([]) == "No sensitive keys detected."


def test_format_redact_summary_with_keys():
    summary = format_redact_summary(["DB_PASSWORD", "API_KEY"])
    assert "2" in summary
    assert "DB_PASSWORD" in summary
    assert "API_KEY" in summary
