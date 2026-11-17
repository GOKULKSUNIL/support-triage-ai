"""Evaluate the classifier on a held-back part of the dev tickets (B-06, T-02d).

Run from cloudserve-support/:  .venv/bin/python -m analysis.classifier_eval
Writes analysis/output/classifier_report.md.

97 ticket texts appear more than once in the development set, so a plain
random split would put copies of the same text on both sides. Splits here are
grouped by text: every copy stays on one side.

The 500 development tickets are split about 80/20 (grouped, stratified by
intent). C and the calibration method are chosen by grouped 5-fold
cross-validation on the 80% only; the 20% is used once, for the figures that
follow. Validation tickets are not touched here.
"""
from pathlib import Path

import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedGroupKFold

from src.classifier import Classifier, _fit
from src.ingest import load_tickets
from src.retrieval import embed

OUT = Path("analysis/output/classifier_report.md")
BANDS = [(0.0, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.01)]
CANDIDATES = [(C, m) for C in (1.0, 10.0, 100.0) for m in ("raw", "sigmoid", "isotonic")]


def ece(conf, correct):
    """Expected calibration error in points: weighted gap between stated and observed."""
    total = 0.0
    for lo in np.arange(0, 1, 0.1):
        m = (conf >= lo) & (conf < lo + 0.1 + (lo >= 0.9))
        if m.sum():
            total += m.mean() * abs(conf[m].mean() - correct[m].mean())
    return total * 100


def calibration(conf, correct):
    lines = ["| confidence band | tickets | stated (mean) | observed accuracy | gap |",
             "|---|---|---|---|---|"]
    for lo, hi in BANDS:
        m = (conf >= lo) & (conf < hi)
        if m.sum():
            s, o = conf[m].mean(), correct[m].mean()
            lines.append(f"| {lo:.1f}–{min(hi, 1):.1f} | {m.sum()} | {s:.1%} | {o:.1%} | {(o - s) * 100:+.1f} pts |")
    return lines


def coverage(conf, correct):
    lines = ["| threshold | share auto-eligible | accuracy above threshold |", "|---|---|---|"]
    for th in (0.5, 0.6, 0.7, 0.8, 0.9, 0.95):
        m = conf >= th
        acc = f"{correct[m].mean():.1%}" if m.sum() else "—"
        lines.append(f"| {th:.2f} | {m.mean():.1%} | {acc} |")
    return lines


def select(X, y, groups):
    lines = ["| C | probabilities | CV accuracy | calibration error (ECE) |", "|---|---|---|---|"]
    folds = list(StratifiedGroupKFold(5, shuffle=True, random_state=0).split(X, y, groups))
    best = None
    for C, method in CANDIDATES:
        conf, correct = np.zeros(len(y)), np.zeros(len(y), bool)
        for tr, te in folds:
            model = _fit(X[tr], y[tr], C, method)
            P = model.predict_proba(X[te])
            conf[te] = P.max(1)
            correct[te] = model.classes_[P.argmax(1)] == y[te]
        e = ece(conf, correct)
        lines.append(f"| {C:g} | {method} | {correct.mean():.1%} | {e:.1f} pts |")
        if best is None or e < best[0]:
            best = (e, C, method)
    return best[1], best[2], lines


def main():
    tickets = load_tickets("data/development_tickets.json")
    X = np.array(embed([t.text for t in tickets]))
    y = np.array([t.labels["intent"] for t in tickets])
    u = np.array([t.labels["urgency"] for t in tickets])
    groups = [t.text.lower() for t in tickets]
    tr, te = next(StratifiedGroupKFold(5, shuffle=True, random_state=42).split(X, y, groups))

    C, method, sel_lines = select(X[tr], y[tr], [groups[i] for i in tr])
    clf = Classifier(models={"intent": _fit(X[tr], y[tr], C, method),
                             "urgency": _fit(X[tr], u[tr], C, method)})
    test_t = [tickets[i] for i in te]
    preds = [clf.classify(t) for t in test_t]
    y_pred = np.array([p.intent for p in preds])
    conf = np.array([p.confidence for p in preds])
    correct = y_pred == y[te]

    report = ["# Classifier evaluation (development tickets, grouped hold-back)", "",
              f"Train {len(tr)}, held back {len(te)}; no ticket text appears on both sides. "
              "Validation set not used.", "",
              "## Choosing C and calibration (grouped 5-fold CV on the training part only)", ""]
    report += sel_lines + ["", f"Chosen: C={C:g}, {method} (lowest calibration error).", "",
                           "## Intent, per class (held back)", "", "```",
                           classification_report(y[te], y_pred, digits=3, zero_division=0), "```", "",
                           "## Calibration on the held-back part", ""]
    report += calibration(conf, correct) + [f"", f"ECE {ece(conf, correct):.1f} pts (target: within 5).", "",
                                            "## Coverage vs accuracy (input to the routing threshold, B-07)", ""]
    report += coverage(conf, correct)
    report += ["", "## Urgency (held back)", "",
               "67 of the 97 repeated texts carry different urgency labels on their copies, "
               "so urgency is not fully determined by the text.", "", "```",
               classification_report(u[te], [p.urgency for p in preds], digits=3, zero_division=0),
               str(confusion_matrix(u[te], [p.urgency for p in preds], labels=["low", "medium", "high"])),
               "```", "", "## Held-back intent errors", "",
               "| ticket | true | predicted | confidence |", "|---|---|---|---|"]
    for t, p in zip(test_t, preds):
        if p.intent != t.labels["intent"]:
            report.append(f"| {t.ticket_id} | {t.labels['intent']} | {p.intent} | {p.confidence:.2f} |")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
