# Design decisions

One entry per decision: what was chosen, what else was considered, the
evidence, and what it costs. Figures come from the development tickets unless
stated; the scripts that produce them are named so every number can be
re-run. Validation tickets are not used for any decision here.

Used in: report §5 (architecture and alternatives), §6 (what was difficult),
§7 (limits), §9 (requirements revision); video minutes 2–5 and 18–20.

| ID | Area | Decision | Status |
|---|---|---|---|
| D-01 | Model provider | Groq `openai/gpt-oss-20b`, OpenRouter fallback | Decided |
| D-02 | Chunking | One passage per article section | Decided |
| D-03 | Embeddings | all-MiniLM-L6-v2, local | Decided |
| D-04 | Retrieval | Top 5, relevance threshold 0.40, no re-ranking | Decided |
| D-05 | Classifier | Embeddings + logistic regression, no LLM | Decided |
| D-06 | Calibration | Isotonic, C = 10 | Decided |
| D-07 | Evaluation splits | Grouped by ticket text | Decided |
| D-08 | Urgency | Predicted but not used for routing | Decided |
| D-09 | Protected rule | FR-05 in code, checks top-3 alternatives, includes data location | Decided |
| D-10 | No-documentation intents | feature_request and unclear_request always escalate | Decided |
| D-11 | Urgent database/performance tickets | No special auto-answer rule | Decided |
| D-12 | Confidence threshold | 0.80 | Decided |
| D-13 | Escalation priority | Topic rules plus predicted "high" urgency (P1–P3) | Decided |

---

## D-01 Model provider

- **Decision:** Groq, model `openai/gpt-oss-20b`, for drafting and checking. OpenRouter as the fallback provider. Judge (PR-04) on `openai/gpt-oss-120b`.
- **Alternatives:** the pack's Llama 3.1 8B; OpenRouter as primary; a local model.
- **Evidence:** the pack's model returns 404 on Groq (retired); Groq serves no Llama chat models and OpenRouter's Llama models are paid (checked 2026-11-08). Groq is fast enough for the p95 < 3 s target and its free daily limit covers a full run.
- **Cost:** depends on one free tier; the fallback model must also be free (still to choose).
- **Lesson:** client templates go stale; provider and model are set in `.env`, not in code.

## D-02 Chunking: by section

- **Decision:** split each article at its `## ` headings (Symptoms, Common causes, Resolution, Notes) and put the title in every passage. 116 passages, ids like `DOC-DEPLOY-003#resolution`.
- **Alternative tested:** fixed 120-word windows with 30-word overlap (59 passages).
- **Evidence** (`analysis/retrieval_eval.py`): right article in top 5: section 98.0%, fixed 98.9%; in top 1: section 90.5%, fixed 89.4%. A tie on accuracy.
- **Why section:** readable citation ids; resolution steps are never cut in half (the Dataset Guide warns about this); matches the Stage 3 spec.
- **Cost:** smaller passages, so recall of *all* needed articles at top 5 is lower (88.8% vs 92.6%).

## D-03 Embedding model

- **Decision:** `all-MiniLM-L6-v2` (22M parameters, 384 dimensions), run locally.
- **Alternatives:** `bge-small-en-v1.5`, `all-mpnet-base-v2`, an API embedding.
- **Why:** free (NFR-07), offline and private (NFR-04), no rate limits during the unattended run, fast on CPU; 98% top-5 hit rate is enough.
- **Limits:** English-centred (fluency gap to check in the fairness audit, B-14); scores bunch in 0.5–0.7, so on-topic and off-topic are hard to separate by score alone.

## D-04 Retrieval: top 5, threshold 0.40, no re-ranking

- **Decision:** cosine search, top 5 passages, drop any scoring below 0.40.
- **Evidence** (threshold sweep, `analysis/retrieval_eval.py`): at 0.40 every unclear ticket drops out (their highest score is 0.38) and 97.8% of tickets that need an article keep one.
- **Cost:** 2.2% of answerable tickets lose their passages and escalate (e.g. vague onboarding tickets scoring 0.30–0.39).
- **Does not catch:** feature requests (median score 0.67), because they talk about real features — see D-10.
- **No re-ranking:** the drafting step reads all 5 passages, so order matters little and top-5 is already 98%. First thing to try if the gate run shows retrieval misses.

## D-05 Classifier: logistic regression, not an LLM

- **Decision:** embeddings + logistic regression for intent (22 classes) and urgency.
- **Alternative:** ask the LLM to classify.
- **Why:** the model never decides. Same input always gives the same output (FR-04), probabilities can be calibrated, no cost, no outage risk, cannot be steered by text inside a ticket.
- **Evidence** (`analysis/classifier_eval.py`): intent precision 100% on 100 held-back tickets; 97.5% in cross-validation. Target 85%.

