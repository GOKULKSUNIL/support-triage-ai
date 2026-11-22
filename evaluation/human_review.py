"""Human review of sent replies (Evaluation Framework: hallucination rate,
citation accuracy, satisfaction proxy; two assessors, agreement reported).

    python -m evaluation.human_review sample --output evaluation/results/<dir> \
        --results <run>/results.jsonl [<older run>/results.jsonl ...] --tickets data/validation_tickets.json \
        [--size 15] [--seed 0]
    python -m evaluation.human_review score --output evaluation/results/<dir>

`sample` collects the sent replies (first results file first, then different
tickets from the next files) and, when there are more than --size (default
50), draws --size of them at random with a fixed seed, so the sample is
repeatable and not chosen by hand. It writes for each assessor
(A and B, filled in independently):
  sentences_<X>.csv  one row per reply sentence with the passage it cites:
                     cited_supports (Y/N) and, only when that is N,
                     any_passage_supports (Y/N)
  replies_<X>.csv    one row per reply: satisfaction 1-5
plus key.csv (which run each reply came from; not shown to assessors) and
RUBRIC.md. `score` reads the filled sheets and writes human_review_report.md.
"""
import argparse
import csv
import json
import random
from pathlib import Path

from src.chunking import build_passages, load_docs
from src.ingest import load_tickets
from src.retrieve import DOCS_PATH

ASSESSORS = ("A", "B")
RUBRIC = """# Human review rubric

Score every reply on your own; do not compare answers with the other assessor
until both sheets are finished. Read the ticket first, then the reply. Ignore
the standard first line ("This reply was drafted automatically ...").

## sentences_<you>.csv: one row per sentence

- **cited_supports**: does the passage in `cited_passage_text` say what the
  sentence says? `Y` if it does (wording may differ), `N` if the sentence adds
  anything the passage does not say: a fact, a number, a condition, advice.
- **any_passage_supports**: only when cited_supports is `N`. Look at the other
  passages listed for the same sentence (`other_passages`). `Y` if one of them
  says it, `N` if none does. Leave blank when cited_supports is `Y`.

## replies_<you>.csv: one row per reply

- **satisfaction** (1-5): as the customer who wrote this ticket, how satisfied
  would you be with this reply?
  - 5: answers the question correctly and clearly; I could act on it without writing back
  - 4: answers the question; a small gap or awkward wording, but I probably would not write back
  - 3: partly answers; useful, but a step is missing or it is generic; I might write back
  - 2: mostly misses my question or is confusing; I would write back
  - 1: wrong, irrelevant or misleading
- **comment** (optional): one line on why, especially for 1-3.

Save the files as CSV with the same names when you finish.
"""


def _sent(path):
    rows = [json.loads(line) for line in open(path, encoding="utf-8")]
    return [r for r in rows if (r.get("reply") or {}).get("status") == "sent"]


def sample(args):
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    tickets = {t.ticket_id: t for t in load_tickets(args.tickets)}
    passages = {p.passage_id: p.text for p in build_passages(load_docs(DOCS_PATH), "section")}
    chosen = []
    for path in args.results:
        for r in _sent(path):
            if r["ticket_id"] not in {c["ticket_id"] for c, _ in chosen}:
                chosen.append((r, path))
    if len(chosen) > args.size:
        keep = set(random.Random(args.seed).sample(range(len(chosen)), args.size))
        chosen = [c for i, c in enumerate(chosen) if i in keep]

    sentence_rows, reply_rows, key_rows = [], [], []
    for n, (r, path) in enumerate(chosen, 1):
        rid = f"R{n:02d}"
        t = tickets[r["ticket_id"]]
        cited = [pid for s in r["reply"]["sentences"] for pid in s["sources"]]
        shown = list(dict.fromkeys(cited + r["sources"]))
        for i, s in enumerate(r["reply"]["sentences"], 1):
            others = "\n\n".join(f"[{p}] {passages.get(p, '')}" for p in shown if p not in s["sources"])
            sentence_rows.append({
                "review_id": rid, "sentence_no": i, "ticket": f"{t.subject}\n{t.body}" if i == 1 else "",
                "sentence": s["text"], "cited_passage": ", ".join(s["sources"]),
                "cited_passage_text": "\n\n".join(passages.get(p, "") for p in s["sources"]),
                "other_passages": others, "cited_supports": "", "any_passage_supports": ""})
        reply_rows.append({"review_id": rid, "ticket": f"{t.subject}\n{t.body}",
                           "reply": r["reply"]["text"], "satisfaction": "", "comment": ""})
        key_rows.append({"review_id": rid, "ticket_id": r["ticket_id"], "results_file": path})

    for who in ASSESSORS:
        _write(out / f"sentences_{who}.csv", sentence_rows)
        _write(out / f"replies_{who}.csv", reply_rows)
    _write(out / "key.csv", key_rows)
    (out / "RUBRIC.md").write_text(RUBRIC, encoding="utf-8")
    print(f"{len(chosen)} replies, {len(sentence_rows)} sentences -> {out}")


