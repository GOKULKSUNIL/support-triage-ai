# Architecture

CloudServe support triage: every incoming ticket is classified, matched to
the knowledge base, and either answered automatically with cited articles or
handed to a person with a context packet. Every decision is logged.

**Design rule: the model never decides.** Classification, routing and the
protected-category rule are deterministic code. The language model only
drafts replies (PR-01) and checks them (PR-02); code decides whether a reply
may be sent.

## 1. System overview

```
                         ┌────────────────────────────────────────────────────────────┐
  ticket file ──────────▶│ evaluation/harness.py   (batch: gate run, evaluation)      │
  (any path)             └──────────────┬─────────────────────────────────────────────┘
                                        │ one ticket at a time
  one ticket (HTTP) ────▶ src/api.py ───┤ (B-20, planned)
                                        ▼
                         ┌────────────────────────────────────────────────────────────┐
                         │ src/pipeline.py   LangGraph graph (section 2)              │
                         └──┬──────────┬──────────┬──────────┬──────────┬─────────────┘
                            │          │          │          │          │
                            ▼          ▼          ▼          ▼          ▼
                       classify    retrieve     route     generate   guardrails
                            │          │                     │          │
                  ┌─────────┘          │                     └────┬─────┘
                  ▼                    ▼                          ▼
          storage/classifier     storage/chroma              src/llm.py ──▶ Groq (primary)
          .joblib                (116 passages)              (cache, retry,  └▶ gpt-oss-120b (fallback)
          (trained from          (built from                  fallback)
          data/development_       data/documentation.json)       │
          tickets.json)                                          ▼
                                                            cache/llm/*.json
                         │
                         ▼  every ticket, in a finally block
                  src/logging_store.py ──▶ decisions.db (SQLite)

  Harness outputs per run: results.jsonl · decisions.db · metrics_report.md · metrics.json
```

## 2. Flow of one ticket

```
 raw record
     │
     ▼
 ┌────────┐  normalise channel, clean text, defaults, flags
 │ ingest │  (malformed / empty / unknown channel never crash; they are flagged)
 └───┬────┘
     ▼
 ┌──────────┐  embeddings + logistic regression, isotonic calibration
 │ classify │  → intent (22), urgency, confidence 0–1, top-3 alternatives
 └───┬──────┘
     ▼
 ┌──────────┐  Chroma cosine search over article sections, top 5,
 │ retrieve │  drop passages scoring < 0.40 (may return nothing)
 └───┬──────┘
     ▼
 ┌──────────┐  checks in this order; first hit escalates
 │  route   │  1 unreadable ticket          4 confidence < 0.80
 └───┬──────┘  2 protected category (FR-05) 5 no passage above 0.40
     │         3 feature / unclear request  else → auto_respond
     │
     ├── escalate ──────────────────────────────────────────────┐
     │                                                          │
     ▼ auto_respond                                             │
 ┌──────────┐  PR-01 writes JSON sentences with passage ids.    │
 │  draft   │  Code rejects: bad JSON or shape, "insufficient",  │
 └───┬──────┘  any cited id not retrieved, no citation at all.   │
     │ ok                                     unusable ─────────┤
     ▼                                                          │
 ┌──────────┐  1 private data (regex): email, phone, card,      │
 │ validate │    API key, another customer's ID                  │
 └───┬──────┘  2 grounding (PR-02): every sentence supported?    │
     │           check can't run → blocked (fail closed)         │
     │ pass                                   blocked ──────────┤
     ▼                                                          ▼
  SENT: label + reply + [DOC-ID] citations          ┌──────────────────┐
                                                    │ escalate         │ packet: PR-03 summary,
                                                    │ priority P1–P3   │ customer ask, intent,
                                                    └──────────────────┘ articles, uncertainty
                                                     (template packet if the model is down)
     │                                                          │
     └──────────────────────────┬───────────────────────────────┘
                                ▼
                     decision-log row (always)
```

## 3. What decides each branch

| Step | Decides | Rule | Requirement |
|---|---|---|---|
| ingest | Ticket can be processed | Flags `malformed`, `empty_text`, `empty_body` escalate at routing | FR-01 |
| route | Protected topic | Intent or any top-3 alternative is security_incident, compliance_request or data_residency; or text mentions compromise or a billing dispute. Fixed in code, no switch | FR-05 |
| route | No documentation exists | feature_request, unclear_request always escalate | FR-04 (Stage 5 addition) |
| route | Classifier sure enough | Calibrated confidence ≥ 0.80 (`CONFIDENCE_THRESHOLD`) | FR-04 |
| route | An article matches | At least one passage ≥ 0.40 (`RELEVANCE_THRESHOLD`) | FR-03 |
| draft | Reply is usable | Valid JSON, status answered, every citation retrieved, ≥ 1 citation | FR-06 |
| validate | Reply is safe | No private data; every sentence supported; fail closed | FR-07 |
| escalate | Queue order | P1 security or compromise; P2 outage topic or predicted high urgency; P3 other | FR-09 (Stage 5 addition) |
| sent reply | Customer knows it is automated | Fixed label added by code | FR-13 |

