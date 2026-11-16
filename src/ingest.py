"""Ingest (FR-01): load tickets from any channel into one normalised Ticket.

Never raises on a bad record. Missing fields get defaults, and a record that
cannot be read at all becomes a Ticket flagged "malformed", so it is still
routed to a person and logged rather than dropped.
"""
import json
import re
import unicodedata
from pathlib import Path

from pydantic import BaseModel, Field

CHANNELS = {"email", "chat", "docs_comment", "forum"}

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_SPACES = re.compile(r"[ \t]+")


class Ticket(BaseModel):
    ticket_id: str
    channel: str
    subject: str = ""
    body: str = ""
    text: str = ""  # cleaned subject + body; what the pipeline reads
    received_at: str = ""
    customer_id: str = ""
    customer_name: str = ""
    customer_tier: str = "unknown"
    customer_region: str = "unknown"
    language_fluency: str = "unknown"
    flags: list[str] = Field(default_factory=list)
    labels: dict | None = None  # ground truth when present; used only for evaluation


def clean_text(value) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFC", str(value))
    text = _CONTROL.sub(" ", text)
    lines = [_SPACES.sub(" ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def _field(record: dict, name: str, default: str) -> str:
    value = record.get(name)
    return default if value is None or str(value).strip() == "" else str(value).strip()


def normalise(record, index: int) -> Ticket:
    if not isinstance(record, dict):
        return Ticket(ticket_id=f"MALFORMED-{index:04d}", channel="unknown", flags=["malformed"])

    flags = []
    channel = _field(record, "channel", "unknown").lower()
    if channel not in CHANNELS:
        flags.append("unknown_channel")

    subject = "" if record.get("subject") is None else str(record["subject"])
    body = "" if record.get("body") is None else str(record["body"])
    text = "\n".join(part for part in (clean_text(subject), clean_text(body)) if part)
    if not clean_text(body):
        flags.append("empty_body")
    if not text:
        flags.append("empty_text")

    ticket_id = _field(record, "ticket_id", f"NOID-{index:04d}")
    if ticket_id.startswith("NOID-"):
        flags.append("missing_id")

    labels = record.get("labels") if isinstance(record.get("labels"), dict) else None
    return Ticket(
        ticket_id=ticket_id,
        channel=channel,
        subject=subject,
        body=body,
        text=text,
        received_at=_field(record, "received_at", ""),
        customer_id=_field(record, "customer_id", ""),
        customer_name=_field(record, "customer_name", ""),
        customer_tier=_field(record, "customer_tier", "unknown").lower(),
        customer_region=_field(record, "customer_region", "unknown").lower(),
        language_fluency=_field(record, "language_fluency", "unknown").lower(),
        flags=flags,
        labels=labels,
    )


def load_tickets(path) -> list[Ticket]:
    """Read a ticket file. Accepts a JSON list, or an object holding one list."""
    raw = json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    if isinstance(raw, dict):
        lists = [v for v in raw.values() if isinstance(v, list)]
        raw = lists[0] if lists else [raw]
    if not isinstance(raw, list):
        raw = [raw]
    return [normalise(record, i) for i, record in enumerate(raw)]
