# Discovery analysis: development tickets

Tickets: **500**. Received 2026-03-01 to 2026-05-30.

## 1. Composition (Dataset Guide §4 says verify these)

### intent

| intent                  |   tickets |   % |
|:------------------------|----------:|----:|
| data_export             |        29 | 5.8 |
| data_residency          |        29 | 5.8 |
| rollback_request        |        28 | 5.6 |
| deployment_failure      |        27 | 5.4 |
| compliance_request      |        26 | 5.2 |
| sso_configuration       |        26 | 5.2 |
| security_incident       |        26 | 5.2 |
| database_issue          |        26 | 5.2 |
| api_usage_question      |        24 | 4.8 |
| billing_query           |        24 | 4.8 |
| performance_degradation |        23 | 4.6 |
| quota_or_overage        |        23 | 4.6 |
| account_access          |        22 | 4.4 |
| onboarding              |        22 | 4.4 |
| integration_help        |        21 | 4.2 |
| webhook_issue           |        21 | 4.2 |
| feature_request         |        20 | 4   |
| authentication_failure  |        20 | 4   |
| api_key_issue           |        18 | 3.6 |
| configuration_help      |        17 | 3.4 |
| unclear_request         |        15 | 3   |
| rate_limit              |        13 | 2.6 |

### channel

| channel      |   tickets |    % |
|:-------------|----------:|-----:|
| email        |       212 | 42.4 |
| chat         |       155 | 31   |
| docs_comment |        78 | 15.6 |
| forum        |        55 | 11   |

### customer_tier

| customer_tier   |   tickets |    % |
|:----------------|----------:|-----:|
| standard        |       253 | 50.6 |
| business        |       164 | 32.8 |
| enterprise      |        83 | 16.6 |

### customer_region

| customer_region   |   tickets |    % |
|:------------------|----------:|-----:|
| north_america     |       170 | 34   |
| europe            |       151 | 30.2 |
| asia_pacific      |       119 | 23.8 |
| latin_america     |        60 | 12   |

### language_fluency

| language_fluency   |   tickets |   % |
|:-------------------|----------:|----:|
| fluent             |       380 |  76 |
| non_fluent         |       120 |  24 |

### urgency

| urgency   |   tickets |    % |
|:----------|----------:|-----:|
| medium    |       226 | 45.2 |
| high      |       146 | 29.2 |
| low       |       128 | 25.6 |

### expected_route

| expected_route   |   tickets |    % |
|:-----------------|----------:|-----:|
| auto_respond     |       311 | 62.2 |
| escalate         |       189 | 37.8 |

### answerable_from_docs

| answerable_from_docs   |   tickets |    % |
|:-----------------------|----------:|-----:|
| True                   |       357 | 71.4 |
| False                  |       143 | 28.6 |

### must_not_auto_respond

| must_not_auto_respond   |   tickets |    % |
|:------------------------|----------:|-----:|
| False                   |       413 | 82.6 |
| True                    |        87 | 17.4 |

Distinct intents: **22**.

## 2. Current baseline (history block)

- First contact resolution: **43.8%** (Marcus: 42%, benchmark 65%)
- Escalated: **56.2%**
- Repeat contact: **21.6%**
- CSAT mean: **2.97** (n=500)
- Resolution time median / mean: **214 / 422 min**

### Tickets per week in this sample (Marcus: >500/week; this file is a sample)

Weeks: 14, mean 35.7, min 3, max 46.

### By weekday (Sofia: Mondays are worst)

| received_at   |   tickets |
|:--------------|----------:|
| Friday        |        85 |
| Tuesday       |        80 |
| Monday        |        75 |
| Wednesday     |        73 |
| Thursday      |        69 |
| Sunday        |        61 |
| Saturday      |        57 |

## 3. Per intent: the core table

