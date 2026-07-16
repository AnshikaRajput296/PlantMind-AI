"""
Multi-Agent Orchestrator
------------------------
Executes the Planner's plan by invoking specialist agents in sequence,
threading a shared AgentContext through the pipeline. This is the heart
of the "not just a chatbot" architecture: every response carries a full,
inspectable reasoning chain across specialized agents.
"""
from __future__ import annotations

from backend.agents.base_agent import AgentContext
from backend.agents.planner_agent import PlannerAgent
from backend.agents.specialist_agents import (
    KnowledgeGraphAgent, VectorSearchAgent, MaintenanceAgent, RootCauseAgent,
    PredictionAgent, ComplianceAgent, AnswerAgent, ReportAgent,
)
from backend.knowledge_graph.graph_builder import GraphStore
from backend.retrieval.hybrid_retriever import HybridRetriever


class Orchestrator:
    def __init__(self, graph: GraphStore, retriever: HybridRetriever):
        self.planner = PlannerAgent()
        self.agents = {
            "KnowledgeGraphAgent": KnowledgeGraphAgent(graph),
            "VectorSearchAgent": VectorSearchAgent(retriever),
            "MaintenanceAgent": MaintenanceAgent(),
            "RootCauseAgent": RootCauseAgent(),
            "PredictionAgent": PredictionAgent(),
            "ComplianceAgent": ComplianceAgent(),
            "AnswerAgent": AnswerAgent(),
            "ReportAgent": ReportAgent(),
        }

    def handle_query(self, query: str) -> AgentContext:
        ctx = AgentContext(query=query)
        ctx = self.planner.run(ctx)
        for agent_name in ctx.data["plan"]:
            agent = self.agents.get(agent_name)
            if agent:
                ctx = agent.run(ctx)
        return ctx
