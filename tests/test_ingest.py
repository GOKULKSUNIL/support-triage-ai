"""FR-01 ingest tests (T-01a-c)."""
import json

from src.ingest import load_tickets, normalise


def test_t01a_one_ticket_per_channel_normalises():
    tickets = load_tickets("data/development_tickets.json")
    by_channel = {t.channel: t for t in tickets}
    assert set(by_channel) == {"email", "chat", "docs_comment", "forum"}
    for t in by_channel.values():
        assert t.ticket_id and t.text and t.flags == []


def test_t01b_odd_records_normalise_without_error():
    cases = [
        {"ticket_id": "X1", "channel": "email", "subject": "Hi", "body": ""},
        {"ticket_id": "X2", "channel": "chat", "body": "login fails 😩 naïve café\x00\x07"},
        {"ticket_id": "X3", "channel": "FORUM", "subject": None, "body": "  spaced\t\tout  "},
        {"ticket_id": "X4"},
    ]
    t1, t2, t3, t4 = (normalise(c, i) for i, c in enumerate(cases))
    assert "empty_body" in t1.flags and t1.text == "Hi"
    assert "\x00" not in t2.text and "😩" in t2.text
    assert t3.channel == "forum" and t3.text == "spaced out"
    assert {"empty_body", "empty_text", "unknown_channel"} <= set(t4.flags)
    assert t4.customer_tier == "unknown"


def test_t01c_unreadable_record_becomes_malformed_ticket(tmp_path):
    path = tmp_path / "tickets.json"
    path.write_text(json.dumps([{"ticket_id": "OK1", "channel": "email", "body": "hello"}, "junk", 42]))
    tickets = load_tickets(path)
    assert len(tickets) == 3  # nothing dropped
    assert [t.flags for t in tickets[1:]] == [["malformed"], ["malformed"]]
