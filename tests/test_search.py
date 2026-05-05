"""Tests for envault.search module."""

from __future__ import annotations

import pytest

from envault.search import (
    SearchError,
    SearchResult,
    format_results,
    parse_env_lines,
    search_env,
)

SAMPLE_ENV = """
# a comment
DB_HOST=localhost
DB_PORT=5432
DB_PASSWORD=s3cr3t
API_KEY=abc123
DEBUG=true
"""


def test_parse_env_lines_basic():
    parsed = parse_env_lines(SAMPLE_ENV)
    keys = {v[0] for v in parsed.values()}
    assert "DB_HOST" in keys
    assert "DB_PORT" in keys
    assert "API_KEY" in keys


def test_parse_env_lines_ignores_comments_and_blanks():
    parsed = parse_env_lines(SAMPLE_ENV)
    for _lineno, (key, _val) in parsed.items():
        assert not key.startswith("#")
        assert key != ""


def test_parse_env_lines_strips_quotes():
    text = 'SECRET="my value"'
    parsed = parse_env_lines(text)
    assert list(parsed.values())[0] == ("SECRET", "my value")


def test_search_env_matches_key():
    results = search_env(SAMPLE_ENV, "DB_", search_keys=True)
    assert len(results) == 3
    assert all(r.matched_on in ("key", "both") for r in results)


def test_search_env_matches_value():
    results = search_env(SAMPLE_ENV, "localhost", search_keys=False, search_values=True)
    assert len(results) == 1
    assert results[0].key == "DB_HOST"
    assert results[0].matched_on == "value"


def test_search_env_matches_both():
    # 'true' appears in value; let's use a pattern that hits key and value
    text = "TRUE_FLAG=true"
    results = search_env(text, "true", search_keys=True, search_values=True)
    assert len(results) == 1
    assert results[0].matched_on == "both"


def test_search_env_case_insensitive_default():
    results = search_env(SAMPLE_ENV, "db_host", search_keys=True)
    assert len(results) == 1
    assert results[0].key == "DB_HOST"


def test_search_env_case_sensitive():
    results = search_env(SAMPLE_ENV, "db_host", search_keys=True, case_sensitive=True)
    assert len(results) == 0


def test_search_env_empty_pattern_raises():
    with pytest.raises(SearchError, match="must not be empty"):
        search_env(SAMPLE_ENV, "")


def test_search_env_invalid_regex_raises():
    with pytest.raises(SearchError, match="Invalid regex"):
        search_env(SAMPLE_ENV, "[invalid")


def test_search_env_no_matches():
    results = search_env(SAMPLE_ENV, "NONEXISTENT_KEY_XYZ")
    assert results == []


def test_format_results_no_matches():
    assert format_results([]) == "No matches found."


def test_format_results_hides_values_by_default():
    results = search_env(SAMPLE_ENV, "DB_HOST")
    output = format_results(results)
    assert "localhost" not in output
    assert "DB_HOST" in output


def test_format_results_shows_values_when_requested():
    results = search_env(SAMPLE_ENV, "DB_HOST")
    output = format_results(results, show_values=True)
    assert "localhost" in output
