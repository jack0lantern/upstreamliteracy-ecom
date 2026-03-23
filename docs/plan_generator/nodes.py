"""
LangGraph node implementations for the plan generator.

Each node is an async function that receives and returns PlanGeneratorState.
Parallel fan-out nodes return partial state dicts that get merged by the graph.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.types import interrupt

from .prompts import (
    critic_agent_prompt,
    decision_checkpoint_prompt,
    decompose_prompt,
    finalize_prompt,
    implementation_agent_prompt,
    ingest_prd_prompt,
    plan_parallel_work_prompt,
    qa_agent_prompt,
)
from .state import (
    AgentTask,
    CriticFeedback,
    CriticVerdict,
    Decision,
    DecisionCategory,
    DecisionOption,
    DecisionStatus,
    FinalOutputs,
    PlanGeneratorState,
    PRDSection,
    QAResult,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LLM helper
# ---------------------------------------------------------------------------

# Default model — swap to any langchain-compatible chat model
_DEFAULT_MODEL = "gpt-4o"


def _get_llm(model: str = _DEFAULT_MODEL, temperature: float = 0.2) -> ChatOpenAI:
    return ChatOpenAI(model=model, temperature=temperature)


async def _llm_call(system: str, user: str, model: str = _DEFAULT_MODEL) -> str:
    """Make an async LLM call and return the raw content string."""
    llm = _get_llm(model)
    messages = [SystemMessage(content=system), HumanMessage(content=user)]
    response = await llm.ainvoke(messages)
    return response.content


def _parse_json(raw: str) -> Any:
    """Best-effort JSON extraction from LLM output."""
    # Strip markdown code fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        # Remove first and last lines (fences)
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    return json.loads(cleaned)


# ===================================================================
# NODE 1: ingest_prd
# ===================================================================

async def ingest_prd(state: dict) -> dict:
    """Parse raw PRD text into structured sections."""
    logger.info("[ingest_prd] Parsing PRD into structured sections")

    prd_raw = state.get("prd_raw", "")
    if not prd_raw:
        raise ValueError("prd_raw is empty — provide a PRD to parse")

    system, user = ingest_prd_prompt(prd_raw)
    raw = await _llm_call(system, user)

    try:
        sections_data = _parse_json(raw)
        sections = [PRDSection(**s) for s in sections_data]
    except Exception:
        logger.warning("[ingest_prd] JSON parse failed, falling back to single section")
        sections = [
            PRDSection(id="full_prd", title="Full PRD", content=prd_raw, requirements=[])
        ]

    logger.info(f"[ingest_prd] Extracted {len(sections)} sections")
    return {"prd_sections": sections}


# ===================================================================
# NODE 2: decompose_prd
# ===================================================================

async def decompose_prd(state: dict) -> dict:
    """Extract modules, domains, and dependencies from PRD sections."""
    logger.info("[decompose_prd] Decomposing PRD into modules and domains")

    sections = [PRDSection(**s) if isinstance(s, dict) else s for s in state.get("prd_sections", [])]
    system, user = decompose_prompt(sections)
    raw = await _llm_call(system, user)

    try:
        data = _parse_json(raw)
    except Exception:
        logger.warning("[decompose_prd] JSON parse failed, using empty decomposition")
        data = {"modules": [], "domains": [], "dependencies": {}}

    logger.info(
        f"[decompose_prd] Found {len(data.get('modules', []))} modules, "
        f"{len(data.get('domains', []))} domains"
    )
    return {
        "modules": data.get("modules", []),
        "domains": data.get("domains", []),
        "dependencies": data.get("dependencies", {}),
    }


# ===================================================================
# NODE 3: decision_checkpoint (INTERRUPT)
# ===================================================================

async def decision_checkpoint(state: dict) -> dict:
    """
    Detect unresolved architectural decisions and interrupt for human input.

    Uses LangGraph's `interrupt()` to pause execution. The CLI runner resumes
    the graph with user-provided resolutions.
    """
    logger.info("[decision_checkpoint] Checking for unresolved decisions")

    # Reconstruct state model for prompt generation
    current_state = PlanGeneratorState(**state)
    system, user = decision_checkpoint_prompt(current_state)
    raw = await _llm_call(system, user)

    try:
        decisions_data = _parse_json(raw)
    except Exception:
        logger.warning("[decision_checkpoint] JSON parse failed, no decisions detected")
        decisions_data = []

    # Build Decision objects
    new_decisions: list[Decision] = []
    already_resolved = {
        d.category.value
        for d in current_state.decisions
        if d.status == DecisionStatus.RESOLVED
    }

    for d in decisions_data:
        cat = d.get("category", "")
        if cat in already_resolved:
            continue
        options = [DecisionOption(**o) for o in d.get("options", [])]
        new_decisions.append(
            Decision(
                category=DecisionCategory(cat),
                question=d.get("question", ""),
                options=options,
                status=DecisionStatus.PENDING,
            )
        )

    if not new_decisions:
        logger.info("[decision_checkpoint] All decisions resolved — proceeding")
        return {
            "decisions": current_state.decisions,
            "has_unresolved_decisions": False,
        }

    # Merge with existing resolved decisions
    all_decisions = [
        d for d in current_state.decisions if d.status == DecisionStatus.RESOLVED
    ] + new_decisions

    logger.info(
        f"[decision_checkpoint] {len(new_decisions)} unresolved decisions — "
        "interrupting for human input"
    )

    # ----- INTERRUPT: pause graph execution -----
    # Present decisions to user and wait for resolutions
    pending_summary = [
        {
            "category": d.category.value,
            "question": d.question,
            "options": [o.model_dump() for o in d.options],
        }
        for d in new_decisions
    ]

    # LangGraph interrupt — execution halts here until resumed
    user_resolutions = interrupt(
        {
            "type": "decision_checkpoint",
            "message": "Please resolve the following architectural decisions.",
            "decisions": pending_summary,
        }
    )

    # ----- RESUMED: apply user resolutions -----
    # user_resolutions expected: {category: {resolution: str, rationale: str}}
    resolved_decisions = []
    for d in all_decisions:
        if d.status == DecisionStatus.RESOLVED:
            resolved_decisions.append(d)
            continue

        res = user_resolutions.get(d.category.value, {})
        if res:
            d.status = DecisionStatus.RESOLVED
            d.resolution = res.get("resolution", "")
            d.rationale = res.get("rationale", "")
        resolved_decisions.append(d)

    return {
        "decisions": resolved_decisions,
        "has_unresolved_decisions": any(
            d.status == DecisionStatus.PENDING for d in resolved_decisions
        ),
    }


# ===================================================================
# NODE 4: plan_parallel_work
# ===================================================================

async def plan_parallel_work(state: dict) -> dict:
    """Create task graph and assign work to implementation agents."""
    logger.info("[plan_parallel_work] Creating task assignments")

    current_state = PlanGeneratorState(**state)
    system, user = plan_parallel_work_prompt(current_state)
    raw = await _llm_call(system, user)

    try:
        data = _parse_json(raw)
        tasks_by_agent = {}
        for agent_name, tasks in data.get("tasks_by_agent", {}).items():
            tasks_by_agent[agent_name] = [AgentTask(**t) for t in tasks]
    except Exception:
        logger.warning("[plan_parallel_work] JSON parse failed, using fallback assignments")
        agent_names = [
            "frontend_agent", "backend_agent", "payments_agent",
            "checkout_agent", "inventory_agent", "auth_agent", "analytics_agent",
        ]
        tasks_by_agent = {
            name: [AgentTask(agent_name=name, description=f"Implement {name.replace('_agent', '')} module")]
            for name in agent_names
        }

    logger.info(f"[plan_parallel_work] Assigned tasks to {len(tasks_by_agent)} agents")
    return {"tasks_by_agent": tasks_by_agent}


# ===================================================================
# NODE 5: implementation_agents (parallel fan-out)
# ===================================================================

IMPLEMENTATION_AGENTS = [
    "frontend_agent",
    "backend_agent",
    "payments_agent",
    "checkout_agent",
    "inventory_agent",
    "auth_agent",
    "analytics_agent",
]


async def _run_single_implementation_agent(
    agent_name: str, state: PlanGeneratorState
) -> tuple[str, str]:
    """Run a single implementation agent and return (agent_name, output)."""
    logger.info(f"[implementation_agents] Running {agent_name}")

    tasks = state.tasks_by_agent.get(agent_name, [])
    if not tasks:
        return agent_name, f"No tasks assigned to {agent_name}."

    system, user = implementation_agent_prompt(
        agent_name, tasks, state.decisions, state.prd_sections
    )

    # If there's prior feedback from critics, include it
    prior_feedback = [
        f for f in state.critic_feedback
        if f.iteration == state.iteration_count - 1
    ]
    if prior_feedback:
        feedback_text = "\n".join(
            f"[{f.critic_name}] {f.issues}" for f in prior_feedback
        )
        user += f"\n\nPrior critic feedback to address:\n{feedback_text}"

    output = await _llm_call(system, user)
    return agent_name, output


async def implementation_agents(state: dict) -> dict:
    """Fan-out: run all implementation agents in parallel."""
    logger.info(
        f"[implementation_agents] Starting parallel execution "
        f"(iteration {state.get('iteration_count', 0)})"
    )

    current_state = PlanGeneratorState(**state)

    # Run all agents concurrently
    tasks = [
        _run_single_implementation_agent(name, current_state)
        for name in IMPLEMENTATION_AGENTS
        if name in current_state.tasks_by_agent
    ]
    results = await asyncio.gather(*tasks)

    agent_outputs = dict(results)
    logger.info(f"[implementation_agents] Completed {len(agent_outputs)} agents")
    return {"agent_outputs": agent_outputs}


# ===================================================================
# NODE 6: qa_agents (parallel fan-out)
# ===================================================================

async def _run_single_qa_agent(
    agent_name: str, state: PlanGeneratorState
) -> QAResult:
    """Run QA for a single implementation agent."""
    logger.info(f"[qa_agents] Validating {agent_name}")

    agent_output = state.agent_outputs.get(agent_name, "")
    tasks = state.tasks_by_agent.get(agent_name, [])

    system, user = qa_agent_prompt(agent_name, agent_output, tasks, state.prd_sections)
    raw = await _llm_call(system, user)

    try:
        data = _parse_json(raw)
        return QAResult(
            agent_name=agent_name,
            passed=data.get("passed", True),
            issues=data.get("issues", []),
            suggestions=data.get("suggestions", []),
        )
    except Exception:
        return QAResult(agent_name=agent_name, passed=True, issues=[], suggestions=[])


async def qa_agents(state: dict) -> dict:
    """Fan-out: run QA agents in parallel, one per implementation agent."""
    logger.info("[qa_agents] Starting parallel QA validation")

    current_state = PlanGeneratorState(**state)

    tasks = [
        _run_single_qa_agent(name, current_state)
        for name in current_state.agent_outputs
    ]
    results = await asyncio.gather(*tasks)

    logger.info(f"[qa_agents] Completed {len(results)} QA checks")
    return {"qa_results": list(results)}


# ===================================================================
# NODE 7: critic_agents (parallel fan-out)
# ===================================================================

CRITIC_AGENTS = [
    "auditor_critic",
    "security_critic",
    "implementation_critic",
    "observability_critic",
]


async def _run_single_critic(
    critic_name: str, agent_outputs: dict[str, str], iteration: int
) -> CriticFeedback:
    """Run a single critic agent."""
    logger.info(f"[critic_agents] Running {critic_name} (iteration {iteration})")

    system, user = critic_agent_prompt(critic_name, agent_outputs)
    raw = await _llm_call(system, user)

    try:
        data = _parse_json(raw)
        return CriticFeedback(
            critic_name=critic_name,
            verdict=CriticVerdict(data.get("verdict", "pass")),
            issues=data.get("issues", []),
            recommendations=data.get("recommendations", []),
            iteration=iteration,
        )
    except Exception:
        return CriticFeedback(
            critic_name=critic_name,
            verdict=CriticVerdict.PASS,
            issues=[],
            recommendations=[],
            iteration=iteration,
        )


async def critic_agents(state: dict) -> dict:
    """Fan-out: run all critic agents in parallel."""
    logger.info("[critic_agents] Starting parallel critic review")

    agent_outputs = state.get("agent_outputs", {})
    iteration = state.get("iteration_count", 0)

    tasks = [
        _run_single_critic(name, agent_outputs, iteration)
        for name in CRITIC_AGENTS
    ]
    results = await asyncio.gather(*tasks)

    # Append to existing feedback (preserve history across iterations)
    existing_feedback = state.get("critic_feedback", [])
    if existing_feedback and isinstance(existing_feedback[0], dict):
        existing_feedback = [CriticFeedback(**f) for f in existing_feedback]

    all_feedback = existing_feedback + list(results)

    logger.info(f"[critic_agents] Completed {len(results)} critic reviews")
    return {"critic_feedback": all_feedback}


# ===================================================================
# NODE 8: critic_router
# ===================================================================

async def critic_router(state: dict) -> dict:
    """
    Decide whether to loop back to implementation_agents or proceed.

    Loop conditions (ALL must be true to loop):
    - iteration_count < 3
    - At least one critic returned verdict=fail
    """
    iteration = state.get("iteration_count", 0)
    feedback = state.get("critic_feedback", [])

    # Get feedback from current iteration only
    current_feedback = [
        (f if isinstance(f, CriticFeedback) else CriticFeedback(**f))
        for f in feedback
        if (f if isinstance(f, dict) else f.__dict__).get("iteration", (f.iteration if isinstance(f, CriticFeedback) else 0)) == iteration
    ]

    has_issues = any(f.verdict == CriticVerdict.FAIL for f in current_feedback)
    can_iterate = iteration < 3

    if has_issues and can_iterate:
        logger.info(
            f"[critic_router] Issues found at iteration {iteration} — "
            "looping back to implementation_agents"
        )
        return {
            "iteration_count": iteration + 1,
            "critic_loop_should_continue": True,
        }
    else:
        reason = "all critics passed" if not has_issues else f"max iterations ({iteration}) reached"
        logger.info(f"[critic_router] Proceeding to finalize — {reason}")
        return {
            "iteration_count": iteration,
            "critic_loop_should_continue": False,
        }


# ===================================================================
# NODE 9: finalize_outputs
# ===================================================================

async def finalize_outputs(state: dict) -> dict:
    """Generate final deliverables: architecture, plan, repo structure, commands."""
    logger.info("[finalize_outputs] Generating final deliverables")

    current_state = PlanGeneratorState(**state)
    system, user = finalize_prompt(current_state)
    raw = await _llm_call(system, user)

    # Parse the markdown output into structured sections
    final = FinalOutputs(
        architecture="",
        implementation_plan="",
        repo_structure="",
        setup_commands=[],
        run_commands=[],
    )

    # Split by known headings
    current_section = ""
    lines_buffer: list[str] = []

    def _flush():
        nonlocal current_section, lines_buffer
        text = "\n".join(lines_buffer).strip()
        if "architecture" in current_section.lower():
            final.architecture = text
        elif "implementation" in current_section.lower():
            final.implementation_plan = text
        elif "repo" in current_section.lower() or "structure" in current_section.lower():
            final.repo_structure = text
        elif "setup" in current_section.lower():
            final.setup_commands = [
                line.strip().lstrip("- ").lstrip("` ").rstrip("`")
                for line in lines_buffer
                if line.strip().startswith(("-", "`"))
            ]
        elif "run" in current_section.lower():
            final.run_commands = [
                line.strip().lstrip("- ").lstrip("` ").rstrip("`")
                for line in lines_buffer
                if line.strip().startswith(("-", "`"))
            ]
        lines_buffer = []

    for line in raw.split("\n"):
        if line.startswith("# ") or line.startswith("## "):
            _flush()
            current_section = line
        else:
            lines_buffer.append(line)
    _flush()

    # Fallback: if parsing didn't capture sections, store raw output
    if not final.architecture and not final.implementation_plan:
        final.implementation_plan = raw

    logger.info("[finalize_outputs] Final deliverables generated")
    return {"final_outputs": final}
