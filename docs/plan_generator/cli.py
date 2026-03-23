"""
CLI runner for the plan generator graph.

Demonstrates:
- Loading a PRD from file or stdin
- Running the graph
- Handling interrupt/resume for human-in-the-loop decisions
- Printing final outputs

Usage:
    # From a file
    python -m plan_generator.cli --prd path/to/prd.md

    # From stdin
    cat prd.md | python -m plan_generator.cli --prd -

    # Resume with decisions from a JSON file
    python -m plan_generator.cli --prd path/to/prd.md --decisions decisions.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import uuid
from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver

from .graph import build_graph
from .state import FinalOutputs


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _read_prd(prd_path: str) -> str:
    """Read PRD from file path or stdin (if '-')."""
    if prd_path == "-":
        return sys.stdin.read()
    return Path(prd_path).read_text(encoding="utf-8")


def _read_decisions(decisions_path: str | None) -> dict | None:
    """Read pre-supplied decisions from a JSON file."""
    if not decisions_path:
        return None
    return json.loads(Path(decisions_path).read_text(encoding="utf-8"))


def _prompt_decisions_interactive(interrupt_value: dict) -> dict:
    """
    Interactively prompt the user to resolve architectural decisions.

    Args:
        interrupt_value: The interrupt payload from decision_checkpoint.

    Returns:
        Dict of {category: {resolution: str, rationale: str}}.
    """
    print("\n" + "=" * 60)
    print("DECISION CHECKPOINT — Human Input Required")
    print("=" * 60)

    decisions = interrupt_value.get("decisions", [])
    resolutions = {}

    for i, decision in enumerate(decisions, 1):
        category = decision["category"]
        question = decision["question"]
        options = decision.get("options", [])

        print(f"\n--- Decision {i}/{len(decisions)}: {category} ---")
        print(f"Question: {question}\n")

        for j, opt in enumerate(options, 1):
            print(f"  [{j}] {opt['name']}")
            for pro in opt.get("pros", []):
                print(f"      + {pro}")
            for con in opt.get("cons", []):
                print(f"      - {con}")
            print()

        while True:
            choice = input(f"Choose option (1-{len(options)}): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(options):
                chosen = options[int(choice) - 1]
                rationale = input("Rationale (optional, press Enter to skip): ").strip()
                resolutions[category] = {
                    "resolution": chosen["name"],
                    "rationale": rationale or f"Selected {chosen['name']}",
                }
                break
            print("Invalid choice, try again.")

    print("\n" + "=" * 60)
    print("Decisions resolved — resuming graph execution")
    print("=" * 60 + "\n")

    return resolutions


def _print_final_outputs(outputs: dict):
    """Pretty-print the final deliverables."""
    final = outputs.get("final_outputs")
    if not final:
        print("\n[WARNING] No final outputs generated.")
        return

    if isinstance(final, dict):
        final = FinalOutputs(**final)

    print("\n" + "=" * 70)
    print("PLAN GENERATOR — FINAL OUTPUT")
    print("=" * 70)

    if final.architecture:
        print("\n## Architecture\n")
        print(final.architecture)

    if final.implementation_plan:
        print("\n## Implementation Plan\n")
        print(final.implementation_plan)

    if final.repo_structure:
        print("\n## Repo Structure\n")
        print(final.repo_structure)

    if final.setup_commands:
        print("\n## Setup Commands\n")
        for cmd in final.setup_commands:
            print(f"  $ {cmd}")

    if final.run_commands:
        print("\n## Run Commands\n")
        for cmd in final.run_commands:
            print(f"  $ {cmd}")

    print("\n" + "=" * 70)


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

async def run(prd_text: str, pre_decisions: dict | None = None):
    """
    Execute the plan generator graph end-to-end.

    Handles the interrupt/resume cycle for decision checkpoints.
    """
    checkpointer = MemorySaver()
    graph = build_graph(checkpointer=checkpointer)

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {"prd_raw": prd_text}

    print("[plan-generator] Starting graph execution...")
    print(f"[plan-generator] Thread ID: {thread_id}\n")

    # First invocation — runs until interrupt or completion
    result = await graph.ainvoke(initial_state, config=config)

    # Handle interrupt/resume loop
    while True:
        # Check graph state for pending interrupts
        graph_state = graph.get_state(config)

        if not graph_state.tasks:
            # No pending tasks — graph completed
            break

        # Find interrupt tasks
        interrupts = []
        for task in graph_state.tasks:
            if hasattr(task, "interrupts") and task.interrupts:
                interrupts.extend(task.interrupts)

        if not interrupts:
            break

        # Process each interrupt (typically just one: decision_checkpoint)
        for irpt in interrupts:
            interrupt_value = irpt.value

            if pre_decisions:
                # Use pre-supplied decisions
                resolutions = pre_decisions
                pre_decisions = None  # Only use once
            else:
                # Interactive prompt
                resolutions = _prompt_decisions_interactive(interrupt_value)

            # Resume graph with user resolutions
            from langgraph.types import Command

            result = await graph.ainvoke(
                Command(resume=resolutions),
                config=config,
            )

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Plan Generator — Multi-Agent Software Factory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m plan_generator.cli --prd my_prd.md
  python -m plan_generator.cli --prd my_prd.md --decisions decisions.json
  python -m plan_generator.cli --prd my_prd.md --verbose
        """,
    )
    parser.add_argument(
        "--prd", required=True,
        help="Path to PRD file (or '-' for stdin)",
    )
    parser.add_argument(
        "--decisions",
        help="Path to JSON file with pre-supplied decisions (skips interactive prompt)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--output", "-o",
        help="Write final output to file (Markdown)",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Read inputs
    prd_text = _read_prd(args.prd)
    pre_decisions = _read_decisions(args.decisions)

    # Run
    result = asyncio.run(run(prd_text, pre_decisions))

    # Output
    _print_final_outputs(result)

    # Optionally write to file
    if args.output:
        final = result.get("final_outputs")
        if isinstance(final, dict):
            final = FinalOutputs(**final)
        if final:
            output_parts = []
            if final.architecture:
                output_parts.append(f"# Architecture\n\n{final.architecture}")
            if final.implementation_plan:
                output_parts.append(f"# Implementation Plan\n\n{final.implementation_plan}")
            if final.repo_structure:
                output_parts.append(f"# Repo Structure\n\n{final.repo_structure}")
            if final.setup_commands:
                output_parts.append(
                    "# Setup Commands\n\n" +
                    "\n".join(f"```bash\n{cmd}\n```" for cmd in final.setup_commands)
                )
            if final.run_commands:
                output_parts.append(
                    "# Run Commands\n\n" +
                    "\n".join(f"```bash\n{cmd}\n```" for cmd in final.run_commands)
                )

            Path(args.output).write_text("\n\n---\n\n".join(output_parts), encoding="utf-8")
            print(f"\n[plan-generator] Output written to {args.output}")


if __name__ == "__main__":
    main()
