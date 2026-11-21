# Metrics report

Input `data/validation_tickets.json`, run 2026-11-21T20:14:00Z → 2026-11-21T20:34:55Z, version `e936ead`, confidence threshold 0.8.

## 1. Volume and reconciliation

- Tickets in: 80; results out: 80; decision-log rows: 80 → **reconciled**
- Tickets that raised an error (escalated, still logged): 0

## 2. Business outcomes

- Answered automatically: 45 (56.2%); escalated: 35 (**43.8%**, target ≤ 30%, baseline 58%)
- First contact resolution proxy (not escalated): 56.2% (target ≥ 65%, baseline 42%)
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

