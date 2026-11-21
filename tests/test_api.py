"""API: /tickets runs the same pipeline as the harness; /health reports the kill switch."""
from fastapi.testclient import TestClient

import src.api as api
from src.logging_store import DecisionLog
from tests.test_control import TICKET, _pipeline, parts  # noqa: F401  (parts is a fixture)

client = TestClient(api.app)


def test_post_ticket_returns_the_pipeline_result(parts, tmp_path, monkeypatch):  # noqa: F811
    log = DecisionLog(str(tmp_path / "log.db"))
    monkeypatch.setattr(api, "_pipeline", lambda: _pipeline(parts, log))
    body = {"channel": TICKET.channel, "subject": TICKET.subject, "body": TICKET.body}
    result = client.post("/tickets", json=body).json()
    assert result["ticket_id"].startswith("API-") and "labels" not in result
    assert result["action"] == "auto_respond" and result["reply"]["status"] == "sent"
    assert result["sources"] and result["requirement_ids"] and log.count() == 1
    metrics = client.get("/metrics/").text
    assert f'tickets_processed_total{{channel="{TICKET.channel}",outcome="auto_respond"}}' in metrics
    assert "response_seconds_count" in metrics and "classification_confidence_bucket" in metrics


def test_missing_body_is_rejected(monkeypatch):
    assert client.post("/tickets", json={"channel": "email"}).status_code == 422


def test_health_shows_the_kill_switch(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'store.db'}")
    assert client.get("/health").json()["automatic_answering"] == "on"
    DecisionLog(str(tmp_path / "store.db")).set_paused(True, "Marcus", "demo")
    assert client.get("/health").json()["automatic_answering"] == "paused"
