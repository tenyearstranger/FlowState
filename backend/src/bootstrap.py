from __future__ import annotations

from src.agents import (
    CodeAgent,
    DeliveryAgent,
    RequirementAgent,
    ReviewAgent,
    SolutionAgent,
    TestAgent,
)
from src.engine import DevFlowEngine
from src.models.pipeline import StageType
from src.store.state_store import StateStore


def register_default_agents(engine: DevFlowEngine) -> DevFlowEngine:
    engine.register_agent(StageType.REQUIREMENT, RequirementAgent())
    engine.register_agent(StageType.SOLUTION, SolutionAgent())
    engine.register_agent(StageType.CODING, CodeAgent())
    engine.register_agent(StageType.TESTING, TestAgent())
    engine.register_agent(StageType.REVIEW, ReviewAgent())
    engine.register_agent(StageType.DELIVERY, DeliveryAgent())
    return engine


def create_engine(state_store: StateStore | None = None) -> DevFlowEngine:
    engine = DevFlowEngine(state_store=state_store)
    return register_default_agents(engine)
