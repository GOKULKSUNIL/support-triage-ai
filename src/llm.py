"""Model access (FR-12) and the prompt register loader.

Prompts live in prompts/<category>/<PR-id>.md with their version in the file
header; they are loaded here, never written inline in code. Every call:
  - is answered from the cache when the same prompt version has already seen
    the same inputs (key = hash of prompt id, version and filled messages),
  - times out, retries with backoff on rate limits and transient errors,
  - falls back to the second provider if one is configured,
  - raises ProviderUnavailable when nothing answered, so callers can escalate.
"""
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError

from src import config

PROMPTS_DIR = config.ROOT / "prompts"
RETRIES = 3
# Groq's free tier allows ~8k tokens a minute per model, about three calls; a
# rate-limited call waits as long as the provider asks (retry-after), up to a
# minute, and is retried more often than other errors.
RATE_LIMIT_RETRIES = 6
MAX_WAIT_S = 65.0


def _retry_after(exc: RateLimitError, attempt: int) -> float:
    try:
        return min(float(exc.response.headers.get("retry-after")) + 1.0, MAX_WAIT_S)
    except (AttributeError, TypeError, ValueError):
        return min(5.0 * 2 ** attempt, MAX_WAIT_S)


class ProviderUnavailable(Exception):
    """No configured provider produced an answer."""


@dataclass(frozen=True)
class Prompt:
    prompt_id: str
    version: str
    system: str
    user: str

    def fill(self, **values) -> list[dict]:
        def sub(template):
            return re.sub(r"\{(\w+)\}", lambda m: str(values[m.group(1)]), template)
        return [{"role": "system", "content": sub(self.system)},
                {"role": "user", "content": sub(self.user)}]


def load_prompt(prompt_id: str) -> Prompt:
    path = next(PROMPTS_DIR.glob(f"*/{prompt_id}.md"))
    text = path.read_text(encoding="utf-8")
    version = re.search(r"^version:\s*(\S+)", text, re.M).group(1)
    system = text.split("SYSTEM:", 1)[1].split("USER:", 1)[0].strip()
    user = text.split("USER:", 1)[1].strip()
    return Prompt(prompt_id, version, system, user)


def _providers() -> list[tuple[str, OpenAI, str]]:
    out = []
    for prefix in ("LLM", "FALLBACK"):
        key = os.getenv(f"{prefix}_API_KEY", "")
        if key and not key.startswith("your_"):
            client = OpenAI(api_key=key, base_url=os.getenv(f"{prefix}_BASE_URL"),
                            timeout=float(os.getenv("LLM_TIMEOUT", 20)), max_retries=0)
            out.append((prefix.lower(), client, os.getenv(f"{prefix}_MODEL")))
    return out


class LLM:
    def __init__(self, cache_dir: str | None = None, providers=None):
        self.cache_dir = (config.path(cache_dir) if cache_dir
                          else config.setting_path("LLM_CACHE_DIR", "./cache/llm"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.providers = _providers() if providers is None else providers

    def _cache_path(self, prompt: Prompt, messages: list[dict]) -> Path:
        key = json.dumps([prompt.prompt_id, prompt.version, messages], sort_keys=True)
        return self.cache_dir / f"{hashlib.sha256(key.encode()).hexdigest()}.json"

    def complete_json(self, prompt: Prompt, **values) -> tuple[dict, dict]:
        """Return (parsed JSON, call info). Raises ProviderUnavailable or ValueError (bad JSON)."""
        messages = prompt.fill(**values)
        path = self._cache_path(prompt, messages)
        if path.exists():
            cached = json.loads(path.read_text(encoding="utf-8"))
            return _parse(cached["content"]), {**cached["info"], "cached": True}

        errors = []
        for name, client, model in self.providers:
            attempt = failures = 0
            while failures < RETRIES and attempt < RATE_LIMIT_RETRIES:
                attempt += 1
                try:
                    resp = client.chat.completions.create(
                        model=model, messages=messages, temperature=0,
                        response_format={"type": "json_object"})
                    content = resp.choices[0].message.content or ""
                    info = {"provider": name, "model": model, "prompt": prompt.prompt_id,
                            "version": prompt.version, "cached": False}
                    parsed = _parse(content)  # raises ValueError before anything is cached
                    path.write_text(json.dumps({"content": content, "info": info}), encoding="utf-8")
                    return parsed, info
                except RateLimitError as exc:
                    errors.append(f"{name}: RateLimitError")
                    time.sleep(_retry_after(exc, attempt))
                except (APITimeoutError, APIConnectionError) as exc:
                    errors.append(f"{name}: {type(exc).__name__}")
                    failures += 1
                    time.sleep(min(2 ** failures, 8))
                except APIStatusError as exc:
                    errors.append(f"{name}: HTTP {exc.status_code}")
                    if exc.status_code < 500:
                        break  # a 4xx will not fix itself on retry; try the next provider
                    failures += 1
                    time.sleep(min(2 ** failures, 8))
        raise ProviderUnavailable("; ".join(errors) or "no provider configured")


def _parse(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("model returned JSON that is not an object")
    return data
