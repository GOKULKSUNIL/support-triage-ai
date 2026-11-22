# Fairness audit

Results `evaluation/results/2026-11-22-validation-run3/results.jsonl` (80 tickets). Short tickets: up to 27 words (the median). Each rate: share (count; 95% range). Gap: points behind the best group on that measure; **bold** = beyond the 5-point tolerance (NFR-06). When a group's 95% range overlaps the best group's, the gap may be chance at this sample size.

Resolution = answered automatically. Labels allow = the share the labels say could be answered automatically, so a group with a lower ceiling is expected to have lower resolution. Missed answers = tickets the labels say could be answered but were handed over.

## Customer tier

| Group | Tickets | Resolution | Gap | Labels allow | Missed answers | Gap | Routing agrees | Gap | Right article | Gap | Drafts blocked | Gap | Satisfaction | Gap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| business | 30 | 63% (19/30; 46%–78%) | 0 | 70% (21/30; 52%–83%) | 33% (7/21; 17%–55%) | 0 | 60% (18/30; 42%–75%) | **15** | 100% (22/22; 85%–100%) | 0 | 26% (7/27; 13%–45%) | **14** | — |  |
| enterprise | 8 | 50% (4/8; 22%–78%) | **13** | 75% (6/8; 41%–93%) | 33% (2/6; 10%–70%) | 0 | 75% (6/8; 41%–93%) | 0 | 100% (6/6; 61%–100%) | 0 | 33% (2/6; 10%–70%) | **21** | — |  |
| standard | 42 | 52% (22/42; 38%–67%) | **11** | 50% (21/42; 36%–64%) | 33% (7/21; 17%–55%) | 0 | 64% (27/42; 49%–77%) | **11** | 92% (23/25; 75%–98%) | **8** | 12% (3/25; 4%–30%) | 0 | — |  |

## Language fluency

| Group | Tickets | Resolution | Gap | Labels allow | Missed answers | Gap | Routing agrees | Gap | Right article | Gap | Drafts blocked | Gap | Satisfaction | Gap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fluent | 61 | 56% (34/61; 43%–67%) | 2 | 66% (40/61; 53%–76%) | 35% (14/40; 22%–50%) | **10** | 64% (39/61; 51%–75%) | 0 | 95% (42/44; 85%–99%) | 5 | 22% (10/45; 13%–36%) | **7** | — |  |
| non_fluent | 19 | 58% (11/19; 36%–77%) | 0 | 42% (8/19; 23%–64%) | 25% (2/8; 7%–59%) | 0 | 63% (12/19; 41%–81%) | 1 | 100% (9/9; 70%–100%) | 0 | 15% (2/13; 4%–42%) | 0 | — |  |

## Length

| Group | Tickets | Resolution | Gap | Labels allow | Missed answers | Gap | Routing agrees | Gap | Right article | Gap | Drafts blocked | Gap | Satisfaction | Gap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| long | 37 | 68% (25/37; 51%–80%) | 0 | 62% (23/37; 46%–76%) | 26% (6/23; 13%–46%) | 0 | 62% (23/37; 46%–76%) | 3 | 96% (26/27; 82%–99%) | 0 | 11% (3/28; 4%–27%) | 0 | — |  |
| short | 43 | 47% (20/43; 33%–61%) | **21** | 58% (25/43; 43%–72%) | 40% (10/25; 23%–59%) | **14** | 65% (28/43; 50%–78%) | 0 | 96% (25/26; 81%–99%) | 0 | 30% (9/30; 17%–48%) | **19** | — |  |

## Customer region

