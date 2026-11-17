# Classifier evaluation (development tickets, grouped hold-back)

Train 400, held back 100; no ticket text appears on both sides. Validation set not used.

## Choosing C and calibration (grouped 5-fold CV on the training part only)

| C | probabilities | CV accuracy | calibration error (ECE) |
|---|---|---|---|
| 1 | raw | 97.8% | 51.8 pts |
| 1 | sigmoid | 97.0% | 27.3 pts |
| 1 | isotonic | 97.2% | 3.1 pts |
| 10 | raw | 99.0% | 15.4 pts |
| 10 | sigmoid | 98.0% | 25.8 pts |
| 10 | isotonic | 97.5% | 2.3 pts |
| 100 | raw | 99.2% | 4.9 pts |
| 100 | sigmoid | 99.0% | 25.9 pts |
| 100 | isotonic | 98.5% | 2.4 pts |

Chosen: C=10, isotonic (lowest calibration error).

## Intent, per class (held back)

```
                         precision    recall  f1-score   support

         account_access      1.000     1.000     1.000         4
          api_key_issue      1.000     1.000     1.000         3
     api_usage_question      1.000     1.000     1.000         5
 authentication_failure      1.000     1.000     1.000         4
          billing_query      1.000     1.000     1.000         4
     compliance_request      1.000     1.000     1.000         5
     configuration_help      1.000     1.000     1.000         4
            data_export      1.000     1.000     1.000         5
         data_residency      1.000     1.000     1.000         6
         database_issue      1.000     1.000     1.000         5
     deployment_failure      1.000     1.000     1.000         6
        feature_request      1.000     1.000     1.000         4
       integration_help      1.000     1.000     1.000         4
             onboarding      1.000     1.000     1.000         4
performance_degradation      1.000     1.000     1.000         4
       quota_or_overage      1.000     1.000     1.000         4
             rate_limit      1.000     1.000     1.000         3
       rollback_request      1.000     1.000     1.000         6
      security_incident      1.000     1.000     1.000         6
      sso_configuration      1.000     1.000     1.000         6
        unclear_request      1.000     1.000     1.000         3
          webhook_issue      1.000     1.000     1.000         5

               accuracy                          1.000       100
              macro avg      1.000     1.000     1.000       100
           weighted avg      1.000     1.000     1.000       100

```

## Calibration on the held-back part

| confidence band | tickets | stated (mean) | observed accuracy | gap |
|---|---|---|---|---|
| 0.8–0.9 | 1 | 85.1% | 100.0% | +14.9 pts |
| 0.9–1.0 | 99 | 99.1% | 100.0% | +0.9 pts |

ECE 1.0 pts (target: within 5).

## Coverage vs accuracy (input to the routing threshold, B-07)

| threshold | share auto-eligible | accuracy above threshold |
|---|---|---|
| 0.50 | 100.0% | 100.0% |
| 0.60 | 100.0% | 100.0% |
| 0.70 | 100.0% | 100.0% |
| 0.80 | 100.0% | 100.0% |
| 0.90 | 99.0% | 100.0% |
| 0.95 | 92.0% | 100.0% |

## Urgency (held back)

67 of the 97 repeated texts carry different urgency labels on their copies, so urgency is not fully determined by the text.

```
              precision    recall  f1-score   support

        high      0.765     0.406     0.531        32
         low      0.250     0.040     0.069        25
      medium      0.481     0.884     0.623        43

    accuracy                          0.520       100
   macro avg      0.499     0.443     0.408       100
weighted avg      0.514     0.520     0.455       100

[[ 1 23  1]
 [ 2 38  3]
 [ 1 18 13]]
```

## Held-back intent errors

| ticket | true | predicted | confidence |
|---|---|---|---|
