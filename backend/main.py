"""
FastAPI Backend -- Unified Asset & Operations Brain
-----------------------------------------------------
Exposes REST endpoints consumed by the Streamlit dashboard (or any other
client / mobile app). Run with:

    uvicorn backend.main:app --reload --port 8000
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend import config
from backend.database import init_db, get_session, Document, Chunk, WorkOrder, Incident, Equipment
from backend.ingestion.document_processor import process_document, chunk_text
from backend.knowledge_graph.graph_builder import GraphStore, build_graph_from_ingestion, render_pyvis_html
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.agents.orchestrator import Orchestrator
from backend.analytics.anomaly_detection import detect_anomalies
from backend.utils.pdf_report import generate_rca_report

app = FastAPI(title="Unified Asset & Operations Brain API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

init_db()
graph_store = GraphStore()
retriever = HybridRetriever()
orchestrator = Orchestrator(graph_store, retriever)


def _rebuild_retriever_index():
    session = get_session()
    try:
        chunks = session.query(Chunk).all()
        docs = {d.id: d for d in session.query(Document).all()}
        index_data = [{
            "chunk_id": c.id, "document_id": c.document_id,
            "filename": docs[c.document_id].filename if c.document_id in docs else "unknown",
            "category": docs[c.document_id].category if c.document_id in docs else "General",
            "child_text": c.text, "parent_text": c.parent_text,
        } for c in chunks]
        retriever.index(index_data)
    finally:
        session.close()


_rebuild_retriever_index()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    query: str


class WorkOrderIn(BaseModel):
    equipment_tag: str
    date: str
    technician: str
    description: str
    failure_mode: str = ""
    downtime_hours: float = 0.0
    cost: float = 0.0


# ---------------------------------------------------------------------------
# Health / stats
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "platform": "Unified Asset & Operations Brain"}


@app.get("/stats")
def platform_stats():
    session = get_session()
    try:
        n_docs = session.query(Document).count()
        n_chunks = session.query(Chunk).count()
        n_wo = session.query(WorkOrder).count()
        n_incidents = session.query(Incident).count()
    finally:
        session.close()
    return {
        "documents": n_docs, "chunks": n_chunks, "work_orders": n_wo,
        "incidents": n_incidents, "graph": graph_store.stats(),
    }


# ---------------------------------------------------------------------------
# Document Intelligence Agent endpoints
# ---------------------------------------------------------------------------
@app.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    dest = config.UPLOADS_DIR / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        ingested = process_document(dest)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process document: {e}")

    session = get_session()
    try:
        doc = Document(
            filename=ingested.filename, doc_type=ingested.doc_type, category=ingested.category,
            raw_text_path=str(dest), summary=ingested.raw_text[:500],
            entity_json=json.dumps(ingested.entities.to_dict()),
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)

        for idx, (child, parent) in enumerate(chunk_text(ingested.raw_text)):
            session.add(Chunk(document_id=doc.id, chunk_index=idx, text=child, parent_text=parent))
        session.commit()

        build_graph_from_ingestion(graph_store, doc.id, ingested.filename,
                                    ingested.category, ingested.entities.to_dict())
        _rebuild_retriever_index()

        return {
            "document_id": doc.id, "filename": doc.filename, "category": doc.category,
            "entities": ingested.entities.to_dict(),
            "chunks_created": len(chunk_text(ingested.raw_text)),
        }
    finally:
        session.close()


@app.get("/documents")
def list_documents():
    session = get_session()
    try:
        docs = session.query(Document).order_by(Document.uploaded_at.desc()).all()
        return [{
            "id": d.id, "filename": d.filename, "category": d.category,
            "doc_type": d.doc_type, "uploaded_at": str(d.uploaded_at),
            "entities": json.loads(d.entity_json) if d.entity_json else {},
        } for d in docs]
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Structured data endpoints (Work Orders / Incidents / Equipment)
# ---------------------------------------------------------------------------
@app.post("/work-orders")
def add_work_order(wo: WorkOrderIn):
    session = get_session()
    try:
        rec = WorkOrder(**wo.dict())
        session.add(rec)
        session.commit()

        eq_node = f"EQUIPMENT::{wo.equipment_tag}"
        graph_store.add_node(eq_node, "Equipment", tag=wo.equipment_tag)
        tech_node = f"TECH::{wo.technician.upper()}"
        graph_store.add_node(tech_node, "Technician", name=wo.technician)
        graph_store.add_edge(tech_node, eq_node, "maintained_by")
        if wo.failure_mode:
            fail_node = f"FAILMODE::{wo.failure_mode.upper()}"
            graph_store.add_node(fail_node, "FailureMode", name=wo.failure_mode)
            graph_store.add_edge(eq_node, fail_node, "caused_failure")
        graph_store.save()
        return {"status": "created", "id": rec.id}
    finally:
        session.close()


@app.get("/work-orders")
def list_work_orders(equipment_tag: str | None = None):
    session = get_session()
    try:
        q = session.query(WorkOrder)
        if equipment_tag:
            q = q.filter(WorkOrder.equipment_tag == equipment_tag)
        rows = q.order_by(WorkOrder.date.desc()).all()
        return [{
            "id": r.id, "equipment_tag": r.equipment_tag, "date": r.date,
            "technician": r.technician, "description": r.description,
            "failure_mode": r.failure_mode, "downtime_hours": r.downtime_hours, "cost": r.cost,
        } for r in rows]
    finally:
        session.close()


@app.get("/equipment")
def list_equipment():
    graph_eq = graph_store.find_by_label("Equipment")
    return graph_eq


# ---------------------------------------------------------------------------
# Knowledge Graph endpoints
# ---------------------------------------------------------------------------
@app.get("/graph/stats")
def graph_stats():
    return graph_store.stats()


@app.get("/graph/full")
def graph_full():
    return graph_store.full_graph_json()


@app.get("/graph/neighbors/{node_id}")
def graph_neighbors(node_id: str, hops: int = 2):
    return graph_store.query_neighbors(node_id, hops=hops)


@app.get("/graph/visualize")
def graph_visualize(focus: str | None = None, hops: int = 2):
    out_path = str(config.GRAPH_DIR / "graph_view.html")
    focus_found = bool(focus) and (focus in graph_store.g)
    render_pyvis_html(graph_store, out_path, focus_node=focus, hops=hops)
    return {
        "html_path": out_path,
        "focus_requested": focus,
        "focus_found": focus_found if focus else None,
    }


@app.get("/graph/cypher-seed")
def graph_cypher_seed():
    return {"cypher": graph_store.to_cypher_seed()}


@app.get("/graph/nodes")
def graph_nodes(label: str | None = None):
    """Lists node IDs currently in the graph, optionally filtered by label
    (e.g. Equipment, Technician). Useful for confirming the exact node ID
    to use with /graph/visualize?focus=... or /graph/neighbors/{node_id}."""
    if label:
        return graph_store.find_by_label(label)
    return [{"id": n, **d} for n, d in graph_store.g.nodes(data=True)]


# ---------------------------------------------------------------------------
# Multi-Agent Orchestrator endpoint (the core "brain" query)
# ---------------------------------------------------------------------------
@app.post("/ask")
def ask(req: QueryRequest):
    ctx = orchestrator.handle_query(req.query)
    return {
        "query": req.query,
        "answer": ctx.data.get("final_answer"),
        "llm_provider": ctx.data.get("llm_provider"),
        "confidence": ctx.data.get("confidence"),
        "intent": ctx.data.get("intent"),
        "equipment_focus": ctx.data.get("equipment_focus"),
        "sources": [{"filename": c.filename, "category": c.category, "score": c.score}
                    for c in ctx.data.get("retrieved_chunks", [])],
        "rca": ctx.data.get("rca"),
        "prediction": ctx.data.get("prediction"),
        "compliance": ctx.data.get("compliance"),
        "graph_context": ctx.data.get("graph_context"),
        "trace": ctx.trace,
        "ctx_data_for_report": {**ctx.data, "trace": ctx.trace,
                                 "retrieved_chunks": [c.__dict__ for c in ctx.data.get("retrieved_chunks", [])]},
    }


# ---------------------------------------------------------------------------
# Analytics endpoints
# ---------------------------------------------------------------------------
@app.get("/analytics/anomalies")
def anomalies():
    session = get_session()
    try:
        rows = session.query(WorkOrder).all()
        data = [{
            "equipment_tag": r.equipment_tag, "date": r.date,
            "downtime_hours": r.downtime_hours, "cost": r.cost,
        } for r in rows]
    finally:
        session.close()
    return detect_anomalies(data)


# ---------------------------------------------------------------------------
# Report generation endpoint
# ---------------------------------------------------------------------------
class ReportRequest(BaseModel):
    query: str
    ctx_data: dict


@app.post("/report/generate")
def report_generate(req: ReportRequest):
    path = generate_rca_report(req.query, req.ctx_data)
    return {"report_path": path, "filename": Path(path).name}