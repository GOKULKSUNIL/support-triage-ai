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
python scripts/check_llm.py
```