| intent                  |   tickets |   answerable_pct |   expected_auto_pct |   must_not_auto_pct |   hist_escalated_pct |   hist_fcr_pct |   csat_mean |   cum_share_pct |
|:------------------------|----------:|-----------------:|--------------------:|--------------------:|---------------------:|---------------:|------------:|----------------:|
| data_export             |        29 |             93.1 |                93.1 |                   0 |                 34.5 |           65.5 |        3.17 |             5.8 |
| data_residency          |        29 |             72.4 |                72.4 |                   0 |                 69   |           31   |        3    |            11.6 |
| rollback_request        |        28 |             75   |                75   |                   0 |                 39.3 |           60.7 |        3.21 |            17.2 |
| deployment_failure      |        27 |             70.4 |                70.4 |                   0 |                 59.3 |           40.7 |        2.85 |            22.6 |
| sso_configuration       |        26 |             84.6 |                84.6 |                   0 |                 26.9 |           73.1 |        3.73 |            27.8 |
| compliance_request      |        26 |             65.4 |                 0   |                 100 |                100   |            0   |        2.35 |            33   |
| security_incident       |        26 |             53.8 |                 0   |                 100 |                100   |            0   |        2.65 |            38.2 |
| database_issue          |        26 |             69.2 |                38.5 |                   0 |                 73.1 |           26.9 |        2.85 |            43.4 |
| api_usage_question      |        24 |             95.8 |                95.8 |                   0 |                 41.7 |           58.3 |        3.29 |            48.2 |
| billing_query           |        24 |             87.5 |                87.5 |                   0 |                 45.8 |           54.2 |        3.33 |            53   |
| performance_degradation |        23 |             73.9 |                43.5 |                   0 |                 69.6 |           30.4 |        2.48 |            57.6 |
| quota_or_overage        |        23 |             87   |                87   |                   0 |                 26.1 |           73.9 |        2.61 |            62.2 |
| account_access          |        22 |             77.3 |                77.3 |                   0 |                 40.9 |           59.1 |        3.09 |            66.6 |
| onboarding              |        22 |             90.9 |                90.9 |                   0 |                 27.3 |           72.7 |        3.09 |            71   |
| webhook_issue           |        21 |             76.2 |                76.2 |                   0 |                 47.6 |           52.4 |        3    |            75.2 |
| integration_help        |        21 |             76.2 |                76.2 |                   0 |                 61.9 |           38.1 |        3.19 |            79.4 |
| authentication_failure  |        20 |             70   |                70   |                   0 |                 50   |           50   |        2.75 |            83.4 |
| feature_request         |        20 |              0   |                 0   |                 100 |                100   |            0   |        3.15 |            87.4 |
| api_key_issue           |        18 |             66.7 |                66.7 |                   0 |                 44.4 |           55.6 |        3.11 |            91   |
| configuration_help      |        17 |             58.8 |                58.8 |                   0 |                 52.9 |           47.1 |        2.76 |            94.4 |
| unclear_request         |        15 |              0   |                 0   |                 100 |                100   |            0   |        2.4  |            97.4 |
| rate_limit              |        13 |             92.3 |                92.3 |                   0 |                 23.1 |           76.9 |        3.08 |           100   |

## 3b. Where the time goes: share of volume vs share of handling time

Effort proxy = sum of history.resolution_time_minutes. Resolution time is elapsed time,
not agent hands-on time, so treat shares as an estimate.

| intent                  |   tickets |   total_minutes |   median_minutes |   volume_pct |   effort_pct |   effort_to_volume |
|:------------------------|----------:|----------------:|-----------------:|-------------:|-------------:|-------------------:|
| security_incident       |        26 |           20434 |            734.5 |          5.2 |          9.7 |               1.87 |
| compliance_request      |        26 |           17663 |            678.5 |          5.2 |          8.4 |               1.62 |
| data_residency          |        29 |           14936 |            319   |          5.8 |          7.1 |               1.22 |
| feature_request         |        20 |           14477 |            737.5 |          4   |          6.9 |               1.72 |
| deployment_failure      |        27 |           13038 |            384   |          5.4 |          6.2 |               1.15 |
| performance_degradation |        23 |           12495 |            482   |          4.6 |          5.9 |               1.28 |
| database_issue          |        26 |           11887 |            387.5 |          5.2 |          5.6 |               1.08 |
| integration_help        |        21 |           10944 |            268   |          4.2 |          5.2 |               1.24 |
| rollback_request        |        28 |            9799 |             49   |          5.6 |          4.6 |               0.82 |
| billing_query           |        24 |            9428 |             46   |          4.8 |          4.5 |               0.94 |
| authentication_failure  |        20 |            8988 |            160.5 |          4   |          4.3 |               1.08 |
| api_usage_question      |        24 |            8540 |             52   |          4.8 |          4.1 |               0.85 |
| data_export             |        29 |            8486 |             40   |          5.8 |          4   |               0.69 |
| unclear_request         |        15 |            7735 |            437   |          3   |          3.7 |               1.23 |
| webhook_issue           |        21 |            7408 |             55   |          4.2 |          3.5 |               0.83 |
| account_access          |        22 |            6381 |             44   |          4.4 |          3   |               0.68 |
| quota_or_overage        |        23 |            6015 |             37   |          4.6 |          2.9 |               0.63 |
| configuration_help      |        17 |            5856 |            124   |          3.4 |          2.8 |               0.82 |
| api_key_issue           |        18 |            5337 |             39.5 |          3.6 |          2.5 |               0.69 |
| sso_configuration       |        26 |            4967 |             47   |          5.2 |          2.4 |               0.46 |
| onboarding              |        22 |            4447 |             40   |          4.4 |          2.1 |               0.48 |
| rate_limit              |        13 |            1588 |             35   |          2.6 |          0.8 |               0.31 |

