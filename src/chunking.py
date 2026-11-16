"""Chunking (FR-03): split the 29 knowledge-base articles into passages.

Two strategies, compared on the development tickets before one is chosen:
  section  one passage per markdown "## " section (Symptoms, Resolution, ...)
  fixed    overlapping windows of N words, ignoring structure

Every passage id is "<doc_id>#<part>", so a citation always resolves back to
a real article.
"""
import json
import re
from pathlib import Path

from pydantic import BaseModel


class Passage(BaseModel):
    passage_id: str
    doc_id: str
    title: str
    section: str
    applies_to: str
    text: str


def load_docs(path) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _slug(heading: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")


def _passage(doc: dict, part: str, section: str, body: str) -> Passage:
    # The title goes into every passage so a section like "Resolution" still
    # says which problem it resolves.
    return Passage(
        passage_id=f"{doc['doc_id']}#{part}",
        doc_id=doc["doc_id"],
        title=doc["title"],
        section=section,
        applies_to=doc.get("applies_to", ""),
        text=f"{doc['title']}\n{section}\n{body.strip()}",
    )


def chunk_by_section(doc: dict) -> list[Passage]:
    parts = re.split(r"^## +(.+)$", doc["content"], flags=re.M)
    passages = []
    for heading, body in zip(parts[1::2], parts[2::2]):
        if body.strip():
            passages.append(_passage(doc, _slug(heading), heading.strip(), body))
    if not passages:  # an article with no sections is kept whole
        passages.append(_passage(doc, "all", "", doc["content"]))
    return passages


def chunk_fixed(doc: dict, size: int = 120, overlap: int = 30) -> list[Passage]:
    words = doc["content"].split()
    step = max(size - overlap, 1)
    passages = []
    for n, start in enumerate(range(0, max(len(words) - overlap, 1), step)):
        passages.append(_passage(doc, f"w{n}", "", " ".join(words[start:start + size])))
    return passages


STRATEGIES = {"section": chunk_by_section, "fixed": chunk_fixed}


def build_passages(docs: list[dict], strategy: str = "section") -> list[Passage]:
    chunk = STRATEGIES[strategy]
    return [p for doc in docs for p in chunk(doc)]
