# AI Developing Guidelines

This document defines **study-specific development guidelines** for AI-assisted work in this repository. It should not be read as a universal instruction set for every future AI assistant or every future project. Its role is to capture the development principles that best fit this repository's QA-oriented study, documentation needs, and comparison-driven experimentation.

## Purpose

The AI assistant should act as a disciplined development partner for this study repository. Its job is not only to produce code or text, but to preserve clarity, traceability, reviewability, and QA-oriented thinking while documentation, experiments, comparisons, and implementation evolve.

## Repository-specific context

The repository is not only an application codebase. It is also a study artifact containing:

- a QA-oriented demonstrator
- comparison material for the repository's own `ai_agents` solution and a `LangGraph` track
- study documentation and concept explanations
- runtime and architecture choices that need to remain explainable after the fact

Because of that, AI-assisted work in this repository should favor explicitness and auditability over speed alone.

## Development behavior

1. The assistant should prefer explicit reasoning over implicit assumptions.
2. The assistant should preserve traceability from request to implementation to verification.
3. The assistant should avoid inventing requirements or silently deciding unclear study behavior.
4. The assistant should keep changes scoped to the actual task unless a broader change is required for correctness or consistency.
5. The assistant should distinguish clearly between study requirements, implementation choices, comparison findings, and temporary workarounds.
6. The assistant should state when a statement is study-specific rather than generally applicable.

## Requirements and acceptance criteria handling

1. Non-trivial work should be guided by concrete acceptance criteria or observable intended outcomes.
2. Acceptance criteria do not always need to be presented as a formal gate before implementation, but they should be made explicit when the task is ambiguous, risky, broad, or likely to affect behavior in multiple places.
3. When acceptance criteria are already implicit in the request and the task is straightforward, the assistant may implement directly and verify afterward.
4. If meaningful acceptance criteria cannot yet be defined, the assistant should explain what is missing.
5. Verification should map back to the intended outcome explicitly.

## Recommended acceptance criteria format

- `When` the user performs a specific action, `the system should` produce a specific observable result.
- `When` an error condition occurs, `the system should` produce a clear and verifiable failure behavior.
- `When` the task is complete, `the result should` be verifiable through code, tests, UI behavior, logs, stored artifacts, or published documentation.

## Retry and escalation policy

1. The assistant should usually try to solve problems independently before interrupting the user.
2. Multiple real attempts are preferable to shallow repetition.
3. The assistant should escalate earlier when:
   - user confirmation is genuinely required
   - the task risks damaging data or the environment
   - required permissions are missing
   - an external dependency blocks progress
   - the current repository state conflicts with the requested change

When escalating, the assistant should state:

- what was attempted
- why it did not work
- what the next reasonable option is

## Verification policy

1. Verification should match the type of requirement or intended outcome.
2. Build logs, deploy logs, and `curl` are not enough by themselves for UI behavior.
3. If an acceptance criterion concerns rendering, clicks, navigation, or client-side behavior, it should be verified in a browser environment when practical.
4. If full verification was not performed, that should be stated explicitly.
5. The assistant should clearly separate:
   - what was implemented
   - what was verified
   - what is still assumed

## QA-oriented architecture expectations

These are expectations that reflect the current study direction rather than absolute laws for every future version:

1. The repository's own `ai_agents` solution should prefer controlled orchestration over unrestricted autonomous loops.
2. Shared working memory should remain visible and inspectable where it is part of the main app design.
3. Agent-private memory should remain reviewable where exposed by the main app.
4. Routing decisions should be explicit and traceable.
5. Partial progress should still be shown when downstream stages fail.
6. Hosted service execution and local execution should remain distinguishable in the study narrative and, where practical, in the interface.

## Documentation expectations

1. Documentation should reflect the actual implemented state of the repository, not only earlier intentions.
2. When the written study material and the implemented system diverge, the divergence should be clarified rather than hidden.
3. Comparison-track documents should not overstate parity between the main `ai_agents` solution and the `LangGraph` solution.
4. Project-specific terms such as shared working memory, selective backtracking, or review gate should be marked clearly when they are being used in a study-specific way.
5. Public-facing study pages should remain readable and navigable, including when documentation is opened from the app.

## Current repository direction

The repository currently points toward:

- explicit orchestration and comparison-friendly runtime behavior
- stronger tracing and persistence
- clearer distinction between local, hosted, and service-based execution paths
- maintainable study documentation that matches the real implementation
- continued comparison between the repository's own solution and external framework approaches such as `LangGraph` and `Hermes`

## Practical operating sequence

For substantial work, the assistant should usually follow this order:

1. Understand the requested outcome and the relevant repository context.
2. Identify whether the task is primarily documentation, implementation, comparison maintenance, or verification.
3. Make acceptance criteria or intended outcomes explicit when needed.
4. Implement or update the relevant files.
5. Verify the result at the level that is practical for the task.
6. Report what changed, what was verified, and what remains assumed or not yet checked.

---

This material has been developed together with Generative AI and then reviewed and adapted to match the repository's actual study and implementation context.
