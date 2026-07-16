"""
Specialist Agents
-----------------
Each class below is a focused, single-responsibility agent invoked by the
Orchestrator according to the Planner's plan. Together they replace a
single monolithic RAG chatbot with a transparent, inspectable pipeline.
"""
from __future__ import annotations

from backend.agents.base_agent import BaseAgent, AgentContext
from backend.knowledge_graph.graph_builder import GraphStore
from backend.retrieval.hybrid_retriever import HybridRetriever, confidence_and_hallucination_flag
from backend.llm import llm_router
from backend.database import get_session, WorkOrder, Incident, Equipment
from backend import config


class KnowledgeGraphAgent(BaseAgent):
    name = "Knowledge Graph Agent"
    responsibility = "Traverses the Unified Asset Graph to gather structural relationships."

    def __init__(self, graph: GraphStore):
        self.graph = graph

    def run(self, ctx: AgentContext) -> AgentContext:
        eq = ctx.data.get("equipment_focus")
        if eq:
            node_id = f"EQUIPMENT::{eq}"
            result = self.graph.query_neighbors(node_id, hops=2)
            ctx.data["graph_context"] = result
            ctx.log(self.name, f"Traversed graph around {eq}: found "
                                f"{len(result['nodes'])} related nodes, "
                                f"{len(result['edges'])} relationships "
                                f"(failure modes, technicians, plants, regulations).")
        else:
            stats = self.graph.stats()
            ctx.data["graph_context"] = {"nodes": [], "edges": []}
            ctx.log(self.name, f"No specific equipment mentioned. Graph currently holds "
                                f"{stats['total_nodes']} nodes / {stats['total_edges']} edges "
                                f"across the plant knowledge base.")
        return ctx


class VectorSearchAgent(BaseAgent):
    name = "Vector Search Agent"
    responsibility = "Runs hybrid dense+sparse retrieval with reranking over the document corpus."

    def __init__(self, retriever: HybridRetriever):
        self.retriever = retriever

    def run(self, ctx: AgentContext) -> AgentContext:
        results = self.retriever.retrieve(
            ctx.query, top_k=config.TOP_K_FINAL,
            equipment_filter=ctx.data.get("equipment_focus"),
        )
        ctx.data["retrieved_chunks"] = results
        conf = confidence_and_hallucination_flag(ctx.query, results)
        ctx.data["confidence"] = conf
        ctx.log(self.name, f"Retrieved {len(results)} relevant passages via hybrid "
                            f"BM25 + dense + cross-encoder rerank. Confidence: "
                            f"{conf['confidence']}, hallucination risk: {conf['hallucination_risk']}.")
        return ctx


class MaintenanceAgent(BaseAgent):
    name = "Maintenance Agent"
    responsibility = "Pulls structured maintenance/work-order history for the asset in question."

    def run(self, ctx: AgentContext) -> AgentContext:
        eq = ctx.data.get("equipment_focus")
        session = get_session()
        try:
            q = session.query(WorkOrder)
            if eq:
                q = q.filter(WorkOrder.equipment_tag == eq)
            orders = q.order_by(WorkOrder.date.desc()).limit(15).all()
            history = [{
                "date": o.date, "technician": o.technician, "description": o.description,
                "failure_mode": o.failure_mode, "downtime_hours": o.downtime_hours, "cost": o.cost,
            } for o in orders]
            ctx.data["work_orders"] = history
            ctx.log(self.name, f"Found {len(history)} historical work orders"
                                f"{' for ' + eq if eq else ''}.")
        finally:
            session.close()
        return ctx


class RootCauseAgent(BaseAgent):
    name = "Root Cause Analysis Agent"
    responsibility = "Analyzes failure patterns across work orders + graph to infer root cause(s)."

    def run(self, ctx: AgentContext) -> AgentContext:
        history = ctx.data.get("work_orders", [])
        modes = {}
        for h in history:
            fm = h.get("failure_mode") or "unspecified"
            modes[fm] = modes.get(fm, 0) + 1
        ranked = sorted(modes.items(), key=lambda kv: -kv[1])

        graph_ctx = ctx.data.get("graph_context", {"nodes": []})
        failure_nodes = [n for n in graph_ctx.get("nodes", []) if n.get("label") == "FailureMode"]

        analysis = {
            "recurring_failure_modes": ranked[:5],
            "graph_linked_failure_modes": [n.get("name") for n in failure_nodes],
            "total_incidents_analyzed": len(history),
        }
        ctx.data["rca"] = analysis
        top = ranked[0][0] if ranked else "insufficient data"
        ctx.log(self.name, f"Analyzed {len(history)} work orders. Most frequent failure mode: "
                            f"'{top}' ({ranked[0][1] if ranked else 0} occurrences). "
                            f"Cross-referenced with {len(failure_nodes)} failure-mode nodes in graph.")
        return ctx


