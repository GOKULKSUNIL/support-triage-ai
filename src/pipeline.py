r"""The ticket pipeline as a LangGraph graph. The harness and the API both call it.

    classify -> retrieve -> route --auto_respond--> draft --ok--> validate --pass--> END (sent)
                                 |                      |                |
                                 |                   unusable          blocked
                                 |                      v                v
                                 \--escalate-------> escalate <----------/ --> END

A ticket is only sent if routing, drafting (PR-01 + citation checks) and the
guardrails (private data + PR-02 grounding) all pass; any failure turns it
into an escalation with the reason. Each node is a thin wrapper around a
module in src/. `Pipeline.process` never raises, and the decision-log row is
written in a `finally` path so every ticket has one.
"""
import time
import traceback
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.classify import Classification, Classifier
from src.generate import Draft, draft
from src.guardrails import Validation, validate
from src.ingest import Ticket
from src.llm import LLM
from src.logging_store import DecisionLog, mask
from src.retrieve import Hit, Index
from src.route import Route, confidence_threshold, priority, route


class State(TypedDict, total=False):
    ticket: Ticket
    classification: Classification
    passages: list[Hit]
    route: Route
    draft: Draft
    validation: Validation
    reply: dict | None
    packet: dict | None


class Pipeline:
    def __init__(self, classifier: Classifier | None = None, index: Index | None = None,
                 log: DecisionLog | None = None, threshold: float | None = None,
                 llm: LLM | None = None):
        self.classifier = classifier or Classifier()
        self.index = index or Index("section")
        self.log = log or DecisionLog()
        self.llm = llm or LLM()
        self.threshold = threshold
        self.graph = self._build()

    def _build(self):
        g = StateGraph(State)
        g.add_node("classify", lambda s: {"classification": self.classifier.classify(s["ticket"])})
        g.add_node("retrieve", lambda s: {"passages": self.index.search(s["ticket"].text)})
        g.add_node("route", lambda s: {"route": route(s["ticket"], s["classification"],
                                                       s["passages"], self.threshold)})
        g.add_node("draft", self._draft)
        g.add_node("validate", self._validate)
        g.add_node("escalate", self._escalate)
        g.add_edge(START, "classify")
        g.add_edge("classify", "retrieve")
        g.add_edge("retrieve", "route")
        next_step = {"auto_respond": "draft", "escalate": "escalate"}
        g.add_conditional_edges("route", lambda s: s["route"].action, next_step)
        g.add_conditional_edges("draft", lambda s: s["route"].action,
                                {"auto_respond": "validate", "escalate": "escalate"})
        g.add_conditional_edges("validate", lambda s: s["route"].action,
                                {"auto_respond": END, "escalate": "escalate"})
        g.add_edge("escalate", END)
        return g.compile()

    @staticmethod
    def _escalated(state: State, reason: str, reqs: list[str]) -> Route:
        level, why = priority(state["classification"], state["ticket"].text)
        return Route(action="escalate", reason=reason, threshold_used=state["route"].threshold_used,
                     priority=level, priority_reason=why, requirement_ids=reqs + ["FR-09"])

    def _draft(self, state: State) -> dict:
        d = draft(state["ticket"], state["passages"], self.llm)
        if d.ok:
            return {"draft": d}
        return {"draft": d, "reply": {"status": d.status, "text": "", "problem": d.problem},
                "route": self._escalated(state, f"Escalated: the drafted reply could not be used "
                                                f"({d.problem}).",
                                         ["FR-12"] if d.status == "provider_unavailable" else ["FR-06"])}

    def _validate(self, state: State) -> dict:
        d = state["draft"]
        v = validate(d, state["passages"], state["ticket"], self.llm)
        if v.blocked:
            failed = "; ".join(f"{c.name}: {c.detail}" for c in v.checks if not c.passed)
            return {"validation": v, "reply": {"status": "blocked", "text": "", "problem": failed},
                    "route": self._escalated(state, f"Escalated: reply blocked by guardrail ({failed}).",
                                             ["FR-07"])}
        return {"validation": v,
                "route": state["route"].model_copy(
                    update={"requirement_ids": ["FR-04", "FR-06", "FR-07", "FR-13"]}),
                "reply": {
            "status": "sent", "text": d.text,
            "sentences": [s.model_dump() for s in d.sentences]}}

    @staticmethod
    def _escalate(state: State) -> dict:
        # Template packet (FR-09); the PR-03 written summary arrives in B-16.
        c, r = state["classification"], state["route"]
        return {"packet": {
            "summary": None,
            "intent": c.intent,
            "alternatives": c.alternatives,
            "suggested_articles": sorted({p.doc_id for p in state["passages"]}),
            "unsure_about": r.reason,
            "priority": r.priority,
            "priority_reason": r.priority_reason,
        }}

    def process(self, ticket: Ticket) -> dict:
        start = time.perf_counter()
        state: State = {"ticket": ticket}
        error = None
        try:
            state = self.graph.invoke(state)
        except Exception as exc:  # one bad ticket must not stop the run
            error = f"{type(exc).__name__}: {exc}"
            tau = confidence_threshold() if self.threshold is None else self.threshold
            state["route"] = Route(action="escalate", threshold_used=tau,
                                   reason=f"Escalated: processing error ({type(exc).__name__}).",
                                   priority="P3", priority_reason="processing error",
                                   requirement_ids=["FR-12", "FR-09"])
            traceback.print_exc()
        finally:
            latency_ms = round((time.perf_counter() - start) * 1000, 1)
            result = self._result(ticket, state, latency_ms, error)
            self._write_log(ticket, result)
        return result

    @staticmethod
    def _result(ticket: Ticket, state: State, latency_ms: float, error: str | None) -> dict:
        c, r = state.get("classification"), state["route"]
        d, v = state.get("draft"), state.get("validation")
        return {
            "ticket_id": ticket.ticket_id,
            "channel": ticket.channel,
            "customer_tier": ticket.customer_tier,
            "customer_region": ticket.customer_region,
            "language_fluency": ticket.language_fluency,
            "flags": ticket.flags,
            "intent": c.intent if c else None,
            "urgency": c.urgency if c else None,
            "confidence": c.confidence if c else None,
            "alternatives": c.alternatives if c else [],
            "action": r.action,
            "reason": r.reason,
            "protected": r.protected,
            "priority": r.priority,
            "stage": ("error" if error else "validate" if v else "draft" if d
                      else "route" if c else "ingest"),
            "requirement_ids": r.requirement_ids,
            "threshold": r.threshold_used,
            "sources": [p.passage_id for p in state.get("passages", [])],
            "reply": state.get("reply"),
            "packet": state.get("packet"),
            "guardrail_checks": [c.model_dump() for c in v.checks] if v else [],
            "blocked": bool(v and v.blocked),
            "llm_calls": [call for call in (d.call if d else None, v.call if v else None) if call],
            "latency_ms": latency_ms,
            "error": error,
            "labels": ticket.labels,
        }

    def _write_log(self, ticket: Ticket, result: dict) -> None:
        self.log.write(
            ticket_id=result["ticket_id"], channel=result["channel"],
            input_text=mask(ticket.text, ticket.customer_name, ticket.customer_id),
            intent=result["intent"], urgency=result["urgency"], confidence=result["confidence"],
            alternatives=result["alternatives"], threshold=result["threshold"],
            action=result["action"], reason=result["reason"], priority=result["priority"],
            stage=result["stage"], requirement_ids=result["requirement_ids"],
            sources_used=result["sources"], guardrail_checks=result["guardrail_checks"],
            blocked=int(result["blocked"]),
            prompt_versions={c["prompt"]: c["version"] for c in result["llm_calls"]},
            model=", ".join(sorted({c["model"] for c in result["llm_calls"] if c.get("model")})) or None,
            latency_ms=result["latency_ms"], error=result["error"],
        )
