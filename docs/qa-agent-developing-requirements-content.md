# QA Agent Developing Requirements

This document describes the current product-level requirements for the QA Agent app itself.

## Product name

`QA Agent Workbench`

## Purpose

The system should help a user transform raw requirement text into structured QA outputs through orchestrated specialized agents, with visible progress, traceability, shared working memory, and controlled feedback loops.

## Primary users

- QA engineer
- test analyst
- developer evaluating local LLM-based QA workflows
- researcher comparing orchestration patterns and models

## Core user goals

- enter or load a scenario and requirement text
- configure how agents run
- run a multi-agent QA workflow
- observe progress while it runs
- inspect intermediate and final outputs
- understand why the workflow stopped, backtracked, or failed
- review logs, working memory, and traceability
- compare structured baseline and LLM-backed execution

## Functional requirements

1. The system should allow the user to enter or load a scenario title and requirement text.
2. The system should allow per-agent configuration for execution mode, provider, model, timeout, and directives.
3. The system should allow one shared LLM configuration to be applied across all agents, while still allowing per-agent overrides.
4. The system should orchestrate specialized agents for requirements analysis, test design, review, and routing.
5. The system should support selective backtracking instead of only full reruns.
6. The system should display run status, run report, runtime activity, and working memory during execution.
7. The system should show completed agent results even if a later agent fails.
8. The system should fail fast when a selected local Ollama model is missing.
9. The system should persist run logs and allow the user to download them.
10. The system should maintain shared run-scoped memory visible in the GUI.
11. The system should support adding new specialized agents without redesigning the whole application structure.

## Non-functional requirements

1. The system should run locally on a developer workstation.
2. The system should support local Ollama inference.
3. The system should provide understandable error messages for configuration and runtime failures.
4. The system should surface runtime progress within a few seconds after run start.
5. The system should enforce per-agent timeout limits.
6. The system should preserve traceability between source requirements and generated QA artifacts.
7. The system should remain usable for research comparison between orchestration strategies and models.
8. The system should maintain readable high-contrast text in the GUI during idle, running, error, and completed states.

## Orchestration requirements

1. The orchestrator should be the routing authority.
2. Downstream agents should not proceed without required upstream artifacts.
3. Routing decisions that affect backtracking or stopping should be inspectable.
4. The workflow should preserve partial progress when later stages fail.
5. The workflow should allow controlled feedback loops bounded by configurable run controls.

## Memory and traceability requirements

1. Shared working memory should be visible to the user.
2. Agent-private memory should be visible to the user.
3. The memory timeline should show how the run evolved.
4. The run log should capture the executed stages, resolved models, timeouts, and summary results.
5. Requirements should remain traceable to generated test designs and review findings.

## Current GUI requirements

1. The GUI should expose run controls with clear explanations.
2. The GUI should expose local backend settings.
3. The GUI should expose a global LLM settings section for bulk updates.
4. The GUI should expose per-agent configuration sections.
5. The GUI should expose result panels for status, report, runtime activity, and working memory.
6. The GUI should provide links to project documentation published through GitHub Pages.

## Example acceptance criteria

- When the user starts a run, the GUI should show runtime progress before the workflow completes.
- When an Ollama model is configured but not installed locally, the run should fail immediately with a clear error.
- When Agent 1 completes and Agent 2 fails, Agent 1’s completed result should still be visible.
- When the workflow runs, the GUI should display shared memory, agent-private memory, and memory timeline.
- When the user downloads the run log, the file should contain the executed stages, models, timeouts, and results.
- When the user applies a global LLM configuration, all agents should update unless the user later changes a specific agent manually.

## Open architecture direction

The product should continue toward:

- richer routing explanations
- stronger run-log completeness
- more declarative orchestration
- easier insertion of new agent types
- better persistence and inspection of memory and handoffs
