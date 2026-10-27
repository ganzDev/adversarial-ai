
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATABASE_PATH = Path(__file__).resolve().parent / "portal.db"

# Never persist values associated with these argument names.
SENSITIVE_KEYS = {
    "password",
    "token",
    "api_key",
    "secret",
    "authorization",
    "credential",
}


def _sanitize(value: Any, key: str = "") -> Any:
    """Remove sensitive values and bound the size of logged data."""
    if key.lower() in SENSITIVE_KEYS:
        return "[REDACTED]"

    if isinstance(value, dict):
        return {
            str(k): _sanitize(v, str(k))
            for k, v in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [_sanitize(item) for item in value[:50]]

    if isinstance(value, str):
        return value[:500]

    if value is None or isinstance(value, (bool, int, float)):
        return value

    return str(value)[:500]


def initialize_audit_log() -> None:
    """Create the audit table if it does not already exist."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS security_audit_events (
                event_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                tool TEXT NOT NULL,
                resource TEXT NOT NULL,
                operation TEXT NOT NULL,
                arguments_json TEXT NOT NULL,
                allowed INTEGER NOT NULL,
                risk TEXT NOT NULL,
                reason TEXT,
                outcome TEXT NOT NULL
            )
            """
        )


def record_tool_event(
    *,
    tool: str,
    resource: str,
    operation: str,
    arguments: dict[str, Any],
    allowed: bool,
    risk: str,
    reason: str | None,
    outcome: str,
) -> str:
    """Persist one tool-attempt event and return its event ID."""
    event_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    safe_arguments = _sanitize(arguments)
    safe_reason = _sanitize(reason) if reason else None

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO security_audit_events (
                event_id, timestamp, tool, resource, operation,
                arguments_json, allowed, risk, reason, outcome
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                timestamp,
                tool[:100],
                resource[:100],
                operation[:50],
                json.dumps(safe_arguments, ensure_ascii=False),
                int(allowed),
                risk[:20],
                safe_reason,
                outcome[:100],
            ),
        )

    return event_id


def list_tool_events(limit: int = 100) -> list[dict[str, Any]]:
    """Return recent audit events, newest first."""
    safe_limit = max(1, min(limit, 500))

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT *
            FROM security_audit_events
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()

    events = []
    for row in rows:
        event = dict(row)
        event["arguments"] = json.loads(event.pop("arguments_json"))
        event["allowed"] = bool(event["allowed"])
        events.append(event)

    return events


def clear_tool_events() -> int:
    """Delete all stored audit events and return the number deleted."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute("DELETE FROM security_audit_events")
        return cursor.rowcount
