"""FR-02 classifier tests (T-02a-c). T-02d is analysis/classifier_eval.py."""
import pytest

from src.classifier import Classifier
from src.ingest import load_tickets, normalise

INTENTS = 22


@pytest.fixture(scope="module")
def clf(tmp_path_factory):
    return Classifier(path=str(tmp_path_factory.mktemp("model") / "classifier.joblib"))


def test_t02a_every_ticket_gets_intent_urgency_and_confidence(clf):
    assert len(clf.models["intent"].classes_) == INTENTS
    for t in load_tickets("data/development_tickets.json")[:20]:
        c = clf.classify(t)
        assert c.intent in clf.models["intent"].classes_
        assert c.urgency in {"low", "medium", "high"}
        assert 0.0 <= c.confidence <= 1.0
        assert len(c.alternatives) == 3 and c.alternatives[0][0] == c.intent


def test_t02b_empty_text_returns_fallback(clf):
    c = clf.classify(normalise({"ticket_id": "E1", "channel": "email", "body": "   "}, 0))
    assert c.fallback and c.intent == "unclear_request" and c.confidence == 0.0


def test_t02c_same_input_same_output(clf):
    t = normalise({"ticket_id": "S1", "channel": "chat",
                   "body": "SSO login loops back to the sign-in page after the IdP redirect"}, 0)
    assert clf.classify(t) == clf.classify(t)
