# QA compare final report — HF QA Agent Service vs Hermes Swarm/internal baseline

## Executive summary

I compiled the six completed compare scenarios from their parent artifacts, Dashboard-visible comments, and parent-task metadata/log evidence.

**Overall result: Hermes Swarm/internal baseline won all 6 scenarios.**

Why Hermes won:
- It was consistently more complete and more directly executable.
- It covered boundary, negative, authorization, integrity, and concurrency cases that the HF service often omitted.
- The HF service was useful as a fast structured seed in every scenario, but all six final HF reviewer verdicts remained `requires_revision`.
- HF service token usage was not exposed by the public service responses, so only Hermes-side orchestration/session tokens were measurable.

Cross-scenario criterion outcome counts:
- Readability: Hermes 3, Tie 3, HF 0
- Correctness: Hermes 6, HF 0
- Completeness: Hermes 6, HF 0
- Relevance: Hermes 5, Tie 1, HF 0
- Usability: Hermes 6, HF 0

Average scores across all six scenarios:

| Criterion | HF average | Hermes average | Winner |
|---|---:|---:|---|
| Readability | 3.83 | 4.50 | Hermes |
| Correctness | 3.17 | 5.00 | Hermes |
| Completeness | 2.33 | 5.00 | Hermes |
| Relevance | 3.67 | 4.50 | Hermes |
| Usability | 3.17 | 5.00 | Hermes |

## Overall comparison table

| Scenario | HF reviewer verdict | HF coverage ratio | HF test cases | Hermes test cases | HF total score | Hermes total score | Overall winner | Assessment |
|---|---|---:|---:|---:|---:|---:|---|---|
| 1. Login and registration | requires_revision | 0.75 | 4 | 25 | 16 | 24 | Hermes | Hermes is immediately usable; HF is a concise seed only. |
| 2. E-commerce checkout | requires_revision | 0.80 | 4 | 12 | 16 | 25 | Hermes | Hermes adds payment negatives, idempotency, and end-to-end continuity. |
| 3. Password reset | requires_revision | 0.75 | 4 | 12 | 15 | 23 | Hermes | Hermes covers the critical security and regression gaps HF missed. |
| 4. Support tickets | requires_revision | 0.83 | 6 | 12 | 18 | 24 | Hermes | HF improved most here, but Hermes still has better role, ownership, and freshness coverage. |
| 5. Inventory management | requires_revision | 0.8333 | 6 | 16 | 15 | 23 | Hermes | Hermes handles domain-specific inventory risk much better. |
| 6. Course enrollment | requires_revision | 0.75 | 3 | 12 | 17 | 25 | Hermes | Hermes covers seats, concurrency, duplicate enrollments, and integrity depth HF lacked. |

## Token usage and measurement notes

Measurement method:
- For each parent compare task, the parent task's recorded worker/session evidence was used together with Hermes local session metadata.
- These are Hermes session-level token counts, not HF service model tokens.
- In some parent artifacts, embedded token tables were point-in-time snapshots before final completion; local session metadata was treated as the stronger final source for Hermes-side counts.

HF QA Agent Service token visibility:
- Not exposed by service responses for all six scenarios.
- Public REST outputs exposed status, outputs, durations, coverage/reviewer data, and run ids, but no token or cost fields.
- Therefore the HF column below records `not exposed by service`, and Hermes-side orchestration remains the only measurable token usage.

Cost note:
- Hermes ran on `gpt-5.5`. Using OpenAI's official standard short-context pricing from July 9, 2026 (`$5.00 / 1M` input tokens, `$0.50 / 1M` cached input tokens, `$30.00 / 1M` output tokens), Hermes' measurable usage in these six scenarios corresponds to about `6.94 USD` including cache reads, or about `4.99 USD` if only input and output tokens are counted.
- In contrast, `qa-agent-service` was run here against free LLMs, so these comparison runs had no direct OpenAI API cost on that side. If the same `qa-agent-service` token volumes had instead been billed at `gpt-5.5` standard API rates, the corresponding cost would have been about `3.46 USD` for the six scenarios.

