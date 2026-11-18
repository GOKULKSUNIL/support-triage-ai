"""FR-10/FR-11 harness tests (T-10a, T-11a-b)."""
import json

from evaluation.harness import main
from evaluation.metrics import compute, render


def test_t10a_every_ticket_in_an_unseen_file_has_a_result_and_log_row(tmp_path, monkeypatch):
    # No provider configured: also shows the run completes when the model is unreachable (T-12a).
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("FALLBACK_API_KEY", "")
    monkeypatch.setenv("LLM_CACHE_DIR", str(tmp_path / "cache"))
    tickets = json.load(open("data/development_tickets.json"))[:4]
    for t in tickets:
        t.pop("labels")
    src = tmp_path / "unseen.json"
    src.write_text(json.dumps(tickets + ["junk", {"ticket_id": "EMPTY", "channel": "chat", "body": ""}]))
    out = tmp_path / "run"
    assert main(["--input", str(src), "--output", str(out)]) == 0
    lines = [json.loads(line) for line in (out / "results.jsonl").read_text().splitlines()]
    assert len(lines) == 6
    assert all(r["action"] == "escalate" for r in lines)  # nothing sent without a model
    assert any("provider unavailable" in r["reason"] for r in lines)
    report = (out / "metrics_report.md").read_text()
    assert "reconciled" in report and "No labels in this file" in report


def _result(tid, intent, action, label_intent, label_route, must_not=False, docs=(), sources=()):
    return {"ticket_id": tid, "channel": "email", "customer_tier": "standard",
            "customer_region": "europe", "language_fluency": "fluent", "flags": [],
            "intent": intent, "urgency": "medium", "confidence": 0.95, "alternatives": [],
            "action": action, "reason": "Escalated: x." if action == "escalate" else "Auto-respond: x.",
            "protected": False, "priority": "P3" if action == "escalate" else "", "threshold": 0.8,
            "sources": list(sources), "reply": None, "packet": None, "latency_ms": 10.0, "error": None,
            "labels": {"intent": label_intent, "urgency": "medium", "expected_route": label_route,
                       "expected_doc_ids": list(docs), "must_not_auto_respond": must_not}}


def test_t11b_figures_match_a_hand_count():
    results = [
        _result("A", "billing_query", "auto_respond", "billing_query", "auto_respond",
                docs=["DOC-BILL-001"], sources=["DOC-BILL-001#resolution"]),
        _result("B", "billing_query", "auto_respond", "billing_query", "escalate",
                docs=["DOC-BILL-001"], sources=["DOC-API-001#symptoms"]),
        _result("C", "feature_request", "auto_respond", "feature_request", "escalate", must_not=True),
        _result("D", "onboarding", "escalate", "onboarding", "auto_respond", docs=["DOC-ONB-001"]),
        _result("E", "security_incident", "escalate", "security_incident", "escalate", must_not=True),
    ] + [_result(f"F{i}", "rate_limit", "auto_respond", "rate_limit", "auto_respond") for i in range(5)]
    m = compute(results, log_rows=10, tickets_in=10)
    assert m["reconciled"] and m["auto"] == 8 and m["escalated"] == 2
    assert m["escalation_rate"] == 0.2
    assert m["must_not_breaches"] == ["C"]
    assert m["avoidable_escalations"] == 1                 # D
    assert m["routing_accuracy"] == 0.7                    # A, E, F0-F4
    assert abs(m["retrieval_hit_rate"] - 1 / 3) < 1e-9     # A of A, B, D
    assert m["auto_label_agrees"] == 6 / 8                 # A, F0-F4


def test_t11a_report_has_all_four_groups():
    m = compute([_result("A", "billing_query", "auto_respond", "billing_query", "auto_respond")], 1, 1)
    text = render(m, {"input": "x.json", "started": "s", "finished": "f", "version": "v", "threshold": 0.8})
    for heading in ("1. Volume and reconciliation", "2. Business outcomes",
                    "3. Technical performance", "4. Governance"):
        assert heading in text


def test_reconciliation_mismatch_is_reported():
    m = compute([_result("A", "x", "escalate", "x", "escalate")], log_rows=0, tickets_in=1)
    assert not m["reconciled"]
