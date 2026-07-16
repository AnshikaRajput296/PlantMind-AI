# Architecture Deep Dive — PlantMind AI

## Design Philosophy
A single RAG chatbot answers "what does the document say." PlantMind AI
answers "why did it fail, who's affected, is it compliant, what's the risk,
and what should we do" — because the question is routed through specialized
agents that each reason over a different slice of the organization's
knowledge (unstructured text, structured work orders, the relationship
graph, and regulatory frameworks) before a final answer is synthesized.

## Layers

**1. Ingestion Layer** — `backend/ingestion/`
Normalizes any industrial document format into plain text, then runs a
rule-based entity extractor tuned for industrial vocabulary (equipment tags
like `P-101`, pressure/temperature readings, regulatory codes, hazard
keywords, failure-mode keywords, manufacturers, personnel, plant/unit
references). Scanned PDFs are rasterized page-by-page and OCR'd
automatically when no embedded text layer is found.

**2. Knowledge Graph Layer** — `backend/knowledge_graph/`
Every ingested document and structured work order updates a live graph:
`Equipment -[belongs_to]-> Plant`, `Technician -[maintained_by]-> Equipment`,
`Equipment -[caused_failure]-> FailureMode`, `Document -[references]->
Regulation`, etc. This lets the platform answer relationship questions
("which technicians have worked on assets with unresolved compliance gaps")
that a flat vector index cannot.

**3. Hybrid Retrieval Layer** — `backend/retrieval/`
Combines BM25 (sparse/lexical) and TF-IDF cosine similarity (dense-style)
with Reciprocal Rank Fusion, then reranks with a lexical/entity-overlap
scorer. Multi-query expansion and a HyDE-lite hypothesis variant improve
recall on natural-language questions. A grounded-confidence score and
hallucination-risk flag are computed from retrieval coverage, not from the
LLM's own self-report — this makes the confidence signal auditable.

**4. Multi-Agent Orchestration Layer** — `backend/agents/`
The Planner classifies intent (root cause / prediction / compliance /
maintenance history / lessons learned / report / general) and assembles a
plan of specialist agents. Each agent writes to a shared `AgentContext`
including a human-readable trace entry — this trace *is* the explainability
layer surfaced in the UI, not a bolted-on SHAP call.

**5. LLM Layer** — `backend/llm/`
Provider-agnostic. Tries Anthropic → OpenAI → local Ollama → offline
Reasoning Engine, in that order, controllable via `LLM_PROVIDER`. The
offline engine guarantees the platform is always demoable, even without
internet access at a hackathon venue.

**6. Presentation Layer** — `frontend/`
Streamlit multipage app: Expert Copilot (chat + agent trace + citations +
confidence + one-click PDF report), Knowledge Graph Explorer (PyVis
interactive graph + Cypher export for Neo4j migration), Maintenance
Intelligence (failure trend charts, work-order logging), Compliance
dashboard, Analytics (Isolation Forest anomaly detection), and Document
Intelligence (drag-and-drop ingestion with live entity extraction preview).

## Data Flow: "Why did Pump P-101 fail repeatedly?"
1. Planner Agent classifies intent as `root_cause`, detects equipment focus `P-101`.
2. Knowledge Graph Agent traverses 2 hops from `EQUIPMENT::P-101` — pulls
   linked failure modes, technicians, plant, manufacturer, regulations.
3. Vector Search Agent retrieves the top-ranked passages from maintenance
   and inspection reports mentioning P-101, with confidence scoring.
4. Maintenance Agent pulls the structured work-order history for P-101 from SQLite.
5. Root Cause Agent aggregates failure-mode frequency across the work
   orders and cross-references graph-linked failure modes.
6. Compliance Agent checks which regulatory frameworks are referenced in
   the retrieved evidence and flags frameworks with no supporting documentation.
7. Answer Agent synthesizes all of the above into one grounded, cited answer.
8. (On request) Report Agent renders the full trace into a PDF.

## Scaling to production
- **Neo4j**: `GraphStore.to_cypher_seed()` already emits the migration script.
- **Vector DB**: swap `HybridRetriever`'s TF-IDF matrix for FAISS/Qdrant/
  Milvus with `sentence-transformers` embeddings — the Agent-facing
  `.retrieve()` interface is unchanged.
- **Postgres**: one connection-string change in `backend/database.py`.
- **Async/queue**: wrap `/documents/upload` in a Celery task for large-batch
  ingestion; return a job ID immediately.
- **Kubernetes**: both `Dockerfile.backend` and `Dockerfile.frontend` are
  already stateless and horizontally scalable behind a load balancer, with
  `storage/` moved to a shared volume or S3-compatible object store.
- **RBAC**: `config.ROLES` defines the role set; wire JWT middleware into
  FastAPI (`fastapi-users` or a custom `Depends`) for production auth.
