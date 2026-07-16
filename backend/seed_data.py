"""
Seed Script
-----------
Populates the platform with realistic synthetic industrial data so the
dashboard is instantly demo-ready after setup: no manual uploads needed
for judges to see the full pipeline working.

Run:  python -m backend.seed_data
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from backend.config import BASE_DIR
from backend.database import init_db, get_session, Document, Chunk, WorkOrder
from backend.ingestion.document_processor import process_document, chunk_text
from backend.knowledge_graph.graph_builder import GraphStore, build_graph_from_ingestion

SAMPLE_DIR = BASE_DIR / "sample_data"


def seed():
    init_db()
    session = get_session()
    graph = GraphStore()

    # 1) Load structured work orders from CSV
    csv_path = SAMPLE_DIR / "work_orders.csv"
    if csv_path.exists() and session.query(WorkOrder).count() == 0:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                wo = WorkOrder(
                    equipment_tag=row["equipment_tag"], date=row["date"],
                    technician=row["technician"], description=row["description"],
                    failure_mode=row["failure_mode"],
                    downtime_hours=float(row["downtime_hours"]), cost=float(row["cost"]),
                )
                session.add(wo)
                eq_node = f"EQUIPMENT::{row['equipment_tag']}"
                graph.add_node(eq_node, "Equipment", tag=row["equipment_tag"])
                tech_node = f"TECH::{row['technician'].upper()}"
                graph.add_node(tech_node, "Technician", name=row["technician"])
                graph.add_edge(tech_node, eq_node, "maintained_by")
                if row["failure_mode"] and row["failure_mode"] != "none":
                    fail_node = f"FAILMODE::{row['failure_mode'].upper()}"
                    graph.add_node(fail_node, "FailureMode", name=row["failure_mode"])
                    graph.add_edge(eq_node, fail_node, "caused_failure")
        session.commit()
        print(f"Seeded {csv_path.name}: work orders loaded.")

    # 2) Ingest unstructured sample documents (reports, SOPs)
    if session.query(Document).count() == 0:
        for path in sorted(SAMPLE_DIR.glob("*.txt")):
            ingested = process_document(path)
            doc = Document(
                filename=ingested.filename, doc_type=ingested.doc_type, category=ingested.category,
                raw_text_path=str(path), summary=ingested.raw_text[:500],
                entity_json=json.dumps(ingested.entities.to_dict()),
            )
            session.add(doc)
            session.commit()
            session.refresh(doc)

            for idx, (child, parent) in enumerate(chunk_text(ingested.raw_text)):
                session.add(Chunk(document_id=doc.id, chunk_index=idx, text=child, parent_text=parent))
            session.commit()

            build_graph_from_ingestion(graph, doc.id, ingested.filename,
                                        ingested.category, ingested.entities.to_dict())
            print(f"Ingested {path.name} -> category '{ingested.category}', "
                  f"{len(ingested.entities.equipment_ids)} equipment IDs found.")

    graph.save()
    session.close()
    print("\nSeed complete. Start the platform with:\n"
          "  uvicorn backend.main:app --reload --port 8000\n"
          "  streamlit run frontend/app.py")


if __name__ == "__main__":
    seed()
