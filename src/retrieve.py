"""Retrieval (FR-03): find the knowledge-base passages that answer a ticket.

Passages are embedded locally (sentence-transformers) and stored in Chroma,
one collection per chunking strategy. A search returns the top-k passages
with a cosine similarity score; anything under the relevance threshold is
dropped, so a ticket with no good match gets an empty list rather than a
weak passage.
"""
import os
from functools import lru_cache

import chromadb
from sentence_transformers import SentenceTransformer

from src.chunking import Passage, build_passages, load_docs

DOCS_PATH = "data/documentation.json"


class Hit(Passage):
    score: float


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))


def embed(texts: list[str]) -> list[list[float]]:
    return _model().encode(texts, normalize_embeddings=True).tolist()


class Index:
    def __init__(self, strategy: str = "section", path: str | None = None,
                 docs_path: str = DOCS_PATH):
        path = path or os.getenv("CHROMA_PATH", "./storage/chroma")
        client = chromadb.PersistentClient(path=path)
        self.passages = {p.passage_id: p for p in build_passages(load_docs(docs_path), strategy)}
        self.collection = client.get_or_create_collection(
            f"kb_{strategy}", metadata={"hnsw:space": "cosine"})
        # Rebuild when the corpus changes, so ids in the store always match
        # the ids chunking produces from documentation.json.
        if set(self.collection.get(include=[])["ids"]) != set(self.passages):
            client.delete_collection(self.collection.name)
            self.collection = client.create_collection(
                f"kb_{strategy}", metadata={"hnsw:space": "cosine"})
            ids = list(self.passages)
            self.collection.add(ids=ids, embeddings=embed([self.passages[i].text for i in ids]))

    def search(self, text: str, k: int | None = None,
               threshold: float | None = None) -> list[Hit]:
        k = k or int(os.getenv("RETRIEVAL_TOP_K", 5))
        # 0.40 chosen on the development tickets: every unclear ticket falls
        # below it, 97.8% of tickets that need an article stay above it.
        threshold = float(os.getenv("RELEVANCE_THRESHOLD", 0.40)) if threshold is None else threshold
        if not text.strip():
            return []
        res = self.collection.query(query_embeddings=embed([text]), n_results=k)
        hits = []
        for pid, dist in zip(res["ids"][0], res["distances"][0]):
            score = 1 - dist
            if score >= threshold:
                hits.append(Hit(**self.passages[pid].model_dump(), score=round(score, 4)))
        return hits
