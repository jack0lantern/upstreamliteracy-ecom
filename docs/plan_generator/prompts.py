"""
Prompt templates for every agent in the plan generator.

Each prompt is a function that accepts the relevant state slice and returns
a formatted system + user message pair for the LLM call.
"""

from __future__ import annotations

from .state import AgentTask, PlanGeneratorState, PRDSection


# ---------------------------------------------------------------------------
# PRD Ingestion
# ---------------------------------------------------------------------------

INGEST_PRD_SYSTEM = """\
You are a PRD parser. Given a raw PRD document, extract it into structured
sections. Each section must have:
- id: a short snake_case identifier
- title: the section heading
- content: the full text of that section
- requirements: a list of discrete, testable requirements extracted from the content

Return valid JSON: a list of objects with keys {id, title, content, requirements}.
"""


def ingest_prd_prompt(prd_raw: str) -> tuple[str, str]:
    return (INGEST_PRD_SYSTEM, f"Parse this PRD:\n\n{prd_raw}")


# ---------------------------------------------------------------------------
# Decomposition
# ---------------------------------------------------------------------------

DECOMPOSE_SYSTEM = """\
You are a software architect. Given structured PRD sections, identify:
1. modules — discrete software modules to build
2. domains — business domains involved
3. dependencies — a mapping of module → list of modules it depends on

Return valid JSON with keys {modules, domains, dependencies}.
"""


def decompose_prompt(sections: list[PRDSection]) -> tuple[str, str]:
    section_text = "\n\n".join(
        f"## {s.title}\n{s.content}" for s in sections
    )
    return (DECOMPOSE_SYSTEM, f"PRD Sections:\n\n{section_text}")


# ---------------------------------------------------------------------------
# Decision Checkpoint
# ---------------------------------------------------------------------------

DECISION_SYSTEM = """\
You are a technical decision analyst. Given PRD sections and current resolved
decisions, detect any UNRESOLVED architectural decisions in these categories:
- backend_framework
- frontend_framework
- database
- api_style
- auth_strategy
- infra

For each unresolved decision, provide 2–3 options with pros and cons.

Return valid JSON: a list of objects with keys:
{category, question, options: [{name, pros: [...], cons: [...]}]}
"""


def decision_checkpoint_prompt(state: PlanGeneratorState) -> tuple[str, str]:
    resolved = {d.category.value: d.resolution for d in state.decisions if d.resolution}
    section_text = "\n".join(f"- {s.title}: {s.content[:200]}" for s in state.prd_sections)
    return (
        DECISION_SYSTEM,
        f"PRD Summary:\n{section_text}\n\nAlready resolved:\n{resolved}",
    )


# ---------------------------------------------------------------------------
# Plan Parallel Work
# ---------------------------------------------------------------------------

PLAN_WORK_SYSTEM = """\
You are a project planner. Given modules, dependencies, and resolved decisions,
create a task graph and assign tasks to these agents:
- frontend_agent
- backend_agent
- payments_agent
- checkout_agent
- inventory_agent
- auth_agent
- analytics_agent

Each task must reference the PRD section IDs it traces to.

Return valid JSON: {tasks_by_agent: {agent_name: [{agent_name, description,
prd_section_ids, dependencies}]}}
"""


def plan_parallel_work_prompt(state: PlanGeneratorState) -> tuple[str, str]:
    decisions_text = "\n".join(
        f"- {d.category.value}: {d.resolution}" for d in state.decisions if d.resolution
    )
    return (
        PLAN_WORK_SYSTEM,
        (
            f"Modules: {state.modules}\n"
            f"Dependencies: {state.dependencies}\n"
            f"Decisions:\n{decisions_text}"
        ),
    )


# ---------------------------------------------------------------------------
# Implementation Agents
# ---------------------------------------------------------------------------

IMPLEMENTATION_SYSTEM_TEMPLATE = """\
You are the {agent_name} agent. Given your assigned tasks and the resolved
architectural decisions, produce a detailed implementation plan section for
your domain. Include:
- File/folder structure
- Key interfaces and data models
- Step-by-step implementation notes
- Integration points with other agents
- Traceability: reference PRD section IDs for every item

Return your plan as structured Markdown.
"""


def implementation_agent_prompt(
    agent_name: str,
    tasks: list[AgentTask],
    decisions: list,
    prd_sections: list[PRDSection],
) -> tuple[str, str]:
    system = IMPLEMENTATION_SYSTEM_TEMPLATE.format(agent_name=agent_name)
    task_text = "\n".join(f"- {t.description} (PRD refs: {t.prd_section_ids})" for t in tasks)
    decision_text = "\n".join(
        f"- {d.category.value}: {d.resolution}" for d in decisions if d.resolution
    )
    section_text = "\n".join(f"[{s.id}] {s.title}" for s in prd_sections)
    user = (
        f"Tasks:\n{task_text}\n\n"
        f"Decisions:\n{decision_text}\n\n"
        f"PRD Sections:\n{section_text}"
    )
    return (system, user)


