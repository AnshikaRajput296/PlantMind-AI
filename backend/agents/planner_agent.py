"""
Planner Agent
-------------
The entry point of every query. Classifies user intent and decides which
downstream specialist agents to invoke, in what order. This is what
differentiates the platform from a single-shot RAG chatbot: the plan
itself is visible to the user as an explainable reasoning chain.
"""
from __future__ import annotations
import re

from backend.agents.base_agent import BaseAgent, AgentContext

INTENT_RULES = [
    ("root_cause", ["why did", "why does", "root cause", "keeps failing", "repeatedly fail", "rca"]),
    ("prediction", ["predict", "remaining useful life", "rul", "risk score", "likely to fail", "when will"]),
    ("compliance", ["compliance", "audit", "iso", "regulation", "violat", "peso", "oisd", "factory act"]),
    ("maintenance_history", ["maintenance history", "last maintenance", "work order", "serviced", "when was"]),
    ("lessons_learned", ["similar incident", "recurring", "pattern", "lessons learned", "past failures"]),
    ("report", ["generate report", "rca report", "audit report", "pdf report", "summarize into a report"]),
]


class PlannerAgent(BaseAgent):
    name = "Planner Agent"
    responsibility = "Classifies intent and builds the multi-agent execution plan."

    def classify(self, query: str) -> str:
        q = query.lower()
        for intent, keywords in INTENT_RULES:
            if any(k in q for k in keywords):
                return intent
        return "general_qa"

    def run(self, ctx: AgentContext) -> AgentContext:
        intent = self.classify(ctx.query)
        equipment_match = re.findall(r"\b([A-Z]{1,4}-\d{2,4}[A-Z]?)\b", ctx.query.upper())

        plan_map = {
            "root_cause": ["KnowledgeGraphAgent", "VectorSearchAgent", "MaintenanceAgent",
                           "RootCauseAgent", "ComplianceAgent", "AnswerAgent"],
            "prediction": ["KnowledgeGraphAgent", "MaintenanceAgent", "PredictionAgent", "AnswerAgent"],
            "compliance": ["VectorSearchAgent", "ComplianceAgent", "AnswerAgent"],
            "maintenance_history": ["KnowledgeGraphAgent", "MaintenanceAgent", "AnswerAgent"],
            "lessons_learned": ["VectorSearchAgent", "MaintenanceAgent", "RootCauseAgent", "AnswerAgent"],
            "report": ["KnowledgeGraphAgent", "VectorSearchAgent", "MaintenanceAgent",
                       "RootCauseAgent", "ComplianceAgent", "AnswerAgent", "ReportAgent"],
            "general_qa": ["VectorSearchAgent", "KnowledgeGraphAgent", "AnswerAgent"],
        }

        plan = plan_map.get(intent, plan_map["general_qa"])
        ctx.data["intent"] = intent
        ctx.data["equipment_focus"] = equipment_match[0] if equipment_match else None
        ctx.data["plan"] = plan
        ctx.log(self.name, f"Classified intent as '{intent}'. Equipment focus: "
                            f"{ctx.data['equipment_focus'] or 'none detected'}. "
                            f"Execution plan: {' -> '.join(plan)}")
        return ctx
