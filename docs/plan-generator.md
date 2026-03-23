You are a senior AI systems engineer specializing in LangGraph and multi-agent orchestration.

Your task is to design and output a production-ready LangGraph implementation for a multi-agent software factory that builds an implementation plan from a PRD.

The system must strictly follow the requirements below.

---

## CORE REQUIREMENTS

- Human-in-the-loop decision checkpoints (hard stops)
- Parallel agent execution
- QA agents paired to each implementation agent
- Critic agents:
  - Auditor Critic
  - Security Critic
  - Implementation Critic
  - Observability Critic
- Critic loop runs 3 times OR until convergence (no changes)
- Full traceability to PRD
- Outputs implementation plan + local dev commands

---

## GRAPH DESIGN

### State Object

Define a strongly-typed shared state that includes:

- prd_sections
- decisions (with status: pending/resolved)
- tasks_by_agent
- qa_results
- critic_feedback
- iteration_count
- final_outputs

---

### Nodes (LangGraph)

You MUST define the following nodes:

1. **ingest_prd**
   - Parse PRD into structured sections

2. **decompose_prd**
   - Extract modules, domains, dependencies

3. **decision_checkpoint (INTERRUPT NODE)**
   - Detect unresolved architectural decisions
   - Present options (2–3 with pros/cons)
   - PAUSE execution until user input

4. **plan_parallel_work**
   - Create task graph
   - Assign to agents

5. **implementation_agents (PARALLEL NODE)**
   - Fan-out execution:
     - frontend_agent
     - backend_agent
     - payments_agent
     - checkout_agent
     - inventory_agent
     - auth_agent
     - analytics_agent

6. **qa_agents (PARALLEL NODE)**
   - Each QA agent validates its paired implementation agent

7. **critic_agents (PARALLEL NODE)**
   - auditor_critic
   - security_critic
   - implementation_critic
   - observability_critic

8. **critic_router**
   - If feedback exists → loop back to implementation_agents
   - Else → proceed

9. **finalize_outputs**
   - Generate:
     - architecture
     - implementation plan
     - repo structure
     - setup/run commands

---

## GRAPH FLOW

ingest_prd
  → decompose_prd
  → decision_checkpoint (interrupt)
  → plan_parallel_work
  → implementation_agents (parallel fan-out)
  → qa_agents (parallel fan-out)
  → critic_agents (parallel fan-out)
  → critic_router
      → (loop to implementation_agents if iteration < 3 AND feedback exists)
      → finalize_outputs

---

## LOOP LOGIC

- Maintain iteration_count in state
- Run max 3 iterations
- Exit early if ALL critics return "no issues"

---

## IMPLEMENTATION DETAILS

- Use LangGraph (Python)
- Use async execution for parallel nodes
- Use TypedDict or Pydantic for state
- Each agent should be a callable node
- Include clear logging at each step

---

## HUMAN-IN-THE-LOOP

- decision_checkpoint must:
  - Detect missing decisions:
    - backend framework
    - frontend framework
    - database
    - API style
    - auth strategy
    - infra
  - Return structured options
  - Pause execution until user resolves

---

## OUTPUT REQUIREMENTS

Return:

1. Full LangGraph code (Python)
2. State definition
3. Node implementations (stubs + prompts)
4. Graph wiring
5. Example CLI runner
6. Example of interrupt/resume flow

---

## QUALITY BAR

- Production-grade structure
- Clean separation of concerns
- Extensible
- Clear developer ergonomics

Do NOT summarize. Output full code.