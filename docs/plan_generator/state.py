"""
Strongly-typed shared state for the plan generator graph.
"""

from __future__ import annotations

import operator
from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DecisionStatus(str, Enum):
    PENDING = "pending"
    RESOLVED = "resolved"


class DecisionCategory(str, Enum):
    BACKEND_FRAMEWORK = "backend_framework"
    FRONTEND_FRAMEWORK = "frontend_framework"
    DATABASE = "database"
    API_STYLE = "api_style"
    AUTH_STRATEGY = "auth_strategy"
    INFRA = "infra"


class CriticVerdict(str, Enum):
    PASS = "pass"
    FAIL = "fail"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class PRDSection(BaseModel):
    id: str
    title: str
    content: str
    requirements: list[str] = Field(default_factory=list)


class DecisionOption(BaseModel):
    name: str
    pros: list[str]
    cons: list[str]


class Decision(BaseModel):
    category: DecisionCategory
    question: str
    options: list[DecisionOption] = Field(default_factory=list)
    status: DecisionStatus = DecisionStatus.PENDING
    resolution: str | None = None
    rationale: str | None = None


class AgentTask(BaseModel):
    agent_name: str
    description: str
    prd_section_ids: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    output: str | None = None


class QAResult(BaseModel):
    agent_name: str
    passed: bool
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class CriticFeedback(BaseModel):
    critic_name: str
    verdict: CriticVerdict
    issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    iteration: int


class FinalOutputs(BaseModel):
    architecture: str = ""
    implementation_plan: str = ""
    repo_structure: str = ""
    setup_commands: list[str] = Field(default_factory=list)
    run_commands: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Reducer helpers
# ---------------------------------------------------------------------------

def merge_lists(left: list, right: list) -> list:
    """Append-only list reducer for LangGraph state channels."""
    return left + right


def replace_value(left: Any, right: Any) -> Any:
    """Last-writer-wins reducer."""
    return right


# ---------------------------------------------------------------------------
# Graph State
# ---------------------------------------------------------------------------

class PlanGeneratorState(BaseModel):
    """Top-level state threaded through every node in the graph."""

    # PRD ingestion
    prd_raw: str = ""
    prd_sections: list[PRDSection] = Field(default_factory=list)

    # Decomposition
    modules: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    dependencies: dict[str, list[str]] = Field(default_factory=dict)

    # Decisions (human-in-the-loop)
    decisions: list[Decision] = Field(default_factory=list)

    # Task assignment
    tasks_by_agent: dict[str, list[AgentTask]] = Field(default_factory=dict)

    # Agent outputs (keyed by agent name)
    agent_outputs: dict[str, str] = Field(default_factory=dict)

    # QA
    qa_results: list[QAResult] = Field(default_factory=list)

    # Critic loop
    critic_feedback: list[CriticFeedback] = Field(default_factory=list)
    iteration_count: int = 0

    # Final
    final_outputs: FinalOutputs = Field(default_factory=FinalOutputs)

    # Control flags
    has_unresolved_decisions: bool = False
    critic_loop_should_continue: bool = False
