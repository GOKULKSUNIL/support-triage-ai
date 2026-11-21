# support-triage-ai

AI support triage: classifies tickets, answers from documentation with citations, and escalates
with context. Built for CloudServe Solutions (FDE capstone, IIT Roorkee).

> Work in progress. Setup and run instructions are filled in as each component lands
> and are tested against a fresh clone.

## Requirements

- Python 3.11. If `python3.11 --version` fails, install it from https://www.python.org/downloads/
  or with uv: `curl -LsSf https://astral.sh/uv/install.sh | sh && uv python install 3.11`
  (then open a new terminal).
- A free Groq API key (https://console.groq.com)

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env   # then edit .env and add your key
```

Check the model provider is reachable (should print `reply: ready`):

```bash
python -m src.llm
```

## Run

Process any ticket file end to end, unattended:

```bash
python -m evaluation.harness --input data/validation_tickets.json --output evaluation/results/<run-name>
```

The output directory gets `results.jsonl` (one line per ticket), `decisions.db`
(the decision log for the run), `metrics_report.md` and `metrics.json`. The
command exits non-zero if tickets in, results out and log rows do not match.

The first run downloads the embedding model (about 90 MB) and trains the
classifier from `data/development_tickets.json` into `storage/`; later runs
reuse both. The full development data is kept in `data/` for that reason.

## Kill switch

Stop all automatic answers at once, without a deployment; every ticket then
goes to a person until it is resumed:

```bash
python -m src.control pause --by "Marcus Adeyemi" --reason "why"
python -m src.control status
python -m src.control resume --by "Marcus Adeyemi" --reason "why"
```

It takes effect on the next ticket, including tickets already being drafted.
The switch is kept in the configured store (`DATABASE_URL`); check `status`
before a full run.

## Tests

```bash
python -m pytest tests/ -q
```
