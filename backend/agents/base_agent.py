"""
Base Agent
----------
Every specialized agent inherits from BaseAgent and implements `run()`.
The Orchestrator calls agents in a planned sequence and accumulates a
shared AgentContext, which becomes the audit trail / reasoning-chain
shown in the UI (Explainable AI requirement).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentContext:
    query: str
    data: dict = field(default_factory=dict)          # shared scratchpad between agents
    trace: list = field(default_factory=list)          # reasoning chain for explainability

    def log(self, agent_name: str, message: str):
        self.trace.append({"agent": agent_name, "message": message})


class BaseAgent:
    name: str = "BaseAgent"
    responsibility: str = ""

    def run(self, ctx: AgentContext) -> AgentContext:
        raise NotImplementedError
