"""Fairness audit (NFR-06): rates and gaps by group match a hand count."""
from types import SimpleNamespace

from evaluation.fairness import audit, render, wilson


def _r(tid, fluency, action, label_route, sources=("DOC-A#x",), blocked=False):
    return {"ticket_id": tid, "customer_tier": "standard", "customer_region": "europe",
            "language_fluency": fluency, "channel": "email", "action": action, "sources": list(sources),
            "reply": {"status": "blocked" if blocked else "sent"}, "blocked": blocked,
            "labels": {"expected_route": label_route, "expected_doc_ids": ["DOC-A"]}}


def test_rates_and_gaps_by_fluency():
    results = [_r("1", "fluent", "auto_respond", "auto_respond"),
               _r("2", "fluent", "auto_respond", "auto_respond"),
               _r("3", "non_fluent", "escalate", "auto_respond", sources=(), blocked=True),
               _r("4", "non_fluent", "auto_respond", "auto_respond")]
    tickets = [SimpleNamespace(ticket_id=str(i), subject="s", body="word " * i) for i in range(1, 5)]
    report, median = audit(results, tickets)
    fl = report["language_fluency"]
    assert fl["fluent"]["resolution"]["rate"] == 1.0 and fl["non_fluent"]["resolution"]["rate"] == 0.5
    assert fl["non_fluent"]["resolution"]["gap"] == 50.0 and fl["fluent"]["resolution"]["gap"] == 0
    assert fl["non_fluent"]["missed"]["rate"] == 0.5 and fl["non_fluent"]["retrieval"]["rate"] == 0.5
    assert fl["non_fluent"]["blocked"]["gap"] == 50.0
    assert set(report["length"]) == {"short", "long"}
    assert "**50**" in render(report, {"results": "x", "tickets": 4, "median_words": median})


def test_wilson_range_contains_the_rate():
    lo, hi = wilson(7, 10)
    assert lo < 0.7 < hi and 0 <= lo and hi <= 1
