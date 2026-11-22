"""Metrics report (FR-11): computed from results.jsonl and the decision log, no manual step.

Four groups, in the order the Evaluation Framework asks for: volume and
reconciliation, business outcomes, technical performance, governance.
Label-based figures are included only when the input file carries labels.
"""
import argparse
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from sklearn.metrics import classification_report, confusion_matrix

from src.guardrails import private_data

PROTECTED_LABEL = "must_not_auto_respond"
BANDS = [(0.0, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.01)]


def _pct(n, d):
    return f"{n / d:.1%}" if d else "—"


def _reason_kind(reason: str) -> str:
    """Group reasons by their wording, without the ticket-specific intent or numbers."""
    text = reason.split(":", 1)[-1]
    while re.search(r"\([^()]*\)", text):  # drop bracketed detail, innermost first
        text = re.sub(r"\([^()]*\)", "", text)
    text = re.sub(r"'[a-z_]+'|\d+(\.\d+)?", "", text)
    text = text.split(";")[0].split(":")[0]
    return re.sub(r"\s+", " ", text).strip(" .") or "other"


def _sent_text(r):
    reply = r.get("reply") or {}
    return reply.get("text", "") if reply.get("status") == "sent" else ""


def _cited_docs(r):
    """Articles the sent reply cites (falls back to the retrieved ones if it has no sentences)."""
    reply = r.get("reply") or {}
    cited = {pid.split("#")[0] for s in reply.get("sentences", []) for pid in s.get("sources", [])}
    return cited or {s.split("#")[0] for s in r["sources"]}


def _private(text):
    # Same check as the guardrail, with no ticket owner: any customer id counts.
    return not private_data(text, SimpleNamespace(customer_id="")).passed


def compute(results: list[dict], log_rows: int, tickets_in: int) -> dict:
    n = len(results)
    auto = [r for r in results if r["action"] == "auto_respond"]
    esc = [r for r in results if r["action"] == "escalate"]
    lat = sorted(r["latency_ms"] for r in results)
    # Time to first reply (Evaluation Framework): for an automatic answer it is the
    # processing time; an escalated ticket's reply comes from a person, outside this run.
    reply_s = [r["latency_ms"] / 1000 for r in auto]
    m = {
        "reply_mean_s": float(np.mean(reply_s)) if reply_s else None,
        "reply_median_s": float(np.median(reply_s)) if reply_s else None,
        "reply_p95_s": float(np.percentile(reply_s, 95)) if reply_s else None,
        "tickets_in": tickets_in, "results_out": n, "log_rows": log_rows,
        "reconciled": tickets_in == n == log_rows,
        "errors": sum(1 for r in results if r["error"]),
        "auto": len(auto), "escalated": len(esc),
        "escalation_rate": len(esc) / n if n else 0.0,
        "escalation_reasons": Counter(_reason_kind(r["reason"]) for r in esc).most_common(),
        "priority": Counter(r["priority"] for r in esc),
        "protected": sum(r["protected"] for r in results),
        "latency_p50_ms": float(np.percentile(lat, 50)) if lat else 0.0,
        "latency_p95_ms": float(np.percentile(lat, 95)) if lat else 0.0,
        "sent": sum(1 for r in results if (r["reply"] or {}).get("status") == "sent"),
        "reply_outcomes": Counter((r["reply"] or {}).get("status") for r in results if r["reply"]),
        "blocked": sum(1 for r in results if r.get("blocked")),
        "guardrail_failures": Counter(c["name"] for r in results for c in r.get("guardrail_checks", [])
                                      if not c["passed"]),
        "cached_calls": sum(1 for r in results for c in r.get("llm_calls", []) if c.get("cached")),
        "llm_calls": sum(len(r.get("llm_calls", [])) for r in results),
        # Governance: an independent scan of every reply actually sent (target 0).
        "private_data_sent": [r["ticket_id"] for r in results if _sent_text(r) and _private(_sent_text(r))],
        # Availability: tickets the system handled end to end, with no processing error and no
        # provider failure (those still reach a person, but the system did not do its job).
        "availability": (sum(1 for r in results if not r["error"] and "provider unavailable" not in r["reason"])
                         / n if n else 0.0),
        "provider_failures": sum(1 for r in results if "provider unavailable" in r["reason"]),
    }
    labelled = [r for r in results if r.get("labels")]
    m["labelled"] = len(labelled)
    if labelled:
        y = [r["labels"]["intent"] for r in labelled]
        p = [r["intent"] or "none" for r in labelled]
        m["intent_report"] = classification_report(y, p, digits=3, zero_division=0)
        m["intent_accuracy"] = float(np.mean([a == b for a, b in zip(y, p)]))
        m["urgency_accuracy"] = float(np.mean([r["urgency"] == r["labels"]["urgency"] for r in labelled]))
        need = [r for r in labelled if r["labels"].get("expected_doc_ids")]
        m["retrieval_hit_rate"] = (np.mean([bool(set(r["labels"]["expected_doc_ids"]) &
                                                 {s.split("#")[0] for s in r["sources"]}) for r in need])
                                   if need else None)
        label_auto = [r["labels"]["expected_route"] == "auto_respond" for r in labelled]
        sys_auto = [r["action"] == "auto_respond" for r in labelled]
        m["label_escalation_rate"] = 1 - float(np.mean(label_auto))
        m["routing_accuracy"] = float(np.mean([a == b for a, b in zip(label_auto, sys_auto)]))
        m["auto_label_agrees"] = (sum(a and b for a, b in zip(label_auto, sys_auto)) / sum(sys_auto)
                                  if any(sys_auto) else None)
        m["avoidable_escalations"] = sum(la and not sa for la, sa in zip(label_auto, sys_auto))
        # Wrong automatic answers, as far as the labels can tell: answered although the labels
        # send it to a person, answered from an article the labels do not expect, or answered
        # under the wrong intent. Whether the reply's content is right needs the human review.
        auto_l = [r for r in labelled if r["action"] == "auto_respond"]
        m["wrong_should_escalate"] = [r["ticket_id"] for r in auto_l
                                      if r["labels"]["expected_route"] != "auto_respond"]
        m["wrong_article"] = [r["ticket_id"] for r in auto_l if r["labels"].get("expected_doc_ids")
                              and not set(r["labels"]["expected_doc_ids"]) & _cited_docs(r)]
        m["wrong_intent"] = [r["ticket_id"] for r in auto_l if r["intent"] != r["labels"]["intent"]]
        m["wrong_any"] = sorted(set(m["wrong_should_escalate"]) | set(m["wrong_article"]) | set(m["wrong_intent"]))
        m["auto_labelled"] = len(auto_l)
        classes = sorted(set(y) | set(p))
        m["confusion"] = (classes, confusion_matrix(y, p, labels=classes).tolist())
        m["must_not_breaches"] = [r["ticket_id"] for r in labelled
                                  if r["labels"].get(PROTECTED_LABEL) and r["action"] == "auto_respond"]
        conf = np.array([r["confidence"] or 0.0 for r in labelled])
        correct = np.array([a == b for a, b in zip(y, p)])
        m["calibration"] = [(lo, hi, int(((conf >= lo) & (conf < hi)).sum()),
                             float(conf[(conf >= lo) & (conf < hi)].mean()),
                             float(correct[(conf >= lo) & (conf < hi)].mean()))
                            for lo, hi in BANDS if ((conf >= lo) & (conf < hi)).any()]
        m["segments"] = {seg: _segments(labelled, seg)
                         for seg in ("customer_tier", "customer_region", "language_fluency")}
    return m


