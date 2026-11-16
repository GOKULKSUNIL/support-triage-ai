"""Chunking tests: every passage traces back to a real article (supports T-03a)."""
from src.chunking import build_passages, load_docs

DOCS = load_docs("data/documentation.json")


def test_every_article_produces_passages_with_unique_ids():
    for strategy in ("section", "fixed"):
        passages = build_passages(DOCS, strategy)
        ids = [p.passage_id for p in passages]
        assert len(ids) == len(set(ids))
        assert {p.doc_id for p in passages} == {d["doc_id"] for d in DOCS}


def test_section_passages_follow_article_headings():
    passages = build_passages(DOCS, "section")
    ids = {p.passage_id for p in passages}
    assert "DOC-DATA-003#resolution" in ids
    assert all(p.passage_id.split("#")[0] == p.doc_id for p in passages)
    assert all(p.title in p.text for p in passages)
