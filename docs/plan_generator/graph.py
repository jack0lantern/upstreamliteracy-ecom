"""
LangGraph wiring — assembles all nodes into the plan generator graph.

Graph flow:
  ingest_prd
    → decompose_prd
    → decision_checkpoint  (interrupt)
    → plan_parallel_work
    → implementation_agents (parallel)
    → qa_agents            (parallel)
    → critic_agents        (parallel)
    → critic_router
        ↻ loop to implementation_agents (if iteration < 3 AND feedback exists)
        → finalize_outputs
"""

from __future__ import annotations

import logging

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .nodes import (
    critic_agents,
    critic_router,
    decision_checkpoint,
    decompose_prd,
    finalize_outputs,
    implementation_agents,
    ingest_prd,
    plan_parallel_work,
    qa_agents,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Conditional edge: critic loop or finalize
# ---------------------------------------------------------------------------

def _should_continue_critic_loop(state: dict) -> str:
    """Route after critic_router: loop back or finalize."""
    if state.get("critic_loop_should_continue", False):
        return "implementation_agents"
    return "finalize_outputs"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph(checkpointer=None):
    """
    Build and compile the plan generator StateGraph.

    Args:
        checkpointer: LangGraph checkpointer for persistence/interrupt-resume.
                      Defaults to MemorySaver (in-memory).

    Returns:
        Compiled LangGraph graph ready for invocation.
    """
    if checkpointer is None:
        checkpointer = MemorySaver()

    graph = StateGraph(dict)

    # --- Add nodes ---
    graph.add_node("ingest_prd", ingest_prd)
    graph.add_node("decompose_prd", decompose_prd)
    graph.add_node("decision_checkpoint", decision_checkpoint)
    graph.add_node("plan_parallel_work", plan_parallel_work)
    graph.add_node("implementation_agents", implementation_agents)
    graph.add_node("qa_agents", qa_agents)
    graph.add_node("critic_agents", critic_agents)
    graph.add_node("critic_router", critic_router)
    graph.add_node("finalize_outputs", finalize_outputs)

    # --- Set entry point ---
    graph.set_entry_point("ingest_prd")

    # --- Linear edges ---
    graph.add_edge("ingest_prd", "decompose_prd")
    graph.add_edge("decompose_prd", "decision_checkpoint")
    graph.add_edge("decision_checkpoint", "plan_parallel_work")
    graph.add_edge("plan_parallel_work", "implementation_agents")
    graph.add_edge("implementation_agents", "qa_agents")
    graph.add_edge("qa_agents", "critic_agents")
    graph.add_edge("critic_agents", "critic_router")

    # --- Conditional edge: critic loop ---
    graph.add_conditional_edges(
        "critic_router",
        _should_continue_critic_loop,
        {
            "implementation_agents": "implementation_agents",
            "finalize_outputs": "finalize_outputs",
        },
    )

    # --- Terminal edge ---
    graph.add_edge("finalize_outputs", END)

    # --- Compile with checkpointer (required for interrupt/resume) ---
    compiled = graph.compile(checkpointer=checkpointer)

    logger.info("[build_graph] Plan generator graph compiled successfully")
    return compiled
