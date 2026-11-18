"""FR-03 retrieval tests (T-03a-b). T-03c (retrieval hit rate) is in the harness metrics report."""
import pytest

from src.retrieve import Index


@pytest.fixture(scope="module")
def index(tmp_path_factory):
    return Index("section", path=str(tmp_path_factory.mktemp("chroma")))


def test_t03a_every_returned_id_exists_in_the_corpus(index):
    hits = index.search("container deploy keeps rolling back, logs show health check timeouts", k=5)
    assert hits
    assert all(h.passage_id in index.passages for h in hits)
    assert hits[0].doc_id == "DOC-DEPLOY-001"


def test_t03b_off_topic_ticket_returns_nothing(index):
    assert index.search("what is a good recipe for lasagna with spinach") == []
    assert index.search("   ") == []
