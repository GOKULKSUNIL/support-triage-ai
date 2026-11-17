# Routing evaluation (development tickets, out-of-fold predictions)

500 tickets; labels mark 311 auto_respond, 189 escalate, 87 must_not_auto_respond.

| threshold | auto rate | auto precision (label agrees) | routing accuracy | must-not breaches |
|---|---|---|---|---|
| 0.50 | 71.4% | 75.4% | 74.0% | 0 |
| 0.60 | 71.0% | 75.2% | 73.6% | 0 |
| 0.70 | 69.6% | 74.7% | 72.2% | 0 |
| 0.80 | 68.4% | 74.3% | 71.0% | 0 |
| 0.90 | 65.4% | 73.7% | 68.8% | 0 |
| 0.95 | 61.2% | 74.5% | 67.8% | 0 |
| 0.98 | 53.8% | 75.1% | 64.8% | 0 |

## Disagreements with the labels at threshold 0.80

| intent | system auto, label escalate | system escalate, label auto |
|---|---|---|
| data_residency | 0 | 21 |
| database_issue | 16 | 1 |
| performance_degradation | 13 | 2 |
| onboarding | 0 | 10 |
| configuration_help | 6 | 3 |
| account_access | 4 | 4 |
| deployment_failure | 8 | 0 |
| api_key_issue | 4 | 3 |
| webhook_issue | 5 | 2 |
| rollback_request | 7 | 0 |
| authentication_failure | 6 | 0 |
| integration_help | 5 | 1 |
| quota_or_overage | 3 | 3 |
| sso_configuration | 4 | 0 |
| api_usage_question | 1 | 3 |
| billing_query | 3 | 1 |
| rate_limit | 1 | 3 |
| data_export | 2 | 0 |

## Why tickets escalated

- protected category: 101
- 'feature_request' has no knowledge-base : 15
- 'unclear_request' has no knowledge-base : 15
- no knowledge-base article matched closel: 12
- confidence 0.71: 3
- confidence 0.64: 3
- confidence 0.77: 2
- confidence 0.69: 2
- confidence 0.51: 2
- confidence 0.70: 1
- confidence 0.79: 1
- confidence 0.65: 1

## Escalation priority (D-13) against labelled urgency

| priority | escalations | labelled high | labelled medium | labelled low |
|---|---|---|---|---|
| P1 | 26 | 24 | 2 | 0 |
| P2 | 7 | 1 | 6 | 0 |
| P3 | 125 | 15 | 69 | 41 |

## must_not_auto_respond tickets the system would answer

| ticket | intent | confidence | reason |
|---|---|---|---|
