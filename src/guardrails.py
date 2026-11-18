"""Guardrails (FR-07): checks that run on every draft before it can be sent.

Check 1, private data, is deterministic code: email addresses, phone
numbers, card numbers, API-key-like tokens and customer IDs other than the
ticket owner's. Check 2, grounding, asks PR-02 whether each sentence is
supported by the retrieved passages. Any failure blocks the reply, and so
does a grounding check that cannot run (fail closed). Every check is
recorded whether it passed or not. There is no switch to turn this off.
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


def grounding(draft: Draft, passages: list[Hit], llm: LLM) -> tuple[Check, dict]:
    prompt = load_prompt("PR-02")
    sentences = "\n".join(f'<sentence index="{i}" cites="{",".join(s.sources)}">{s.text}</sentence>'
                          for i, s in enumerate(draft.sentences))
    block = "\n".join(f'<passage id="{p.passage_id}">{p.text}</passage>' for p in passages)
    try:
        raw, call = llm.complete_json(prompt, sentences=sentences, passages=block)
    except (ProviderUnavailable, ValueError) as exc:
        return Check(name="grounding", passed=False,
                     detail=f"check could not run, blocked ({type(exc).__name__})"), {}
    results = raw.get("results")
    if not isinstance(results, list) or len(results) != len(draft.sentences):
        return Check(name="grounding", passed=False,
                     detail="check returned the wrong number of results, blocked"), call
    unsupported = [r.get("index") for r in results
                   if not isinstance(r, dict) or r.get("supported") is not True]
    detail = (f"unsupported sentence(s): {unsupported}" if unsupported
              else f"all {len(results)} sentences supported")
    return Check(name="grounding", passed=not unsupported, detail=detail), call


def validate(draft: Draft, passages: list[Hit], ticket: Ticket, llm: LLM) -> Validation:
    checks = [private_data(draft.text, ticket)]
    ground, call = grounding(draft, passages, llm)
    checks.append(ground)
    return Validation(checks=checks, blocked=not all(c.passed for c in checks), call=call)
