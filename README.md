# CloudServe Support System

AI-assisted ticket triage and answering for CloudServe Solutions (FDE capstone).

> Work in progress. Setup and run instructions are filled in as each component lands
> and are tested against a fresh clone.

## Requirements

- Python 3.11
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
