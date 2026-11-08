"""Connectivity check: confirm the model provider in .env answers.

Run from the repo root:  python scripts/check_llm.py
"""
import os
import sys
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.environ.get("LLM_API_KEY", "")
if not api_key or api_key == "your_groq_key_here":
    sys.exit("LLM_API_KEY is not set. Copy .env.example to .env and add your key.")

client = OpenAI(api_key=api_key, base_url=os.environ["LLM_BASE_URL"], timeout=30)
model = os.environ["LLM_MODEL"]

start = time.perf_counter()
response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Reply with the word ready."}],
    temperature=0,
)
elapsed = time.perf_counter() - start

print(f"model:   {model}")
print(f"reply:   {response.choices[0].message.content.strip()}")
print(f"latency: {elapsed:.2f}s")
