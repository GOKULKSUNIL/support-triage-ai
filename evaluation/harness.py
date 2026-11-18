"""Run the full pipeline over a ticket file, unattended (FR-10, FR-11).

    python -m evaluation.harness --input data/validation_tickets.json --output evaluation/results/<run>

Writes to the output directory:
  results.jsonl       one line per ticket, written as each ticket finishes
  decisions.db        the decision log for this run
  metrics_report.md   the report, computed from the two files above
  metrics.json        the same figures, machine-readable
Every ticket is processed even if others fail; the run ends with a
reconciliation of tickets in, results out and log rows.
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from evaluation.metrics import compute, render
from src.ingest import load_tickets
from src.logging_store import DecisionLog
from src.pipeline import Pipeline
from src.route import confidence_threshold


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _version():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                              text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", required=True, help="ticket JSON file (any file with the ticket schema)")
    ap.add_argument("--output", required=True, help="directory for this run's outputs")
    args = ap.parse_args(argv)

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    db = out / "decisions.db"
    db.unlink(missing_ok=True)  # one log per run, so it reconciles against this run only
    started = _now()

    tickets = load_tickets(args.input)
    pipeline = Pipeline(log=DecisionLog(str(db)))
    results = []
    with open(out / "results.jsonl", "w", encoding="utf-8") as f:
        for i, ticket in enumerate(tickets, 1):
            result = pipeline.process(ticket)
            results.append(result)
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
            f.flush()
            print(f"[{i}/{len(tickets)}] {ticket.ticket_id} {result['action']}", file=sys.stderr)

    meta = {"input": args.input, "started": started, "finished": _now(),
            "version": _version(), "threshold": confidence_threshold()}
    metrics = compute(results, pipeline.log.count(), len(tickets))
    (out / "metrics_report.md").write_text(render(metrics, meta), encoding="utf-8")
    (out / "metrics.json").write_text(json.dumps({**meta, **metrics}, indent=2, default=str),
                                      encoding="utf-8")
    print(f"Done: {len(results)} tickets, reconciled={metrics['reconciled']}. Report: "
          f"{out / 'metrics_report.md'}", file=sys.stderr)
    return 0 if metrics["reconciled"] else 1


if __name__ == "__main__":
    sys.exit(main())
