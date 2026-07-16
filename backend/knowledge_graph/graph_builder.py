"""
Knowledge Graph Agent
----------------------
Builds and maintains the organization's Unified Asset Graph.

Schema (identical to the Neo4j design so this module is a drop-in swap
for a real Neo4j deployment -- see `to_cypher_seed()` below which emits
the equivalent Cypher CREATE statements for production migration):

Nodes: Equipment, Asset, Technician, Plant, Sensor, Incident, Document,
       FailureMode, Regulation, Department, WorkOrder

Edges: belongs_to, maintained_by, caused_failure, mentions, related_to,
       installed_at, violates, references

For the hackathon build we use NetworkX (in-memory, zero-config) with
JSON persistence, and PyVis for interactive HTML visualization. Swapping
in real Neo4j only requires replacing `GraphStore` internals -- the
Agent-facing API (`add_node`, `add_edge`, `query_neighbors`, etc.) stays
identical, so no other code changes.
"""
from __future__ import annotations

import json
from pathlib import Path
import networkx as nx

from backend.config import GRAPH_JSON_PATH


class GraphStore:
    def __init__(self):
        self.g = nx.MultiDiGraph()
        self._load()

    # ------------------------------------------------------------------
    def _load(self):
        if GRAPH_JSON_PATH.exists():
            try:
                data = json.loads(GRAPH_JSON_PATH.read_text())
                self.g = nx.node_link_graph(data, directed=True, multigraph=True, edges="links")
            except Exception:
                self.g = nx.MultiDiGraph()

    def save(self):
        data = nx.node_link_data(self.g, edges="links")
        GRAPH_JSON_PATH.write_text(json.dumps(data, default=str))

    # ------------------------------------------------------------------
    def add_node(self, node_id: str, label: str, **attrs):
        if node_id not in self.g:
            self.g.add_node(node_id, label=label, **attrs)
        else:
            self.g.nodes[node_id].update(attrs)

    def add_edge(self, src: str, dst: str, relation: str, **attrs):
        if src not in self.g or dst not in self.g:
            return
        self.g.add_edge(src, dst, key=relation, relation=relation, **attrs)

    # ------------------------------------------------------------------
    def query_neighbors(self, node_id: str, hops: int = 1):
        if node_id not in self.g:
            return {"nodes": [], "edges": []}
        visited = {node_id}
        frontier = {node_id}
        for _ in range(hops):
            nxt = set()
            for n in frontier:
                nxt |= set(self.g.successors(n)) | set(self.g.predecessors(n))
            visited |= nxt
            frontier = nxt

        nodes = [{"id": n, **self.g.nodes[n]} for n in visited]
        edges = []
        for u, v, k, d in self.g.edges(keys=True, data=True):
            if u in visited and v in visited:
                edges.append({"source": u, "target": v, "relation": d.get("relation", k)})
        return {"nodes": nodes, "edges": edges}

    def find_by_label(self, label: str):
        return [{"id": n, **d} for n, d in self.g.nodes(data=True) if d.get("label") == label]

    def stats(self):
        by_label = {}
        for _, d in self.g.nodes(data=True):
            by_label[d.get("label", "Unknown")] = by_label.get(d.get("label", "Unknown"), 0) + 1
        by_relation = {}
        for _, _, d in self.g.edges(data=True):
            r = d.get("relation", "related_to")
            by_relation[r] = by_relation.get(r, 0) + 1
        return {
            "total_nodes": self.g.number_of_nodes(),
            "total_edges": self.g.number_of_edges(),
            "nodes_by_label": by_label,
            "edges_by_relation": by_relation,
        }

    def full_graph_json(self):
        return nx.node_link_data(self.g, edges="links")

    def to_cypher_seed(self, limit: int = 500) -> str:
        """Emit Cypher CREATE statements -- ready to paste into a real
        Neo4j instance when moving this hackathon build to production."""
        lines = []
        for i, (n, d) in enumerate(self.g.nodes(data=True)):
            if i >= limit:
                break
            label = d.get("label", "Node")
            props = {k: v for k, v in d.items() if k != "label"}
            props["id"] = n
            prop_str = ", ".join(f'{k}: "{str(v)[:200]}"' for k, v in props.items())
            lines.append(f'CREATE (:{label} {{{prop_str}}})')
        for i, (u, v, d) in enumerate(self.g.edges(data=True)):
            if i >= limit:
                break
            rel = d.get("relation", "RELATED_TO").upper()
            lines.append(
                f'MATCH (a {{id: "{u}"}}), (b {{id: "{v}"}}) CREATE (a)-[:{rel}]->(b)'
            )
        return "\n".join(lines)


