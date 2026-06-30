# Next steps for comparing agent frameworks

This note describes how the QA Agent POC should now be compared with external agent frameworks such as LangGraph, Hermes Agent Framework, OpenClaw, CrewAI, AutoGen, and OpenAI Agents SDK.

## Purpose

The goal is no longer only to ask whether those frameworks support "agents" in a general sense. The goal is to compare them against the concrete QA Agent POC that now exists in this repository.

The key comparison question should therefore be:

> Which framework best supports a QA-oriented multi-agent workflow with routing, shared working memory, observability, selective backtracking, model flexibility, and future agent expansion?

## Recommended comparison method

Use the current QA Agent POC as the reference baseline.

The comparison should not depend only on narrative inspection of traces or on whether a framework "looks agentic". It should depend on a shared evaluation workflow where outputs from different frameworks can be reviewed in the same way.

This means the comparison layer must become **framework-independent**:

- a framework produces a run,
- the run is normalized into a shared schema,
- the shared schema is loaded into the GUI,
- the same evaluators assess the generated test cases,
- the results are stored in one comparable dataset.

In practical terms, this means the QA Agent workbench should support both:

1. native runs produced by the current POC
2. imported runs produced by external frameworks such as LangGraph, Hermes Agent Framework, OpenClaw, CrewAI, AutoGen, or OpenAI Agents SDK

For each external framework, compare it against the current POC in the following areas:

1. Orchestration model
- Can it express orchestrator-first routing?
- Can it route selectively back to one agent instead of rerunning everything?
- Can stop conditions and feedback limits be controlled clearly?

2. Agent-role modeling
- How naturally can it model:
  - Orchestrator Agent
  - Requirements Analyst
  - Test Design Agent
  - Review Agent
- Can new agents be added without rewriting the whole flow?

3. Memory and state
- Does it support shared memory?
- Does it support private per-agent state?
- Does it support persistence or checkpointing across runs?

4. Observability and debugging
- Does it expose runtime traces, events, reasoning steps, and routing decisions?
- Is it easier or harder to debug than the current POC?

5. Model and provider flexibility
- Can different agents use different models?
- Does it support local Ollama, OpenAI-compatible endpoints, and cloud APIs cleanly?

6. Tool and integration readiness
- Does it support tool calling, MCP-like integration patterns, external APIs, files, databases, or test tooling?
- Would it make future QA agents such as DeepEval or state-machine modeling easier to add?

7. QA suitability
- Is the framework naturally suited for requirement analysis, test design, review, and backtracking?
- Or is it stronger for other kinds of workflows than QA?

8. Evaluation portability
- Can its outputs be normalized into the same run/evaluation schema as the current POC?
- Can the resulting test cases be reviewed in the same GUI without rewriting the human or DeepEval process?
- Does it preserve enough structured context to support later comparative analysis?

## Required normalization layer

To compare multiple frameworks fairly, the project should define a shared importable run format. The evaluation logic should operate on this normalized structure rather than on framework-specific traces.

The normalized run structure should include fields such as:

- `run_source`
- `framework_name`
- `framework_run_id`
- `scenario_title`
- `source_requirements`
- `requirements`
- `test_designs`
- `review`
- `agent_configs`
- `notes`
- `raw_trace`

This enables the GUI to load outputs from different frameworks and present them through the same evaluation workflow.

## Evaluation workflow that should be identical across frameworks

The same three evaluators should be applied regardless of which framework produced the test cases:

1. **Built-in Review Agent**
2. **DeepEval**
3. **Human QA specialist**

The key comparison unit should therefore not be the framework trace itself, but the generated test cases and their associated requirement context.

For fair comparison, all frameworks should be evaluated with:

- the same source scenario,
- the same normalized test-case structure,
- the same human scoring rubric,
- the same DeepEval scoring approach,
- the same exported evaluation dataset.

## Recommended scoring approach

The current project now uses or is moving toward a shared `0-100` score format for evaluation results.

Recommended scoring interpretation:

- `approved`: binary judgment, `true` or `false`
- `score`: normalized comparative score, `0-100`

Recommended evaluator roles:

