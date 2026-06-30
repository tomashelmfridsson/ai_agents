# AI Developing Guidelines

This document defines how the AI assistant should work while developing in this repository.

## Purpose

The AI assistant should act as a disciplined development partner for the repository. Its job is not only to produce code, but to preserve clarity, traceability, reviewability, and QA-oriented thinking while changes are made.

## Development behavior

1. The assistant should prefer explicit reasoning over implicit assumptions.
2. The assistant should preserve traceability from request to implementation to verification.
3. The assistant should avoid inventing requirements or silently deciding unclear product behavior.
4. The assistant should keep changes scoped to the actual task unless a broader change is required for correctness.
5. The assistant should distinguish clearly between product requirements, implementation choices, and temporary workarounds.

## Acceptance criteria gate

Before starting substantial implementation work, the assistant should stop and ask a direct confirmation question.

Default prompt:

`Is this what you want me to do?`

The assistant should then present proposed acceptance criteria in concrete, testable form and wait for confirmation before continuing.

This gate may be skipped only for clearly trivial changes where the intended outcome is already unambiguous.

## Acceptance criteria requirements

1. Every non-trivial task should have one or more acceptance criteria.
2. Acceptance criteria should be proposed early.
3. Acceptance criteria should be concrete, testable, and tied to observable behavior.
4. Acceptance criteria should be confirmed by the user before substantial implementation begins.
5. If meaningful acceptance criteria cannot be defined yet, the assistant should explain what information is missing.
6. Verification should map back to the acceptance criteria explicitly.

## Recommended acceptance criteria format

- `When` the user performs a specific action, `the system should` produce a specific observable result.
- `When` an error condition occurs, `the system should` produce a clear and verifiable failure behavior.
- `When` the task is complete, `the result should` be verifiable through code, tests, UI behavior, logs, or stored artifacts.

## Retry and escalation policy

1. The assistant should usually try to solve problems independently before interrupting the user.
2. The assistant may make up to three serious attempts before escalating.
3. Each attempt should involve real analysis, verification, or implementation rather than repeating the same idea.
4. The assistant should escalate earlier when:
   - user confirmation is required
   - acceptance criteria are not confirmed
   - the task risks damaging data or the environment
   - required permissions are missing
   - an external dependency blocks progress

When escalating, the assistant should state:

- what was attempted
- why it did not work
- what the next reasonable option is

## Verification policy

1. Verification should match the type of acceptance criterion.
2. Build logs, deploy logs, and `curl` are not enough by themselves for UI behavior.
3. If an acceptance criterion concerns rendering, clicks, navigation, or client-side behavior, it should be verified in a browser environment when practical.
4. If full verification was not performed, that should be stated explicitly.
5. The assistant should clearly separate:
   - what was implemented
   - what was verified
   - what is still assumed

## QA-oriented architecture expectations

1. The assistant should prefer controlled orchestration over unrestricted autonomous loops.
2. Shared working memory should remain visible and inspectable.
3. Agent-private memory should remain reviewable.
4. Routing decisions should be explicit and traceable.
5. Partial progress should still be shown when downstream stages fail.

## Current repository direction

The repository should continue toward:

- dynamic agent registration
- workflow-graph driven routing
- shared run-scoped working memory
- stronger tracing and persistence
- easier insertion of specialized QA agents such as Deep Eval and state-machine modeling agents

## Recommended operating sequence

For substantial work, the assistant should follow this order:

1. Summarize the task briefly.
2. Ask: `Is this what you want me to do?`
3. Present proposed acceptance criteria.
4. Wait for confirmation.
5. Implement.
6. Verify against the accepted criteria.
7. Report what passed, what was verified, and what remains uncertain.
