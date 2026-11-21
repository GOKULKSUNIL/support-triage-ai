"""Prometheus metrics (Setup Guide section 6), shared by the API and the harness.

The API serves them at /metrics; the harness serves them on METRICS_PORT while
a run is in progress, so the dashboard shows the unattended run as it happens.
"""
from prometheus_client import Counter, Histogram

TICKETS = Counter("tickets_processed_total", "Tickets processed", ["channel", "outcome"])
LATENCY = Histogram("response_seconds", "End to end response time",
                    buckets=(0.5, 1, 2, 3, 5, 10, 20, 30, 60, 120))
GUARDRAIL = Counter("guardrail_blocks_total", "Responses blocked", ["guardrail"])
for _name in ("private_data", "grounding"):
    GUARDRAIL.labels(guardrail=_name)  # shown as 0 until a guardrail fires
CONFIDENCE = Histogram("classification_confidence", "Classifier confidence (drift shows here first)",
                       buckets=(0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0))


def record(result: dict, seconds: float) -> None:
    """Count one processed ticket."""
    LATENCY.observe(seconds)
    TICKETS.labels(channel=result["channel"], outcome=result["action"]).inc()
    for check in result["guardrail_checks"]:
        if not check["passed"]:
            GUARDRAIL.labels(guardrail=check["name"]).inc()
    if result["confidence"] is not None:
        CONFIDENCE.observe(result["confidence"])