- **Human QA score**
  - based on a rubric with dimensions such as:
    - relevance to requirements
    - coverage and completeness
    - oracle and expected-result quality
    - executability and clarity
  - each dimension can be scored `0-5`
  - average is normalized to `0-100`

- **DeepEval score**
  - also stored as `0-100`
  - should represent DeepEval's aggregated assessment of the generated test cases

- **Built-in Review Agent score**
  - should be treated as a derived internal score or proxy unless the Review Agent is later redesigned to produce an explicit evaluation score natively

This is important because the study should later compare:

- framework vs framework
- model vs model
- Review Agent vs DeepEval vs Human QA specialist

## Required GUI direction

The GUI should support an evaluation mode that is not limited to the current POC's own runs.

The target workflow should be:

1. Run the current POC normally, or import an external framework run as JSON
2. Normalize the run into the shared schema
3. Load the test cases into the same Evaluation panel
4. Save:
   - Review Agent evaluation
   - DeepEval evaluation
   - Human QA evaluation
5. Export a common CSV dataset for later analysis

This means the correct long-term design is:

- **Evaluate current run**
- **Import external run for evaluation**

not:

- separate, framework-specific review UIs

## Recommended way to score the frameworks

Use a simple qualitative scale first:

- Strong fit
- Partial fit
- Weak fit
- Unknown / not yet validated

Then add short evidence for each score.

Example:

- LangGraph: Strong fit for orchestration and persistence, because graph-based routing and checkpoint patterns align well with orchestrator-first backtracking.
- OpenAI Agents SDK: Strong fit for tools and runtime integration, but partial fit for complex explicit multi-step orchestration unless carefully structured.

In addition to that qualitative architecture score, the project should later add a second comparison layer:

- **output quality comparison**
- **evaluation agreement comparison**

Example:

- How often does the Human QA specialist agree with DeepEval?
- How often does the Review Agent disagree with both?
- Which framework produces the strongest test cases under the same scenario?

## What should be compared first

The first comparison round should focus on the frameworks most relevant to the current architecture:

1. LangGraph
2. OpenAI Agents SDK
3. Hermes Agent Framework
4. OpenClaw

Reason:

- LangGraph is highly relevant for orchestration, graph flow, and persistence.
- OpenAI Agents SDK is highly relevant for tools, tracing, handoffs, and modern agent runtime structure.
- Hermes Agent Framework and OpenClaw are relevant because they are part of the project's earlier comparison interest and may offer different agent modeling tradeoffs.

CrewAI and AutoGen can remain in scope, but they do not need to be first if the main goal is to compare against the architecture already built.

For each of these first-round frameworks, the preferred outcome should be:

- one native or exported run example,
- one normalization mapping into the shared schema,
- one imported evaluation in the GUI,
- one comparable CSV export row set.

## Recommended output artifact

The cleanest next deliverable is a comparison matrix with one row per framework and one column per criterion:

- orchestration
- memory/state
- observability
- tool integration
- local model support
- multi-model flexibility
- QA workflow suitability
- migration effort from current POC
- import/normalization effort into the evaluation layer
- evaluator comparability across runs

Then add a short narrative conclusion:

- Which framework is the strongest architectural match
- Which framework is the strongest runtime/tooling match
- Which framework is the easiest migration path
- Which parts of the current POC are already good enough and should not be replaced unnecessarily

In addition, the evaluation dataset should support analysis tables such as:

- `run_id`
- `framework_name`
- `scenario_title`
- `model_setup`
- `review_agent_approved`
- `review_agent_score`
- `deepeval_approved`
- `deepeval_score`
- `human_approved`
- `human_score`
- `notes`

## Important conclusion

The comparison should not assume that the current POC must be replaced.

A valid result may be:

- keep the current POC architecture,
- borrow selected ideas from external frameworks,
- add missing capabilities incrementally,
- avoid migration unless a framework gives clear benefits in persistence, tools, tracing, or agent expansion.

Another valid result is that the current QA Agent POC remains the execution baseline, while external frameworks are primarily compared through imported runs and shared evaluation rather than through full migration.
