import os
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(
    os.environ.get(
        "APP_DATABASE_PATH",
        str(Path(__file__).resolve().parent / "portal.db"),
    )
)


def get_connection():
    """Create a connection to the local SQLite database."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    """Create database tables and insert fictional test data."""
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                role TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                priority TEXT NOT NULL
            );
            """
        )

        employee_count = connection.execute(
            "SELECT COUNT(*) FROM employees"
        ).fetchone()[0]

        if employee_count == 0:
            connection.executemany(
                """
                INSERT INTO employees (id, name, department, role)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (101, "Alex Morgan", "IT", "System Administrator"),
                    (102, "Jamie Chen", "Finance", "Financial Analyst"),
                    (103, "Taylor Reed", "HR", "HR Coordinator"),
                    (104, "Jordan Patel", "Engineering", "Software Engineer"),
                ],
            )

        ticket_count = connection.execute(
            "SELECT COUNT(*) FROM tickets"
        ).fetchone()[0]

        if ticket_count == 0:
            connection.executemany(
                """
                INSERT INTO tickets
                    (id, title, description, status, priority)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        1,
                        "Email access issue",
                        "A user cannot access the internal email portal.",
                        "open",
                        "medium",
                    ),
                    (
                        2,
                        "Slow development server",
                        "The test development server is responding slowly.",
                        "in_progress",
                        "high",
                    ),
                    (
                        3,
                        "Password reset request",
                        "A fictional employee needs a password reset.",
                        "open",
                        "low",
                    ),
                ],
            )


def list_employees():
    """Return employee records for the simulated portal."""
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, name, department, role FROM employees ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]


def get_employee(employee_id: int):
    """Return one employee, or None if the ID does not exist."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, name, department, role
            FROM employees
            WHERE id = ?
            """,
            (employee_id,),
        ).fetchone()
        return dict(row) if row else None


def list_tickets():
    """Return support tickets for the simulated portal."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, title, description, status, priority
            FROM tickets
            ORDER BY id
            """
        ).fetchall()
        return [dict(row) for row in rows]


def get_ticket(ticket_id: int):
    """Return one ticket, or None if the ID does not exist."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, title, description, status, priority
            FROM tickets
            WHERE id = ?
            """,
            (ticket_id,),
        ).fetchone()
        return dict(row) if row else None