def _segments(rows, field):
    out = {}
    for value in sorted({r[field] for r in rows}):
        grp = [r for r in rows if r[field] == value]
        out[value] = {
            "tickets": len(grp),
            "intent_accuracy": float(np.mean([r["intent"] == r["labels"]["intent"] for r in grp])),
            "routing_accuracy": float(np.mean([(r["action"] == "auto_respond") ==
                                               (r["labels"]["expected_route"] == "auto_respond")
                                               for r in grp])),
            "escalation_rate": float(np.mean([r["action"] == "escalate" for r in grp])),
        }
    return out


def render(m: dict, meta: dict) -> str:
    L = [f"# Metrics report", "",
         f"Input `{meta['input']}`, run {meta['started']} → {meta['finished']}, "
         f"version `{meta['version']}`, confidence threshold {meta['threshold']}.", "",
         "## 1. Volume and reconciliation", "",
         f"- Tickets in: {m['tickets_in']}; results out: {m['results_out']}; decision-log rows: {m['log_rows']} "
         f"→ **{'reconciled' if m['reconciled'] else 'MISMATCH'}**",
         f"- Tickets that raised an error (escalated, still logged): {m['errors']}", ""]
    L += _results_table(m)
    L += ["## 2. Business outcomes", "",
         "Targets and baselines from the Evaluation Framework, tier one.", "",
         f"- First contact resolution (closed with no human; here: answered automatically): "
         f"**{_pct(m['auto'], m['results_out'])}** ({m['auto']} tickets; target ≥ 60%, baseline 42%; "
         f"Brief section 1 says 65%). An upper bound: it assumes every automatic reply solved the issue",
         f"- Escalation rate (passed to a person): **{m['escalation_rate']:.1%}** ({m['escalated']} tickets; "
         f"target ≤ 30%, baseline 58%)",
         "- Time to first reply, automatic answers: " +
         (f"mean {m['reply_mean_s']:.1f} s, median {m['reply_median_s']:.1f} s, p95 {m['reply_p95_s']:.1f} s"
          if m["reply_mean_s"] is not None else "none sent") +
         " (target under 5 minutes, baseline 8 to 12 hours). Escalated tickets wait for a person; "
         "that time is outside this run",
         "- Customer satisfaction (target ≥ 4.0, baseline 3.2): not computed by the harness; measured by "
         "human review of a sample of sent replies against a rubric (see the report for sample, rubric "
         "and scorer)",
         "- Repeat contacts (target: halved): not measurable in an offline run, which sees each ticket once"]
    if m["labelled"]:
        k = m["auto_labelled"]
        L += [f"- **Wrong automatic answers (as far as the labels can tell): {len(m['wrong_any'])} of {k}** "
              f"({_pct(len(m['wrong_any']), k)})" + (f": {', '.join(m['wrong_any'])}" if m["wrong_any"] else ""),
              f"    - answered although the labels send it to a person: {len(m['wrong_should_escalate'])}"
              + (f" ({', '.join(m['wrong_should_escalate'])})" if m["wrong_should_escalate"] else ""),
              f"    - answered from an article the labels do not expect: {len(m['wrong_article'])}"
              + (f" ({', '.join(m['wrong_article'])})" if m["wrong_article"] else ""),
              f"    - answered under the wrong intent: {len(m['wrong_intent'])}"
              + (f" ({', '.join(m['wrong_intent'])})" if m["wrong_intent"] else ""),
              "    - whether each reply's content is correct is measured by the human review "
              "(hallucination rate, citation accuracy)",
              f"- Labels escalate {m['label_escalation_rate']:.1%} of these tickets",
              f"- Avoidable escalations (labels say auto, system escalated): {m['avoidable_escalations']}"]
    L += ["- Drafting outcomes for tickets routing allowed: " +
          (", ".join(f"{k} {v}" for k, v in sorted(m["reply_outcomes"].items())) or "none"),
          f"- Replies blocked by a guardrail: {m['blocked']} "
          f"({', '.join(f'{k} {v}' for k, v in m['guardrail_failures'].items()) or 'none'})",
          f"- Model calls: {m['llm_calls']} ({m['cached_calls']} answered from cache)", "",
          "Escalation reasons:", ""] + [f"- {k}: {v}" for k, v in m["escalation_reasons"]] + [
          "", "Escalation priority: " + ", ".join(f"{k} {v}" for k, v in sorted(m["priority"].items())), "",
          "## 3. Technical performance", "",
          f"- Latency per ticket: p50 {m['latency_p50_ms']:.0f} ms, p95 {m['latency_p95_ms']:.0f} ms (target p95 < 3 s)",
          f"- Availability (handled end to end, no error, no provider failure): {m['availability']:.1%} "
          f"(target ≥ 99.5%); provider failures {m['provider_failures']}, each handed to a person"]
    if m["labelled"]:
        hit = m["retrieval_hit_rate"]
        L += [f"- Intent accuracy {m['intent_accuracy']:.1%}; urgency accuracy {m['urgency_accuracy']:.1%}",
              f"- Retrieval hit rate (expected article among returned passages): "
              f"{'—' if hit is None else f'{hit:.1%}'}",
              f"- Routing agrees with labels: {m['routing_accuracy']:.1%}; of auto-routed tickets, labels agree "
              f"on {'—' if m['auto_label_agrees'] is None else format(m['auto_label_agrees'], '.1%')}", "",
              "Per-intent precision and recall:", "", "```", m["intent_report"], "```"]
    else:
        L += ["- No labels in this file: accuracy, hit rate and calibration not computed."]
    L += ["", "## 4. Governance", "",
          f"- Protected-rule escalations: {m['protected']}",
          f"- Private data in sent replies (independent scan of every sent reply, target 0): "
          f"**{len(m['private_data_sent'])}**" + (f" ({', '.join(m['private_data_sent'])})" if m["private_data_sent"] else ""),
          f"- Decision log complete: {'yes' if m['reconciled'] else 'NO'}"]
    if m["labelled"]:
        b = m["must_not_breaches"]
        L += [f"- must_not_auto_respond tickets auto-routed: **{len(b)}**" + (f" ({', '.join(b)})" if b else ""),
              "", "Calibration (stated confidence vs observed intent accuracy):", "",
              "| band | tickets | stated | observed | gap |", "|---|---|---|---|---|"]
        L += [f"| {lo:.1f}–{min(hi, 1):.1f} | {k} | {s:.1%} | {o:.1%} | {(o - s) * 100:+.1f} pts |"
              for lo, hi, k, s, o in m["calibration"]]
        L += ["", "Segments (fairness, NFR-06 tolerance 5 points):", ""]
        for seg, groups in m["segments"].items():
            L += [f"**{seg}**", "", "| group | tickets | intent acc. | routing acc. | escalation |",
                  "|---|---|---|---|---|"]
            L += [f"| {g} | {v['tickets']} | {v['intent_accuracy']:.1%} | {v['routing_accuracy']:.1%} | "
                  f"{v['escalation_rate']:.1%} |" for g, v in groups.items()]
            L.append("")
        classes, cm = m["confusion"]
        L += ["## Appendix: intent confusion matrix", "", "Rows: labelled intent; columns: predicted intent "
              "(numbered as the rows).", "",
              "| labelled \\ predicted | " + " | ".join(str(i + 1) for i in range(len(classes))) + " |",
              "|---|" + "---|" * len(classes)]
        L += [f"| {i + 1}. {c} | " + " | ".join(str(v) if v else "·" for v in row) + " |"
              for i, (c, row) in enumerate(zip(classes, cm))]
    return "\n".join(L) + "\n"


