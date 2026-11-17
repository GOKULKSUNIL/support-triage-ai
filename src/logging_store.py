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

COLUMNS = (
    "decision_id", "created_at", "ticket_id", "channel", "input_text", "intent", "urgency",
    "confidence", "alternatives", "threshold", "action", "reason", "priority", "sources_used",
    "guardrail_checks", "blocked", "prompt_versions", "model", "latency_ms", "error",
)
_SCHEMA = f"CREATE TABLE IF NOT EXISTS decisions ({', '.join(COLUMNS)}, PRIMARY KEY (decision_id))"


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
    return url.removeprefix("sqlite:///")


class DecisionLog:
    def __init__(self, path: str | None = None):
        self.path = path or _db_path()
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(_SCHEMA)

    def _connect(self):
        return sqlite3.connect(self.path)

    def write(self, **fields) -> str:
        unknown = set(fields) - set(COLUMNS)
        if unknown:
            raise ValueError(f"unknown decision-log fields: {sorted(unknown)}")
        row = {c: None for c in COLUMNS}
        row.update(decision_id=uuid.uuid4().hex,
                   created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        for key, value in fields.items():
            row[key] = json.dumps(value) if isinstance(value, (list, dict, tuple)) else value
        with self._connect() as db:
            db.execute(f"INSERT INTO decisions VALUES ({', '.join('?' * len(COLUMNS))})",
                       [row[c] for c in COLUMNS])
        return row["decision_id"]

    def count(self) -> int:
        with self._connect() as db:
            return db.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]

    def rows(self) -> list[dict]:
        with self._connect() as db:
            db.row_factory = sqlite3.Row
            return [dict(r) for r in db.execute("SELECT * FROM decisions ORDER BY created_at")]
