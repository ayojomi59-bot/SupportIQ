"""Small SQLite persistence layer for SupportIQ tickets."""

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(os.getenv("SUPPORTIQ_DB_PATH", "supportiq.db"))


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            category TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            urgency TEXT NOT NULL,
            confidence REAL NOT NULL,
            rationale TEXT NOT NULL,
            suggested_reply TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL
        )
        """
    )
    return connection


def create_ticket(subject: str, message: str, analysis: Any) -> dict:
    created_at = datetime.now(timezone.utc).isoformat()
    with connect() as db:
        cursor = db.execute(
            """INSERT INTO tickets
            (subject, message, category, sentiment, urgency, confidence, rationale,
             suggested_reply, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (subject, message, analysis.category, analysis.sentiment, analysis.urgency,
             analysis.confidence, json.dumps(analysis.rationale), analysis.suggested_reply,
             created_at),
        )
        ticket_id = cursor.lastrowid
    return get_ticket(ticket_id)


def _serialize(row: sqlite3.Row) -> dict:
    item = dict(row)
    item["rationale"] = json.loads(item["rationale"])
    return item


def get_ticket(ticket_id: int) -> dict | None:
    with connect() as db:
        row = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    return _serialize(row) if row else None


def list_tickets(status: str | None = None) -> list[dict]:
    with connect() as db:
        if status and status != "all":
            rows = db.execute(
                "SELECT * FROM tickets WHERE status = ? ORDER BY id DESC", (status,)
            ).fetchall()
        else:
            rows = db.execute("SELECT * FROM tickets ORDER BY id DESC").fetchall()
    return [_serialize(row) for row in rows]


def update_status(ticket_id: int, status: str) -> dict | None:
    with connect() as db:
        cursor = db.execute("UPDATE tickets SET status = ? WHERE id = ?", (status, ticket_id))
        if cursor.rowcount == 0:
            return None
    return get_ticket(ticket_id)


def dashboard_stats() -> dict[str, int]:
    with connect() as db:
        row = db.execute(
            """SELECT COUNT(*) AS total,
            SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) AS open,
            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) AS in_progress,
            SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) AS resolved,
            SUM(CASE WHEN urgency = 'high' AND status != 'resolved' THEN 1 ELSE 0 END) AS urgent
            FROM tickets"""
        ).fetchone()
    return {key: int(row[key] or 0) for key in ("total", "open", "in_progress", "resolved", "urgent")}
