"""Fairness audit (NFR-06, Governance Framework section 3): outcomes by customer group.

    python -m evaluation.fairness --results <run>/results.jsonl --tickets data/validation_tickets.json \
        --output evaluation/results/<dir> [--retrieval data/development_tickets.json] [--review <dir>]

Segments: tier, language fluency, ticket length (short = up to the median word
count, long = above it), region and channel. For each group:
  resolution     answered automatically
  labels allow   share the labels say could be answered automatically (the ceiling)
  missed         of the tickets the labels say could be answered, share handed over
  routing        system and labels agree on answer vs hand over
  retrieval      expected article among the passages found
  blocked        drafts blocked by a guardrail
  satisfaction   mean human-review score (only with --review, once it is scored)
Gaps are measured from the best group, in points, against the 5-point tolerance;
each rate has a 95% Wilson interval, because most groups are small.

--retrieval runs the search step alone (no model calls) on another labelled file,
e.g. the 500 development tickets, so the fluency gap in retrieval can be checked
on a larger sample.
"""
import argparse
import csv
import json
import math
from pathlib import Path

from src.ingest import load_tickets

TOLERANCE = 5.0  # points (NFR-06)
SEGMENTS = ("customer_tier", "language_fluency", "length", "customer_region", "channel")
# measure -> True if higher is better, False if lower is better, None if not a quality measure
MEASURES = {"resolution": True, "labels_allow": None, "missed": False, "routing": True,
            "retrieval": True, "blocked": False, "satisfaction": True}


def wilson(k, n, z=1.96):
    if not n:
        return (float("nan"), float("nan"))
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (centre - half, centre + half)


def _rate(flags):
    flags = list(flags)
    k, n = sum(flags), len(flags)
    return {"k": k, "n": n, "rate": k / n if n else None, "ci": wilson(k, n)}


def _words(ticket):
    return len(f"{ticket.subject} {ticket.body}".split())


def _group(rows, satisfaction):
    label_auto = [r["labels"]["expected_route"] == "auto_respond" for r in rows]
    sys_auto = [r["action"] == "auto_respond" for r in rows]
    need = [r for r in rows if r["labels"].get("expected_doc_ids")]
    drafted = [r for r in rows if r.get("reply")]
    m = {
        "tickets": len(rows),
        "resolution": _rate(sys_auto),
        "labels_allow": _rate(label_auto),
        "missed": _rate([not s for s, la in zip(sys_auto, label_auto) if la]),
        "routing": _rate([s == la for s, la in zip(sys_auto, label_auto)]),
        "retrieval": _rate([bool(set(r["labels"]["expected_doc_ids"]) & {s.split("#")[0] for s in r["sources"]})
                            for r in need]),
        "blocked": _rate([bool(r.get("blocked")) for r in drafted]),
    }
    scores = [satisfaction[r["ticket_id"]] for r in rows if r["ticket_id"] in satisfaction]
    m["satisfaction"] = {"k": None, "n": len(scores), "ci": None,
                         "rate": sum(scores) / len(scores) if scores else None}
    return m


def _satisfaction(review_dir):
    """Mean of both assessors' 1-5 scores per ticket, from a scored human-review folder."""
    if not review_dir:
        return {}
    out = Path(review_dir)
    key = {row["review_id"]: row["ticket_id"] for row in csv.DictReader(open(out / "key.csv", encoding="utf-8"))}
    scores = {}
    for who in ("A", "B"):
        for row in csv.DictReader(open(out / f"replies_{who}.csv", encoding="utf-8-sig")):
            if row["satisfaction"].strip():
                scores.setdefault(key[row["review_id"]], []).append(int(row["satisfaction"]))
    return {tid: sum(v) / len(v) for tid, v in scores.items()}


