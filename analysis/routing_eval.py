"""Choose the confidence threshold and check the protected rule (B-07, T-05c).

Run from cloudserve-support/:  .venv/bin/python -m analysis.routing_eval
Writes analysis/output/routing_report.md.

Every development ticket is classified by a model that never saw its text
(grouped 5-fold, out-of-fold predictions), retrieved against the index, and
routed at each candidate threshold. Results are compared with the labels:
  auto rate          share of tickets the system would answer itself
  auto precision     share of those the labels also mark auto_respond
  must-not breaches  must_not_auto_respond tickets the system would answer
"""
import os
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedGroupKFold

from src.classifier import Classifier, _fit
from src.ingest import load_tickets
from src.retrieval import Index, embed
from src.routing import route

OUT = Path("analysis/output/routing_report.md")
THRESHOLDS = (0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.98)


def out_of_fold(tickets):
    X = np.array(embed([t.text for t in tickets]))
    y = np.array([t.labels["intent"] for t in tickets])
    u = np.array([t.labels["urgency"] for t in tickets])
    groups = [t.text.lower() for t in tickets]
    preds = [None] * len(tickets)
    for tr, te in StratifiedGroupKFold(5, shuffle=True, random_state=0).split(X, y, groups):
        clf = Classifier(models={"intent": _fit(X[tr], y[tr]), "urgency": _fit(X[tr], u[tr])})
        for i in te:
            preds[i] = clf.classify(tickets[i])
    return preds


def main():
    tickets = load_tickets("data/development_tickets.json")
    preds = out_of_fold(tickets)
    index = Index("section")
    passages = [index.search(t.text) for t in tickets]
    label_auto = np.array([t.labels["expected_route"] == "auto_respond" for t in tickets])
    must_not = np.array([t.labels["must_not_auto_respond"] for t in tickets])

    report = ["# Routing evaluation (development tickets, out-of-fold predictions)", "",
              f"{len(tickets)} tickets; labels mark {label_auto.sum()} auto_respond, "
              f"{(~label_auto).sum()} escalate, {must_not.sum()} must_not_auto_respond.", "",
              "| threshold | auto rate | auto precision (label agrees) | routing accuracy | must-not breaches |",
              "|---|---|---|---|---|"]
    for th in THRESHOLDS:
        auto = np.array([route(t, c, p, th).action == "auto_respond"
                         for t, c, p in zip(tickets, preds, passages)])
        prec = (auto & label_auto).sum() / auto.sum() if auto.sum() else float("nan")
        acc = (auto == label_auto).mean()
        report.append(f"| {th:.2f} | {auto.mean():.1%} | {prec:.1%} | {acc:.1%} | {(auto & must_not).sum()} |")

    th = float(os.getenv("CONFIDENCE_THRESHOLD", 0.80))
    routes = [route(t, c, p, th) for t, c, p in zip(tickets, preds, passages)]
    auto = np.array([r.action == "auto_respond" for r in routes])
    report += ["", f"## Disagreements with the labels at threshold {th:.2f}", "",
               "| intent | system auto, label escalate | system escalate, label auto |", "|---|---|---|"]
    over, under = Counter(), Counter()
    for t, a, la in zip(tickets, auto, label_auto):
        if a and not la:
            over[t.labels["intent"]] += 1
        elif la and not a:
            under[t.labels["intent"]] += 1
    for intent in sorted(set(over) | set(under), key=lambda i: -(over[i] + under[i])):
        report.append(f"| {intent} | {over[intent]} | {under[intent]} |")

    report += ["", "## Why tickets escalated", ""]
    kinds = Counter(r.reason.split(":")[1].split("(")[0].split(" in ")[0].strip()[:40]
                    for r in routes if r.action == "escalate")
    report += [f"- {k}: {v}" for k, v in kinds.most_common()]

    report += ["", "## Escalation priority (D-13) against labelled urgency", "",
               "| priority | escalations | labelled high | labelled medium | labelled low |",
               "|---|---|---|---|---|"]
    for level in ("P1", "P2", "P3"):
        u = Counter(t.labels["urgency"] for t, r in zip(tickets, routes) if r.priority == level)
        report.append(f"| {level} | {sum(u.values())} | {u['high']} | {u['medium']} | {u['low']} |")

    report += ["", "## must_not_auto_respond tickets the system would answer", "",
               "| ticket | intent | confidence | reason |", "|---|---|---|---|"]
    for t, c, r in zip(tickets, preds, routes):
        if r.action == "auto_respond" and t.labels["must_not_auto_respond"]:
            report.append(f"| {t.ticket_id} | {t.labels['intent']} | {c.confidence:.2f} | {r.reason} |")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