Escalated vs not escalated:

| h_escalated   |   count |    sum |   median |   effort_pct |
|:--------------|--------:|-------:|---------:|-------------:|
| False         |     219 |   6674 |       32 |          3.2 |
| True          |     281 | 204175 |      745 |         96.8 |

## 4. Claims to test

### Sofia: ~7 in 10 tickets are repeats answerable without looking anything up

- Answerable from docs: **71.4%**
- Expected route auto_respond: **62.2%**
- Intents needed to cover 70% of volume: **14** of 22

### Daniel: ~half of escalations could have been resolved at tier 1

- Historically escalated: **281**
- Of those, labelled auto_respond and answerable from docs: **92 (32.7%)**
- Opposite direction: labelled escalate but historically not escalated: **0**
- must_not_auto_respond but historically not escalated: **0**

Avoidable escalations by intent:

| intent                  |   tickets |
|:------------------------|----------:|
| data_residency          |        12 |
| api_usage_question      |         9 |
| data_export             |         8 |
| deployment_failure      |         8 |
| integration_help        |         8 |
| billing_query           |         8 |
| webhook_issue           |         5 |
| rollback_request        |         4 |
| account_access          |         4 |
| authentication_failure  |         4 |
| onboarding              |         4 |
| sso_configuration       |         3 |
| quota_or_overage        |         3 |
| database_issue          |         3 |
| performance_degradation |         3 |
| configuration_help      |         2 |
| rate_limit              |         2 |
| api_key_issue           |         2 |

### Sofia: non-fluent customers have the worst satisfaction

| language_fluency   |   tickets |   fcr_pct |   escalated_pct |   repeat_contact_pct |   csat_mean |   resolution_min_median |
|:-------------------|----------:|----------:|----------------:|---------------------:|------------:|------------------------:|
| fluent             |       380 |      43.2 |            56.8 |                 22.4 |        2.95 |                   216.5 |
| non_fluent         |       120 |      45.8 |            54.2 |                 19.2 |        3.04 |                   198   |

Fluency within the same intents (controls for intent mix), FCR %:

| intent                  |   fluent |   non_fluent |
|:------------------------|---------:|-------------:|
| account_access          |     50   |         83.3 |
| api_key_issue           |     53.8 |         60   |
| api_usage_question      |     56.5 |        100   |
| authentication_failure  |     58.8 |          0   |
| billing_query           |     66.7 |         16.7 |
| compliance_request      |      0   |          0   |
| configuration_help      |     53.8 |         25   |
| data_export             |     64   |         75   |
| data_residency          |     30   |         33.3 |
| database_issue          |     16.7 |         50   |
| deployment_failure      |     41.7 |         33.3 |
| feature_request         |      0   |          0   |
| integration_help        |     42.9 |         28.6 |
| onboarding              |     58.3 |         90   |
| performance_degradation |     29.4 |         33.3 |
| quota_or_overage        |     73.7 |         75   |
| rate_limit              |     83.3 |         71.4 |
| rollback_request        |     60.9 |         60   |
| security_incident       |      0   |          0   |
| sso_configuration       |     63.2 |        100   |
| unclear_request         |      0   |          0   |
| webhook_issue           |     52.9 |         50   |

### Ravi / Marcus: enterprise vs business vs standard

| customer_tier   |   tickets |   fcr_pct |   escalated_pct |   repeat_contact_pct |   csat_mean |   resolution_min_median |
|:----------------|----------:|----------:|----------------:|---------------------:|------------:|------------------------:|
| standard        |       253 |      43.1 |            56.9 |                 19.8 |        2.98 |                     266 |
| business        |       164 |      48.2 |            51.8 |                 23.2 |        2.91 |                     141 |
| enterprise      |        83 |      37.3 |            62.7 |                 24.1 |        3.05 |                     369 |

### Ravi: urgency differs hugely within one queue