def _write(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def _read(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _yn(value):
    return value.strip().upper()[:1] == "Y"


def _kappa(a, b):
    """Cohen's kappa for two equal-length lists of labels."""
    n = len(a)
    if not n:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    labels = set(a) | set(b)
    pe = sum((a.count(k) / n) * (b.count(k) / n) for k in labels)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def _assessor(out, who):
    sentences = _read(out / f"sentences_{who}.csv")
    replies = _read(out / f"replies_{who}.csv")
    supported = {}  # (review_id, sentence_no) -> (cited passage supports, any passage supports)
    for s in sentences:
        cited = _yn(s["cited_supports"])
        supported[(s["review_id"], int(s["sentence_no"]))] = (cited, cited or _yn(s["any_passage_supports"]))
    hallucinated = {}
    for (rid, _), (_, any_ok) in supported.items():
        hallucinated[rid] = hallucinated.get(rid, False) or not any_ok
    satisfaction = {r["review_id"]: int(r["satisfaction"]) for r in replies if r["satisfaction"].strip()}
    return supported, hallucinated, satisfaction


def score(args):
    out = Path(args.output)
    (sa, ha, ca), (sb, hb, cb) = (_assessor(out, who) for who in ASSESSORS)
    keys, rids = sorted(sa), sorted(ha)
    both = sorted(set(ca) & set(cb))
    lines = ["# Human review report", "",
             f"{len(rids)} replies, {len(keys)} sentences, two assessors (A, B) scoring independently "
             f"against `RUBRIC.md`.", "",
             "| Measure | Assessor A | Assessor B | Target | Agreement | Cohen's kappa |", "|---|---|---|---|---|---|"]
    cite_a, cite_b = [sa[k][0] for k in keys], [sb[k][0] for k in keys]
    lines.append(f"| Citation accuracy (cited passage supports the sentence) | {sum(cite_a) / len(keys):.1%} | "
                 f"{sum(cite_b) / len(keys):.1%} | ≥ 95% | "
                 f"{sum(x == y for x, y in zip(cite_a, cite_b)) / len(keys):.1%} | {_kappa(cite_a, cite_b):.2f} |")
    hal_a, hal_b = [ha[r] for r in rids], [hb[r] for r in rids]
    lines.append(f"| Hallucination rate (replies with an unsupported sentence) | {sum(hal_a) / len(rids):.1%} | "
                 f"{sum(hal_b) / len(rids):.1%} | ≤ 5% | "
                 f"{sum(x == y for x, y in zip(hal_a, hal_b)) / len(rids):.1%} | {_kappa(hal_a, hal_b):.2f} |")
    if both:
        sat_a, sat_b = [ca[r] for r in both], [cb[r] for r in both]
        lines.append(f"| Satisfaction (mean 1-5) | {sum(sat_a) / len(both):.2f} | {sum(sat_b) / len(both):.2f} | "
                     f"≥ 4.0 | {sum(abs(x - y) <= 1 for x, y in zip(sat_a, sat_b)) / len(both):.1%} within 1 point | "
                     f"{_kappa(sat_a, sat_b):.2f} (exact score) |")
        lines += ["", f"Satisfaction, both assessors averaged: {(sum(sat_a) + sum(sat_b)) / (2 * len(both)):.2f}"]
    disagree = [r for r in rids if ha[r] != hb[r]]
    lines += ["", f"Replies where the assessors disagree on hallucination: {', '.join(disagree) or 'none'}"]
    (out / "human_review_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m evaluation.human_review")
    sub = parser.add_subparsers(dest="command", required=True)
    s = sub.add_parser("sample")
    s.add_argument("--output", required=True)
    s.add_argument("--results", required=True, nargs="+")
    s.add_argument("--tickets", required=True)
    s.add_argument("--size", type=int, default=50, help="replies to review")
    s.add_argument("--seed", type=int, default=0, help="random seed for the draw")
    sub.add_parser("score").add_argument("--output", required=True)
    args = parser.parse_args(argv)
    (sample if args.command == "sample" else score)(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
