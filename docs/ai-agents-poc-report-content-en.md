# AI Agents POC Report

## Purpose

This document serves as the project's consolidated report on the literature study and the construction of a QA agentic proof-of-concept (POC). The primary purpose of the POC is to build a practical understanding of how [AI agents](../theoretical-background-and-central-concepts-en/#ai-agent) and [agentic solutions](../theoretical-background-and-central-concepts-en/#agentic-ai) work, especially from a [QA](../theoretical-background-and-central-concepts-en/#software-quality-assurance) perspective. The focus is therefore on exploring how specialized agent roles, [orchestration](../theoretical-background-and-central-concepts-en/#orchestrator), routing, [memory](../theoretical-background-and-central-concepts-en/#agent-memory), feedback loops, and review can be used for requirement-based [test design](../theoretical-background-and-central-concepts-en/#test-design) and test generation, and on describing which agentic capabilities have already been demonstrated and which areas still remain to be evaluated.

## The project's development journey

The work started by understanding how [AI agents](../theoretical-background-and-central-concepts-en/#ai-agent) function in theory and in practice. The first phase therefore focused on reading about the concept of agents, [agentic orchestration](../theoretical-background-and-central-concepts-en/#orchestrator), [memory](../theoretical-background-and-central-concepts-en/#agent-memory), routing, feedback loops, and review in [multi-agent environments](../theoretical-background-and-central-concepts-en/#multi-agent-system). The goal was not only to use a ready-made [agent framework](../theoretical-background-and-central-concepts-en/#agent-framework), but first to understand what is actually required to build an agentic QA system. This is described in the literature study.

After that, we tried to build our own agentic solution from scratch. Before we could do that, we needed actual agents. We built three agents: one to analyze a broad requirement with a title and refine it into usable requirements; a second agent that wrote test designs and test cases from those requirements; and then, because the literature study suggested that this would still not be sufficient without an execution phase, we introduced an independent review agent. Since we had no System Under Test (SUT), this review agent was given the task of approving or rejecting the test cases against the requirements. These agents were created with AI-assisted coding and were first run locally, but are now published publicly on Hugging Face using a Docker-based solution. Each agent was essentially an LLM with a prompt containing a directive describing the task and the deliverable it should generate.

Once the individual agents were in place, the next step was to create a multi-agent solution. The first version was sequential: requirements were analyzed, test cases were created, and the result was then reviewed. These early experiments ran on local LLMs, mainly Llama-based models through local inference. This gave practical insight into how far we could get with our own sequential orchestration, but also showed the limitations in quality, stability, and execution time.

The next step was to move to Hugging Face-based execution for the live LLMs used in the workflow. That gave access to stronger and more flexible models while preserving control over our own agent logic and experimental environment.

## From sequential flow to agentic routing

One important insight was that the workflow should not remain strictly synchronous in the form `requirements -> design -> review` as a fixed sequential pipe. In practice, the agents needed to jump between nodes more intelligently depending on the quality of intermediate results. That led to a smarter orchestration approach.

To support this, three central mechanisms were needed so that too much irrelevant information would not reduce the agents' effectiveness:

- private agent memory for local notes and intermediate results
- shared memory for common context between agents
- non-fixed routing where the next step is decided dynamically instead of being fully hardcoded, which eventually became an LLM-based orchestration model

This led to a solution in which the orchestrator became the controlling component. Routing could then be decided from results, gaps, feedback, and stop conditions rather than a static step order. Even so, the set of possible transitions was still partly constrained. For example, if the Test Design Agent judged the requirements to be weak, it could send work back to the Requirements Agent for revision, and if the Review Agent could not approve the output, it could send work back to Test Design for improvement of one or more test cases.

An important refinement in this orchestration was to formulate the target explicitly as reaching `approved=true` from the Review Agent rather than using a vaguer expression such as `quality sufficient`. The latter leaves more room for interpretation about when a run should actually stop, while `approved=true` provides a clear verification target, sharper routing decisions, and better traceability afterward. For this POC, `approved=true` is therefore a better control target than a general quality expression, because the orchestrator can work toward a concrete review signal rather than a diffuse sense of quality.

To improve orchestration further, an LLM-based orchestrator was later introduced. This brought several improvements, especially because the earlier hardcoded orchestration definitions had caused loops between agents, just as many of the research papers in the literature study also describe. Those looping discussions became very token-expensive, so limits had to be introduced for the maximum number of cycles and how many times one agent could send feedback to another.

## Current AI Agents page and architecture

The current AI Agents solution can be described in several parts:

- the public agent solution uses Hugging Face-hosted models together with agent-adjacent execution through MCP and REST
- the orchestration logic in the app is custom-built and includes an LLM-based Orchestrator Agent
- there is a GUI built in Gradio and hosted on Hugging Face; the app includes the Hugging Face orchestration service, but also allows users to run custom agent models with custom directives

The AI Agents part was therefore built in Gradio. One important reason was that there was already some previous familiarity with Gradio, which made it a pragmatic choice for quickly producing a functioning public experimental environment. The next experiment, with LangGraph as the orchestrator, was instead run in Streamlit. The reason was not that Streamlit was necessarily the preferred framework in itself, but that Gradio introduced several practical limitations for that particular track of the work, which made Streamlit the more workable alternative.

## Hugging Face publication, endpoints, and MCP

As part of the development, the agents were published on Hugging Face so that they became available through public endpoints and MCP-related integration patterns. This made it possible to move the architecture from purely local experimentation to a more open and integrable solution where the agents could be used outside the local app environment.

Early in the work, the idea was that `qa-agent-service`, which became the working name for the agent solution, should consist of three separate agents callable through REST and MCP and primarily used through Hugging Face keys. When Hermes Agent later became a comparison and integration track, it became clear that a better solution was to expose the service's REST and MCP endpoints publicly. That made the agent service easier to reuse across different clients and frameworks instead of tying it to a more closed key-dependent setup. This was done through a Docker-based solution.

This was an important transition because it made it possible to combine:

- custom agent design and orchestrator logic
- external hosted agent services
- future integrations with tools and standardized agent interfaces

## LangGraph as the next step

After this, a LangGraph-based solution was also built. LangGraph can be described as a code library within the LangChain ecosystem for graph-based agentic orchestration. It provided a way to express agent nodes, transitions, and control flow in a more formalized manner.

That solution became somewhat similar to an MBT-inspired structure, where nodes, transitions, and states became explicit. At the same time, the work showed that LangGraph did not by itself provide the same simple agentic freedom as the custom-built solution. Compared with our own architecture, the LangGraph solution became more hardcoded, while our own solution could more easily use an LLM-based orchestrator to control routing dynamically.

- LangGraph is strong for explicit graph structure and control
- the custom-built agentic solution is stronger in dynamic routing and orchestrator-led flexibility

## Observability, directives, and memory visibility

A central design principle throughout the work was that the user should be able to see what was sent to each agent, what came out of each agent, and how the agent reasoned. The solution was therefore built with clear observability in mind. At the same time, the GUI itself should be seen as secondary in this POC rather than the main contribution.

Each agent received directives describing how it should reason, which role it had, and what quality level was expected. At the same time, both shared memory and agent-private memory were exposed in the interface so that it was possible to follow not only the final result but also the internal working context during execution.

This was important for two reasons:

- to understand why a result became good or weak
- to debug routing, memory, feedback, and agent behavior

## Agent directives

In the current `qa-agent-service`, agent behavior is declared in the agent registry and then built into the prompt together with scenario, agent input, shared memory, agent-private memory, model configuration, output contract, and strict JSON rules.

These directives were refined continuously along the way, and the idea arose whether it should be possible to adjust them during a run. The research literature discusses this topic, but also its difficulties. Standard Operating Procedure (SOP) thinking suggests that agent instructions should remain stable and well-defined; otherwise, not only token costs but also bias, errors, and hallucinations may increase and then be amplified by the next agent.

In the current HF QA agent service configuration, all three agents normally run with `Qwen/Qwen2.5-7B-Instruct`, using temperature `0.2` for Requirements Analyst and Test Designer and `0.1` for Review Agent. This was primarily because the model was free, fast, and good enough, but far from the best when later compared with GPT-5.5 through the Hermes Agent Framework.

### Requirements Analyst Agent

```text
Purpose: Extract only requirements supported by the provided text and make uncertainty explicit.
Required behavior:
- Preserve traceability to original requirement text.
- Create stable requirement IDs using REQ-001, REQ-002, etc.
- Separate supported requirements from assumptions, ambiguities, and open questions.
- Prefer smaller, testable requirements when the text contains multiple behaviors.
Required output:
- requirement_id
- original_text
- normalized_text
- priority
- acceptance_criteria
- assumptions
- open_questions
- ambiguities
- decision_basis
- agent_explanation
Forbidden behavior:
- Do not invent missing business rules.
- Do not silently resolve ambiguity.
- Do not produce vague acceptance criteria.
Quality bar: Each requirement must be testable, traceable, and clearly separated from uncertainty.
```

### Test Design Agent

```text
Purpose: Create concrete, reviewable, executable test cases from structured requirements.
Required behavior:
- Maintain traceability to requirement IDs.
- Include concrete preconditions, data, steps, expected results, and oracle logic.
- Cover relevant positive, negative, boundary, validation, authorization, and error paths.
- Preserve valid existing test cases during selective revision.
Required output:
- test_case_id
- requirement_ids
- title
- test_type
- scenario_type
- preconditions
- test_data
- steps
- expected_results
- oracle
- risks
- decision_basis
- agent_explanation
Forbidden behavior:
- Do not use vague steps or expected results.
- Do not create placeholders.
- Do not ignore unresolved assumptions or ambiguities.
Quality bar: Every test case must be specific, executable, observable, and traceable.
```

### Review Agent

```text
Purpose: Critically review generated requirements and tests and decide whether quality is sufficient.
Required behavior:
- Check traceability, oracle strength, observable expected results, and coverage.
- Check unresolved assumptions, placeholder language, and suspicious one-to-one mappings.
- Identify weakest test cases first and provide targeted improvement actions.
Required output:
- approved
- verdict
- coverage_ratio
- findings
- improvement_actions
- decision_basis
- agent_explanation
Forbidden behavior:
- Do not approve generic or weakly testable cases.
- Do not ignore weak oracle logic or missing negative and boundary coverage.
- Do not make the final orchestration decision.
Quality bar: The review must explain exactly why quality passes or fails with concrete recommendations.
```

The directives also show an important part of the project's direction: the goal was not only to make models generate text, but to give them explicit quality contracts per role and a strict output contract. In that way, the directives became a central part of how agent behavior, traceability, reviewability, and structured JSON output could be studied in the POC.

## Loops, limits, and `approve = true`

A recurring problem was that the agents sometimes ended up in loops where they sent feedback back and forth without actually reaching a strong enough final result. To handle this, limits were introduced for:

- the total number of rounds
- the total number of feedback messages
- the number of feedback messages between the same pair of agents

This became central to the architecture because the goal was that the Review Agent should eventually be able to set `approve = true`. In practice, this proved difficult to achieve consistently. It worked in some isolated runs, but in general it was much harder than expected to get the full chain to reach a robust approved end state.

## The evaluation question

An important part of the work therefore became the question of how the output from the Test Design Agent should actually be evaluated. It is not enough for the agent to produce many test cases; the decisive question is how relevant, testable, traceable, and reviewable those test cases are. The same question arose for the review step itself: how strong is the Review Agent at distinguishing between superficial and genuinely robust test designs?

This evaluation question is one of the most important conclusions so far. The system can produce artifacts, but it is considerably harder to determine with high reliability when quality is truly sufficient. In both the internal solution and the LangGraph solution, the test cases are downloadable for evaluation. The idea was to use a tool such as DeepEval together with senior QA expertise built from many years in the QA role.

## Standard scenarios for comparison

To compare solutions more systematically, six standard scenarios were created:

- Scenario 1 - login and registration
- Scenario 2 - e-commerce checkout
- Scenario 3 - password reset
- Scenario 4 - support tickets
- Scenario 5 - inventory management
- Scenario 6 - course enrollment

These are reused as recurring test inputs across the different solutions in order to compare routing, requirements analysis, test design, review behavior, observability, and the probability of reaching an approved result.

## Hermes as the next investigation track

The next step in the work was therefore to investigate whether the Hermes Agent Framework could contribute something that was missing in the earlier solutions. That makes Hermes relevant both as a comparison object and as a possible source of inspiration for how agent structure, communication, and control can be organized going forward.

## Hermes results as a comparison point

An important intermediate result was that Hermes Agent could create a working test-case generator relatively quickly. This is in itself an important observation for the POC result: it was easy to produce a clear QA-oriented multi-agent structure in Hermes without first having to build all orchestration logic from scratch.

The Hermes solution that was created was a Kanban Swarm with the following structure:

- a root task functioning as a shared blackboard
- a Requirements Analyst
- a Test Designer
- a QA Risk Reviewer
- a Verifier
- a Synthesizer

It is important to clarify that both the **shared blackboard** and the **Synthesizer** here belong to the Hermes Agent solution. They are not parts of the custom HF QA agent service solution or the app's internal orchestrator architecture.

The practical flow was:

- requirements in
- shared blackboard / root task
- parallel specialist workers
- verifier gate
- synthesizer
- final test design

This flow also describes the Hermes track specifically. The custom-built solution instead uses its own orchestrator, shared memory, agent-private memory, and routing between the Requirements Analyst, Test Design, and Review Agent.

This matters because Hermes therefore showed that it is possible to build a fairly complete test-case generator with clear role separation, a verification step, and synthesis of the final artifact in a relatively direct way.

## What the Hermes solution produced

In the Hermes case, a concrete login and lockout requirement was used as input. The solution produced, among other things:

- acceptance criteria
- assumptions
- risks and open questions
- scenarios
- traceability matrix
- release gate recommendation

The verifier step also reported a passed gate result and broad coverage of lockout rules, invalid credentials, timing risks, and traceability. This makes the Hermes result relevant as a concrete comparison object against the custom HF-based QA agent service solution.

## Important comparison limitation

At the same time, the comparison must be described honestly: the Hermes solution was run in a much stronger model environment, in this case GPT-5.5, while the current HF QA agent service solution has largely been built on smaller models such as Qwen or Qwen2.5-7B-Instruct.

This means that a direct quality comparison between the results is not automatically fair. Differences in output may be caused by at least three things:

- differences in framework and orchestration model
- differences in prompting, verification, and artifact structure
- differences in raw model capacity

It is therefore important that the report does not present the Hermes result as better solely because the final artifact was stronger. Part of that strength may very well be due to GPT-5.5 being a significantly stronger model than the smaller Qwen variant used in the HF solution.

## What the comparison still shows

Despite this limitation, the Hermes run shows several things that are valuable for the POC result:

- it is easy to get a useful test-case generator working in Hermes
- role separation becomes clear and easy to explain
- the blackboard, verifier-gate, and synthesizer pattern in Hermes works well for QA-like artifact flows
- Hermes provides a concrete comparison point for how quickly a useful result can be reached with an external agent framework

This is therefore not only an alternative experiment, but also an argument for why external framework comparison is relevant: some frameworks can provide a faster path to functioning agent flows, while the custom-built solution provides greater control over routing, memory, observability, and future extensibility.

## Comparison with the HF QA agent service

When Hermes is compared with the custom HF QA agent service solution, the focus should therefore be on several dimensions at once, not only on final quality:

- orchestration model
- role separation
- verifier gate
- artifact output
- traceability
- reproducibility
- observability
- model capacity

In Hermes, orchestration was clearly expressed through Kanban tasks, a shared blackboard, and a final synthesizer role. In the HF solution, the corresponding strengths lie more in the custom-built orchestrator, shared memory, agent-private memory, feedback limits, and the clear runtime visibility inside the app.

### Comparison between three solutions

In the comparison, it is important to distinguish between the agent framework itself and the underlying agent service. Both the custom `ai_agent` solution and the LangGraph solution use the HF QA agent service as the agent backend, while the Hermes Agent Kanban solution was run as a separate swarm structure.

| Dimension | Our custom `ai_agent` solution | LangGraph solution | Hermes Agent Kanban solution |
|---|---|---|---|
| Agent backend | HF QA agent service | HF QA agent service | Hermes/Kanban swarm with GPT-5.5 in the tested run |
| Model strength | Mainly Qwen / Qwen2.5-7B-Instruct in the current comparison | Mainly Qwen / Qwen2.5-7B-Instruct in the current comparison | GPT-5.5 |
| Orchestration | Custom-built orchestrator in the app | Graph-based orchestration in LangGraph | Kanban tasks, shared blackboard, and synthesizer in the Hermes swarm track |
| Role separation | Clear and governed by custom architecture | Clear, but more formally defined through graph nodes | Very clear and quick to establish |
| Routing | Dynamic routing through the orchestrator and selective backtracking | More graph-driven and more explicitly defined in the flow | More workflow-driven through the swarm structure |
| Memory | Shared memory, agent-private memory, and memory timeline | Depends on graph and state implementation, but supports explicit state flow | Blackboard-like sharing between tasks |
| Verification | Review Agent and stop conditions, but `approve = true` has been difficult to reach consistently | Review and verification steps can be built in, but more explicitly in the flow definition | Clear verifier gate before the Hermes Synthesizer |
| Observability | Strong GUI visibility into input, output, reasoning, memory, and runtime events | Good traceability in graph and node flow, but less integrated than our own GUI solution | Kanban/task trace and artifacts |
| Strength | Strong research platform for routing, memory, observability, and evaluation | Strong for explicit graph structure, node control, and MBT-like modeling | Fast route to a complete test-case generator |
| Limitation | Result quality is affected by smaller models and the difficulty of reaching stable `approve = true` | Can become more hardcoded and less free in dynamic agentic routing | Strength is likely affected by the larger model |

The table should not be interpreted as showing that one solution is generally best. It rather shows that the solutions have different strengths: the custom `ai_agent` solution gives the greatest control over agentic behavior and observability, LangGraph provides a strong and explicit graph model for flows and states, while the Hermes Agent Kanban solution shows how quickly a usable test-case generator can be created in an external agent framework.

## Conclusion about Hermes in the report

Parts of the Hermes result should therefore be included in the POC report to support two conclusions:

- it is relatively easy in Hermes to create a test-case generator with several QA-like roles
- the comparison against the custom HF QA agent service solution must be made with a clear reservation that the models are not equivalent

A correct interpretation is therefore that Hermes demonstrated high practical productivity and a fast path to a functioning QA flow, while the custom solution is still stronger as a research platform for studying routing, memory, observability, feedback loops, and agentic behavior in greater detail.

## Current status assessment against the project goal

The current QA Agent POC has now reached a level where it provides practical understanding of several central agent concepts that previously existed only as theory in the project brief. The POC shows, in executable form, how a multi-agent system can be organized around specialized roles, controlled by an orchestrator, and combined with both structured baseline execution and LLM-backed execution.

What has now clearly been achieved is:

- specialized agent roles with clear responsibility
- orchestrator-first routing
- selective backtracking instead of only full reruns
- shared working memory and agent-private memory
- per-agent model, provider, timeout, and directive configuration
- runtime visibility through GUI, runtime activity, and live log
- preservation of partial results on failure
- support for both local Ollama execution and external model strategies