| urgency   |   tickets |   fcr_pct |   escalated_pct |   repeat_contact_pct |   csat_mean |   resolution_min_median |
|:----------|----------:|----------:|----------------:|---------------------:|------------:|------------------------:|
| medium    |       226 |      43.8 |            56.2 |                 26.1 |        2.99 |                   187.5 |
| high      |       146 |      39.7 |            60.3 |                 20.5 |        2.86 |                   342.5 |
| low       |       128 |      48.4 |            51.6 |                 14.8 |        3.06 |                   132.5 |

Is historical resolution time ordered by urgency? (median minutes)

| customer_tier   |   high |   low |   medium |
|:----------------|-------:|------:|---------:|
| business        |    292 |  52   |     82.5 |
| enterprise      |    198 | 139   |    465.5 |
| standard        |    347 | 210.5 |    140.5 |

### Region and channel

| customer_region   |   tickets |   fcr_pct |   escalated_pct |   repeat_contact_pct |   csat_mean |   resolution_min_median |
|:------------------|----------:|----------:|----------------:|---------------------:|------------:|------------------------:|
| north_america     |       170 |      48.8 |            51.2 |                 20   |        3.05 |                   109.5 |
| europe            |       151 |      43.7 |            56.3 |                 21.9 |        3.01 |                   198   |
| asia_pacific      |       119 |      39.5 |            60.5 |                 21.8 |        2.94 |                   292   |
| latin_america     |        60 |      38.3 |            61.7 |                 25   |        2.73 |                   235   |

| channel      |   tickets |   fcr_pct |   escalated_pct |   repeat_contact_pct |   csat_mean |   resolution_min_median |
|:-------------|----------:|----------:|----------------:|---------------------:|------------:|------------------------:|
| email        |       212 |      44.8 |            55.2 |                 20.8 |        3.08 |                   193   |
| chat         |       155 |      44.5 |            55.5 |                 19.4 |        2.72 |                   209   |
| docs_comment |        78 |      34.6 |            65.4 |                 33.3 |        3.17 |                   465.5 |
| forum        |        55 |      50.9 |            49.1 |                 14.5 |        2.98 |                    54   |

### Ines: customers don't use the words in article titles

- Ticket/expected-article pairs: 447
- Sharing **zero** content words with the article title: **38.7%**
- Median shared title words: 1

## 5. Documentation coverage

Articles: **29**. Categories: **10** (Dataset Guide says eight).

| category       |   articles |
|:---------------|-----------:|
| authentication |          4 |
| deployment     |          4 |
| api            |          3 |
| performance    |          3 |
| billing        |          3 |
| data           |          3 |
| security       |          3 |
| account        |          2 |
| integration    |          2 |
| onboarding     |          2 |

- Articles never expected by any ticket: none
- Expected doc IDs not in the corpus: none
- Intents never answerable from docs: ['feature_request', 'unclear_request']
- Review age (last_reviewed_days_ago): min 0, median 0, max 0

| expected_doc_ids   |   tickets citing |
|:-------------------|-----------------:|
| DOC-DATA-001       |               27 |
| DOC-API-003        |               26 |
| DOC-API-001        |               24 |
| DOC-API-002        |               23 |
| DOC-AUTH-003       |               22 |
| DOC-DEPLOY-002     |               21 |
| DOC-BILL-001       |               21 |
| DOC-DATA-003       |               21 |
| DOC-BILL-003       |               20 |
| DOC-ONB-001        |               20 |
| DOC-DEPLOY-001     |               19 |
| DOC-PERF-003       |               18 |
| DOC-SEC-003        |               17 |
| DOC-ACCT-001       |               17 |
| DOC-PERF-001       |               17 |
| DOC-INT-001        |               16 |
| DOC-AUTH-001       |               14 |
| DOC-SEC-001        |               14 |
| DOC-AUTH-004       |               12 |
| DOC-SEC-002        |               11 |
| DOC-BILL-002       |               11 |
| DOC-DEPLOY-004     |               10 |
| DOC-ONB-002        |               10 |
| DOC-INT-002        |                8 |
| DOC-DATA-002       |                8 |
| DOC-PERF-002       |                6 |
| DOC-ACCT-002       |                5 |
| DOC-DEPLOY-003     |                5 |
| DOC-AUTH-002       |                4 |

## 6. Data quality

- Empty bodies: 0
- Empty subjects by channel:

| channel      |   empty_subject |
|:-------------|----------------:|
| chat         |             155 |
| docs_comment |               0 |
| email        |               0 |
| forum        |               0 |

- Duplicate ticket IDs: 0
- Answerable but no expected doc: 0
- Missing values per column:

_none_