def build_graph_from_ingestion(store: GraphStore, doc_id: int, filename: str,
                                category: str, entities: dict):
    """Populates the graph from a single ingested document's extracted entities."""
    doc_node = f"DOC::{doc_id}"
    store.add_node(doc_node, "Document", name=filename, category=category)

    for eq in entities.get("equipment_ids", []):
        eq_node = f"EQUIPMENT::{eq}"
        store.add_node(eq_node, "Equipment", tag=eq)
        store.add_edge(doc_node, eq_node, "mentions")

    for plant in entities.get("plants", []):
        plant_node = f"PLANT::{plant.upper()}"
        store.add_node(plant_node, "Plant", name=plant)
        for eq in entities.get("equipment_ids", []):
            store.add_edge(f"EQUIPMENT::{eq}", plant_node, "belongs_to")

    for person in entities.get("personnel", []):
        tech_node = f"TECH::{person.upper()}"
        store.add_node(tech_node, "Technician", name=person)
        for eq in entities.get("equipment_ids", []):
            store.add_edge(tech_node, f"EQUIPMENT::{eq}", "maintained_by")

    for reg in entities.get("regulations", []):
        reg_node = f"REG::{reg.upper()}"
        store.add_node(reg_node, "Regulation", code=reg)
        store.add_edge(doc_node, reg_node, "references")

    for fail in entities.get("failure_causes", []):
        fail_node = f"FAILMODE::{fail.upper()}"
        store.add_node(fail_node, "FailureMode", name=fail)
        for eq in entities.get("equipment_ids", []):
            store.add_edge(f"EQUIPMENT::{eq}", fail_node, "caused_failure")
        store.add_edge(doc_node, fail_node, "mentions")

    for mfr in entities.get("manufacturers", []):
        mfr_node = f"MFR::{mfr.upper()}"
        store.add_node(mfr_node, "Manufacturer", name=mfr)
        for eq in entities.get("equipment_ids", []):
            store.add_edge(f"EQUIPMENT::{eq}", mfr_node, "manufactured_by")

    store.save()


def render_pyvis_html(store: GraphStore, out_path: str, focus_node: str | None = None, hops: int = 2):
    from pyvis.network import Network
    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="#111827",
                   directed=True, notebook=False)
    net.barnes_hut()

    color_map = {
        "Equipment": "#2563EB", "Document": "#94A3B8", "Plant": "#F59E0B",
        "Technician": "#10B981", "Regulation": "#EF4444", "FailureMode": "#DC2626",
        "Manufacturer": "#7C3AED", "Incident": "#F97316", "WorkOrder": "#0EA5E9",
    }

    subgraph = store.g
    if focus_node and focus_node in store.g:
        neigh = store.query_neighbors(focus_node, hops=hops)
        node_ids = {n["id"] for n in neigh["nodes"]}
        subgraph = store.g.subgraph(node_ids)

    for n, d in subgraph.nodes(data=True):
        label = d.get("label", "Node")
        title = json.dumps(d, indent=2, default=str)
        display = d.get("name") or d.get("tag") or d.get("code") or n
        net.add_node(n, label=str(display)[:24], title=title,
                     color=color_map.get(label, "#94A3B8"),
                     borderWidth=1, font={"color": "#111827", "size": 13})

    for u, v, d in subgraph.edges(data=True):
        net.add_edge(u, v, title=d.get("relation", ""), label=d.get("relation", ""),
                     color="#42474E", font={"color": "#6B7280", "size": 10})

    net.write_html(out_path, notebook=False)