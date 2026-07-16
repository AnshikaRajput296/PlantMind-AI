import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from theme import inject_theme, api_get, page_header, kpi_card, chart_card_open, chart_card_close

inject_theme()
page_header("Knowledge Graph Explorer",
            "Unified Asset Graph — Equipment, Technicians, Plants, Failure Modes, "
            "Regulations, and Documents.")

stats = api_get("/graph/stats")
if stats:
    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Total Nodes", stats["total_nodes"], "hub")
    with c2:
        kpi_card("Total Relationships", stats["total_edges"], "share")
    with c3:
        kpi_card("Node Types", len(stats["nodes_by_label"]), "category")

chart_card_open("Graph Visualization")
focus = st.text_input("Focus on a node (e.g. EQUIPMENT::P-101) — leave blank for full graph")
render_hops = st.slider("Relationship depth (hops)", 1, 3, 1,
                         help="1 hop = only direct relationships (technicians, failure modes, plant, "
                              "manufacturer). 2+ hops will also pull in other equipment connected "
                              "through a shared technician or document, which can look dense.")
if st.button("Render Graph"):
    params = {"focus": focus, "hops": render_hops} if focus else {}
    result = api_get("/graph/visualize", params=params)
    if result:
        if focus and result.get("focus_found") is False:
            st.warning(f"'{focus}' was not found in the graph, so the full graph is shown below "
                       f"instead. Check the exact spelling in the equipment list below — node IDs "
                       f"are case-sensitive.")
        html_path = result["html_path"]
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read()
            st.components.v1.html(html, height=620, scrolling=True)
        except FileNotFoundError:
            st.warning("Graph not yet generated. Ingest some documents first.")
chart_card_close()

chart_card_open("Available Equipment Nodes")
st.caption("Use one of these exact IDs in the focus box above.")
eq_nodes = api_get("/graph/nodes", params={"label": "Equipment"})
if eq_nodes:
    tag_list = ", ".join(f"EQUIPMENT::{n.get('tag', n['id'].split('::')[-1])}" for n in eq_nodes)
    st.code(tag_list, language=None)
else:
    st.caption("No equipment nodes yet.")
chart_card_close()

chart_card_open("Equipment Neighborhood Lookup")
eq_tag = st.text_input("Equipment tag", value="P-101")
hops = st.slider("Hops", 1, 3, 2)
if st.button("Query Neighbors"):
    node_id = f"EQUIPMENT::{eq_tag}"
    neigh = api_get(f"/graph/neighbors/{node_id}", params={"hops": hops})
    if neigh:
        st.caption(f"{len(neigh['nodes'])} nodes, {len(neigh['edges'])} relationships")
        st.json(neigh)
chart_card_close()

with st.expander("Production Migration: Cypher Seed for Neo4j"):
    st.caption("This build uses in-memory NetworkX for zero-config demos. "
               "Export the equivalent Cypher to seed a real Neo4j instance in production.")
    if st.button("Generate Cypher"):
        cy = api_get("/graph/cypher-seed")
        if cy:
            st.code(cy["cypher"], language="cypher")