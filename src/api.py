"""HTTP interface: one ticket at a time through the same pipeline as the harness.

    uvicorn src.api:app --port 8000        then open http://localhost:8000/docs

POST /tickets   run one ticket; returns the action, the reply or the escalation
                packet, citations, reason, priority and requirement ids
GET  /health    liveness, kill-switch state and the configured models
GET  /metrics   Prometheus metrics (Setup Guide section 6): tickets by channel
                and outcome, latency, guardrail blocks, confidence

Decisions are written to the configured store (DATABASE_URL), the same store
the kill switch (python -m src.control) reads. The classifier and the vector
index load on the first ticket, so /health answers straight away.
"""
import os
import uuid
from functools import lru_cache

from fastapi import FastAPI
from prometheus_client import Counter, Histogram, make_asgi_app
from pydantic import BaseModel

from src.ingest import normalise
from src.logging_store import DecisionLog
from src.pipeline import Pipeline

app = FastAPI(title="CloudServe support triage",
              description="Classifies a ticket, answers it from the knowledge base when it is safe "
                          "to, and otherwise hands it to a person with context.")
app.mount("/metrics", make_asgi_app())

TICKETS = Counter("tickets_processed_total", "Tickets processed", ["channel", "outcome"])
LATENCY = Histogram("response_seconds", "End to end response time",
                    buckets=(0.5, 1, 2, 3, 5, 10, 20, 30, 60, 120))
GUARDRAIL = Counter("guardrail_blocks_total", "Responses blocked", ["guardrail"])
for _name in ("private_data", "grounding"):
    GUARDRAIL.labels(guardrail=_name)  # shown as 0 until a guardrail fires
CONFIDENCE = Histogram("classification_confidence", "Classifier confidence (drift shows here first)",
                       buckets=(0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0))


class TicketIn(BaseModel):
    channel: str
    subject: str = ""
    body: str
    ticket_id: str | None = None
    customer_id: str = ""
    customer_name: str = ""
    customer_tier: str = "unknown"
    customer_region: str = "unknown"
    language_fluency: str = "unknown"
    received_at: str = ""

    model_config = {"json_schema_extra": {"examples": [{
        "channel": "email", "subject": "Build keeps failing",
        "body": "Our builds fail during dependency resolution since this morning. What should we check?",
        "customer_tier": "business", "customer_region": "europe", "language_fluency": "fluent"}]}}


@lru_cache(maxsize=1)
def _pipeline() -> Pipeline:
    return Pipeline()


@app.post("/tickets")
def process_ticket(ticket: TicketIn) -> dict:
    record = ticket.model_dump()
    record["ticket_id"] = ticket.ticket_id or f"API-{uuid.uuid4().hex[:8]}"
    with LATENCY.time():
        result = _pipeline().process(normalise(record, 0))
    result.pop("labels", None)
    TICKETS.labels(channel=result["channel"], outcome=result["action"]).inc()
    for check in result["guardrail_checks"]:
        if not check["passed"]:
            GUARDRAIL.labels(guardrail=check["name"]).inc()
    if result["confidence"] is not None:
        CONFIDENCE.observe(result["confidence"])
    return result


@app.get("/health")
def health() -> dict:
    pause = DecisionLog().paused()
    return {"status": "ok",
            "automatic_answering": "paused" if pause else "on",
            "paused": pause,
            "model": os.getenv("LLM_MODEL"),
            "fallback_model": os.getenv("FALLBACK_MODEL") or None}
