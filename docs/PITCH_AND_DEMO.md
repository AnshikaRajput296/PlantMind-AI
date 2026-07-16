# PlantMind AI — Hackathon Presentation Kit

## Elevator Pitch (30 seconds)
"Industrial companies lose decades of engineering knowledge every time a
senior technician retires, and their teams waste over a third of their time
just searching for the right document. PlantMind AI turns every maintenance
report, inspection log, SOP, and compliance document into a living
Knowledge Graph, queried by ten specialized AI agents instead of one
chatbot — so instead of 'here's a paragraph that mentions your pump,' you
get a root-cause analysis, a risk score, a compliance gap check, and a
cited PDF report, in one conversation."

## One-Paragraph Summary
PlantMind AI is a Unified Asset & Operations Brain for industrial plants.
It ingests maintenance reports, inspection logs, SOPs, P&IDs, work orders,
and compliance documents in any format (including scanned PDFs and images
via OCR), automatically extracts equipment IDs, failure modes, hazards, and
regulatory references, and builds a live Knowledge Graph connecting
equipment, technicians, plants, failure modes, and regulations. A
multi-agent orchestrator — Planner, Knowledge Graph, Vector Search,
Maintenance, Root Cause Analysis, Failure Prediction, Compliance, and
Answer/Report agents — routes every question through the right combination
of structured and unstructured reasoning, with full explainability and
one-click RCA/audit PDF generation.

## Demo Script (5 minutes)
1. **(30s) Open the dashboard.** Point out the live stats: documents
   ingested, graph nodes/relationships, work orders — all populated from
   the seed data, showing this isn't a mockup.
2. **(60s) Expert Copilot.** Ask *"Why did Pump P-101 fail repeatedly?"*
   Narrate the agent trace as it streams: Planner classifies intent →
   Knowledge Graph traverses relationships → Vector Search retrieves
   evidence → Maintenance Agent pulls work-order history → Root Cause
   Agent finds the recurring failure mode → Compliance Agent checks
   standards → Answer Agent cites sources. Show the confidence badge.
3. **(45s) Knowledge Graph Explorer.** Type `EQUIPMENT::P-101`, render the
   graph, show the interactive node relationships. Mention the one-click
   Cypher export for Neo4j production migration.
4. **(45s) Document Intelligence.** Upload a sample scanned image or PDF
   live, show entities extracted in real time, mention it just updated the
   graph automatically.
5. **(45s) Maintenance Intelligence.** Show the recurring-failure-mode chart
   and most-vulnerable-assets chart built from the same data.
6. **(30s) Compliance dashboard.** Run a compliance check, show referenced
   frameworks vs. gaps.
7. **(30s) Generate the RCA PDF report** from the Copilot page — hand the
   judges a real downloadable artifact.
8. **(15s) Close** on the offline-first architecture: "this entire demo
   just ran with zero API keys and zero internet dependency — plug in
   Claude or GPT and the answers get even richer, with no code changes."

## Judge Q&A Prep

**"How is this different from a normal RAG chatbot?"**
A single RAG chatbot retrieves text and paraphrases it. PlantMind AI routes
every query through a Planner that decides which of 10 specialized agents
are relevant, combines structured data (SQL work orders), graph
relationships (Knowledge Graph), and unstructured retrieval (Hybrid RAG),
and produces root-cause analysis, risk scores, and compliance gap
assessments — outputs a chatbot cannot produce because it has no access to
structured maintenance history or asset relationships.

**"Why NetworkX instead of Neo4j / TF-IDF instead of a vector DB?"**
For a hackathon judged live, zero-config reliability matters more than raw
scale. We built to the exact same schema Neo4j would use — the app emits
ready-to-run Cypher (`/graph/cypher-seed`) to migrate directly. Swapping in
FAISS/Qdrant/Milvus is a contained change to one module
(`HybridRetriever`), not a rewrite.

**"Does this actually work without an LLM API key?"**
Yes — that's intentional. The `llm_router` falls back to a deterministic,
evidence-grounded Reasoning Engine so judging never depends on venue wifi
or a live API key. Add `ANTHROPIC_API_KEY` and it upgrades automatically.

**"How would this scale to a real plant with millions of documents?"**
Ingestion becomes an async Celery/Redis queue; the vector index moves to a
sharded FAISS/Qdrant/Milvus cluster; NetworkX moves to a Neo4j cluster
(schema already compatible); FastAPI services are already stateless and
horizontally scalable behind a load balancer/Kubernetes, detailed in
`docs/ARCHITECTURE.md`.

**"What's the business impact?"**
Reducing the reported 35% of time employees spend searching for
information directly recovers labor hours; faster, evidence-grounded root
cause analysis reduces repeat failures and downtime cost (visible directly
in the Maintenance Intelligence dashboard); automated compliance gap
detection reduces audit risk; and the Knowledge Graph captures
retiring engineers' tacit knowledge before it's lost.

## Innovation Points to Emphasize
- Multi-agent orchestration with a visible, auditable reasoning chain (not
  a black box).
- Retrieval-grounded confidence scoring computed from evidence coverage,
  not LLM self-reported certainty.
- Automatic Knowledge Graph construction from unstructured text at
  ingestion time — no manual graph modeling.
- One-click migration path from hackathon-scale to enterprise-scale
  infrastructure (Cypher export, pluggable vector store, pluggable LLM).
- Fully offline-capable demo — resilient to venue connectivity issues.

## Future Scope
- Voice Copilot for field technicians (speech-to-text/text-to-speech
  scaffold is present in the architecture; wire in a streaming ASR/TTS
  provider).
- Computer vision on P&ID diagrams to auto-detect symbols and link them to
  graph nodes.
- Digital twin overlay: real-time sensor feed integration for live
  anomaly detection instead of retrospective analysis.
- Federated deployment across multiple plants with a shared corporate
  Knowledge Graph and per-plant access scoping.
