"""Stage 1 discovery analysis: test the stakeholder interview claims against ticket data.

Prints facts only. Interpretation belongs in the discovery workbook.

Run from the repo root:
    python analysis/discovery.py \
        --tickets ../Capstone_Pack/05_Datasets/development_tickets.json \
        --docs ../Capstone_Pack/05_Datasets/documentation.json \
        --output analysis/output/discovery_report.md
"""
import argparse
import json
import re
from pathlib import Path

import pandas as pd

STOPWORDS = set(
    "a an the and or but to of in on for with is are was were be been it this that my our we i "
    "you your can cannot not no do does did have has had from at by as when after before how "
    "why what which there their they them so if all any just now get getting".split()
)


def load_tickets(path):
    raw = json.loads(Path(path).read_text())
    df = pd.json_normalize(raw)
    df.columns = [c.replace("labels.", "").replace("history.", "h_") for c in df.columns]
    df["received_at"] = pd.to_datetime(df["received_at"])
    return df


def pct(series):
    return round(100 * series.mean(), 1)


def table(df):
    return df.to_markdown() if not df.empty else "_none_"


def distribution(df, col):
    counts = df[col].value_counts()
    return pd.DataFrame({"tickets": counts, "%": (100 * counts / len(df)).round(1)})


def segment(df, col):
    """Baseline outcomes for each value of a customer or ticket attribute."""
    return (
        df.groupby(col)
        .agg(
            tickets=("ticket_id", "count"),
            fcr_pct=("h_first_contact_resolution", pct),
            escalated_pct=("h_escalated", pct),
            repeat_contact_pct=("h_repeat_contact", pct),
            csat_mean=("h_csat_rating", "mean"),
            resolution_min_median=("h_resolution_time_minutes", "median"),
        )
        .round(2)
        .sort_values("tickets", ascending=False)
    )


def tokens(text):
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOPWORDS and len(w) > 2}


def title_overlap(df, docs):
    """Share of tickets whose wording shares no content word with the title of the
    article that answers them: a proxy for what a title/keyword search would miss."""
    titles = {d["doc_id"]: tokens(d["title"]) for d in docs}
    rows = []
    for _, t in df[df["answerable_from_docs"]].iterrows():
        words = tokens(f"{t['subject']} {t['body']}")
        for doc_id in t["expected_doc_ids"]:
            if doc_id in titles:
                rows.append({"intent": t["intent"], "shared_title_words": len(words & titles[doc_id])})
    return pd.DataFrame(rows)


