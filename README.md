# 🧠 PlantMind AI — Unified Asset & Operations Brain

**An enterprise-grade AI platform for Industrial Knowledge Intelligence.**
Not a PDF chatbot — a multi-agent knowledge system that unifies maintenance
reports, inspection logs, SOPs, compliance documents, and work-order history
into a single queryable Knowledge Graph + Hybrid RAG pipeline, orchestrated
by 10 specialized AI agents.

> Built for hackathon judging: runs **fully offline with zero API keys**
> (a deterministic Reasoning Engine stands in for the LLM), and upgrades
> transparently to Claude / GPT / Ollama the moment you add a key.

---

## 1. What's actually inside this build

This is a **real, runnable prototype** of the architecture described in the
brief — scoped to run on a single laptop with zero paid cloud services, so
it's 100% demoable at a hackathon venue with no wifi. Every "enterprise"
component has a lightweight local stand-in with a clearly marked upgrade
path to the full cloud-scale version:

| Requirement in brief | This build (hackathon-ready) | Production upgrade path |
|---|---|---|
| Neo4j Knowledge Graph | NetworkX (in-memory, JSON-persisted) with **identical node/edge schema** | Swap `GraphStore` internals for `neo4j` driver — `to_cypher_seed()` already emits the Cypher to migrate your data in one paste |
| FAISS / Pinecone / Qdrant / Milvus | Hybrid BM25 + TF-IDF cosine retrieval, RRF fusion, lexical reranking | Swap `HybridRetriever`'s dense index for `sentence-transformers` embeddings + FAISS/Qdrant client |
| Llama 3 / GPT / Claude / Groq | Pluggable `llm_router.py` — auto-detects `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / local Ollama; falls back to an offline template-grounded Reasoning Engine | Just set an env var — no code changes |
| PostgreSQL | SQLite via SQLAlchemy | Change one connection string in `backend/database.py` |
| PaddleOCR / Docling | Tesseract via `pytesseract` (installed automatically in Docker) | Swap OCR backend in `backend/ingestion/ocr.py` |
| Kubernetes / Redis / Celery | Not included (out of scope for a single-laptop hackathon demo) | `docker-compose.yml` included as the first step toward this; architecture doc explains the full path |

**Everything else — the 10-agent orchestrator, knowledge graph construction,
entity extraction, hybrid retrieval with reranking, RCA/prediction/compliance
agents, anomaly detection, PDF report generation, and the full dashboard —
is real, working code, not stubs.**

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Streamlit Frontend (Dark UI)                 │
│  Expert Copilot · Knowledge Graph · Maintenance · Compliance ·   │
│  Analytics · Documents                                            │
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
│ Graph        │ │ (BM25+Dense │ │ (Work Orders,│ │ (Claude/GPT/ │
│ (NetworkX)   │ │  +Rerank)   │ │ Docs,Chunks) │ │ Ollama/Mock) │
└──────────────┘ └─────────────┘ └──────────────┘ └──────────────┘
        ▲
┌───────┴─────────────────────────────────────────────────────────┐
│              Document Intelligence / Ingestion Pipeline           │
│  PDF · Scanned PDF (OCR) · DOCX · XLSX/CSV · Images · TXT/JSON    │
│  → Entity Extraction (Equipment, Pressure, Temp, Dates, Hazards,  │
│    Regulations, Failure causes, Manufacturers, Personnel)         │
└─────────────────────────────────────────────────────────────────┘
```

Full details in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## 3. Step-by-step: run it on your system

### Prerequisites
- Python 3.10+ (3.11 recommended)
- ~2 GB free disk space
- (Optional) Tesseract OCR binary for scanned-document support
- (Optional) An Anthropic or OpenAI API key for full LLM-generated answers —
  **not required**, the platform works without one

### Step 1 — Unzip and enter the project
```bash
unzip industrial-ai-platform.zip
cd industrial-ai-platform
```

### Step 2 — Create a virtual environment
```bash
python3 -m venv venv

# macOS / Linux:
source venv/bin/activate

# Windows (PowerShell):
venv\Scripts\Activate.ps1
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — (Optional but recommended) Install Tesseract OCR
This enables scanned-PDF and P&ID image text extraction. The platform runs
fine without it — OCR calls will just return a friendly notice instead.

```bash
# macOS
brew install tesseract

# Ubuntu / Debian
sudo apt-get update && sudo apt-get install -y tesseract-ocr

# Windows
# Download installer: https://github.com/UB-Mannheim/tesseract/wiki
```

### Step 5 — (Optional) Configure an LLM provider
Copy the example env file and add a key if you want real LLM-generated
answers instead of the offline Reasoning Engine:
```bash
cp .env.example .env
# then edit .env and set ANTHROPIC_API_KEY=sk-ant-... (or OPENAI_API_KEY=...)
```
On macOS/Linux you can also just export it in your shell:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```
**Skip this step entirely for a zero-config demo** — the built-in Reasoning
Engine still produces grounded, cited answers from retrieved evidence.

