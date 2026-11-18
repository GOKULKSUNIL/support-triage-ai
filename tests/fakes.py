"""Test doubles: a scripted model so drafting and guardrails run without a provider."""
from src.llm import ProviderUnavailable
from src.retrieve import Hit


def hit(pid="DOC-DEPLOY-003#resolution", text="Pin dependencies to exact versions and commit the lock file."):
    return Hit(passage_id=pid, doc_id=pid.split("#")[0], title="Build failures", section="Resolution",
               applies_to="All plans", text=text, score=0.7)


class FakeLLM:
    """Answers each prompt id from a script: a dict, an exception, or a function of the inputs."""

    def __init__(self, **script):
        self.script = script
        self.calls = []

    def complete_json(self, prompt, **values):
        self.calls.append(prompt.prompt_id)
        answer = self.script.get(prompt.prompt_id.replace("-", ""))
        if answer is None:
            raise ProviderUnavailable("not scripted")
        if isinstance(answer, Exception):
            raise answer
        if callable(answer):
            answer = answer(**values)
        return answer, {"provider": "fake", "model": "fake-model", "prompt": prompt.prompt_id,
                        "version": prompt.version, "cached": False}


def reply(*sentences, status="answered"):
    return {"status": status, "missing": "" if status == "answered" else "not covered",
            "sentences": [{"text": t, "sources": s} for t, s in sentences]}


def grounded(n, supported=True):
    return {"results": [{"index": i, "supported": supported, "passage_id": None, "reason": "r"}
                        for i in range(n)]}
