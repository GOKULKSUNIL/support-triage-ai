"""Answer drafting (FR-06, FR-13): a cited reply built only from retrieved passages.

The model (PR-01) returns sentences with the passage ids they came from.
Code, not the model, then decides whether the draft is usable: the JSON must
have the right shape, every cited id must be one of this ticket's retrieved
passages, and at least one sentence must carry a citation. Anything else is
not sent; the ticket escalates with the reason. Code also renders the
citations and puts the fixed automated-reply label first.
"""
from pydantic import BaseModel

from src.ingest import Ticket
from src.llm import LLM, ProviderUnavailable, load_prompt
from src.retrieve import Hit

AUTO_LABEL = ("This reply was drafted automatically from our documentation. "
              "Reply to this message to reach a person.")


class Sentence(BaseModel):
    text: str
    sources: list[str] = []


class Draft(BaseModel):
    ok: bool
    status: str  # "answered" | "insufficient" | "rejected" | "provider_unavailable"
    sentences: list[Sentence] = []
    missing: str = ""
    problem: str = ""  # why the draft cannot be sent; empty when ok
    text: str = ""     # rendered reply, set only when ok
    call: dict = {}    # provider, model, prompt id and version, cached


def _passages_block(passages: list[Hit], with_title: bool = True) -> str:
    return "\n".join(
        f'<passage id="{p.passage_id}"' + (f' title="{p.title}"' if with_title else "") +
        f">{p.text}</passage>" for p in passages)


def check(raw: dict, passages: list[Hit]) -> tuple[str, list[Sentence], str, str]:
    """Validate PR-01 output. Returns (status, sentences, missing, problem)."""
    status = raw.get("status")
    if status not in ("answered", "insufficient"):
        return "rejected", [], "", f"unexpected status {status!r}"
    missing = str(raw.get("missing") or "")
    if status == "insufficient":
        return status, [], missing, f"documentation does not answer this: {missing or 'not stated'}"
    items = raw.get("sentences")
    if not isinstance(items, list) or not items:
        return "rejected", [], missing, "no sentences in the draft"
    try:
        sentences = [Sentence(text=s["text"], sources=list(s.get("sources") or [])) for s in items]
    except (TypeError, KeyError, ValueError):
        return "rejected", [], missing, "sentences are not in the required shape"
    retrieved = {p.passage_id for p in passages}
    invented = sorted({sid for s in sentences for sid in s.sources} - retrieved)
    if invented:
        return "rejected", sentences, missing, f"cites passages that were not retrieved: {', '.join(invented)}"
    if not any(s.sources for s in sentences):
        return "rejected", sentences, missing, "no sentence carries a citation"
    return status, sentences, missing, ""


def render(sentences: list[Sentence], passages: list[Hit]) -> str:
    titles = {p.doc_id: p.title for p in passages}
    lines, cited = [], []
    for s in sentences:
        docs = list(dict.fromkeys(sid.split("#")[0] for sid in s.sources))
        cited += [d for d in docs if d not in cited]
        lines.append(s.text.strip() + "".join(f" [{d}]" for d in docs))
    footer = "\n".join(f"- [{d}] {titles.get(d, d)}" for d in cited)
    return f"{AUTO_LABEL}\n\n" + " ".join(lines) + f"\n\nSources:\n{footer}"


def escalation_packet(ticket: Ticket, c, passages: list[Hit], reason: str, priority: str,
                      priority_reason: str, llm: LLM) -> dict:
    """Handover note for Tier 2 (FR-09). Code supplies the facts; PR-03 adds the
    written summary. If the model is unavailable or its answer is unusable, the
    template packet is returned without a summary, so every escalation has one."""
    retrieved = sorted({p.doc_id for p in passages})
    packet = {
        "summary": None, "customer_asks": None, "unsure_about": reason,
        "suggested_articles": retrieved,
        "intent": c.intent if c else None,
        "confidence": c.confidence if c else None,
        "alternatives": c.alternatives if c else [],
        "route_reason": reason, "priority": priority, "priority_reason": priority_reason,
        "source": "template",
    }
    if c is None or not ticket.text:
        return packet
    prompt = load_prompt("PR-03")
    titles = {p.doc_id: p.title for p in passages}
    try:
        raw, call = llm.complete_json(
            prompt, channel=ticket.channel, tier=ticket.customer_tier, subject=ticket.subject,
            body=ticket.body, intent=c.intent, confidence=f"{c.confidence:.2f}",
            # Only alternatives with a real chance; listing 0.00 ones invents doubt.
            alternatives="; ".join(f"{i} {p:.2f}" for i, p in c.alternatives[1:] if p >= 0.05)
            or "none",
            reason=reason, articles="; ".join(f"{d}: {titles[d]}" for d in retrieved) or "none")
    except (ProviderUnavailable, ValueError):
        return packet
    if not all(isinstance(raw.get(k), str) and raw.get(k).strip()
               for k in ("summary", "customer_asks", "unsure_about")):
        return packet
    suggested = [d for d in raw.get("suggested_articles") or [] if d in titles]
    return {**packet, "summary": raw["summary"].strip(), "customer_asks": raw["customer_asks"].strip(),
            "unsure_about": raw["unsure_about"].strip(), "suggested_articles": suggested,
            "source": f"{call['prompt']} v{call['version']}", "call": call}


def draft(ticket: Ticket, passages: list[Hit], llm: LLM) -> Draft:
    prompt = load_prompt("PR-01")
    try:
        raw, call = llm.complete_json(prompt, channel=ticket.channel, subject=ticket.subject,
                                      body=ticket.body, passages=_passages_block(passages))
    except ProviderUnavailable as exc:
        return Draft(ok=False, status="provider_unavailable", problem=f"provider unavailable ({exc})",
                     call={"prompt": prompt.prompt_id, "version": prompt.version})
    except ValueError as exc:
        return Draft(ok=False, status="rejected", problem=f"reply was not valid JSON ({exc})",
                     call={"prompt": prompt.prompt_id, "version": prompt.version})
    status, sentences, missing, problem = check(raw, passages)
    if problem:
        return Draft(ok=False, status=status, sentences=sentences, missing=missing,
                     problem=problem, call=call)
    return Draft(ok=True, status=status, sentences=sentences, missing=missing,
                 text=render(sentences, passages), call=call)