def build_report(df, docs):
    out = []
    add = out.append

    add("# Discovery analysis: development tickets\n")
    add(f"Tickets: **{len(df)}**. Received {df['received_at'].min():%Y-%m-%d} to "
        f"{df['received_at'].max():%Y-%m-%d}.\n")

    add("## 1. Composition (Dataset Guide §4 says verify these)\n")
    for col in ["intent", "channel", "customer_tier", "customer_region", "language_fluency",
                "urgency", "expected_route", "answerable_from_docs", "must_not_auto_respond"]:
        add(f"### {col}\n\n{table(distribution(df, col))}\n")
    add(f"Distinct intents: **{df['intent'].nunique()}**.\n")

    add("## 2. Current baseline (history block)\n")
    add(f"- First contact resolution: **{pct(df['h_first_contact_resolution'])}%** "
        "(Marcus: 42%, benchmark 65%)")
    add(f"- Escalated: **{pct(df['h_escalated'])}%**")
    add(f"- Repeat contact: **{pct(df['h_repeat_contact'])}%**")
    add(f"- CSAT mean: **{df['h_csat_rating'].mean():.2f}** (n={df['h_csat_rating'].notna().sum()})")
    add(f"- Resolution time median / mean: **{df['h_resolution_time_minutes'].median():.0f} / "
        f"{df['h_resolution_time_minutes'].mean():.0f} min**\n")

    weeks = df.set_index("received_at").resample("W")["ticket_id"].count()
    add("### Tickets per week in this sample (Marcus: >500/week; this file is a sample)\n")
    add(f"Weeks: {len(weeks)}, mean {weeks.mean():.1f}, min {weeks.min()}, max {weeks.max()}.\n")
    dow = df["received_at"].dt.day_name().value_counts()
    add(f"### By weekday (Sofia: Mondays are worst)\n\n{table(dow.to_frame('tickets'))}\n")

    add("## 3. Per intent: the core table\n")
    per_intent = (
        df.groupby("intent")
        .agg(
            tickets=("ticket_id", "count"),
            answerable_pct=("answerable_from_docs", pct),
            expected_auto_pct=("expected_route", lambda s: pct(s == "auto_respond")),
            must_not_auto_pct=("must_not_auto_respond", pct),
            hist_escalated_pct=("h_escalated", pct),
            hist_fcr_pct=("h_first_contact_resolution", pct),
            csat_mean=("h_csat_rating", "mean"),
        )
        .round(2)
        .sort_values("tickets", ascending=False)
    )
    per_intent["cum_share_pct"] = (100 * per_intent["tickets"].cumsum() / len(df)).round(1)
    add(table(per_intent) + "\n")

    add("## 3b. Where the time goes: share of volume vs share of handling time\n")
    add("Effort proxy = sum of history.resolution_time_minutes. Resolution time is elapsed time,\n"
        "not agent hands-on time, so treat shares as an estimate.\n")
    effort = df.groupby("intent").agg(
        tickets=("ticket_id", "count"),
        total_minutes=("h_resolution_time_minutes", "sum"),
        median_minutes=("h_resolution_time_minutes", "median"),
    )
    effort["volume_pct"] = (100 * effort["tickets"] / effort["tickets"].sum()).round(1)
    effort["effort_pct"] = (100 * effort["total_minutes"] / effort["total_minutes"].sum()).round(1)
    effort["effort_to_volume"] = (effort["effort_pct"] / effort["volume_pct"]).round(2)
    add(table(effort.sort_values("effort_pct", ascending=False)) + "\n")
    esc_effort = df.groupby("h_escalated")["h_resolution_time_minutes"].agg(["count", "sum", "median"])
    esc_effort["effort_pct"] = (100 * esc_effort["sum"] / esc_effort["sum"].sum()).round(1)
    add("Escalated vs not escalated:\n")
    add(table(esc_effort) + "\n")

    add("## 4. Claims to test\n")

    add("### Sofia: ~7 in 10 tickets are repeats answerable without looking anything up\n")
    add(f"- Answerable from docs: **{pct(df['answerable_from_docs'])}%**")
    add(f"- Expected route auto_respond: **{pct(df['expected_route'] == 'auto_respond')}%**")
    top = per_intent["cum_share_pct"]
    add(f"- Intents needed to cover 70% of volume: **{int((top < 70).sum()) + 1}** of {len(top)}\n")

    add("### Daniel: ~half of escalations could have been resolved at tier 1\n")
    esc = df[df["h_escalated"]]
    avoidable = esc[(esc["expected_route"] == "auto_respond") & esc["answerable_from_docs"]]
    add(f"- Historically escalated: **{len(esc)}**")
    add(f"- Of those, labelled auto_respond and answerable from docs: **{len(avoidable)} "
        f"({100 * len(avoidable) / max(len(esc), 1):.1f}%)**")
    missed = df[(df["expected_route"] == "escalate") & ~df["h_escalated"]]
    add(f"- Opposite direction: labelled escalate but historically not escalated: **{len(missed)}**")
    unsafe = df[df["must_not_auto_respond"] & ~df["h_escalated"]]
    add(f"- must_not_auto_respond but historically not escalated: **{len(unsafe)}**\n")
    add(f"Avoidable escalations by intent:\n\n{table(avoidable['intent'].value_counts().to_frame('tickets'))}\n")

    add("### Sofia: non-fluent customers have the worst satisfaction\n")
    add(table(segment(df, "language_fluency")) + "\n")
    add("Fluency within the same intents (controls for intent mix), FCR %:\n")
    fl = df.pivot_table(index="intent", columns="language_fluency",
                        values="h_first_contact_resolution", aggfunc="mean")
    add(table((100 * fl).round(1)) + "\n")

    add("### Ravi / Marcus: enterprise vs business vs standard\n")
    add(table(segment(df, "customer_tier")) + "\n")

    add("### Ravi: urgency differs hugely within one queue\n")
    add(table(segment(df, "urgency")) + "\n")
    add("Is historical resolution time ordered by urgency? (median minutes)\n")
    add(table(df.pivot_table(index="customer_tier", columns="urgency",
                             values="h_resolution_time_minutes", aggfunc="median")) + "\n")

    add("### Region and channel\n")
    add(table(segment(df, "customer_region")) + "\n")
    add(table(segment(df, "channel")) + "\n")

    add("### Ines: customers don't use the words in article titles\n")
    ov = title_overlap(df, docs)
    if not ov.empty:
        add(f"- Ticket/expected-article pairs: {len(ov)}")
        add(f"- Sharing **zero** content words with the article title: "
            f"**{pct(ov['shared_title_words'] == 0)}%**")
        add(f"- Median shared title words: {ov['shared_title_words'].median():.0f}\n")

    add("## 5. Documentation coverage\n")
    doc_df = pd.DataFrame(docs)
    add(f"Articles: **{len(doc_df)}**. Categories: **{doc_df['category'].nunique()}** "
        f"(Dataset Guide says eight).\n")
    add(table(doc_df["category"].value_counts().to_frame("articles")) + "\n")
    cited = df.explode("expected_doc_ids")["expected_doc_ids"].dropna()
    never = sorted(set(doc_df["doc_id"]) - set(cited))
    unknown = sorted(set(cited) - set(doc_df["doc_id"]))
    add(f"- Articles never expected by any ticket: {never or 'none'}")
    add(f"- Expected doc IDs not in the corpus: {unknown or 'none'}")
    no_doc = per_intent[per_intent["answerable_pct"] == 0].index.tolist()
    add(f"- Intents never answerable from docs: {no_doc or 'none'}")
    add(f"- Review age (last_reviewed_days_ago): min {doc_df['last_reviewed_days_ago'].min()}, "
        f"median {doc_df['last_reviewed_days_ago'].median():.0f}, "
        f"max {doc_df['last_reviewed_days_ago'].max()}\n")
    add(table(cited.value_counts().to_frame("tickets citing").head(29)) + "\n")

    add("## 6. Data quality\n")
    add(f"- Empty bodies: {(df['body'].str.strip() == '').sum()}")
    add(f"- Empty subjects by channel:\n\n"
        f"{table(df.assign(empty=df['subject'].str.strip() == '').groupby('channel')['empty'].sum().to_frame('empty_subject'))}\n")
    add(f"- Duplicate ticket IDs: {df['ticket_id'].duplicated().sum()}")
    add(f"- Answerable but no expected doc: "
        f"{(df['answerable_from_docs'] & (df['expected_doc_ids'].str.len() == 0)).sum()}")
    add(f"- Missing values per column:\n\n{table(df.isna().sum()[df.isna().sum() > 0].to_frame('missing'))}\n")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tickets", required=True, help="Path to a tickets JSON file")
    parser.add_argument("--docs", required=True, help="Path to documentation.json")
    parser.add_argument("--output", required=True, help="Path for the markdown report")
    args = parser.parse_args()

    df = load_tickets(args.tickets)
    docs = json.loads(Path(args.docs).read_text())
    report = build_report(df, docs)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report)
    print(f"wrote {out} ({len(df)} tickets)")


if __name__ == "__main__":
    main()
