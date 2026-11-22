# Metrics report

Input `data/validation_tickets.json`, run 2026-11-21T20:14:00Z → 2026-11-21T20:34:55Z, version `e936ead`, confidence threshold 0.8.

## 1. Volume and reconciliation

- Tickets in: 80; results out: 80; decision-log rows: 80 → **reconciled**
- Tickets that raised an error (escalated, still logged): 0

## Results table (Evaluation Framework)

| Measure | Baseline | Target | Achieved | Basis | Notes |
|---|---|---|---|---|---|
| First contact resolution | 42% | 60% | 56.2% | 80 tickets, one run | Upper bound: assumes every automatic reply solved the issue |
| Mean time to first reply | 8 to 12 hrs | < 5 min | 14.9 s (median 16.8 s) | 45 automatic replies | Processing time; escalated tickets wait for a person |
| Satisfaction proxy | 3.2 / 5 | 4.0 | human review (pending) |  | Two assessors, rubric |
| Escalation rate | 58% | ≤ 30% | 43.8% | 80 tickets, one run | Labels escalate 40.0% |
| Wrong automatic answers (labels) | — | — | 14 of 45 | Labels only | Routing, article or intent wrong; content checked by human review |
| Classification precision | — | 85% | 100.0% accuracy | Per class in section 3 |  |
| Hallucination rate | — | ≤ 5% | human review (pending) |  | Two assessors |
| Citation accuracy | — | 95% | human review (pending) |  | Two assessors |
| Latency p95 | — | < 3 s | 30.0 s | 80 tickets | Free-tier rate-limit waits |
| Availability | — | 99.5% | 100.0% | 80 tickets | 0 provider failures |
| Private data occurrences | — | 0 | 0 | 45 sent replies scanned |  |
| Cross-group variation | — | < 5 pts | see `evaluation/fairness.py` |  |  |

## 2. Business outcomes

Targets and baselines from the Evaluation Framework, tier one.

- First contact resolution (closed with no human; here: answered automatically): **56.2%** (45 tickets; target ≥ 60%, baseline 42%; Brief section 1 says 65%). An upper bound: it assumes every automatic reply solved the issue
- Escalation rate (passed to a person): **43.8%** (35 tickets; target ≤ 30%, baseline 58%)
- Time to first reply, automatic answers: mean 14.9 s, median 16.8 s, p95 24.2 s (target under 5 minutes, baseline 8 to 12 hours). Escalated tickets wait for a person; that time is outside this run
- Customer satisfaction (target ≥ 4.0, baseline 3.2): not computed by the harness; measured by human review of a sample of sent replies against a rubric (see the report for sample, rubric and scorer)
- Repeat contacts (target: halved): not measurable in an offline run, which sees each ticket once
- **Wrong automatic answers (as far as the labels can tell): 14 of 45** (31.1%): VAL-0014, VAL-0016, VAL-0022, VAL-0025, VAL-0034, VAL-0038, VAL-0046, VAL-0051, VAL-0055, VAL-0060, VAL-0070, VAL-0071, VAL-0072, VAL-0080
    - answered although the labels send it to a person: 13 (VAL-0014, VAL-0016, VAL-0022, VAL-0025, VAL-0034, VAL-0038, VAL-0046, VAL-0051, VAL-0055, VAL-0060, VAL-0070, VAL-0071, VAL-0072)
    - answered from an article the labels do not expect: 1 (VAL-0080)
    - answered under the wrong intent: 0
    - whether each reply's content is correct is measured by the human review (hallucination rate, citation accuracy)
- Labels escalate 40.0% of these tickets
- Avoidable escalations (labels say auto, system escalated): 16
- Drafting outcomes for tickets routing allowed: blocked 12, insufficient 1, sent 45
- Replies blocked by a guardrail: 12 (grounding 12)
- Model calls: 148 (11 answered from cache)

Escalation reasons:

- reply blocked by guardrail: 12
- protected category: 11
- has no knowledge-base answer: 9
- no knowledge-base article matched closely enough to answer: 2
- the drafted reply could not be used: 1

Escalation priority: P1 4, P2 2, P3 29

## 3. Technical performance

- Latency per ticket: p50 14426 ms, p95 29965 ms (target p95 < 3 s)
- Availability (handled end to end, no error, no provider failure): 100.0% (target ≥ 99.5%); provider failures 0, each handed to a person
- Intent accuracy 100.0%; urgency accuracy 43.8%
- Retrieval hit rate (expected article among returned passages): 96.2%
- Routing agrees with labels: 63.7%; of auto-routed tickets, labels agree on 71.1%

Per-intent precision and recall:

```
                         precision    recall  f1-score   support

         account_access      1.000     1.000     1.000         4
          api_key_issue      1.000     1.000     1.000         6
     api_usage_question      1.000     1.000     1.000         4
 authentication_failure      1.000     1.000     1.000         3
          billing_query      1.000     1.000     1.000        10
     compliance_request      1.000     1.000     1.000         1
     configuration_help      1.000     1.000     1.000         3
            data_export      1.000     1.000     1.000         1
         data_residency      1.000     1.000     1.000         6
         database_issue      1.000     1.000     1.000         1
     deployment_failure      1.000     1.000     1.000         5
        feature_request      1.000     1.000     1.000         3
       integration_help      1.000     1.000     1.000         3
             onboarding      1.000     1.000     1.000         4
performance_degradation      1.000     1.000     1.000         3
       quota_or_overage      1.000     1.000     1.000         2
             rate_limit      1.000     1.000     1.000         1
       rollback_request      1.000     1.000     1.000         6
      security_incident      1.000     1.000     1.000         4
      sso_configuration      1.000     1.000     1.000         1
        unclear_request      1.000     1.000     1.000         6
          webhook_issue      1.000     1.000     1.000         3

               accuracy                          1.000        80
              macro avg      1.000     1.000     1.000        80
           weighted avg      1.000     1.000     1.000        80

```

## 4. Governance

- Protected-rule escalations: 11
- Private data in sent replies (independent scan of every sent reply, target 0): **0**
- Decision log complete: yes
- must_not_auto_respond tickets auto-routed: **0**

Calibration (stated confidence vs observed intent accuracy):

| band | tickets | stated | observed | gap |
|---|---|---|---|---|
| 0.8–0.9 | 1 | 89.0% | 100.0% | +11.0 pts |
| 0.9–1.0 | 79 | 99.7% | 100.0% | +0.3 pts |

Segments (fairness, NFR-06 tolerance 5 points):

**customer_tier**

| group | tickets | intent acc. | routing acc. | escalation |
|---|---|---|---|---|
| business | 30 | 100.0% | 60.0% | 36.7% |
| enterprise | 8 | 100.0% | 75.0% | 50.0% |
| standard | 42 | 100.0% | 64.3% | 47.6% |

**customer_region**

| group | tickets | intent acc. | routing acc. | escalation |
|---|---|---|---|---|
| asia_pacific | 21 | 100.0% | 71.4% | 38.1% |
| europe | 25 | 100.0% | 64.0% | 32.0% |
| latin_america | 7 | 100.0% | 85.7% | 71.4% |
| north_america | 27 | 100.0% | 51.9% | 51.9% |

**language_fluency**

| group | tickets | intent acc. | routing acc. | escalation |
|---|---|---|---|---|
| fluent | 61 | 100.0% | 63.9% | 44.3% |
| non_fluent | 19 | 100.0% | 63.2% | 42.1% |

## Appendix: intent confusion matrix

Rows: labelled intent; columns: predicted intent (numbered as the rows).

| labelled \ predicted | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1. account_access | 4 | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · |
| 2. api_key_issue | · | 6 | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · |
| 3. api_usage_question | · | · | 4 | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · |
| 4. authentication_failure | · | · | · | 3 | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · |
| 5. billing_query | · | · | · | · | 10 | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · |
| 6. compliance_request | · | · | · | · | · | 1 | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · |
| 7. configuration_help | · | · | · | · | · | · | 3 | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · |
| 8. data_export | · | · | · | · | · | · | · | 1 | · | · | · | · | · | · | · | · | · | · | · | · | · | · |
| 9. data_residency | · | · | · | · | · | · | · | · | 6 | · | · | · | · | · | · | · | · | · | · | · | · | · |
| 10. database_issue | · | · | · | · | · | · | · | · | · | 1 | · | · | · | · | · | · | · | · | · | · | · | · |
| 11. deployment_failure | · | · | · | · | · | · | · | · | · | · | 5 | · | · | · | · | · | · | · | · | · | · | · |
| 12. feature_request | · | · | · | · | · | · | · | · | · | · | · | 3 | · | · | · | · | · | · | · | · | · | · |
| 13. integration_help | · | · | · | · | · | · | · | · | · | · | · | · | 3 | · | · | · | · | · | · | · | · | · |
| 14. onboarding | · | · | · | · | · | · | · | · | · | · | · | · | · | 4 | · | · | · | · | · | · | · | · |
| 15. performance_degradation | · | · | · | · | · | · | · | · | · | · | · | · | · | · | 3 | · | · | · | · | · | · | · |
| 16. quota_or_overage | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | 2 | · | · | · | · | · | · |
| 17. rate_limit | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | 1 | · | · | · | · | · |
| 18. rollback_request | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | 6 | · | · | · | · |
| 19. security_incident | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | 4 | · | · | · |
| 20. sso_configuration | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | 1 | · | · |
| 21. unclear_request | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | 6 | · |
| 22. webhook_issue | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | · | 3 |
