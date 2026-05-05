"""Tests for envault.audit module."""

import json
from pathlib import Path

import pytest

from envault.audit import (
    AUDIT_FILENAME,
    format_event,
    read_events,
    record_event,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_record_event_creates_file(vault_dir):
    record_event(vault_dir, "lock", actor="ABCD1234")
    audit_file = vault_dir / AUDIT_FILENAME
    assert audit_file.exists()


def test_record_event_returns_event_dict(vault_dir):
    event = record_event(vault_dir, "unlock", actor="DEADBEEF", details={"env": ".env"})
    assert event["action"] == "unlock"
    assert event["actor"] == "DEADBEEF"
    assert event["details"] == {"env": ".env"}
    assert "timestamp" in event


def test_multiple_events_appended(vault_dir):
    record_event(vault_dir, "add_recipient", actor="AAA", details={"fingerprint": "FP1"})
    record_event(vault_dir, "add_recipient", actor="AAA", details={"fingerprint": "FP2"})
    events = read_events(vault_dir)
    assert len(events) == 2
    assert events[0]["details"]["fingerprint"] == "FP1"
    assert events[1]["details"]["fingerprint"] == "FP2"


def test_read_events_empty_when_no_file(vault_dir):
    events = read_events(vault_dir)
    assert events == []


def test_read_events_returns_list_on_corrupt_file(vault_dir):
    (vault_dir / AUDIT_FILENAME).write_text("not valid json", encoding="utf-8")
    events = read_events(vault_dir)
    assert events == []


def test_record_event_recovers_from_corrupt_file(vault_dir):
    (vault_dir / AUDIT_FILENAME).write_text("!!!", encoding="utf-8")
    event = record_event(vault_dir, "lock")
    assert event["action"] == "lock"
    events = read_events(vault_dir)
    assert len(events) == 1


def test_format_event_with_details():
    event = {
        "timestamp": "2024-01-01T00:00:00+00:00",
        "action": "lock",
        "actor": "ABCD",
        "details": {"file": ".env.vault"},
    }
    result = format_event(event)
    assert "lock" in result
    assert "ABCD" in result
    assert "file=.env.vault" in result


def test_format_event_without_details():
    event = {
        "timestamp": "2024-01-01T00:00:00+00:00",
        "action": "unlock",
        "actor": None,
        "details": {},
    }
    result = format_event(event)
    assert "unlock" in result
    assert "(" not in result
