# Fairness audit

Results `evaluation/results/2026-11-22-validation-run4/results.jsonl` (80 tickets). Short tickets: up to 27 words (the median). Each rate: share (count; 95% range). Gap: points behind the best group on that measure; **bold** = beyond the 5-point tolerance (NFR-06). When a group's 95% range overlaps the best group's, the gap may be chance at this sample size.

Resolution = answered automatically. Labels allow = the share the labels say could be answered automatically, so a group with a lower ceiling is expected to have lower resolution. Missed answers = tickets the labels say could be answered but were handed over.

## Customer tier

| Group | Tickets | Resolution | Gap | Labels allow | Missed answers | Gap | Routing agrees | Gap | Right article | Gap | Drafts blocked | Gap | Satisfaction | Gap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| business | 30 | 73% (22/30; 56%–86%) | 0 | 70% (21/30; 52%–83%) | 24% (5/21; 11%–45%) | 0 | 63% (19/30; 46%–78%) | **12** | 100% (22/22; 85%–100%) | 0 | 15% (4/27; 6%–32%) | 0 | — |  |
| enterprise | 8 | 50% (4/8; 22%–78%) | **23** | 75% (6/8; 41%–93%) | 33% (2/6; 10%–70%) | **10** | 75% (6/8; 41%–93%) | 0 | 100% (6/6; 61%–100%) | 0 | 33% (2/6; 10%–70%) | **19** | — |  |
| standard | 42 | 48% (20/42; 33%–62%) | **26** | 50% (21/42; 36%–64%) | 33% (7/21; 17%–55%) | **10** | 69% (29/42; 54%–81%) | **6** | 92% (23/25; 75%–98%) | **8** | 20% (5/25; 9%–39%) | **5** | — |  |

## Language fluency

| Group | Tickets | Resolution | Gap | Labels allow | Missed answers | Gap | Routing agrees | Gap | Right article | Gap | Drafts blocked | Gap | Satisfaction | Gap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fluent | 61 | 56% (34/61; 43%–67%) | **7** | 66% (40/61; 53%–76%) | 30% (12/40; 18%–45%) | 5 | 70% (43/61; 58%–80%) | 0 | 95% (42/44; 85%–99%) | 5 | 22% (10/45; 13%–36%) | **15** | — |  |
| non_fluent | 19 | 63% (12/19; 41%–81%) | 0 | 42% (8/19; 23%–64%) | 25% (2/8; 7%–59%) | 0 | 58% (11/19; 36%–77%) | **13** | 100% (9/9; 70%–100%) | 0 | 8% (1/13; 1%–33%) | 0 | — |  |

## Length

| Group | Tickets | Resolution | Gap | Labels allow | Missed answers | Gap | Routing agrees | Gap | Right article | Gap | Drafts blocked | Gap | Satisfaction | Gap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| long | 37 | 57% (21/37; 41%–71%) | 1 | 62% (23/37; 46%–76%) | 35% (8/23; 19%–55%) | **11** | 62% (23/37; 46%–76%) | **10** | 96% (26/27; 82%–99%) | 0 | 25% (7/28; 13%–43%) | **12** | — |  |
| short | 43 | 58% (25/43; 43%–72%) | 0 | 58% (25/43; 43%–72%) | 24% (6/25; 11%–43%) | 0 | 72% (31/43; 57%–83%) | 0 | 96% (25/26; 81%–99%) | 0 | 13% (4/30; 5%–30%) | 0 | — |  |

## Customer region

| Group | Tickets | Resolution | Gap | Labels allow | Missed answers | Gap | Routing agrees | Gap | Right article | Gap | Drafts blocked | Gap | Satisfaction | Gap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| asia_pacific | 21 | 62% (13/21; 41%–79%) | 1 | 71% (15/21; 50%–86%) | 20% (3/15; 7%–45%) | 0 | 81% (17/21; 60%–92%) | 5 | 100% (17/17; 82%–100%) | 0 | 24% (4/17; 10%–47%) | **24** | — |  |
| europe | 25 | 56% (14/25; 37%–73%) | **7** | 64% (16/25; 45%–80%) | 38% (6/16; 18%–61%) | **18** | 60% (15/25; 41%–77%) | **26** | 95% (18/19; 75%–99%) | **5** | 26% (5/19; 12%–49%) | **26** | — |  |
| latin_america | 7 | 29% (2/7; 8%–64%) | **34** | 43% (3/7; 16%–75%) | 33% (1/3; 6%–79%) | **13** | 86% (6/7; 49%–97%) | 0 | 100% (3/3; 44%–100%) | 0 | 0% (0/2; 0%–66%) | 0 | — |  |
| north_america | 27 | 63% (17/27; 44%–78%) | 0 | 52% (14/27; 34%–69%) | 29% (4/14; 12%–55%) | **9** | 59% (16/27; 41%–75%) | **26** | 93% (13/14; 69%–99%) | **7** | 10% (2/20; 3%–30%) | **10** | — |  |

## Channel

| Group | Tickets | Resolution | Gap | Labels allow | Missed answers | Gap | Routing agrees | Gap | Right article | Gap | Drafts blocked | Gap | Satisfaction | Gap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| chat | 22 | 50% (11/22; 31%–69%) | **12** | 59% (13/22; 39%–77%) | 38% (5/13; 18%–64%) | **26** | 64% (14/22; 43%–80%) | **18** | 85% (11/13; 58%–96%) | **15** | 20% (3/15; 7%–45%) | 3 | — |  |
| docs_comment | 16 | 62% (10/16; 39%–82%) | 0 | 50% (8/16; 28%–72%) | 12% (1/8; 2%–47%) | 0 | 75% (12/16; 51%–90%) | **7** | 100% (10/10; 72%–100%) | 0 | 17% (2/12; 5%–45%) | 0 | — |  |
| email | 31 | 61% (19/31; 44%–76%) | 1 | 68% (21/31; 50%–81%) | 33% (7/21; 17%–55%) | **21** | 61% (19/31; 44%–76%) | **21** | 100% (22/22; 85%–100%) | 0 | 17% (4/23; 7%–37%) | 1 | — |  |
| forum | 11 | 55% (6/11; 28%–79%) | **8** | 55% (6/11; 28%–79%) | 17% (1/6; 3%–56%) | 4 | 82% (9/11; 52%–95%) | 0 | 100% (8/8; 68%–100%) | 0 | 25% (2/8; 7%–59%) | **8** | — |  |

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
