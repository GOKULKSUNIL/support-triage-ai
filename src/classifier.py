"""Classification (FR-02): predict intent and urgency with a calibrated confidence.

Ticket text is embedded with the same local model retrieval uses, then two
logistic regressions are trained on the development tickets: one for the 22
intents, one for urgency. Probabilities are calibrated (isotonic, 3-fold) so
that a stated 0.85 means right about 85% of the time, which is what makes the
routing threshold meaningful. Isotonic was chosen over sigmoid and raw
probabilities on the development tickets (see analysis/classifier_eval.py).
No LLM is involved.

The trained model is saved to storage/; if it is missing it is retrained from
the development tickets, so a fresh clone works with no extra step.
"""
import os
from pathlib import Path

import joblib
from pydantic import BaseModel
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression

from src.ingest import Ticket, load_tickets
from src.retrieval import embed

TRAIN_PATH = "data/development_tickets.json"
FALLBACK_INTENT = "unclear_request"


class Classification(BaseModel):
    intent: str
    urgency: str
    confidence: float  # calibrated probability of the predicted intent
    alternatives: list[tuple[str, float]]  # top 3 intents, best first
    fallback: bool = False


def _fit(X, y, C: float = 10.0, method: str = "isotonic"):
    base = LogisticRegression(C=C, max_iter=3000, random_state=0)
    if method == "raw":
        return base.fit(X, y)
    return CalibratedClassifierCV(base, method=method, cv=3).fit(X, y)


def train(tickets: list[Ticket]) -> dict:
    tickets = [t for t in tickets if t.labels and t.text]
    X = embed([t.text for t in tickets])
    return {
        "intent": _fit(X, [t.labels["intent"] for t in tickets]),
        "urgency": _fit(X, [t.labels["urgency"] for t in tickets]),
    }


class Classifier:
    def __init__(self, models: dict | None = None, path: str | None = None):
        if models is None:
            path = Path(path or os.getenv("CLASSIFIER_PATH", "./storage/classifier.joblib"))
            if path.exists():
                models = joblib.load(path)
            else:
                models = train(load_tickets(TRAIN_PATH))
                path.parent.mkdir(parents=True, exist_ok=True)
                joblib.dump(models, path)
        self.models = models

    def classify(self, ticket: Ticket) -> Classification:
        if not ticket.text.strip():
            return Classification(intent=FALLBACK_INTENT, urgency="medium",
                                  confidence=0.0, alternatives=[], fallback=True)
        x = embed([ticket.text])
        intent_model, urgency_model = self.models["intent"], self.models["urgency"]
        probs = intent_model.predict_proba(x)[0]
        ranked = sorted(zip(intent_model.classes_, probs), key=lambda p: -p[1])
        urgency = urgency_model.classes_[urgency_model.predict_proba(x)[0].argmax()]
        return Classification(
            intent=ranked[0][0],
            urgency=urgency,
            confidence=round(float(ranked[0][1]), 4),
            alternatives=[(c, round(float(p), 4)) for c, p in ranked[:3]],
        )