def _results_table(m):
    """The Evaluation Framework's results table (section 4), as far as code can fill it."""
    n, review = m["results_out"], "human review (pending)"
    rows = [
        ("First contact resolution", "42%", "60%", _pct(m["auto"], n), f"{n} tickets, one run",
         "Upper bound: assumes every automatic reply solved the issue"),
        ("Mean time to first reply", "8 to 12 hrs", "< 5 min",
         "—" if m["reply_mean_s"] is None else f"{m['reply_mean_s']:.1f} s (median {m['reply_median_s']:.1f} s)",
         f"{m['auto']} automatic replies", "Processing time; escalated tickets wait for a person"),
        ("Satisfaction proxy", "3.2 / 5", "4.0", review, "", "Two assessors, rubric"),
        ("Escalation rate", "58%", "≤ 30%", f"{m['escalation_rate']:.1%}", f"{n} tickets, one run",
         f"Labels escalate {m['label_escalation_rate']:.1%}" if m["labelled"] else ""),
        ("Wrong automatic answers (labels)", "—", "—",
         f"{len(m['wrong_any'])} of {m['auto_labelled']}" if m["labelled"] else "—", "Labels only",
         "Routing, article or intent wrong; content checked by human review"),
        ("Classification precision", "—", "85%",
         f"{m['intent_accuracy']:.1%} accuracy" if m["labelled"] else "—", "Per class in section 3", ""),
        ("Hallucination rate", "—", "≤ 5%", review, "", "Two assessors"),
        ("Citation accuracy", "—", "95%", review, "", "Two assessors"),
        ("Latency p95", "—", "< 3 s", f"{m['latency_p95_ms'] / 1000:.1f} s", f"{n} tickets",
         "Free-tier rate-limit waits"),
        ("Availability", "—", "99.5%", f"{m['availability']:.1%}", f"{n} tickets",
         f"{m['provider_failures']} provider failures"),
        ("Private data occurrences", "—", "0", str(len(m["private_data_sent"])), f"{m['sent']} sent replies scanned", ""),
        ("Cross-group variation", "—", "< 5 pts", "see `evaluation/fairness.py`", "", ""),
    ]
    out = ["## Results table (Evaluation Framework)", "",
           "| Measure | Baseline | Target | Achieved | Basis | Notes |", "|---|---|---|---|---|---|"]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return out + [""]


def main(argv=None):
    """Re-render a run's report from its saved results and decision log, without re-running it."""
    ap = argparse.ArgumentParser(prog="python -m evaluation.metrics")
    ap.add_argument("--run", required=True, help="a harness output folder (results.jsonl, decisions.db, metrics.json)")
    ap.add_argument("--output", help="report file (default: <run>/metrics_report.md)")
    args = ap.parse_args(argv)
    run = Path(args.run)
    results = [json.loads(line) for line in open(run / "results.jsonl", encoding="utf-8")]
    old = json.loads((run / "metrics.json").read_text(encoding="utf-8"))
    log_rows = old["log_rows"]  # if the log was not kept with the results, use the count the run recorded
    if (run / "decisions.db").exists():
        with sqlite3.connect(run / "decisions.db") as db:
            log_rows = db.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
    meta = {k: old[k] for k in ("input", "started", "finished", "version", "threshold")}
    m = compute(results, log_rows, old["tickets_in"])
    Path(args.output or run / "metrics_report.md").write_text(render(m, meta), encoding="utf-8")
    (run / "metrics.json").write_text(json.dumps({**meta, **m}, indent=2, default=str), encoding="utf-8")
    print(f"Report: {args.output or run / 'metrics_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