def audit(results, tickets, satisfaction=None):
    """Per segment, per group: every measure, plus its gap to the best group."""
    words = {t.ticket_id: _words(t) for t in tickets}
    median = sorted(words[r["ticket_id"]] for r in results)[len(results) // 2]
    rows = [{**r, "length": "short" if words[r["ticket_id"]] <= median else "long"} for r in results]
    report = {}
    for seg in SEGMENTS:
        groups = {g: _group([r for r in rows if r[seg] == g], satisfaction or {})
                  for g in sorted({r[seg] for r in rows})}
        for name, higher_better in MEASURES.items():
            vals = {g: m[name]["rate"] for g, m in groups.items() if m[name]["rate"] is not None}
            if higher_better is None or not vals:
                continue
            best = max(vals.values()) if higher_better else min(vals.values())
            scale = 1 if name == "satisfaction" else 100
            for g, v in vals.items():
                groups[g][name]["gap"] = abs(best - v) * scale
        report[seg] = groups
    return report, median


def retrieval_check(path):
    """Search step only (no model calls): expected article among the passages, by segment."""
    from src.retrieve import Index
    index = Index("section")
    rows = []
    for t in load_tickets(path):
        if t.labels and t.labels.get("expected_doc_ids"):
            hits = {h.doc_id for h in index.search(t.text)}
            rows.append({"customer_tier": t.customer_tier, "language_fluency": t.language_fluency,
                         "customer_region": t.customer_region, "channel": t.channel,
                         "hit": bool(set(t.labels["expected_doc_ids"]) & hits)})
    out = {}
    for seg in ("language_fluency", "customer_tier", "customer_region", "channel"):
        groups = {g: _rate([r["hit"] for r in rows if r[seg] == g]) for g in sorted({r[seg] for r in rows})}
        best = max(v["rate"] for v in groups.values())
        for v in groups.values():
            v["gap"] = (best - v["rate"]) * 100
        out[seg] = groups
    return {"file": path, "tickets": len(rows), "segments": out}


def _cell(v, satisfaction=False):
    if v["rate"] is None:
        return "—"
    if satisfaction:
        return f"{v['rate']:.2f} (n={v['n']})"
    lo, hi = v["ci"]
    return f"{v['rate']:.0%} ({v['k']}/{v['n']}; {lo:.0%}–{hi:.0%})"


def _gap(v, satisfaction=False):
    g = v.get("gap")
    if g is None:
        return ""
    if satisfaction:
        return f"{g:.2f}"
    return f"**{g:.0f}**" if g > TOLERANCE else f"{g:.0f}"


def render(report, meta, retrieval=None):
    L = ["# Fairness audit", "",
         f"Results `{meta['results']}` ({meta['tickets']} tickets). Short tickets: up to {meta['median_words']} "
         f"words (the median). Each rate: share (count; 95% range). Gap: points behind the best group on "
         f"that measure; **bold** = beyond the {TOLERANCE:.0f}-point tolerance (NFR-06). When a group's 95% "
         f"range overlaps the best group's, the gap may be chance at this sample size.", "",
         "Resolution = answered automatically. Labels allow = the share the labels say could be answered "
         "automatically, so a group with a lower ceiling is expected to have lower resolution. Missed answers "
         "= tickets the labels say could be answered but were handed over.", ""]
    head = ("| Group | Tickets | Resolution | Gap | Labels allow | Missed answers | Gap | Routing agrees | Gap | "
            "Right article | Gap | Drafts blocked | Gap | Satisfaction | Gap |")
    for seg, groups in report.items():
        L += [f"## {seg.replace('_', ' ').capitalize()}", "", head, "|" + "---|" * 15]
        for g, m in groups.items():
            cells = [g, str(m["tickets"]), _cell(m["resolution"]), _gap(m["resolution"]), _cell(m["labels_allow"])]
            for name in ("missed", "routing", "retrieval", "blocked"):
                cells += [_cell(m[name]), _gap(m[name])]
            cells += [_cell(m["satisfaction"], True), _gap(m["satisfaction"], True)]
            L.append("| " + " | ".join(cells) + " |")
        L.append("")
    if retrieval:
        L += [f"## Search step alone on `{retrieval['file']}` ({retrieval['tickets']} tickets that need an article)",
              "", "No model calls: the expected article among the passages found.", ""]
        for seg, groups in retrieval["segments"].items():
            L += [f"**{seg.replace('_', ' ')}**", "", "| Group | Right article | Gap |", "|---|---|---|"]
            L += [f"| {g} | {_cell(v)} | {_gap(v)} |" for g, v in groups.items()]
            L.append("")
    if not any(m["satisfaction"]["n"] for groups in report.values() for m in groups.values()):
        L.append("Satisfaction: not yet scored (human review pending); rerun with `--review` once it is.")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m evaluation.fairness")
    ap.add_argument("--results", required=True)
    ap.add_argument("--tickets", required=True, help="the ticket file the run processed")
    ap.add_argument("--output", required=True)
    ap.add_argument("--retrieval", help="labelled ticket file for the search-only check")
    ap.add_argument("--review", help="scored human-review folder, for satisfaction by group")
    args = ap.parse_args(argv)

    results = [json.loads(line) for line in open(args.results, encoding="utf-8")]
    results = [r for r in results if r.get("labels")]
    report, median = audit(results, load_tickets(args.tickets), _satisfaction(args.review))
    retrieval = retrieval_check(args.retrieval) if args.retrieval else None
    meta = {"results": args.results, "tickets": len(results), "median_words": median}
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    (out / "fairness_report.md").write_text(render(report, meta, retrieval), encoding="utf-8")
    (out / "fairness.json").write_text(json.dumps({**meta, "segments": report, "retrieval": retrieval},
                                                  indent=2, default=str), encoding="utf-8")
    print(f"Fairness report: {out / 'fairness_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