| Scenario | Hermes session id | Model | Input tokens | Output tokens | Cache read | Cache write | Reasoning tokens | API calls | Tool calls | HF service tokens |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1. Login and registration | 20260706_122325_589974 | gpt-5.5 | 113330 | 9992 | 622592 | 0 | 1626 | 18 | 22 | not exposed by service |
| 2. E-commerce checkout | 20260706_122820_5c2fc1 | gpt-5.5 | 113466 | 11630 | 732160 | 0 | 1062 | 20 | 27 | not exposed by service |
| 3. Password reset | 20260706_122325_13ad06 | gpt-5.5 | 57609 | 7829 | 377856 | 0 | 1067 | 12 | 13 | not exposed by service |
| 4. Support tickets | 20260706_122820_33227c | gpt-5.5 | 63444 | 11668 | 652800 | 0 | 746 | 18 | 21 | not exposed by service |
| 5. Inventory management | 20260706_122325_651ab2 | gpt-5.5 | 127381 | 12584 | 732672 | 0 | 1833 | 21 | 32 | not exposed by service |
| 6. Course enrollment | 20260706_122820_0d8014 | gpt-5.5 | 106681 | 15661 | 786432 | 0 | 1424 | 17 | 24 | not exposed by service |
| **Total Hermes measurable orchestration/session usage** | 6 sessions | gpt-5.5 | **581911** | **69364** | **3904512** | **0** | **7758** | **106** | **139** | **HF service totals not measurable** |

## Per-scenario scoring with concise justification

### Scenario 1 — login and registration
Artifact: `/Users/tomashelmfridsson/.hermes/kanban/boards/hermes-qa-agent/workspaces/t_48cf121d/scenario1_login_registration_comparison.md`

| Criterion | HF score | Hermes score | Winner | Brief justification |
|---|---:|---:|---|---|
| Readability | 3 | 5 | Hermes | HF is structured but sparse; Hermes uses clearer manual-test layout and priorities. |
| Correctness | 4 | 5 | Hermes | HF captures the explicit requirements, but Hermes handles auth and invalid-credential behavior more safely. |
| Completeness | 2 | 5 | Hermes | HF produced only four core cases; Hermes covers positive, negative, admin, session, accessibility, usability, and conditional reset paths. |
| Relevance | 4 | 4 | Tie | HF stays close to the brief; Hermes adds release-QA adjacent checks. |
| Usability | 3 | 5 | Hermes | Hermes cases are more directly executable as manual or e2e tests. |

Recommendation: Use the Hermes/Kanban-style baseline as the immediate QA execution set. HF is useful as a fast seed and review signal, but its final reviewer verdict remained `requires_revision`.

### Scenario 2 — e-commerce checkout
Artifact: `/Users/tomashelmfridsson/.hermes/kanban/boards/hermes-qa-agent/workspaces/t_55e33084/final_comparison.md`

| Criterion | HF score | Hermes score | Winner | Brief justification |
|---|---:|---:|---|---|
| Readability | 4 | 4 | Tie | Both are understandable; HF is shorter, Hermes is more structured. |
| Correctness | 3 | 5 | Hermes | HF captures the core flow, but Hermes maps better to checkout requirements and acceptance criteria. |
| Completeness | 2 | 5 | Hermes | Hermes adds empty-cart, invalid/declined/timeout payment, tax rounding, duplicate submit, tampering, and confirmation-access coverage. |
| Relevance | 4 | 4 | Tie | Both are relevant; Hermes covers more real checkout risks. |
| Usability | 3 | 5 | Hermes | Hermes is much closer to directly executable manual or automated checkout tests. |

Recommendation: Use the Hermes internal baseline. HF successfully executed the REST chain but the reviewer never approved the output, and the final test set remained too narrow.

### Scenario 3 — password reset
Artifact: `/Users/tomashelmfridsson/.hermes/kanban/boards/hermes-qa-agent/workspaces/t_bbbb787f/final_comparison.md`

| Criterion | HF score | Hermes score | Winner | Brief justification |
|---|---:|---:|---|---|
| Readability | 4 | 4 | Tie | HF is concise; Hermes is longer but still clear and more execution-oriented. |
| Correctness | 3 | 5 | Hermes | Hermes maps more directly to registered-only behavior, reset-form update, and invalid/expired token handling. |
| Completeness | 2 | 5 | Hermes | Hermes covers unregistered email, invalid format, repeated request, weak password, mismatched confirmation, invalid/expired/consumed token, old/new login, and normalization. |
| Relevance | 3 | 4 | Hermes | HF is on-topic but duplicates cases and over-links requirements; Hermes adds relevant security/regression checks. |
| Usability | 3 | 5 | Hermes | Hermes has stronger oracles and clearer manual/automation suitability. |

