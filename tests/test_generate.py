"""FR-06 / FR-13 drafting tests (T-06a-c, T-13a)."""
from src.generate import AUTO_LABEL, draft
from src.ingest import normalise
from tests.fakes import FakeLLM, hit, reply

TICKET = normalise({"ticket_id": "G1", "channel": "email", "subject": "Builds failing",
                    "body": "Builds fail during dependency resolution."}, 0)
PASSAGES = [hit(), hit("DOC-DEPLOY-003#common-causes", "An unpinned dependency released a new version.")]


def test_t06a_sent_reply_cites_only_retrieved_passages():
    llm = FakeLLM(PR01=reply(("Pin your dependencies.", ["DOC-DEPLOY-003#resolution"]),
                             ("Thanks for getting in touch.", [])))
    d = draft(TICKET, PASSAGES, llm)
    assert d.ok and "[DOC-DEPLOY-003]" in d.text and "Sources:" in d.text
    cited = {sid for s in d.sentences for sid in s.sources}
    assert cited and cited <= {p.passage_id for p in PASSAGES}


def test_t06b_citation_to_a_passage_not_retrieved_is_rejected():
    llm = FakeLLM(PR01=reply(("Restart the service.", ["DOC-PERF-009#resolution"])))
    d = draft(TICKET, PASSAGES, llm)
    assert not d.ok and d.status == "rejected" and "DOC-PERF-009#resolution" in d.problem


def test_t06b_reply_without_any_citation_is_rejected():
    d = draft(TICKET, PASSAGES, FakeLLM(PR01=reply(("Pin your dependencies.", []))))
    assert not d.ok and "no sentence carries a citation" in d.problem


def test_t06c_insufficient_answer_is_not_sent():
    d = draft(TICKET, PASSAGES, FakeLLM(PR01=reply(status="insufficient")))
    assert not d.ok and d.status == "insufficient"


def test_bad_shape_and_provider_down_are_not_sent():
    assert not draft(TICKET, PASSAGES, FakeLLM(PR01={"status": "maybe"})).ok
    assert draft(TICKET, PASSAGES, FakeLLM()).status == "provider_unavailable"
    assert not draft(TICKET, PASSAGES, FakeLLM(PR01=ValueError("bad json"))).ok


def test_t13a_every_reply_starts_with_the_automated_label():
    llm = FakeLLM(PR01=reply(("Pin your dependencies.", ["DOC-DEPLOY-003#resolution"])))
    assert draft(TICKET, PASSAGES, llm).text.startswith(AUTO_LABEL)
