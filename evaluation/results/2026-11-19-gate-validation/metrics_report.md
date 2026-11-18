# Metrics report

Input `data/validation_tickets.json`, run 2026-11-18T18:49:23Z → 2026-11-18T19:09:21Z, version `fb90bca`, confidence threshold 0.8.

## 1. Volume and reconciliation

- Tickets in: 80; results out: 80; decision-log rows: 80 → **reconciled**
- Tickets that raised an error (escalated, still logged): 0

## 2. Business outcomes

- Answered automatically: 46 (57.5%); escalated: 34 (**42.5%**, target ≤ 30%, baseline 58%)
- First contact resolution proxy (not escalated): 57.5% (target ≥ 65%, baseline 42%)
- Labels escalate 40.0% of these tickets
- Avoidable escalations (labels say auto, system escalated): 13
- Drafting outcomes for tickets routing allowed: blocked 11, insufficient 1, sent 46
- Replies blocked by a guardrail: 11 (grounding 11)
- Model calls: 149 (11 answered from cache)

Escalation reasons:

- protected category: 11
- reply blocked by guardrail: 11
- has no knowledge-base answer: 9
- no knowledge-base article matched closely enough to answer: 2
- the drafted reply could not be used: 1

Escalation priority: P1 4, P2 4, P3 26

## 3. Technical performance

- Latency per ticket: p50 16592 ms, p95 25350 ms (target p95 < 3 s)
- Intent accuracy 100.0%; urgency accuracy 43.8%
- Retrieval hit rate (expected article among returned passages): 96.2%
- Routing agrees with labels: 70.0%; of auto-routed tickets, labels agree on 76.1%

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
| business | 30 | 100.0% | 66.7% | 30.0% |
| enterprise | 8 | 100.0% | 87.5% | 37.5% |
| standard | 42 | 100.0% | 69.0% | 52.4% |

**customer_region**

| group | tickets | intent acc. | routing acc. | escalation |
|---|---|---|---|---|
| asia_pacific | 21 | 100.0% | 76.2% | 33.3% |
| europe | 25 | 100.0% | 60.0% | 44.0% |
| latin_america | 7 | 100.0% | 85.7% | 71.4% |
| north_america | 27 | 100.0% | 70.4% | 40.7% |

**language_fluency**

| group | tickets | intent acc. | routing acc. | escalation |
|---|---|---|---|---|
| fluent | 61 | 100.0% | 75.4% | 39.3% |
| non_fluent | 19 | 100.0% | 52.6% | 52.6% |