# ---------------------------------------------------------------------------
# QA Agents
# ---------------------------------------------------------------------------

QA_SYSTEM_TEMPLATE = """\
You are the QA agent paired with {agent_name}. Review the implementation plan
produced by your paired agent and validate:
1. All assigned PRD requirements are addressed
2. No contradictions with resolved decisions
3. Integration points are clearly defined
4. No obvious gaps or ambiguities

Return valid JSON: {{passed: bool, issues: [...], suggestions: [...]}}
"""


def qa_agent_prompt(
    agent_name: str,
    agent_output: str,
    tasks: list[AgentTask],
    prd_sections: list[PRDSection],
) -> tuple[str, str]:
    system = QA_SYSTEM_TEMPLATE.format(agent_name=agent_name)
    task_text = "\n".join(f"- {t.description}" for t in tasks)
    return (system, f"Agent output:\n{agent_output}\n\nTasks:\n{task_text}")


# ---------------------------------------------------------------------------
# Critic Agents
# ---------------------------------------------------------------------------

AUDITOR_CRITIC_SYSTEM = """\
You are the Auditor Critic. Review the full set of agent outputs and verify:
- Every PRD requirement is traced to at least one implementation task
- No requirements are missed or duplicated without reason
- Cross-agent dependencies are consistent

Return JSON: {verdict: "pass"|"fail", issues: [...], recommendations: [...]}
"""

SECURITY_CRITIC_SYSTEM = """\
You are the Security Critic. Review all agent outputs for:
- OWASP Top 10 risks in the proposed architecture
- Auth/authz gaps
- Data exposure risks
- Input validation gaps
- Secrets management

Return JSON: {verdict: "pass"|"fail", issues: [...], recommendations: [...]}
"""

IMPLEMENTATION_CRITIC_SYSTEM = """\
You are the Implementation Critic. Review all agent outputs for:
- Code quality and maintainability
- Proper separation of concerns
- Scalability considerations
- Error handling strategy
- Testing strategy completeness

Return JSON: {verdict: "pass"|"fail", issues: [...], recommendations: [...]}
"""

OBSERVABILITY_CRITIC_SYSTEM = """\
You are the Observability Critic. Review all agent outputs for:
- Logging strategy
- Metrics and monitoring
- Tracing / distributed tracing
- Alerting recommendations
- Health check endpoints

Return JSON: {verdict: "pass"|"fail", issues: [...], recommendations: [...]}
"""

CRITIC_SYSTEMS = {
    "auditor_critic": AUDITOR_CRITIC_SYSTEM,
    "security_critic": SECURITY_CRITIC_SYSTEM,
    "implementation_critic": IMPLEMENTATION_CRITIC_SYSTEM,
    "observability_critic": OBSERVABILITY_CRITIC_SYSTEM,
}


def critic_agent_prompt(critic_name: str, agent_outputs: dict[str, str]) -> tuple[str, str]:
    system = CRITIC_SYSTEMS[critic_name]
    combined = "\n\n---\n\n".join(
        f"## {name}\n{output}" for name, output in agent_outputs.items()
    )
    return (system, f"Agent outputs to review:\n\n{combined}")


# ---------------------------------------------------------------------------
# Finalize
# ---------------------------------------------------------------------------

FINALIZE_SYSTEM = """\
You are a technical writer. Given all agent outputs, QA results, critic
feedback, and resolved decisions, produce the final deliverables:

1. **Architecture overview** — high-level diagram description and component map
2. **Implementation plan** — ordered, detailed steps with PRD traceability
3. **Repo structure** — proposed directory tree
4. **Setup commands** — local dev environment setup (install, env, db, etc.)
5. **Run commands** — how to start/test/deploy locally

Return structured Markdown with clear headings for each section.
"""


def finalize_prompt(state: PlanGeneratorState) -> tuple[str, str]:
    outputs = "\n\n---\n\n".join(
        f"## {name}\n{output}" for name, output in state.agent_outputs.items()
    )
    qa = "\n".join(
        f"- {r.agent_name}: {'PASS' if r.passed else 'FAIL'} — issues: {r.issues}"
        for r in state.qa_results
    )
    critics = "\n".join(
        f"- {f.critic_name} (iter {f.iteration}): {f.verdict.value} — {f.issues}"
        for f in state.critic_feedback
    )
    decisions = "\n".join(
        f"- {d.category.value}: {d.resolution}" for d in state.decisions if d.resolution
    )
    return (
        FINALIZE_SYSTEM,
        (
            f"Agent Outputs:\n{outputs}\n\n"
            f"QA Results:\n{qa}\n\n"
            f"Critic Feedback:\n{critics}\n\n"
            f"Decisions:\n{decisions}"
        ),
    )