## 4. Modules

| File | Responsibility |
|---|---|
| `src/ingest.py` | Load any ticket file; one normalised `Ticket` per record |
| `src/chunking.py` | Split the 29 articles into passages by section (`DOC-ID#section`) |
| `src/retrieve.py` | Embed passages into Chroma; search with the relevance threshold |
| `src/classify.py` | Train/load the intent and urgency classifier; calibrated confidence |
| `src/route.py` | Protected rule, routing decision, escalation priority |
| `src/llm.py` | Prompt loading, response cache, timeout, rate-limit wait, fallback provider |
| `src/generate.py` | PR-01 drafting, citation checks, rendering, automated-reply label |
| `src/guardrails.py` | Private-data check and PR-02 grounding check |
| `src/pipeline.py` | The LangGraph graph tying the steps together; never raises |
| `src/logging_store.py` | SQLite decision log, customer name and ID masked |
| `evaluation/harness.py` | One command over any ticket file; writes results and report |
| `evaluation/metrics.py` | Volume, business, technical and governance figures |
| `prompts/` | Prompt texts with versions and the register |

## 5. Data and storage

| Store | Contents | Created by | In git |
|---|---|---|---|
| `data/` | Development, validation tickets; 29 articles; reference replies | Course pack | Yes |
| `storage/chroma/` | Embedded passages | First search (rebuilt if articles change) | No |
| `storage/classifier.joblib` | Trained classifier | First classification | No |
| `cache/llm/` | Model responses, keyed by prompt id + version + inputs | Each new model call | No |
| `<run>/decisions.db` | One row per ticket | Harness run | No |
| `<run>/results.jsonl`, `metrics_report.md` | Per-ticket results, run report | Harness run | — |

## 6. External services

| Service | Used for | Without it |
|---|---|---|
| Groq, `openai/gpt-oss-20b` | PR-01 drafting, PR-02 grounding, PR-03 escalation summary | Fallback provider; if none answers, the ticket escalates with "provider unavailable" and a template packet |
| Groq, `openai/gpt-oss-120b` (fallback) | Same prompts when the main model fails or its daily allowance is used up (Groq counts limits per model) | Ticket escalates |
| Hugging Face | One-time download of `all-MiniLM-L6-v2` | Needed once per machine; then offline |

Classification, retrieval, routing and logging run locally and never need
the network.

## 7. Failure handling

| Failure | Behaviour |
|---|---|
| Malformed or empty ticket | Flagged at ingest, escalated, logged |
| No passage above threshold | Escalated: no matching article |
| Rate limit (429) | Wait as long as the provider asks (up to 65 s), retry up to 6 times, then fallback; if it asks for more than 65 s (daily allowance used up), go to the fallback at once |
| Timeout / connection error | Retry with backoff (3 times), then fallback |
| Model returns bad JSON | Draft rejected → escalated (never cached) |
| Grounding check cannot run | Reply blocked (fail closed) → escalated |
| Any unexpected exception | Caught in `Pipeline.process`; ticket escalated with the error; log row still written |

## 8. Configuration (`.env`)

| Variable | Default | Meaning |
|---|---|---|
| `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` | Groq, `openai/gpt-oss-20b` | Primary provider |
| `FALLBACK_API_KEY`, `FALLBACK_BASE_URL`, `FALLBACK_MODEL` | blank, blank, `openai/gpt-oss-120b` | Fallback model; with key and URL blank it runs on the main provider; blank model disables it |
| `CONFIDENCE_THRESHOLD` | 0.80 | Minimum calibrated confidence to auto-respond |
| `RELEVANCE_THRESHOLD` | 0.40 | Minimum passage similarity |
| `RETRIEVAL_TOP_K` | 5 | Passages retrieved per ticket |
| `EMBEDDING_MODEL` | all-MiniLM-L6-v2 | Local embedding model |
| `CHROMA_PATH`, `DATABASE_URL` | `./storage/...` | Local stores |

The protected-category rule and the guardrails have no configuration on
purpose: they cannot be switched off.
