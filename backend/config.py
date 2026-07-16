"""
Central configuration for the Unified Asset & Operations Brain platform.
All paths, feature flags, and provider settings live here so the rest
of the codebase never hardcodes a path or a secret.
"""
from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv
load_dotenv()
print("GROQ_API_KEY =", os.getenv("GROQ_API_KEY"))
# ---------------------------------------------------------------------------
# Filesystem layout
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
GRAPH_DIR = STORAGE_DIR / "graph"
REPORTS_DIR = STORAGE_DIR / "reports"
DB_PATH = STORAGE_DIR / "platform.db"
GRAPH_JSON_PATH = GRAPH_DIR / "knowledge_graph.json"

for d in (STORAGE_DIR, UPLOADS_DIR, GRAPH_DIR, REPORTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# LLM provider configuration
# ---------------------------------------------------------------------------
# The platform is provider-agnostic. Set the corresponding environment
# variable to activate a real LLM. If none are set, the LLM Router falls
# back to a deterministic, template-grounded "Reasoning Engine" so the
# whole platform still runs end-to-end with zero API keys (useful for
# offline hackathon demos / judging without internet access).

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto")  # auto | groq | anthropic | openai | ollama | mock
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ---------------------------------------------------------------------------
# Retrieval configuration
# ---------------------------------------------------------------------------
CHUNK_SIZE = 700
CHUNK_OVERLAP = 120
TOP_K_DENSE = 8
TOP_K_SPARSE = 8
TOP_K_FINAL = 6

# ---------------------------------------------------------------------------
# Compliance reference set (used by Compliance Agent)
# ---------------------------------------------------------------------------
COMPLIANCE_FRAMEWORKS = ["ISO 9001", "ISO 45001", "ISO 14001", "Factory Act", "OISD", "PESO"]

# ---------------------------------------------------------------------------
# RBAC roles
# ---------------------------------------------------------------------------
ROLES = ["Admin", "Engineer", "Manager", "Auditor", "Operator"]

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))