## D-06 Calibration: isotonic

- **Decision:** isotonic calibration, C = 10.
- **Alternatives tested:** raw probabilities and sigmoid calibration, C in {1, 10, 100}.
- **Evidence** (grouped CV on the training part only): calibration error with sigmoid 25.8 pts, raw 15.4 pts, isotonic 2.3 pts; held-back 1.0 pt. Target: within 5.
- **What went wrong first:** sigmoid was used first and stated ~74% confidence on predictions that were right 100% of the time. A threshold on that score would have been meaningless.

## D-07 Evaluation splits grouped by text

- **Decision:** every split keeps all copies of a ticket text on one side.
- **Evidence:** only 343 of the 500 development texts are distinct; 97 appear more than once.
- **What went wrong first:** the first random split put copies on both sides and inflated the held-back score.

## D-08 Urgency is predicted but not used for routing

- **Decision:** urgency is reported (log, escalation packet) but routing does not depend on it.
- **Evidence:** 67 of the 97 repeated texts carry different urgency labels on their copies, so the text does not determine urgency. Held-back urgency accuracy 52%.
- **Cost:** urgency shown to Tier 2 is a hint only; see D-11.

## D-09 Protected rule (FR-05)

- **Decision:** checked before anything else, fixed in code with no flag. Escalates if the intent or any top-3 alternative is security_incident, compliance_request or data_residency, or the text mentions account compromise or a billing dispute.
- **Why data location stays protected although labels mark some auto:** DOC-DATA-003 applies to Business/Enterprise only, cannot give written confirmation, and its notes say metadata is stored centrally regardless of region; an automatic "your data stays in the EU" could be wrong.
- **Evidence** (`analysis/routing_eval.py`): 101 of 500 tickets escalated by this rule.
- **Cost:** 21 data_residency tickets the labels mark auto go to a person.

## D-10 No-documentation intents always escalate

- **Decision:** feature_request and unclear_request always escalate (`NO_DOC_INTENTS` in `src/routing.py`; a new line in FR-04, not FR-05, which is about risk).
- **Evidence:** as built, 13 feature requests would be auto-answered at 0.91–1.00 confidence from the billing article. Stage 1, Ines: "Feature requests, obviously, since there is no answer to retrieve." Dataset Guide: these have no documentation.
- **Effect** (measured after the change, `analysis/routing_eval.py`): must-not breaches 13 → 0 at every threshold; auto rate 71.0% → 68.4%; auto precision 71.5% → 74.3%.
- **Chain:** recorded in the Stage 5 revision log as a PRD change from the build.

## D-11 Urgent database/performance tickets

- **Decision:** no special rule in the auto-answer decision. Urgency is used instead to prioritise tickets once they escalate (D-13).
- **Evidence:** labels escalate high-urgency database_issue and performance_degradation tickets (10 each). Catching them needs urgency (52%, D-08) or escalating every such ticket: auto precision 74% → 80% but auto rate 68% → 59% (46 tickets, 20 of them label-auto).
- **Cost:** about 29 tickets where our route differs from the label policy; explained in the report.

## D-12 Confidence threshold 0.80

- **Decision:** 0.80 (`CONFIDENCE_THRESHOLD` in `.env`).
- **Evidence:** on development tickets the threshold barely changes the result (intent is ~100% correct at every level); 0.50 → 0.80 costs 15 auto-answers (3%).
- **Why 0.80 anyway:** confidence is calibrated, so 0.80 means at least 80% likely right. A wrong auto-reply costs more than an escalation. The hidden set may be harder than the development set.
- **Limit:** the development data could not test the threshold; the validation run is the real check.

## D-13 Escalation priority

- **Decision (option C):** escalated tickets get a priority for the Tier 2 queue. P1: security incident or account-compromise wording. P2: outage-type topic (database, performance, deployment failure, rollback) or predicted urgency "high". P3: everything else. Each carries a written reason. Priority never changes whether a ticket is auto-answered.
- **Alternatives:** A, predicted urgency only (misses more than half of urgent tickets); B, topic rules only (ignores urgency in the text).
- **Evidence:** held-back urgency "high" predictions are right 77% of the time even though recall is low (D-08); in the labels security_incident is high 24/26, rollback_request 23/28. On the 158 dev escalations (`analysis/routing_eval.py`): P1 26 tickets, 24 labelled high; P2 7; P3 125, of which 15 labelled high.
- **Cost:** 15 urgent escalations sit in P3, mostly compliance and data-location tickets the urgency model did not flag. Some P2 "high" flags will be wrong (about 1 in 4).
- **Chain:** not in PRD v1; recorded in the Stage 5 revision log as an addition to FR-09 (escalation packet).
