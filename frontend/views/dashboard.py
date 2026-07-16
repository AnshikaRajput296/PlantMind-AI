import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from theme import (inject_theme, api_get, page_header, kpi_card, agent_card,
                    chart_card_open, chart_card_close)

inject_theme()

right_html = """
<div style="display:flex;gap:8px;align-items:center;">
    <span style="font-size:13.5px;color:var(--text-secondary);border:1px solid var(--border);
                 border-radius:8px;padding:7px 12px;background:var(--surface);">Last 30 days</span>
</div>
"""
page_header("Unified Asset & Operations Brain",
            "Industrial Knowledge Intelligence Platform", right_html)

stats = api_get("/stats")

if stats:
    kpi_defs = [
        ("Documents Ingested", stats["documents"], "description"),
        ("Knowledge Chunks", stats["chunks"], "data_object"),
        ("Work Orders", stats["work_orders"], "assignment"),
        ("Graph Nodes", stats["graph"]["total_nodes"], "hub"),
        ("Graph Relationships", stats["graph"]["total_edges"], "share"),
    ]
    cols = st.columns(5)
    for (label, value, icon), col in zip(kpi_defs, cols):
        with col:
            kpi_card(label, value, icon)

    st.markdown('<div class="section-title">Knowledge Graph Composition</div>', unsafe_allow_html=True)
    g = stats["graph"]
    c1, c2 = st.columns(2)
    with c1:
        chart_card_open("Nodes by Type")
        if g["nodes_by_label"]:
            st.bar_chart(g["nodes_by_label"], color="#2563EB")
        else:
            st.caption("No data yet. Upload documents or run the seed script.")
        chart_card_close()
    with c2:
        chart_card_open("Relationships by Type")
        if g["edges_by_relation"]:
            st.bar_chart(g["edges_by_relation"], color="#2563EB")
        else:
            st.caption("No data yet.")
        chart_card_close()
else:
    st.warning("Could not reach the backend API. Make sure it's running on port 8000.")

st.markdown('<div class="section-title">Multi-Agent Architecture</div>', unsafe_allow_html=True)
agents_info = [
    ("Planner Agent", "Classifies intent and builds the execution plan", "route"),
    ("Document Intelligence", "Multi-format ingestion, OCR, entity extraction", "description"),
    ("Knowledge Graph Agent", "Traverses asset relationships", "hub"),
    ("Vector Search Agent", "Hybrid BM25 and dense retrieval with reranking", "manage_search"),
    ("Maintenance Agent", "Structured work-order history retrieval", "build"),
    ("Root Cause Analysis", "Failure pattern and causal analysis", "troubleshoot"),
    ("Failure Prediction", "Risk score and remaining useful life", "trending_up"),
    ("Compliance Agent", "ISO, OISD, PESO, and Factory Act gap checks", "verified"),
    ("Answer Generator", "Grounded, cited final synthesis", "smart_toy"),
    ("Report Generator", "Automated RCA and audit PDF reports", "summarize"),
]
cols = st.columns(5)
for i, (name, desc, icon) in enumerate(agents_info):
    with cols[i % 5]:
        agent_card(name, desc, icon)

st.info("Use the sidebar to open the Expert Copilot, explore the knowledge graph, "
        "review maintenance intelligence, run compliance checks, and view analytics.")