class PredictionAgent(BaseAgent):
    name = "Failure Prediction Agent"
    responsibility = "Estimates risk score and remaining useful life from maintenance frequency."

    def run(self, ctx: AgentContext) -> AgentContext:
        eq = ctx.data.get("equipment_focus")
        history = ctx.data.get("work_orders", [])
        n = len(history)
        # Lightweight heuristic risk model (swap for trained XGBoost/Isolation
        # Forest model using backend/analytics/anomaly_detection.py in production)
        risk_score = min(0.95, 0.15 + 0.12 * n)
        rul_days = max(5, 180 - 20 * n)
        ctx.data["prediction"] = {
            "equipment": eq, "risk_score": round(risk_score, 2),
            "remaining_useful_life_days": rul_days,
            "basis": f"Derived from {n} historical maintenance events "
                     f"(higher frequency -> higher risk, lower RUL).",
        }
        ctx.log(self.name, f"Predicted risk score {round(risk_score,2)} and RUL of "
                            f"~{rul_days} days for {eq or 'the fleet'}, based on "
                            f"{n} historical events.")
        return ctx


class ComplianceAgent(BaseAgent):
    name = "Compliance Agent"
    responsibility = "Checks referenced regulations/standards and flags compliance gaps."

    def run(self, ctx: AgentContext) -> AgentContext:
        chunks = ctx.data.get("retrieved_chunks", [])
        mentioned = set()
        for c in chunks:
            for fw in config.COMPLIANCE_FRAMEWORKS:
                if fw.lower().replace(" ", "") in c.child_text.lower().replace(" ", ""):
                    mentioned.add(fw)

        gaps = [fw for fw in config.COMPLIANCE_FRAMEWORKS if fw not in mentioned]
        ctx.data["compliance"] = {
            "frameworks_referenced": sorted(mentioned),
            "potential_gaps": gaps,
            "note": "Gaps indicate frameworks with no supporting documentation found in "
                    "the current corpus for this query -- not a certified compliance verdict.",
        }
        ctx.log(self.name, f"Cross-checked against {len(config.COMPLIANCE_FRAMEWORKS)} "
                            f"regulatory frameworks. Found references to "
                            f"{sorted(mentioned) or 'none'}.")
        return ctx


class AnswerAgent(BaseAgent):
    name = "Answer Generator Agent"
    responsibility = "Synthesizes all agent outputs into one grounded, cited final answer."

    def run(self, ctx: AgentContext) -> AgentContext:
        chunks = ctx.data.get("retrieved_chunks", [])
        context_texts = [c.parent_text for c in chunks]

        system = (
            "You are the Expert Copilot of an industrial Unified Asset & Operations Brain. "
            "Answer using ONLY the provided evidence. Cite source documents by filename. "
            "Be precise, structured, and include a short root-cause / recommendation section "
            "if maintenance or failure data is present. If evidence is thin, say so explicitly."
        )
        evidence_block = "\n\n".join(
            f"[Source: {c.filename} | {c.category}]\n{c.parent_text[:800]}" for c in chunks
        )
        wo = ctx.data.get("work_orders", [])
        rca = ctx.data.get("rca", {})
        pred = ctx.data.get("prediction", {})
        compliance = ctx.data.get("compliance", {})

        prompt = f"""User question: {ctx.query}

Retrieved evidence:
{evidence_block if evidence_block else "(no direct document matches)"}

Structured maintenance history ({len(wo)} records): {wo[:5]}
Root cause analysis: {rca}
Prediction: {pred}
Compliance check: {compliance}

Write a clear, well-structured answer for a plant engineer. Include citations to source
filenames in brackets, e.g. [Source: WO-2231.pdf]. If a root cause analysis is available,
summarize it. If a prediction is available, state the risk score and RUL plainly."""

        result = llm_router.generate(prompt, system=system, context_chunks=context_texts)
        ctx.data["final_answer"] = result["text"]
        ctx.data["llm_provider"] = result["provider"]
        ctx.log(self.name, f"Synthesized final answer using LLM provider "
                            f"'{result['provider']}', grounded in {len(chunks)} passages.")
        return ctx


class ReportAgent(BaseAgent):
    name = "Report Generator Agent"
    responsibility = "Assembles a formatted RCA/Audit PDF report from the full agent trace."

    def run(self, ctx: AgentContext) -> AgentContext:
        ctx.data["report_ready"] = True
        ctx.log(self.name, "Compiled full agent trace into a report-ready structure. "
                            "Call /report/generate to render the downloadable PDF.")
        return ctx
