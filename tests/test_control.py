"""Kill switch: pausing stops automatic answers at once, in flight too, and resuming restores them."""
import json
import re

import pytest

from src import control
from src.classify import Classifier
from src.ingest import normalise
from src.logging_store import DecisionLog
from src.pipeline import Pipeline
from src.retrieve import Index
from tests.fakes import FakeLLM, grounded, reply

# A routine ticket the router answers automatically (labelled auto_respond).
TICKET = normalise(json.load(open("data/development_tickets.json"))[0], 0)


def _writer(**values):
    """Drafts one sentence citing the first passage it was given."""
    first = re.search(r'<passage id="([^"]+)"', values["passages"]).group(1)
    return reply(("Pin dependencies to exact versions.", [first]))


@pytest.fixture(scope="module")
def parts(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("control")
    return Classifier(path=str(tmp / "clf.joblib")), Index("section", path=str(tmp / "chroma"))


def _pipeline(parts, log, writer=_writer):
    classifier, index = parts
    return Pipeline(classifier=classifier, index=index, log=log, control=log,
                    llm=FakeLLM(PR01=writer, PR02=lambda **v: grounded(v["sentences"].count("<sentence"))))


def test_pause_escalates_without_calling_the_model_and_resume_restores(parts, tmp_path):
    log = DecisionLog(str(tmp_path / "log.db"))
    pipe = _pipeline(parts, log)
    assert pipe.process(TICKET)["reply"]["status"] == "sent"

    log.set_paused(True, "Marcus", "wrong billing article")
    pipe.llm.calls.clear()
    result = pipe.process(TICKET)
    assert result["action"] == "escalate"
    assert "paused" in result["reason"] and "Marcus" in result["reason"]
    assert "PR-01" not in pipe.llm.calls  # nothing drafted while paused

    log.set_paused(False, "Marcus", "article corrected")
    assert pipe.process(TICKET)["reply"]["status"] == "sent"
    assert log.count() == 3 and [e["paused"] for e in log.control_history()] == [1, 0]


def test_ticket_in_flight_when_switch_is_pulled_is_not_sent(parts, tmp_path):
    log = DecisionLog(str(tmp_path / "log.db"))

    def writer_then_pause(**values):
        log.set_paused(True, "Marcus", "pulled while drafting")
        return _writer(**values)

    result = _pipeline(parts, log, writer_then_pause).process(TICKET)
    assert result["action"] == "escalate" and result["reply"]["status"] == "paused"
    assert "pulled while drafting" in result["reason"]


def test_command_line_pause_resume_status(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'log.db'}")
    control.main(["status"])
    assert "ON (the switch has never been used)" in capsys.readouterr().out
    control.main(["pause", "--by", "Marcus", "--reason", "test"])
    assert "PAUSED" in capsys.readouterr().out
    assert DecisionLog(str(tmp_path / "log.db")).paused()["changed_by"] == "Marcus"
    control.main(["resume", "--by", "Marcus", "--reason", "done"])
    assert "Automatic answering: ON" in capsys.readouterr().out


def test_harness_run_obeys_the_switch_in_the_configured_store(tmp_path, monkeypatch):
    # The run writes its own decisions.db, but the switch is read from DATABASE_URL.
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'store.db'}")
    DecisionLog(str(tmp_path / "store.db")).set_paused(True, "Marcus", "demo")
    assert Pipeline(classifier=object(), index=object(), log=DecisionLog(str(tmp_path / "run.db")),
                    llm=FakeLLM()).control.paused()["reason"] == "demo"
