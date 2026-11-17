"""FR-08 decision-log tests (T-08a-c). Full-run reconciliation is checked by the harness."""
import json

import pytest

from src.decision_log import DecisionLog, mask


@pytest.fixture
def log(tmp_path):
    return DecisionLog(str(tmp_path / "decisions.db"))


def test_t08a_one_row_per_ticket(log):
    for i in range(7):
        log.write(ticket_id=f"T{i}", action="escalate", reason="r",
                  alternatives=[("a", 0.9), ("b", 0.1)], sources_used=[])
    assert log.count() == 7
    row = log.rows()[0]
    assert row["created_at"].endswith("Z") and len(row["decision_id"]) == 32
    assert json.loads(row["alternatives"]) == [["a", 0.9], ["b", 0.1]]


def test_t08b_failed_ticket_still_has_a_row(log):
    log.write(ticket_id="BAD1", action="escalate", reason="provider_unavailable",
              error="TimeoutError: provider did not answer in 20s")
    (row,) = log.rows()
    assert row["ticket_id"] == "BAD1" and row["error"].startswith("TimeoutError")


def test_t08c_no_raw_customer_name_or_id(log):
    text = "Hi, this is Xin Kulkarni (CUST-1131). Xin here again: deploys fail."
    masked = mask(text, "Xin Kulkarni", "CUST-1131")
    log.write(ticket_id="T1", input_text=masked)
    stored = log.rows()[0]["input_text"]
    assert "Xin" not in stored and "Kulkarni" not in stored and "CUST-1131" not in stored
    assert "[NAME]" in stored and "[CUSTOMER_ID]" in stored and "deploys fail" in stored


def test_unknown_field_is_rejected(log):
    with pytest.raises(ValueError):
        log.write(ticket_id="T1", customer_name="Xin Kulkarni")
