# Retrieval comparison (development tickets)

500 tickets; 357 need at least one article, 143 need none.

### section (116 passages)

| k | hit@k | recall@k |
|---|---|---|
| 1 | 90.5% | 72.3% |
| 3 | 95.2% | 83.4% |
| 5 | 98.0% | 88.8% |

Threshold sweep (section, top passage score):

| threshold | needs-article tickets keeping ≥1 passage | no-article tickets returning nothing |
|---|---|---|
| 0.20 | 100.0% | 2.1% |
| 0.25 | 100.0% | 4.2% |
| 0.30 | 100.0% | 9.8% |
| 0.35 | 99.4% | 12.6% |
| 0.40 | 97.8% | 14.7% |
| 0.45 | 96.6% | 14.7% |
| 0.50 | 92.2% | 16.8% |
| 0.55 | 84.9% | 24.5% |
| 0.60 | 65.3% | 40.6% |
| 0.65 | 44.8% | 57.3% |
| 0.70 | 24.4% | 79.0% |

### fixed (59 passages)

| k | hit@k | recall@k |
|---|---|---|
| 1 | 89.4% | 71.4% |
| 3 | 95.2% | 84.8% |
| 5 | 98.9% | 92.6% |

Threshold sweep (fixed, top passage score):

| threshold | needs-article tickets keeping ≥1 passage | no-article tickets returning nothing |
|---|---|---|
| 0.20 | 100.0% | 2.8% |
| 0.25 | 99.7% | 8.4% |
| 0.30 | 99.4% | 9.8% |
| 0.35 | 98.9% | 12.6% |
| 0.40 | 98.0% | 13.3% |
| 0.45 | 95.8% | 18.2% |
| 0.50 | 86.3% | 32.2% |
| 0.55 | 64.7% | 45.5% |
| 0.60 | 45.4% | 64.3% |
| 0.65 | 28.6% | 79.0% |
| 0.70 | 11.5% | 91.6% |

