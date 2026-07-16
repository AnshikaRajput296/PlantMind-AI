"""
LLM Router
----------
Provider-agnostic LLM access layer. Tries providers in this order unless
LLM_PROVIDER pins one explicitly:

  1. Groq             (GROQ_API_KEY set)   -- free, fast, OpenAI-compatible
  2. Anthropic Claude  (ANTHROPIC_API_KEY set)
  3. OpenAI GPT        (OPENAI_API_KEY set)
  4. Ollama (local Llama 3 / Mistral / Gemma)  (if reachable)
  5. Reasoning Engine (Mock) -- deterministic, template-grounded generator
     so the whole platform runs offline with zero API keys, e.g. for
     hackathon judging on venue wifi.

Every agent in the platform calls `generate()` -- swapping models is a
one-line env var change, satisfying the "switch models easily" requirement.
"""
from __future__ import annotations

import requests

from backend import config


def _try_groq(prompt: str, system: str) -> str | None:
    if not config.GROQ_API_KEY:
        return None
    try:
        from openai import OpenAI  # Groq exposes an OpenAI-compatible API
        client = OpenAI(api_key=config.GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
        resp = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            max_tokens=1000,
        )
        return resp.choices[0].message.content
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Groq Error:", repr(e))
        return None


def _try_anthropic(prompt: str, system: str) -> str | None:
    if not config.ANTHROPIC_API_KEY:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=1000,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in resp.content if hasattr(b, "text"))
    except Exception:
        return None


def _try_openai(prompt: str, system: str) -> str | None:
    if not config.OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            max_tokens=1000,
        )
        return resp.choices[0].message.content
    except Exception:
        return None


def _try_ollama(prompt: str, system: str) -> str | None:
    try:
        r = requests.post(
            f"{config.OLLAMA_BASE_URL}/api/generate",
            json={"model": config.OLLAMA_MODEL, "prompt": f"{system}\n\n{prompt}", "stream": False},
            timeout=3,
        )
        if r.status_code == 200:
            return r.json().get("response")
    except Exception:
        return None
    return None


def _mock_reasoning_engine(prompt: str, system: str, context_chunks: list[str] | None = None) -> str:
    """Deterministic, template-grounded synthesis so demos never fail even
    with zero internet / zero API keys. Summarizes retrieved evidence into
    a structured, readable answer."""
    if not context_chunks:
        return ("Based on the platform's current knowledge base, I do not have enough "
                "grounded evidence to answer this precisely. Please upload the relevant "
                "maintenance, inspection, or compliance documents so the Knowledge Graph "
                "and Retrieval Agents can ground a confident answer.")

    bullet_points = []
    for c in context_chunks[:4]:
        snippet = c.strip().replace("\n", " ")
        snippet = snippet[:220] + ("..." if len(snippet) > 220 else "")
        bullet_points.append(f"- {snippet}")

    return (
        "Synthesized from the retrieved evidence across the knowledge base:\n\n"
        + "\n".join(bullet_points)
        + "\n\nThis answer was assembled by the offline Reasoning Engine "
          "(no external LLM key configured). Configure GROQ_API_KEY, "
          "ANTHROPIC_API_KEY, or OPENAI_API_KEY for natural-language synthesis "
          "with full reasoning."
    )


def generate(prompt: str, system: str = "You are an industrial operations AI copilot.",
             context_chunks: list[str] | None = None) -> dict:
    """Returns {"text": ..., "provider": ...}"""
    provider_order = []
    if config.LLM_PROVIDER == "auto":
        provider_order = ["groq", "anthropic", "openai", "ollama", "mock"]
    else:
        provider_order = [config.LLM_PROVIDER, "mock"]

    for provider in provider_order:
        if provider == "groq":
            out = _try_groq(prompt, system)
        elif provider == "anthropic":
            out = _try_anthropic(prompt, system)
        elif provider == "openai":
            out = _try_openai(prompt, system)
        elif provider == "ollama":
            out = _try_ollama(prompt, system)
        elif provider == "mock":
            out = _mock_reasoning_engine(prompt, system, context_chunks)
        else:
            out = None

        if out:
            return {"text": out, "provider": provider}

    return {"text": _mock_reasoning_engine(prompt, system, context_chunks), "provider": "mock"}