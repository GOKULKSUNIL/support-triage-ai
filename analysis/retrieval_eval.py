"""Compare chunking strategies and pick the relevance threshold (B-04, T-03c).

Run from cloudserve-support/:  .venv/bin/python -m analysis.retrieval_eval
Writes analysis/output/retrieval_report.md.

For each strategy, on the development tickets:
  hit@k     share of tickets with expected_doc_ids where at least one expected
            article is among the top-k results
  recall@k  share of all expected articles that were found
Then, for the threshold: the top score of tickets that need an article is
compared with the top score of tickets that need none (expected_doc_ids
empty). A good threshold keeps the first group and empties the second.
"""
from pathlib import Path

from src.ingest import load_tickets
from src.retrieval import Index

OUT = Path("analysis/output/retrieval_report.md")
KS = (1, 3, 5)
THRESHOLDS = [round(0.20 + 0.05 * i, 2) for i in range(11)]


def doc_ids(hits):
    seen = []
    for h in hits:
        if h.doc_id not in seen:
            seen.append(h.doc_id)
    return seen


def evaluate(strategy, tickets):
    index = Index(strategy)
    rows = []
    for t in tickets:
        hits = index.search(t.text, k=10, threshold=0.0)
        rows.append((t, hits))
    lines = [f"### {strategy} ({len(index.passages)} passages)", "",
             "| k | hit@k | recall@k |", "|---|---|---|"]
    need = [(t, h) for t, h in rows if t.labels["expected_doc_ids"]]
    for k in KS:
        hit = rec = total = 0
        for t, h in need:
            exp = set(t.labels["expected_doc_ids"])
            found = exp & set(doc_ids(h)[:k])
            hit += bool(found)
            rec += len(found)
            total += len(exp)
        lines.append(f"| {k} | {hit / len(need):.1%} | {rec / total:.1%} |")
    lines.append("")
    return rows, lines


def threshold_table(rows):
    need = [h for t, h in rows if t.labels["expected_doc_ids"]]
    none = [h for t, h in rows if not t.labels["expected_doc_ids"]]
    lines = ["| threshold | needs-article tickets keeping ≥1 passage | no-article tickets returning nothing |",
             "|---|---|---|"]
    for th in THRESHOLDS:
        keep = sum(bool(h) and h[0].score >= th for h in need) / len(need)
        empty = sum(not h or h[0].score < th for h in none) / len(none)
        lines.append(f"| {th:.2f} | {keep:.1%} | {empty:.1%} |")
    return lines


def main():
    tickets = load_tickets("data/development_tickets.json")
    n_need = sum(bool(t.labels["expected_doc_ids"]) for t in tickets)
    report = ["# Retrieval comparison (development tickets)", "",
              f"{len(tickets)} tickets; {n_need} need at least one article, "
              f"{len(tickets) - n_need} need none.", ""]
    for strategy in ("section", "fixed"):
        rows, lines = evaluate(strategy, tickets)
        report += lines + [f"Threshold sweep ({strategy}, top passage score):", ""]
        report += threshold_table(rows) + [""]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
