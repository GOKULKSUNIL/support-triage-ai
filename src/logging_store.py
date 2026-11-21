"""Decision log (FR-08): one SQLite row per processed ticket.

The pipeline writes the row in a `finally` path, so escalations and failures
are logged as well as auto-responses, and the row count can be reconciled
against the number of tickets processed. The customer's name and ID are
masked in the stored text; the row keeps the ticket id so a decision can be
traced months later without holding the customer's identity.
"""
import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src import config

COLUMNS = (
    "decision_id", "created_at", "ticket_id", "channel", "input_text", "intent", "urgency",
    "confidence", "alternatives", "threshold", "action", "reason", "priority", "stage",
    "requirement_ids", "sources_used", "guardrail_checks", "blocked", "prompt_versions", "model",
    "latency_ms", "error",
)
_SCHEMA = f"CREATE TABLE IF NOT EXISTS decisions ({', '.join(COLUMNS)}, PRIMARY KEY (decision_id))"
# Kill switch: every pause and resume is appended, never overwritten, so the
# latest row is the current state and the table is its own audit trail.
_CONTROL_SCHEMA = "CREATE TABLE IF NOT EXISTS control_events (changed_at, paused, changed_by, reason)"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def mask(text: str, customer_name: str = "", customer_id: str = "") -> str:
    """Replace the customer's name (full and each part) and ID in free text."""
    if customer_id:
        text = re.sub(re.escape(customer_id), "[CUSTOMER_ID]", text, flags=re.I)
    names = [customer_name] + customer_name.split() if customer_name else []
    for part in sorted({n for n in names if len(n) >= 3}, key=len, reverse=True):
        text = re.sub(rf"\b{re.escape(part)}\b", "[NAME]", text, flags=re.I)
    return text


def _db_path() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///./storage/decisions.db")
    return str(config.path(url.removeprefix("sqlite:///")))


class DecisionLog:
    def __init__(self, path: str | None = None):
        self.path = path or _db_path()
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(_SCHEMA)
            db.execute(_CONTROL_SCHEMA)
            # An older log file gains any column added since it was created.
            existing = {row[1] for row in db.execute("PRAGMA table_info(decisions)")}
            for column in COLUMNS:
                if column not in existing:
                    db.execute(f"ALTER TABLE decisions ADD COLUMN {column}")

    def _connect(self):
        return sqlite3.connect(self.path)

    def write(self, **fields) -> str:
        unknown = set(fields) - set(COLUMNS)
        if unknown:
            raise ValueError(f"unknown decision-log fields: {sorted(unknown)}")
        row = {c: None for c in COLUMNS}
        row.update(decision_id=uuid.uuid4().hex, created_at=_now())
        for key, value in fields.items():
            row[key] = json.dumps(value) if isinstance(value, (list, dict, tuple)) else value
        with self._connect() as db:
            db.execute(f"INSERT INTO decisions ({', '.join(COLUMNS)}) "
                       f"VALUES ({', '.join('?' * len(COLUMNS))})", [row[c] for c in COLUMNS])
        return row["decision_id"]

    def count(self) -> int:
        with self._connect() as db:
            return db.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]

    def rows(self) -> list[dict]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            return [dict(r) for r in db.execute("SELECT * FROM decisions ORDER BY created_at")]

    def set_paused(self, paused: bool, by: str, reason: str) -> None:
        with self._connect() as db:
            db.execute("INSERT INTO control_events VALUES (?, ?, ?, ?)", (_now(), int(paused), by, reason))

    def control_history(self) -> list[dict]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            return [dict(r) for r in db.execute("SELECT * FROM control_events ORDER BY rowid")]

    def control_state(self) -> dict | None:
        """The latest pause/resume event, or None if the switch was never used."""
        history = self.control_history()
        return history[-1] if history else None

    def paused(self) -> dict | None:
        """The pause event in force, or None while automatic answering is on."""
        state = self.control_state()
        return state if state and state["paused"] else None