### Step 6 — Seed the platform with demo data
This loads realistic synthetic maintenance logs, inspection reports, and
SOPs so the dashboard is populated the moment it opens (no manual uploads
needed for a live demo):
```bash
python -m backend.seed_data
```
You should see output confirming work orders and documents were ingested
and the Knowledge Graph was built.

### Step 7 — Start the backend API (Terminal 1)
```bash
uvicorn backend.main:app --reload --port 8000
```
Leave this running. Verify it's up: open `http://localhost:8000/health` —
you should see `{"status": "ok", ...}`. Interactive API docs are at
`http://localhost:8000/docs`.

### Step 8 — Start the dashboard (Terminal 2 — new terminal, same venv)
```bash
# activate the venv again in this new terminal first
streamlit run frontend/app.py
```
Your browser should open automatically to `http://localhost:8501`. If not,
open it manually.

### Step 9 — Try it out
- Go to **💬 Expert Copilot** and click the example question
  *"Why did Pump P-101 fail repeatedly?"* — watch the multi-agent trace.
- Go to **🕸️ Knowledge Graph Explorer**, type `EQUIPMENT::P-101`, click
  **Render Graph** to see the interactive asset graph.
- Go to **📁 Documents** and upload a PDF/image/CSV to watch live ingestion.
- Go to **🔧 Maintenance Intelligence** to see failure trends and log a new
  work order.
- Go to **📊 Analytics** to see Isolation-Forest anomaly detection.
- Generate an **RCA PDF report** directly from the Copilot page.

### (Alternative) Run everything with Docker
```bash
docker compose up --build
```
This builds and starts both the backend (auto-seeded) and frontend. Visit
`http://localhost:8501`.

---

## 4. Project Structure
```
industrial-ai-platform/
├── backend/
│   ├── main.py                  # FastAPI app + all REST endpoints
│   ├── config.py                # Central settings
│   ├── database.py              # SQLAlchemy models (SQLite)
│   ├── seed_data.py              # Demo data loader
│   ├── ingestion/                # Document Intelligence Agent
│   │   ├── document_processor.py # Multi-format parsing + chunking
│   │   ├── extractors.py         # Rule-based entity extraction
│   │   └── ocr.py                # Tesseract OCR wrapper
│   ├── knowledge_graph/
│   │   └── graph_builder.py      # NetworkX graph, PyVis viz, Cypher export
│   ├── retrieval/
│   │   └── hybrid_retriever.py   # BM25 + TF-IDF + RRF + rerank + confidence
│   ├── llm/
│   │   └── llm_router.py         # Anthropic/OpenAI/Ollama/offline router
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── planner_agent.py
│   │   ├── specialist_agents.py  # KG/Vector/Maintenance/RCA/Prediction/Compliance/Answer/Report
│   │   └── orchestrator.py       # Wires the multi-agent pipeline
│   ├── analytics/
│   │   └── anomaly_detection.py  # Isolation Forest
│   └── utils/
│       └── pdf_report.py         # Automated RCA/Audit PDF generation
├── frontend/
│   ├── app.py                    # Executive dashboard (home)
│   ├── theme.py                  # Dark glassmorphism theme + API client
│   └── pages/                    # Copilot, Graph, Maintenance, Compliance, Analytics, Documents
├── sample_data/                  # Synthetic maintenance logs, reports, SOPs
├── docs/                         # Pitch deck content, demo script, judge Q&A, roadmap
├── storage/                      # SQLite DB, graph JSON, uploaded files, generated reports
├── requirements.txt
├── docker-compose.yml
├── Dockerfile.backend / Dockerfile.frontend
└── .env.example
```

---

## 5. Troubleshooting
- **`ModuleNotFoundError`** → make sure the venv is activated and
  `pip install -r requirements.txt` completed without errors.
- **Streamlit page blank / connection refused** → make sure the backend
  (`uvicorn`, port 8000) is running *before* you open the dashboard.
- **OCR returns a placeholder message** → install Tesseract (Step 4) and
  restart the backend.
- **Port already in use** → `uvicorn backend.main:app --port 8001` and
  set `API_BASE=http://localhost:8001` before launching Streamlit.
- **Want real LLM answers instead of the offline Reasoning Engine** →
  set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` and restart the backend.

---

## 6. Hackathon deliverables
See the `docs/` folder for: pitch content, demo script, judge Q&A prep,
architecture deep-dive, innovation/business-value talking points, and
future scope — everything needed to present this end to end.
