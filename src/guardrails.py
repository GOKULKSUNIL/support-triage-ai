"""Guardrails (FR-07): checks that run on every ticket and every draft.

On the ticket, before drafting: instruction integrity, code that looks for
text trying to give the system instructions; a match hands the ticket to a
person and records the words (Governance Framework: block, escalate, record).

On the draft, before it can be sent:
1. private data, deterministic code: email addresses, phone numbers, card
   numbers, API-key-like tokens and customer IDs other than the ticket owner's;
2. grounding: PR-02 says whether each sentence is supported by the passages;
3. tone and scope: promises that are not the system's to make (refunds,
   credits, guarantees, a fix or a date), found by code unless the cited
   passage says the same words, plus sentences PR-02 marks as a commitment.
Any failure blocks the reply, and so does a grounding check that cannot run
(fail closed). Every check is recorded whether it passed or not. There is no
switch to turn this off.
"""
import re

from pydantic import BaseModel

from src.generate import Draft
from src.ingest import Ticket
from src.llm import LLM, ProviderUnavailable, load_prompt
from src.retrieve import Hit

_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_PHONE = re.compile(r"(?<!\w)\+?\d[\d ()-]{7,}\d(?!\w)")
_CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")
_API_KEY = re.compile(r"\b(?:sk|pk|rk|key|api|tok|gsk)[-_][A-Za-z0-9_-]{12,}\b|\b[A-Za-z0-9]{32,}\b")
_CUSTOMER_ID = re.compile(r"\bCUST-\d+\b", re.I)
# Both lists were checked on development data only: no development ticket matches
# _INJECTION, no reference reply matches _COMMITMENT, and _COMMITMENT catches every
# must_not_claim example ("a refund has been issued", "the issue has been fixed on
# our side", a delivery date for a fix).
_INJECTION = re.compile(
    r"\b(ignore|disregard|forget|override|bypass)\b[^.\n]{0,40}?\b(instructions?|rules|prompts?|guidelines|guardrails?)\b"
    r"|\b(system|developer) prompt\b|\byou are now\b|\bdeveloper mode\b|\bjailbreak\b"
    r"|\b(reveal|print|show|repeat|output)\b[^.\n]{0,20}\b(your|the)\s+(system\s+)?(prompt|instructions)\b"
    r"|\bnew instructions\b|\bpretend (to be|you are)\b", re.I)
_COMMITMENT = re.compile(
    r"\b(refund(s|ed)?|reimburs\w*|compensat\w*|discount\w*|free of charge|waive[ds]?|guarantee[ds]?"
    r"|credit(s|ed)? (to|on|for) your|we will (fix|resolve|restore|repair|refund|credit)\w*"
    r"|(has|have) been (fixed|resolved|issued|refunded|credited|patched)|fixed on our (side|end)"
    r"|(the|a) fix (will|should|is going to) (be|ship|land|go|arrive)"
    r"|(will|should) be (fixed|resolved|released|shipped|patched|available) (by|on|in|next|this|within|soon)"
    r"|next (week|month|release|sprint)"
    r"|within \d+\s*(minutes?|hours?|days?|business days?)"
    r"|by (today|tomorrow|end of (the )?day|monday|tuesday|wednesday|thursday|friday))\b", re.I)


class Check(BaseModel):
    name: str
    passed: bool
    detail: str = ""


class Validation(BaseModel):
    checks: list[Check]
    blocked: bool
    call: dict = {}


def _luhn(number: str) -> bool:
    digits = [int(d) for d in re.sub(r"\D", "", number)][::-1]
    total = sum(d if i % 2 == 0 else (d * 2 - 9 if d * 2 > 9 else d * 2) for i, d in enumerate(digits))
    return len(digits) >= 13 and total % 10 == 0


def _is_phone(candidate: str) -> bool:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", candidate.strip()):  # an ISO date, not a number
        return False
    return len(re.sub(r"\D", "", candidate)) >= 9


def private_data(text: str, ticket: Ticket) -> Check:
    found = []
    if _EMAIL.search(text):
        found.append("email address")
    if any(_luhn(m.group(0)) for m in _CARD.finditer(text)):
        found.append("card number")
    elif any(_is_phone(m.group(0)) for m in _PHONE.finditer(text)):
        found.append("phone number")
    if _API_KEY.search(text):
        found.append("API-key-like token")
    others = {m.group(0).upper() for m in _CUSTOMER_ID.finditer(text)} - {ticket.customer_id.upper()}
    if others:
        found.append("another customer's ID")
    return Check(name="private_data", passed=not found, detail=", ".join(found))


def instruction_integrity(ticket: Ticket) -> Check:
    found = sorted({m.group(0) for m in _INJECTION.finditer(ticket.text)})
    return Check(name="instruction_integrity", passed=not found,
                 detail=f"possible instruction in the ticket, recorded for review: {found}" if found else "")


def grounding(draft: Draft, passages: list[Hit], llm: LLM) -> tuple[Check, dict, list[int]]:
    """Returns the check, the model call and the sentences PR-02 marks as a commitment."""
    prompt = load_prompt("PR-02")
    sentences = "\n".join(f'<sentence index="{i}" cites="{",".join(s.sources)}">{s.text}</sentence>'
                          for i, s in enumerate(draft.sentences))
    block = "\n".join(f'<passage id="{p.passage_id}">{p.text}</passage>' for p in passages)
    try:
        raw, call = llm.complete_json(prompt, sentences=sentences, passages=block)
    except (ProviderUnavailable, ValueError) as exc:
        return Check(name="grounding", passed=False,
                     detail=f"check could not run, blocked ({type(exc).__name__})"), {}, []
    results = raw.get("results")
    if not isinstance(results, list) or len(results) != len(draft.sentences):
        return Check(name="grounding", passed=False,
                     detail="check returned the wrong number of results, blocked"), call, []
    unsupported = [r.get("index") for r in results
                   if not isinstance(r, dict) or r.get("supported") is not True]
    commitments = [r.get("index") for r in results if isinstance(r, dict) and r.get("commitment") is True]
    detail = (f"unsupported sentence(s): {unsupported}" if unsupported
              else f"all {len(results)} sentences supported")
    return Check(name="grounding", passed=not unsupported, detail=detail), call, commitments


def tone_scope(draft: Draft, passages: list[Hit], flagged: list[int]) -> Check:
    """A promise is allowed only when the passage the sentence cites says the same words."""
    text = {p.passage_id: p.text.lower() for p in passages}
    found = []
    for i, s in enumerate(draft.sentences):
        cited = " ".join(text.get(pid, "") for pid in s.sources)
        words = [m.group(0) for m in _COMMITMENT.finditer(s.text) if m.group(0).lower() not in cited]
        if words or i in flagged:
            found.append(f"{i}: {', '.join(words) or 'commitment (PR-02)'}")
    return Check(name="tone_scope", passed=not found,
                 detail=f"commitment(s) the system cannot make: {found}" if found else "")


def validate(draft: Draft, passages: list[Hit], ticket: Ticket, llm: LLM) -> Validation:
    checks = [private_data(draft.text, ticket)]
    ground, call, flagged = grounding(draft, passages, llm)
    checks += [ground, tone_scope(draft, passages, flagged)]
    return Validation(checks=checks, blocked=not all(c.passed for c in checks), call=call)
