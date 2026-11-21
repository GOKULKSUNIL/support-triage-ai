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
import time
import uuid
from functools import lru_cache

from fastapi import FastAPI
from prometheus_client import make_asgi_app
from pydantic import BaseModel

from src import monitoring
from src.ingest import normalise
from src.logging_store import DecisionLog
from src.pipeline import Pipeline

app = FastAPI(title="CloudServe support triage",
              description="Classifies a ticket, answers it from the knowledge base when it is safe "
                          "to, and otherwise hands it to a person with context.")
app.mount("/metrics", make_asgi_app())


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
    started = time.perf_counter()
    result = _pipeline().process(normalise(record, 0))
    result.pop("labels", None)
    monitoring.record(result, time.perf_counter() - started)
    return result


@app.get("/health")
def health() -> dict:
    pause = DecisionLog().paused()
    return {"status": "ok",
            "automatic_answering": "paused" if pause else "on",
            "paused": pause,
            "model": os.getenv("LLM_MODEL"),
            "fallback_model": os.getenv("FALLBACK_MODEL") or None}
