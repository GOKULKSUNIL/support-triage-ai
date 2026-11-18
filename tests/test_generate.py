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


def _cls(intent="security_incident"):
    from src.classify import Classification
    return Classification(intent=intent, urgency="high", confidence=0.97,
                          alternatives=[(intent, 0.97), ("account_access", 0.02), ("api_key_issue", 0.01)])


PACKET_FIELDS = {"summary", "customer_asks", "unsure_about", "suggested_articles", "intent",
                 "confidence", "alternatives", "route_reason", "priority", "source"}


def test_t09a_escalation_packet_has_every_field():
    from src.generate import escalation_packet
    llm = FakeLLM(PR03={"summary": "Customer reports a suspected breach.", "customer_asks": "Help.",
                        "unsure_about": "Protected category.", "suggested_articles": ["DOC-DEPLOY-003",
                                                                                      "DOC-FAKE-999"]})
    p = escalation_packet(TICKET, _cls(), PASSAGES, "Escalated: protected category.", "P1", "security", llm)
    assert PACKET_FIELDS <= set(p) and p["summary"] and p["source"].startswith("PR-03")
    assert p["suggested_articles"] == ["DOC-DEPLOY-003"]  # ids not retrieved are dropped


def test_t09b_provider_down_still_gives_template_packet():
    from src.generate import escalation_packet
    for llm in (FakeLLM(), FakeLLM(PR03={"summary": ""})):  # down, or unusable answer
        p = escalation_packet(TICKET, _cls(), PASSAGES, "Escalated: x.", "P1", "security", llm)
        assert PACKET_FIELDS <= set(p) and p["source"] == "template" and p["summary"] is None
        assert p["intent"] == "security_incident" and p["suggested_articles"] == ["DOC-DEPLOY-003"]
