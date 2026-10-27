import json

from environment import audit_log


def test_record_and_retrieve_tool_event(tmp_path, monkeypatch):
    test_db = tmp_path / "test_audit.db"
    monkeypatch.setattr(audit_log, "DATABASE_PATH", test_db)

    audit_log.initialize_audit_log()

    event_id = audit_log.record_tool_event(
        tool="read_ticket",
        resource="support_tickets",
        operation="read",
        arguments={"ticket_id": 1},
        allowed=True,
        risk="low",
        reason=None,
        outcome="success",
    )

    events = audit_log.list_tool_events()

    assert len(events) == 1
    assert events[0]["event_id"] == event_id
    assert events[0]["tool"] == "read_ticket"
    assert events[0]["allowed"] is True
    assert events[0]["arguments"] == {"ticket_id": 1}
    assert events[0]["outcome"] == "success"


def test_sensitive_arguments_are_redacted(tmp_path, monkeypatch):
    test_db = tmp_path / "test_audit.db"
    monkeypatch.setattr(audit_log, "DATABASE_PATH", test_db)

    audit_log.initialize_audit_log()

    audit_log.record_tool_event(
        tool="test_tool",
        resource="test_resource",
        operation="read",
        arguments={
            "username": "test-user",
            "password": "do-not-store-this",
            "nested": {"api_key": "secret-key"},
        },
        allowed=False,
        risk="high",
        reason="Denied",
        outcome="denied",
    )

    events = audit_log.list_tool_events()
    serialized = json.dumps(events)

    assert "do-not-store-this" not in serialized
    assert "secret-key" not in serialized
    assert events[0]["arguments"]["password"] == "[REDACTED]"
    assert events[0]["arguments"]["nested"]["api_key"] == "[REDACTED]"


def test_event_arguments_are_size_limited(tmp_path, monkeypatch):
    test_db = tmp_path / "test_audit.db"
    monkeypatch.setattr(audit_log, "DATABASE_PATH", test_db)

    audit_log.initialize_audit_log()

    audit_log.record_tool_event(
        tool="test_tool",
        resource="test_resource",
        operation="read",
        arguments={"input": "x" * 1000},
        allowed=True,
        risk="low",
        reason=None,
        outcome="success",
    )

    event = audit_log.list_tool_events()[0]
    assert len(event["arguments"]["input"]) == 500