| Group | Tickets | Resolution | Gap | Labels allow | Missed answers | Gap | Routing agrees | Gap | Right article | Gap | Drafts blocked | Gap | Satisfaction | Gap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| asia_pacific | 21 | 62% (13/21; 41%–79%) | **6** | 71% (15/21; 50%–86%) | 27% (4/15; 11%–52%) | 2 | 71% (15/21; 50%–86%) | **14** | 100% (17/17; 82%–100%) | 0 | 24% (4/17; 10%–47%) | **24** | — |  |
| europe | 25 | 68% (17/25; 48%–83%) | 0 | 64% (16/25; 45%–80%) | 25% (4/16; 10%–49%) | 0 | 64% (16/25; 45%–80%) | **22** | 95% (18/19; 75%–99%) | **5** | 11% (2/19; 3%–31%) | **11** | — |  |
| latin_america | 7 | 29% (2/7; 8%–64%) | **39** | 43% (3/7; 16%–75%) | 33% (1/3; 6%–79%) | **8** | 86% (6/7; 49%–97%) | 0 | 100% (3/3; 44%–100%) | 0 | 0% (0/2; 0%–66%) | 0 | — |  |
| north_america | 27 | 48% (13/27; 31%–66%) | **20** | 52% (14/27; 34%–69%) | 50% (7/14; 27%–73%) | **25** | 52% (14/27; 34%–69%) | **34** | 93% (13/14; 69%–99%) | **7** | 30% (6/20; 15%–52%) | **30** | — |  |

## Channel

| Group | Tickets | Resolution | Gap | Labels allow | Missed answers | Gap | Routing agrees | Gap | Right article | Gap | Drafts blocked | Gap | Satisfaction | Gap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| chat | 22 | 41% (9/22; 23%–61%) | **32** | 59% (13/22; 39%–77%) | 54% (7/13; 29%–77%) | **54** | 55% (12/22; 35%–73%) | **27** | 85% (11/13; 58%–96%) | **15** | 33% (5/15; 15%–58%) | **33** | — |  |
| docs_comment | 16 | 62% (10/16; 39%–82%) | **10** | 50% (8/16; 28%–72%) | 25% (2/8; 7%–59%) | **25** | 62% (10/16; 39%–82%) | **19** | 100% (10/10; 72%–100%) | 0 | 17% (2/12; 5%–45%) | **17** | — |  |
| email | 31 | 58% (18/31; 41%–74%) | **15** | 68% (21/31; 50%–81%) | 33% (7/21; 17%–55%) | **33** | 65% (20/31; 47%–79%) | **17** | 100% (22/22; 85%–100%) | 0 | 22% (5/23; 10%–42%) | **22** | — |  |
| forum | 11 | 73% (8/11; 43%–90%) | 0 | 55% (6/11; 28%–79%) | 0% (0/6; 0%–39%) | 0 | 82% (9/11; 52%–95%) | 0 | 100% (8/8; 68%–100%) | 0 | 0% (0/8; 0%–32%) | 0 | — |  |

## Search step alone on `data/development_tickets.json` (357 tickets that need an article)

No model calls: the expected article among the passages found.

**language fluency**

| Group | Right article | Gap |
|---|---|---|
| fluent | 95% (256/270; 91%–97%) | 0 |
| non_fluent | 89% (77/87; 80%–94%) | **6** |

**customer tier**

| Group | Right article | Gap |
|---|---|---|
| business | 91% (112/123; 85%–95%) | 4 |
| enterprise | 95% (56/59; 86%–98%) | 0 |
| standard | 94% (165/175; 90%–97%) | 1 |

**customer region**

| Group | Right article | Gap |
|---|---|---|
| asia_pacific | 92% (70/76; 84%–96%) | 3 |
| europe | 93% (107/115; 87%–96%) | 2 |
| latin_america | 95% (41/43; 85%–99%) | 0 |
| north_america | 93% (115/123; 88%–97%) | 2 |

**channel**

| Group | Right article | Gap |
|---|---|---|
| chat | 91% (108/119; 84%–95%) | **7** |
| docs_comment | 94% (45/48; 83%–98%) | 4 |
| email | 94% (144/153; 89%–97%) | 3 |
| forum | 97% (36/37; 86%–100%) | 0 |

Satisfaction: not yet scored (human review pending); rerun with `--review` once it is.
