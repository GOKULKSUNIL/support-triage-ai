"""Routing (FR-04, FR-05): decide auto_respond or escalate. Pure code, no model call.

The protected rule (FR-05) is checked first and is fixed here in code: there
is no flag or environment variable that turns it off. Intents with no
documentation (feature and unclear requests) always escalate. After that a
ticket is auto-responded only if the classifier is confident enough AND at
least one passage passed the relevance threshold. Every decision carries a one-line
reason a manager can read.
"""
import os
import re

from pydantic import BaseModel

from src.classify import Classification
from src.ingest import Ticket
from src.retrieve import Hit

PROTECTED_INTENTS = frozenset({"security_incident", "compliance_request", "data_residency"})
_COMPROMISE = re.compile(r"\b(hacked|compromised|unauthori[sz]ed access)\b", re.I)
_BILLING_DISPUTE = re.compile(
    r"\b(refund|chargeback|dispute[sd]?|overcharged|charged for (a )?service[s]? (we|i) (did not|didn't|never) use)\b",
    re.I)
BLOCKING_FLAGS = frozenset({"malformed", "empty_text", "empty_body"})
# No article can answer these (D-10): a feature request still matches articles
# about the existing feature, so the relevance threshold alone does not stop it.
NO_DOC_INTENTS = frozenset({"feature_request", "unclear_request"})
# Escalation priority (D-13): orders the Tier 2 queue, never changes the route.
OUTAGE_INTENTS = frozenset({"database_issue", "performance_degradation",
                            "deployment_failure", "rollback_request"})


class Route(BaseModel):
    action: str  # "auto_respond" | "escalate"
    reason: str
    threshold_used: float
    protected: bool = False
    protected_reason: str = ""
    priority: str = ""  # "P1" | "P2" | "P3" on escalations, "" on auto_respond
    priority_reason: str = ""
    requirement_ids: list[str] = []  # the requirement(s) behind this decision, for the log


def priority(c: Classification, text: str) -> tuple[str, str]:
    if c.intent == "security_incident":
        return "P1", "security incident"
    if m := _COMPROMISE.search(text):
        return "P1", f"possible account compromise (\"{m.group(0)}\")"
    if c.intent in OUTAGE_INTENTS:
        return "P2", f"outage-type topic ({c.intent})"
    if c.urgency == "high":
        return "P2", "predicted urgency high"
    return "P3", "normal"


def protected_check(c: Classification, text: str) -> tuple[bool, str]:
    candidates = [c.intent] + [intent for intent, _ in c.alternatives]
    hit = next((i for i in candidates if i in PROTECTED_INTENTS), None)
    if hit:
        return True, f"protected category: {hit}"
    if m := _COMPROMISE.search(text):
        return True, f"possible account compromise (\"{m.group(0)}\")"
    if m := _BILLING_DISPUTE.search(text):
        return True, f"possible billing dispute (\"{m.group(0)}\")"
    return False, ""


def confidence_threshold() -> float:
    return float(os.getenv("CONFIDENCE_THRESHOLD", 0.80))


def route(ticket: Ticket, c: Classification, passages: list[Hit],
          threshold: float | None = None) -> Route:
    tau = confidence_threshold() if threshold is None else threshold

    def escalate(reason, reqs, protected=False, protected_reason=""):
        level, why = priority(c, ticket.text)
        return Route(action="escalate", reason=reason, threshold_used=tau,
                     protected=protected, protected_reason=protected_reason,
                     priority=level, priority_reason=why, requirement_ids=reqs + ["FR-09"])

    blocking = BLOCKING_FLAGS & set(ticket.flags)
    if blocking:
        return escalate(f"Escalated: ticket could not be read properly ({', '.join(sorted(blocking))}).",
                        ["FR-01", "FR-12"])
    protected, why = protected_check(c, ticket.text)
    if protected:
        return escalate(f"Escalated: {why}; these always go to a person.", ["FR-05"], True, why)
    if c.fallback:
        return escalate("Escalated: the classifier could not process this ticket.", ["FR-02", "FR-12"])
    if c.intent in NO_DOC_INTENTS:
        return escalate(f"Escalated: '{c.intent}' has no knowledge-base answer; it needs a person.",
                        ["FR-04"])
    if c.confidence < tau:
        return escalate(f"Escalated: confidence {c.confidence:.2f} in '{c.intent}' is below the "
                        f"threshold {tau:.2f}.", ["FR-04"])
    if not passages:
        return escalate(f"Escalated: no knowledge-base article matched closely enough to answer "
                        f"'{c.intent}'.", ["FR-03", "FR-12"])
    return Route(action="auto_respond", threshold_used=tau, requirement_ids=["FR-04"],
                 reason=f"Auto-respond: '{c.intent}' at confidence {c.confidence:.2f} "
                        f"(threshold {tau:.2f}), answered from {passages[0].doc_id}.")
