"""FR-04/FR-05 routing tests (T-04a-c, T-05a-b). T-05c is analysis/routing_eval.py."""
import inspect

import src.routing as routing
from src.classifier import Classification
from src.ingest import normalise
from src.retrieval import Hit
from src.routing import route

PASSAGE = Hit(passage_id="DOC-ACCT-001#resolution", doc_id="DOC-ACCT-001", title="t",
              section="Resolution", applies_to="All plans", text="t", score=0.7)


def ticket(body="My new role does not show up after it was granted"):
    return normalise({"ticket_id": "R1", "channel": "email", "body": body}, 0)


def cls(intent="account_access", confidence=0.95, alts=None):
    alts = alts or [(intent, confidence), ("onboarding", 0.03), ("api_key_issue", 0.01)]
    return Classification(intent=intent, urgency="medium", confidence=confidence, alternatives=alts)


def test_t04a_same_ticket_same_route():
    assert route(ticket(), cls(), [PASSAGE], 0.8) == route(ticket(), cls(), [PASSAGE], 0.8)


def test_t04b_threshold_boundary():
    assert route(ticket(), cls(confidence=0.79), [PASSAGE], 0.80).action == "escalate"
    assert route(ticket(), cls(confidence=0.81), [PASSAGE], 0.80).action == "auto_respond"


def test_t04c_every_decision_has_a_reason():
    cases = [(cls(), [PASSAGE]), (cls(), []), (cls(confidence=0.2), [PASSAGE]),
             (cls("security_incident"), [PASSAGE]), (cls("feature_request"), [PASSAGE])]
    for c, p in cases:
        assert route(ticket(), c, p, 0.8).reason


def test_no_passage_escalates():
    assert route(ticket(), cls(), [], 0.8).action == "escalate"


def test_t05a_protected_ticket_never_auto_even_at_high_confidence():
    for intent in ("security_incident", "compliance_request", "data_residency"):
        r = route(ticket(), cls(intent, 0.99), [PASSAGE], 0.5)
        assert r.action == "escalate" and r.protected
    # protected intent only among the alternatives
    alts = [("account_access", 0.90), ("security_incident", 0.08), ("onboarding", 0.02)]
    assert route(ticket(), cls(alts=alts, confidence=0.90), [PASSAGE], 0.5).protected
    for body in ("I think our account was hacked", "We were overcharged and want a refund"):
        assert route(ticket(body), cls(confidence=0.99), [PASSAGE], 0.5).protected


def test_t05b_protected_rule_cannot_be_disabled(monkeypatch):
    monkeypatch.setenv("CONFIDENCE_THRESHOLD", "0.0")
    for name in ("DISABLE_PROTECTED", "PROTECTED_RULE", "FR05_ENABLED"):
        monkeypatch.setenv(name, "false")
    assert route(ticket(), cls("security_incident", 0.99), [PASSAGE]).action == "escalate"
    assert "getenv" not in inspect.getsource(routing.protected_check)


def test_no_doc_intents_always_escalate():
    for intent in ("feature_request", "unclear_request"):
        assert route(ticket(), cls(intent, 1.0), [PASSAGE], 0.5).action == "escalate"


def test_escalation_priority():
    def prio(c, body="My new role does not show up after it was granted", p=None):
        return route(ticket(body), c, [] if p is None else p, 0.8).priority

    assert prio(cls("security_incident", 0.99)) == "P1"
    assert prio(cls(), "Our account was hacked last night") == "P1"
    assert prio(cls("database_issue")) == "P2"
    high = cls().model_copy(update={"urgency": "high"})
    assert prio(high) == "P2"
    assert prio(cls()) == "P3"
    assert route(ticket(), cls(), [PASSAGE], 0.8).priority == ""  # auto_respond: no queue


def test_unreadable_ticket_escalates():
    t = normalise("junk", 3)
    assert route(t, cls(), [PASSAGE], 0.5).action == "escalate"
