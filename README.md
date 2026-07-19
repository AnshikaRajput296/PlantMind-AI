# PlantMind AI

### Unified Asset & Operations Brain — Industrial Knowledge Intelligence Platform

An enterprise-grade, multi-agent AI platform that turns scattered industrial
documents — maintenance reports, inspection logs, SOPs, compliance records,
and work orders — into a single, queryable knowledge system. Built for the
**AI for Industrial Knowledge Intelligence** hackathon theme.

Not a PDF chatbot. A live Knowledge Graph, a hybrid retrieval engine, and
**10 specialized AI agents** working together to deliver root-cause analysis,
failure prediction, and compliance auditing — with every answer fully
explainable and cited.

---

## Table of Contents
- [Problem Statement](#problem-statement)
- [What This Platform Does](#what-this-platform-does)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Screenshots](#screenshots)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [How the Multi-Agent Pipeline Works](#how-the-multi-agent-pipeline-works)
- [Configuration](#configuration)
- [Roadmap](#roadmap)
- [License](#license)

---

## Problem Statement

Industrial companies lose an estimated **35% of employee time** searching for
information scattered across maintenance reports, inspection logs, P&ID
drawings, SOPs, compliance documents, spreadsheets, and emails. When senior
engineers retire, decades of undocumented operational knowledge disappear
with them. PlantMind AI addresses this by building a continuously
self-updating "knowledge brain" that understands every document, every
asset, and every relationship between them.

## What This Platform Does

1. **Ingests** any industrial document format — PDF (native or scanned),
   DOCX, XLSX/CSV, images, and text — and automatically extracts structured
   entities: equipment IDs, pressure/temperature readings, hazards,
   regulatory codes, failure causes, personnel, and manufacturers.
2. **Builds a live Knowledge Graph** connecting Equipment, Technicians,
   Plants, Failure Modes, Regulations, and Documents.
3. **Answers natural-language questions** by routing them through a
   multi-agent pipeline — not a single LLM call — combining structured data
   (work-order history), graph relationships, and hybrid document retrieval.
4. **Produces grounded, cited answers** with a confidence score, a visible
   agent reasoning chain, and one-click downloadable RCA/audit PDF reports.
5. **Flags anomalies** in maintenance patterns using Isolation Forest, and
   surfaces recurring failure trends across the asset fleet.

## Key Features

| Capability | Description |
|---|---|
| **Multi-format ingestion** | PDF, scanned PDF (OCR), DOCX, XLSX, CSV, images, TXT, JSON |
| **Automatic entity extraction** | Equipment IDs, pressure, temperature, dates, hazards, regulations, failure modes, manufacturers, personnel |
| **Live Knowledge Graph** | Auto-built and updated on every ingestion; Neo4j-compatible schema |
| **Hybrid RAG retrieval** | BM25 + dense retrieval, Reciprocal Rank Fusion, reranking, multi-query expansion, parent-child chunking |
| **10 specialized AI agents** | Planner, Document Intelligence, Knowledge Graph, Vector Search, Maintenance, Root Cause Analysis, Failure Prediction, Compliance, Answer Generator, Report Generator |
| **Explainable AI** | Every answer includes a visible, step-by-step agent reasoning trace |
| **Confidence & hallucination scoring** | Computed from retrieval evidence coverage, not LLM self-report |
| **Compliance auditing** | Cross-checks documents against ISO 9001, ISO 45001, ISO 14001, Factory Act, OISD, PESO |
| **Anomaly detection** | Isolation Forest over downtime, cost, and maintenance frequency |
| **Automated PDF reports** | One-click RCA / audit report generation |
| **Pluggable LLM router** | Groq, Anthropic Claude, OpenAI, local Ollama, or a fully offline Reasoning Engine — zero API keys required to run |
| **Enterprise UI** | Light, professional dashboard (Linear / Notion / Azure Portal style) — no emojis, no dark "hacker" theme |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Streamlit Frontend (Light UI)                 │
│  Dashboard · Expert Copilot · Knowledge Graph · Maintenance ·    │
│  Compliance · Analytics · Documents                               │
└───────────────────────────┬───────────────────────────────────────┘
                             │ REST (FastAPI)
┌───────────────────────────▼───────────────────────────────────────┐
│                      Multi-Agent Orchestrator                     │
│  Planner → [KnowledgeGraph, VectorSearch, Maintenance, RootCause, │
│             Prediction, Compliance] → Answer → Report              │
└───────┬───────────────┬───────────────┬───────────────┬───────────┘
        │               │               │               │
┌───────▼─────┐ ┌───────▼─────┐ ┌───────▼─────┐ ┌───────▼─────┐
│ Knowledge    │ │ Hybrid RAG  │ │ SQLite       │ │ LLM Router   │
│ Graph        │ │ (BM25+Dense │ │ (Work Orders,│ │ (Groq/Claude/│
│ (NetworkX)   │ │  +Rerank)   │ │ Docs,Chunks) │ │ GPT/Ollama)  │
└──────────────┘ └─────────────┘ └──────────────┘ └──────────────┘
        ▲
┌───────┴─────────────────────────────────────────────────────────┐
│              Document Intelligence / Ingestion Pipeline           │
│  PDF · Scanned PDF (OCR) · DOCX · XLSX/CSV · Images · TXT/JSON    │
│  → Rule-based Entity Extraction                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Tech Stack

**Backend:** FastAPI, SQLAlchemy (SQLite), NetworkX, PyVis, scikit-learn,
rank-bm25, PyMuPDF, python-docx, openpyxl, pytesseract, ReportLab

**Frontend:** Streamlit (`st.navigation`), Plotly

**AI / LLM:** Pluggable router — Groq, Anthropic Claude, OpenAI GPT, local
Ollama, or an offline template-grounded Reasoning Engine

**ML:** Isolation Forest (anomaly detection), BM25 + TF-IDF hybrid
retrieval with Reciprocal Rank Fusion and lexical reranking

## Screenshots
The following screenshots showcase the core capabilities of **PlantMind AI**, including document intelligence, multi-agent reasoning, knowledge graph exploration, maintenance analytics, compliance validation, and automated reporting.<br>

### Dashboard Overview
<img width="1917" height="867" alt="image" src="https://github.com/user-attachments/assets/791e2436-c6ec-4562-95f1-8636388dd550" />
<img width="1562" height="476" alt="image" src="https://github.com/user-attachments/assets/14d075dc-e251-41cc-9ce1-30a4466f1808" />

### Expert Copilot
<img width="1917" height="872" alt="image" src="https://github.com/user-attachments/assets/1ecc04b8-83b3-4e60-bec6-920bc2420140" />

### Knowledge Graph Explorer
<img width="1917" height="872" alt="image" src="https://github.com/user-attachments/assets/2f4af928-971d-4c9e-b251-71617c2f9044" />
<img width="1917" height="870" alt="image" src="https://github.com/user-attachments/assets/38022dbb-b3c8-4dce-aeb1-288943422049" />

### Compliance Agent
<img width="1917" height="867" alt="Screenshot 2026-07-19 131451" src="https://github.com/user-attachments/assets/9ae7898b-ade3-4fb8-92b0-5e758edaa0da" />

### Analytics Agent
<img width="1917" height="866" alt="image" src="https://github.com/user-attachments/assets/87d8f820-49e9-47cb-bc8e-1a57744c92e5" />

### Document Intelligence
<img width="1917" height="871" alt="image" src="https://github.com/user-attachments/assets/a914927d-9712-4fa9-babb-b79284dc3491" />

## Getting Started

### Prerequisites
- Python 3.10–3.12 (3.11 recommended)
- ~2 GB free disk space
- (Optional) Tesseract OCR for scanned documents
- (Optional) A free [Groq API key](https://console.groq.com) for natural-language answers

### Installation

```bash
git clone https://github.com/<your-username>/plantmind-ai.git
cd plantmind-ai

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### (Optional) Enable an LLM provider
```bash
cp .env.example .env
# edit .env and set GROQ_API_KEY=gsk_...
```
Skip this step to run fully offline — the platform still produces
grounded, cited answers via the built-in Reasoning Engine.

### Seed demo data
```bash
python -m backend.seed_data
```

### Run
```bash
# Terminal 1
uvicorn backend.main:app --reload --port 8000

# Terminal 2
streamlit run frontend/app.py
```
Open `http://localhost:8501`.

### Docker (alternative)
```bash
docker compose up --build
```

### Troubleshooting
- **`ModuleNotFoundError`** — activate the venv and re-run `pip install -r requirements.txt`.
- **Frontend loads but shows no data** — make sure the backend (port 8000) is running first, and that `python -m backend.seed_data` completed successfully.
- **OCR returns a placeholder message** — install Tesseract (`sudo apt-get install tesseract-ocr` / `brew install tesseract` / [Windows installer](https://github.com/UB-Mannheim/tesseract/wiki)).
- **Answers say `LLM Provider: mock`** — expected with no API key configured; this is the offline Reasoning Engine, not an error. Add `GROQ_API_KEY` to `.env` for natural-language synthesis.

## Project Structure

```
plantmind-ai/
├── backend/
│   ├── main.py                   # FastAPI app + REST endpoints
│   ├── config.py                 # Settings, .env loading
│   ├── database.py               # SQLAlchemy models
│   ├── seed_data.py              # Demo data loader
│   ├── ingestion/                # Document parsing, OCR, entity extraction
│   ├── knowledge_graph/          # Graph builder, PyVis viz, Cypher export
│   ├── retrieval/                # Hybrid BM25 + dense retriever
│   ├── llm/                      # Pluggable LLM router
│   ├── agents/                   # Planner + 9 specialist agents + orchestrator
│   ├── analytics/                # Isolation Forest anomaly detection
│   └── utils/                    # PDF report generation
├── frontend/
│   ├── app.py                    # st.navigation entry point
│   ├── theme.py                  # Design system (light enterprise theme)
│   └── views/                    # Dashboard, Copilot, Graph, Maintenance, Compliance, Analytics, Documents
├── sample_data/                  # Synthetic maintenance logs, reports, SOPs
├── docs/                         # Architecture deep-dive, pitch, demo script
├── storage/                      # Generated: SQLite DB, graph JSON, reports
├── requirements.txt
├── docker-compose.yml
└── .env.example
```

## How the Multi-Agent Pipeline Works

Example query: *"Why did Pump P-101 fail repeatedly?"*

1. **Planner Agent** classifies intent as `root_cause`, detects equipment focus `P-101`.
2. **Knowledge Graph Agent** traverses relationships around `P-101` (technicians, failure modes, plant, manufacturer).
3. **Vector Search Agent** retrieves relevant passages via hybrid BM25 + dense retrieval with reranking and confidence scoring.
4. **Maintenance Agent** pulls the structured work-order history from SQLite.
5. **Root Cause Analysis Agent** aggregates failure-mode frequency and cross-references the graph.
6. **Compliance Agent** checks which regulatory frameworks are referenced and flags gaps.
7. **Answer Generator Agent** synthesizes everything into one grounded, cited response.
8. **Report Generator Agent** (on request) renders the full trace into a downloadable PDF.

Every step is logged and shown to the user as an explainable reasoning chain.

## Configuration

All settings are controlled via `.env` (copy from `.env.example`):

| Variable | Purpose |
|---|---|
| `LLM_PROVIDER` | `auto` \| `groq` \| `anthropic` \| `openai` \| `ollama` \| `mock` |
| `GROQ_API_KEY` | Free tier at console.groq.com (recommended) |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` | Alternative LLM providers |
| `OLLAMA_BASE_URL` | For fully local LLM inference |
| `API_BASE` | Frontend → backend URL (default `http://localhost:8000`) |

No key is required — the platform runs fully offline via a deterministic,
evidence-grounded Reasoning Engine when none is configured.

## Roadmap

- Voice Copilot for field technicians (speech-to-text / text-to-speech)
- Computer vision on P&ID diagrams with automatic symbol-to-graph linking
- Real-time sensor feed integration for live (not retrospective) anomaly detection
- Multi-plant federated deployment with per-plant access scoping
- Production migration to Neo4j, PostgreSQL, and a distributed vector store (migration path already documented in `docs/ARCHITECTURE.md`)

## License

This project was built for hackathon submission. Consider adding a license
(MIT is a common permissive default for hackathon projects) before making
the repository public.
