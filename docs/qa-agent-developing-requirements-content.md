# QA Agent Developing Requirements

This document should be read as the **study-specific working requirements** for this repository and its QA Agent POC. It is not a generic product specification for any future QA platform. The purpose is to describe what the demonstrator in this study needed to support, what the implemented solution now actually supports, and what remains directional rather than fully realized.

## Study context

These requirements belong to a research-oriented POC that investigates how a QA-oriented multi-agent workflow can transform raw requirement text into structured QA outputs. The study compares:

- the repository's own `ai_agents` solution
- a `LangGraph` comparison track
- external and local model strategies
- hosted agent execution versus more direct in-app orchestration

The requirements should therefore be interpreted as requirements for **this study's demonstrator and comparison environment**, not as a final enterprise product scope.

## Product name

`QA Agent Workbench`

## Purpose

The system should help a user transform raw requirement text into structured QA outputs through orchestrated specialized agents, with visible progress, traceability, shared working memory, controlled feedback loops, and enough runtime transparency to support comparative study work.

## Primary users in this study

- researcher evaluating agentic QA workflows
- Senior QA or test analyst reviewing generated outputs
- developer experimenting with orchestration patterns, runtime choices, and model backends

## Core study goals

- enter or load a scenario and requirement text
- configure how agents run
- run a multi-agent QA workflow
- observe progress while it runs
- inspect intermediate and final outputs
- understand why the workflow stopped, backtracked, or failed
- review logs, working memory, and traceability
- compare structured baseline, local-model, service-based, and hosted execution patterns
- compare the repository's own solution with the `LangGraph` comparison track

## Current validated scope

The current repository and associated study work show that the demonstrator supports:

- orchestrator-led routing in the main `ai_agents` solution
- specialized roles for requirements analysis, test design, and review
- selective backtracking instead of only full reruns
- shared working memory, agent-private memory, and memory timeline visibility
- runtime activity, run report, and partial-result preservation on failure
- local execution strategies such as `Ollama`
- hosted execution via `qa-agent-service`
- comparison against a separate `LangGraph` solution
- documentation published through GitHub Pages

## Functional requirements for this study

1. The system should allow the user to enter or load a scenario title and requirement text.
2. The system should allow per-agent configuration for execution mode, provider, model, timeout, and directives where that is supported by the active backend.
3. The system should allow one shared LLM configuration to be applied across all agents, while still allowing per-agent overrides in the main app flow.
4. The system should orchestrate specialized agents for requirements analysis, test design, review, and routing.
5. The system should support selective backtracking instead of only full reruns.
6. The system should display run status, run report, runtime activity, and working memory during execution.
7. The system should show completed agent results even if a later agent fails.
8. The system should fail fast when a selected local Ollama model is missing.
9. The system should persist run logs and allow the user to download them.
10. The system should maintain shared run-scoped memory visible in the GUI.
11. The system should support study-driven comparison between at least two orchestration approaches, where the repository's own solution and a `LangGraph` comparison track can be discussed side by side.
12. The system should expose links to the project's study documentation so the implementation can be read together with the written material.

## Non-functional requirements for this study

1. The system should run locally on a developer workstation.
2. The system should support local model experimentation through `Ollama`.
3. The system should support hosted agent execution through `qa-agent-service`.
4. The system should provide understandable error messages for configuration and runtime failures.
5. The system should surface runtime progress within a few seconds after run start.
6. The system should enforce per-agent timeout limits where the active runtime supports them.
7. The system should preserve traceability between source requirements and generated QA artifacts.
8. The system should remain usable for research comparison between orchestration strategies, model backends, and hosted versus local execution choices.
9. The system should maintain readable high-contrast text in the GUI during idle, running, error, and completed states.

## Orchestration requirements

1. The orchestrator should be the routing authority in the repository's own `ai_agents` solution.
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

## GUI requirements

1. The GUI should expose run controls with clear explanations.
2. The GUI should expose backend settings for both local and hosted execution patterns used in the study.
3. The GUI should expose a global LLM settings section for bulk updates where relevant.
4. The GUI should expose per-agent configuration sections in the main `ai_agents` flow.
5. The GUI should expose result panels for status, report, runtime activity, and working memory.
6. The GUI should provide links to project documentation published through GitHub Pages.
7. Documentation links should preferably open in a separate browser tab when that improves readability or avoids in-app scrolling limitations.

## Comparison-specific clarification

Not every requirement above applies identically to every comparison track.

- The repository's own `ai_agents` solution is the main reference implementation for shared working memory, runtime visibility, and orchestrator-first routing.
- The `LangGraph` solution functions as a comparison track for graph-based orchestration and should not be forced to mirror every UI or implementation detail of the main app.
- `qa-agent-service` represents a service-oriented execution pattern and should be understood as part of the study architecture, not as proof that all agents always run locally in one app.

## Example acceptance criteria

- When the user starts a run, the GUI should show runtime progress before the workflow completes.
- When an Ollama model is configured but not installed locally, the run should fail immediately with a clear error.
- When one completed stage is followed by a later failure, the completed result should still be visible.
- When the workflow runs, the GUI should display shared memory, agent-private memory, and memory timeline in the main `ai_agents` solution.
- When the user downloads the run log, the file should contain the executed stages, models, timeouts, and results.
- When the user opens documentation from the app, the linked study pages should be readable without being blocked by in-app scrolling constraints.

## Directional items, not guaranteed current behavior

The following should be treated as direction or extension targets rather than fully guaranteed current scope:

- richer routing explanations
- more declarative orchestration
- easier insertion of new agent types
- stronger persistence and inspection of handoffs
- deeper framework comparison across more external agent platforms

---

This material has been developed together with Generative AI and then reviewed and adapted to match the repository's actual study scope.