Recommendation: Use the Hermes baseline as the working test-design artifact. HF is a compact starting point, but not final-quality without more revision.

### Scenario 4 — support tickets
Artifact: `/Users/tomashelmfridsson/.hermes/kanban/boards/hermes-qa-agent/workspaces/t_d93d1b48/final_comparison.md`

| Criterion | HF score | Hermes score | Winner | Brief justification |
|---|---:|---:|---|---|
| Readability | 4 | 4 | Tie | HF is compact; Hermes is longer but well-structured by priority and type. |
| Correctness | 3 | 5 | Hermes | HF covered the core requirements but had duplicated status/view cases; Hermes mapped more cleanly to acceptance criteria. |
| Completeness | 2 | 5 | Hermes | Hermes covered validation, whitespace, boundaries, XSS, authorization, duplicate submit, errors, accessibility, and state consistency. |
| Relevance | 3 | 4 | Hermes | HF stayed relevant but duplicated cases; Hermes covered broader but still relevant support-ticket risks. |
| Usability | 3 | 5 | Hermes | Hermes had clearer preconditions, steps, expected results, and traceability. |

Recommendation: Use the Hermes Swarm/internal baseline. HF was a useful compact start, but remained unapproved after three review cycles.

### Scenario 5 — inventory management
Artifact: `/Users/tomashelmfridsson/.hermes/kanban/boards/hermes-qa-agent/workspaces/t_2c2a43b8/final_comparison_scenario_5_inventory.md`

| Criterion | HF score | Hermes score | Winner | Brief justification |
|---|---:|---:|---|---|
| Readability | 4 | 4 | Tie | HF is concise; Hermes is longer but clearer for execution and domain reasoning. |
| Correctness | 3 | 5 | Hermes | HF under-modeled negative inventory risk; Hermes covered stock deductions, threshold semantics, authorization, and audit contents. |
| Completeness | 2 | 5 | Hermes | Hermes included boundary, authorization, audit integrity, concurrency, data integrity, and accessibility/usability scenarios. |
| Relevance | 3 | 4 | Hermes | Hermes stayed focused on real inventory risks; HF included some weaker or less justified cases. |
| Usability | 3 | 5 | Hermes | Hermes provided better setup data, exact boundaries, state-change checks, and automation recommendations. |

Recommendation: Use the Hermes baseline as the stronger QA output. HF is a useful structured draft, but not final without domain-specific improvements.

### Scenario 6 — course enrollment
Artifact: `/Users/tomashelmfridsson/.hermes/kanban/boards/hermes-qa-agent/workspaces/t_69f24c0f/scenario6_course_enrollment_final_comparison.md`

| Criterion | HF score | Hermes score | Winner | Brief justification |
|---|---:|---:|---|---|
| Readability | 4 | 5 | Hermes | Hermes uses clearer IDs, priorities, categories, and coverage mapping. |
| Correctness | 4 | 5 | Hermes | Hermes adds state integrity, no-confirmation-on-failure, duplicate enrollment, persistence, term filtering, and server-side validation. |
| Completeness | 2 | 5 | Hermes | Hermes covers positive, negative, edge, concurrency, regression, access-control, usability, accessibility, and stale-client scenarios. |
| Relevance | 4 | 4 | Tie | Both stay focused on course enrollment; Hermes adds broader but still relevant checks. |
| Usability | 3 | 5 | Hermes | Hermes is closer to direct manual or automated execution. |

Recommendation: Use the Hermes Swarm/internal baseline as the working QA artifact. HF is a useful draft but too sparse for release-gate coverage.

## Final recommendation

Recommended operating model from these six comparisons:
1. Use **HF QA Agent Service** as a fast draft generator and review signal.
2. Use **Hermes Swarm/internal baseline** as the stronger final QA artifact until the HF reviewer/test-designer loop can consistently reach `approved=true`.
3. Prioritize HF improvements in:
   - negative and boundary coverage,
   - authorization/integrity/concurrency reasoning,
   - domain-specific reviewer feedback quality,
   - token/cost exposure in service responses.
