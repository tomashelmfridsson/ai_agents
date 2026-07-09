# AI Agent POC Report

## Purpose

This document serves as the project's consolidated report on the literature study and the development of a QA-oriented agentic Proof of Concept (POC). The primary purpose of the POC is to build a practical understanding of how [AI agents](../theoretical-background-and-central-concepts-en/#ai-agent) and [agentic solutions](../theoretical-background-and-central-concepts-en/#agentic-ai) work, particularly from a [Software Quality Assurance](../theoretical-background-and-central-concepts-en/#software-quality-assurance) perspective.

The focus is therefore on exploring how specialized agent roles, [orchestration](../theoretical-background-and-central-concepts-en/#orchestrator), routing, [memory](../theoretical-background-and-central-concepts-en/#agent-memory), feedback loops, and review can be used for requirement-based [test design](../theoretical-background-and-central-concepts-en/#test-design) and test generation. The report also describes which agentic capabilities have already been demonstrated and which areas still remain to be evaluated.

## The project's development journey

The work began by understanding how [AI agents](../theoretical-background-and-central-concepts-en/#ai-agent) function in theory and practice. The first phase therefore focused on studying the concept of agents, agentic [orchestration](../theoretical-background-and-central-concepts-en/#orchestrator), [memory](../theoretical-background-and-central-concepts-en/#agent-memory), routing, feedback loops, and review in [multi-agent environments](../theoretical-background-and-central-concepts-en/#multi-agent-system). The goal was not only to use a ready-made [agent framework](../theoretical-background-and-central-concepts-en/#agent-framework), but first to understand what is actually required to build an agentic QA system. This approach is supported by the survey papers Large Language Model-Based Agents for Software Engineering and Agents in Software Engineering, which show that understanding agent architecture, memory, planning, and collaboration is a prerequisite for constructing effective agentic systems.

After that, we tried to build our own agentic solution from scratch. Before that was possible, we first needed to build the agents themselves. We developed three agents: one agent to analyze a high-level requirement and refine it into usable requirements, one agent to create [test design](../theoretical-background-and-central-concepts-en/#test-design) and test cases from those requirements, and an independent review agent. The decision to divide the work between specialized agent roles is supported by several studies, including AgentCoder, MetaGPT, and The Rise of Agentic Testing. All of them show that role specialization can improve quality, traceability, and the possibility of feedback compared with a single general-purpose agent.

The literature study clearly indicated that a solution without some form of execution or review phase is rarely sufficient. Since we did not have a System Under Test (SUT), we therefore chose to let an independent review agent evaluate the test cases against the requirements. This is in line with AgentCoder, where a separate test agent is used to verify the generated solution. The Rise of Agentic Testing also emphasizes the importance of an independent review function to reduce the risk that the same agent both produces and approves its own result.

These agents were developed with AI-assisted coding, first run locally, and later published publicly on [Hugging Face](../theoretical-background-and-central-concepts-en/#hugging-face) through a Docker-based solution. Each agent was, in practice, an [LLM](../theoretical-background-and-central-concepts-en/#large-language-models) with a [prompt](../theoretical-background-and-central-concepts-en/#prompt-engineering) and a directive describing the task and which [artifact](../theoretical-background-and-central-concepts-en/#artefakt) should be produced.

Once the individual agents were ready, the next step was to create a multi-agent solution. The first version was sequential: requirements were analyzed, test cases were created, and the result was then reviewed. These early experiments ran with local [LLMs](../theoretical-background-and-central-concepts-en/#large-language-models), mainly Llama-based models through local inference. This gave practical understanding of how far we could get with our own sequential [orchestration](../theoretical-background-and-central-concepts-en/#orchestrator), but also which limitations emerged in quality, stability, and [execution time](../theoretical-background-and-central-concepts-en/#exekveringstid).

The next step was to move to Hugging Face-based execution for the live LLMs used in the workflow. This gave us access to stronger and more flexible models while preserving control over our own agent logic and experimental environment.

## From sequential flow to agentic routing

An important insight was that the workflow should not be strictly synchronous in the form `requirements -> design -> review` as a fixed sequential pipe. In practice, the agents needed to be able to move between nodes more intelligently depending on the quality of intermediate results. That led to more flexible orchestration. The literature study shows that modern agentic systems rarely rely on strictly sequential workflows. Instead, orchestrators, dynamic routing, and iterative feedback loops are used to coordinate collaboration between specialized agents.

To support this, three central mechanisms were needed:

- private [agent memory](../theoretical-background-and-central-concepts-en/#agent-memory) for local notes and intermediate results
- [shared memory](../theoretical-background-and-central-concepts-en/#shared-working-memory) for common context between the agents
- dynamic routing where the next step is determined from the result and not only through hardcoded step order

The distinction between private and shared memory is consistent with the memory model described in Agents in Software Engineering, where Short-Term Memory, Working Memory, Long-Term Memory, and External Memory are used for different parts of the agent's reasoning.

This led to a solution in which the orchestrator became the controlling component. Routing could then be determined from results, shortcomings, feedback, and stop conditions rather than from a completely static step order. At the same time, some transitions were still constrained. If the Test Design Agent, for example, judged that the requirements were weak, the work could be sent back to the Requirements Analyst Agent, and if the review agent could not approve the result, the work could be sent back to the Test Design Agent for improvement.

An important refinement in this orchestration was to formulate the target explicitly as reaching `approved=true` from the Review Agent, instead of using a vaguer expression such as `quality sufficient`. The latter leaves more room for interpretation about when the run should actually stop, whereas `approved=true` provides a clearer [verification target](../theoretical-background-and-central-concepts-en/#verification-and-validation), sharper routing decisions, and better [traceability](../theoretical-background-and-central-concepts-en/#requirement-traceability) afterward. For this POC, `approved=true` is therefore a better control target than a general quality expression, because the orchestrator can then work toward a concrete review signal rather than a diffuse sense of quality.

To achieve even better orchestration, an [LLM](../theoretical-background-and-central-concepts-en/#large-language-models)-based [orchestrator](../theoretical-background-and-central-concepts-en/#orchestrator) was then built. This brought several improvements, especially because we had previously seen problems with loops between agents. Similar issues are also described in MetaGPT, where the authors show that uncontrolled communication between many agents quickly leads to increased token consumption and more information noise. Standardized workflows and structured communication are therefore used between the agents. The hardcoded orchestration definitions sometimes led to looping discussions between agents and high token consumption. We therefore had to introduce maximum limits for the number of cycles and for how many feedback messages one agent could send to another.

## Current AI agent page and architecture

The current AI agent solution can be described in three parts:

- the public agent solution uses [Hugging Face](../theoretical-background-and-central-concepts-en/#hugging-face)-hosted models and agent-adjacent execution via [MCP](../theoretical-background-and-central-concepts-en/#model-context-protocol) and [REST](../theoretical-background-and-central-concepts-en/#rest-api)
- orchestration handling in the app is custom-built and includes an [LLM](../theoretical-background-and-central-concepts-en/#large-language-models)-based orchestrator agent
- the solution has a GUI built in [Gradio](../theoretical-background-and-central-concepts-en/#gradio), where users can both use the hosted orchestration service and choose their own agent models with their own directives

The AI agent part was built in [Gradio](../theoretical-background-and-central-concepts-en/#gradio). One important reason was that there was already some previous experience with Gradio, which made it a pragmatic choice for quickly producing a working public experimental environment. The next experiment, with [LangGraph](../theoretical-background-and-central-concepts-en/#langgraph) as the orchestrator, was instead run in [Streamlit](../theoretical-background-and-central-concepts-en/#streamlit). The reason was not that Streamlit was necessarily the first choice in itself, but that Gradio introduced several practical limitations in that part of the work.

## HF publication, endpoints, and MCP

As part of the development, the agents were published on [Hugging Face](../theoretical-background-and-central-concepts-en/#hugging-face) so that they became available through public endpoints and [MCP](../theoretical-background-and-central-concepts-en/#model-context-protocol)-related integration patterns. This made it possible to move the architecture from local experimentation only to a more open and integrable solution where the agents could be used outside the local app environment.

Early in the work, the idea was that `qa-agent-service`, which became the working name for the agent solution, would consist of three separate agents callable through [REST](../theoretical-background-and-central-concepts-en/#rest-api) and [MCP](../theoretical-background-and-central-concepts-en/#model-context-protocol), primarily through Hugging Face keys. When [Hermes Agent Framework](../theoretical-background-and-central-concepts-en/#hermes-agent-framework) later began to be used as a comparison and integration track, it became clear that a better solution was to make the service's REST and MCP endpoints public. This made the agent service easier to reuse across different clients and frameworks, rather than tying it to a more closed key-dependent setup. This was implemented with a Docker solution.

This was an important transition because it made it possible to combine:

- custom agent design and orchestrator logic
- external hosted agent services
- future integrations with tools and standardized agent interfaces

## LangGraph as the next step

After this, a [LangGraph](../theoretical-background-and-central-concepts-en/#langgraph)-based solution was also built. LangGraph can be described as a code library within the [LangChain](../theoretical-background-and-central-concepts-en/#langchain) ecosystem for graph-based agentic orchestration. It provided a way to express agent nodes, transitions, and control flow in a more formalized way.

That solution became somewhat similar to an MBT-inspired structure, where nodes, transitions, and states became clear. At the same time, the work showed that LangGraph did not by itself provide the same simple agentic freedom as the custom-built solution. Compared with our own architecture, the LangGraph solution became more hardcoded, while our own solution could more extensively use an LLM-based orchestrator to control routing dynamically.

- LangGraph is strong for explicit graph structure and control
- the custom-built agentic solution is stronger in dynamic routing and orchestrator-led flexibility

## Observability, directives, and memory visibility

A central design principle throughout the work was that the user should be able to see what was sent to each agent, what came out of each agent, and how the agent reasoned. The solution was therefore built with clear [observability](../theoretical-background-and-central-concepts-en/#observability) in focus. The GUI part should, however, still be regarded as secondary in this POC.

Each agent received directives describing how it should reason, which role it had, and what quality level was expected. At the same time, both [shared memory](../theoretical-background-and-central-concepts-en/#shared-working-memory) and [agent-private memory](../theoretical-background-and-central-concepts-en/#agent-memory) were exposed in the interface, making it possible to follow not only the final result but also the internal working context during execution.

This was important for two reasons:

- to understand why a result became good or poor
- to troubleshoot routing, memory, feedback, and agent behavior

## Agent directives

In the current `qa-agent-service`, agent behavior is declared in the agent registry and then built into the [prompt](../theoretical-background-and-central-concepts-en/#prompt-engineering) together with scenario, agent input, [shared memory](../theoretical-background-and-central-concepts-en/#shared-working-memory), [agent-private memory](../theoretical-background-and-central-concepts-en/#agent-memory), model configuration, output contract, and strict JSON rules.

These directives were refined continuously during the work. One important question was whether they should be adjustable during a run. The research literature discusses this, but also highlights the difficulties. Standard Operating Procedures (SOP), for example, emphasize that agent instructions should be stable and well-defined. Otherwise, not only token costs risk increasing, but bias, errors, and hallucinations may also be amplified between agents.

In the current HF QA agent service configuration, all three agents normally run with `Qwen/Qwen2.5-7B-Instruct`, using temperature `0.2` for Requirements Analyst and Test Designer and `0.1` for the Review Agent. That choice was made primarily because the model was free, fast, and good enough, but it was far from the best when we later tested against GPT-5.5 using the [Hermes Agent Framework](../theoretical-background-and-central-concepts-en/#hermes-agent-framework).

The literature study shows that high-quality test design requires more than the generation of well-formulated test cases. The study Automatic High-Level Test Case Generation using Large Language Models shows that generative models can often create test cases that look structured and reasonable, but that they can still miss important edge cases, use overly generic test data, or lack sufficient domain grounding. This motivates why the Test Design Agent in the POC has a clear quality contract requiring concrete preconditions, test data, steps, expected results, oracle logic, and traceability to requirement IDs.

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

The directives also show an important part of the project's direction: the goal was not only to make the models generate text, but to give them clear quality contracts per role and a strict output contract. In this way, the directives became a central part of how agent behavior, traceability, reviewability, and structured JSON output could be studied in the POC.

Several research papers emphasize the importance of clear and stable agent instructions. MetaGPT describes this through the concept of Standard Operating Procedures (SOP), where each agent works according to clearly defined tasks and produces standardized artifacts. This reduces both information noise and the risk that incorrect assumptions spread between agents.

## Loops, limits, and approve true

A recurring problem was that the agents sometimes got stuck in loops where they sent feedback back and forth without actually reaching a sufficiently good final result. To handle this, limits were introduced for:

- total number of rounds
- total number of feedback messages
- number of feedback messages between the same pair of agents

This became central to the architecture because the goal was that the Review Agent should ultimately be able to set `approve = true`. In practice, this proved difficult to achieve consistently. In some isolated runs it worked, but in general it was much harder than expected to get the whole chain to reach a robust approved end state.

## The evaluation question

An important part of the work therefore became the question of how the output from the Test Design Agent should actually be evaluated. This challenge is also described in Automatic High-Level Test Case Generation using Large Language Models. The authors show that automatic quality metrics, such as F1-score and BERTScore, only provide part of the picture. To assess whether test cases are truly useful, human expert review is also required, especially regarding domain knowledge, edge cases, and the relevance of test data. It is not enough that the agent produces many test cases; the decisive question is how relevant, testable, traceable, and reviewable those test cases are. In the same way, the question arose of how strong the review step actually is: how good is the Review Agent at distinguishing between superficial and genuinely robust test designs? This is consistent with Automatic High-Level Test Case Generation using Large Language Models, where the authors show that the hardest part of AI-generated test design is not only producing test cases, but understanding domain context and determining what should actually be tested. The study also shows that automatic measures such as F1-score, BERTScore, and semantic similarity metrics can provide some information about similarity and linguistic quality, but do not fully capture the practical value of the test cases. Automatic metrics therefore need to be complemented with expert review, especially when assessing edge cases, test data, and domain-specific scenarios.

This evaluation question is one of the most central conclusions so far. The system can produce artifacts, but it is significantly harder to determine with high reliability when quality is truly sufficient. In both the internal solution and the LangGraph solution, the test cases are downloadable for further evaluation. The idea was to use, for example, [DeepEval](../theoretical-background-and-central-concepts-en/#deepeval), but also senior QA experience from practical work in the role of QA expert.

## Standard scenarios for comparison

To compare solutions more systematically, six standard scenarios were created:

- Scenario 1 - login and registration
- Scenario 2 - e-commerce checkout
- Scenario 3 - password reset
- Scenario 4 - support tickets
- Scenario 5 - inventory management
- Scenario 6 - course enrollment

These are used as recurring test cases in the different solutions in order to compare routing, requirements analysis, test design, review behavior, observability, and the probability of reaching an approved result.

## Hermes

The next step in the work was to investigate whether the [Hermes Agent Framework](../theoretical-background-and-central-concepts-en/#hermes-agent-framework) could add something that was missing from the earlier solutions. This makes Hermes relevant both as a comparison object and as a possible source of inspiration for how agent structure, communication, and control can be organized going forward.

## Hermes results as a comparison point

An important intermediate result was that Hermes Agent was able to create a functioning test-case generator relatively quickly. This is in itself an important observation for the POC result: it was easy to produce a clear QA-like multi-agent structure in Hermes without first needing to build all the orchestration logic from scratch.

The Hermes solution that was developed was a Kanban Swarm with the following structure:

- a root task that functioned as a [shared blackboard](../theoretical-background-and-central-concepts-en/#shared-blackboard)
- a Requirements Analyst
- a Test Designer
- a QA Risk Reviewer
- a Verifier
- a [Synthesizer](../theoretical-background-and-central-concepts-en/#synthesizer)

It is important to clarify that both **[shared blackboard](../theoretical-background-and-central-concepts-en/#shared-blackboard)** and **[Synthesizer](../theoretical-background-and-central-concepts-en/#synthesizer)** here belong to the Hermes Agent solution. They are therefore not parts of the custom-built HF QA agent service solution or the app's internal orchestrator architecture.

The flow was, in practice:

- requirements in
- shared blackboard / root task
- parallel specialist workers
- verifier gate
- synthesizer
- final test design

This flow also describes the Hermes track specifically. The custom-built solution instead uses its own orchestrator, shared memory, agent-private memory, and routing between the Requirements Analyst, Test Design, and Review Agent.

This is important because Hermes thereby showed that it is possible to create a fairly complete test-case generator with clear role separation, verification steps, and synthesis of the final artifact in a relatively direct way.

## What the Hermes solution produced

In the Hermes case, a concrete login/lockout requirement was used as the input. The solution produced, among other things:

- acceptance criteria
- assumptions
- risks and open questions
- scenarios
- traceability matrix
- release gate recommendation

The verifier step also reported a passed gate result and extensive coverage of, among other things, lockout rules, invalid credentials, timing risks, and traceability. This makes the Hermes result relevant as a concrete comparison object against the custom HF-based QA agent service solution.

## Important comparison limitation

At the same time, the comparison must be described honestly: the Hermes solution was run with a significantly stronger model environment, in this case GPT-5.5, while the current HF QA agent service solution has largely been built on smaller models such as Qwen or Qwen2.5-7B-Instruct. This is also supported by the literature on requirement-based test case generation. The study Automatic High-Level Test Case Generation using Large Language Models shows that model comparisons should not be interpreted solely in terms of model size. Smaller models can perform well if they are domain-adapted, while larger general models may provide better language and structure but still miss domain-specific edge cases. The differences between Hermes and the HF QA agent service should therefore be understood as a combination of model capacity, domain context, prompting, and agent architecture.

This means that a direct quality comparison between the results is not automatically fair. The findings in the literature study also show that model size alone does not determine quality. Automatic High-Level Test Case Generation using Large Language Models shows that smaller models can perform very well if they are adapted to the right domain and have access to relevant context. The differences between Hermes and the custom solution should therefore not be attributed only to model capacity, but also to differences in domain context, prompting, and agent architecture.

At the same time, the results indicate that very large general models do not always have to be the most relevant choice for this type of task. In this project, we are not primarily looking for a model that can do "everything", but for a model that is good at interpreting requirements, reasoning about testability, and producing useful test artifacts. The literature also points to smaller models working very well when they are adapted to the right domain or given the right context.

Differences in output may be due to at least three things:

- differences in framework and orchestration model
- differences in prompting, verification, and artifact structure
- differences in raw model capacity

It is therefore important that the report does not present the Hermes result as better solely because the final artifact was stronger. Part of that strength may very well be due to GPT-5.5 being a significantly stronger model than the smaller Qwen variant in the HF solution.

## What the comparison still shows

Despite this limitation, the Hermes run shows several things that are valuable for the POC result:

- it is easy to create a useful test-case generator in Hermes
- role separation becomes clear and easy to describe
- the blackboard, verifier-gate, and synthesizer pattern in Hermes works well for QA-like artifact flows
- Hermes provides a concrete comparison object for how quickly a useful result can be achieved with an external agent framework

This is therefore not only an alternative experiment, but also an argument for why external framework comparison is relevant: some frameworks can provide a faster path to functioning agent flows, while the custom-built solution instead provides greater control over routing, memory, observability, and future extension.

## Token consumption in the custom-built solution

An important new observation in the work is that token consumption can now also be tracked for the custom-built solution when `qa-agent-service` is used as the agent backend. This means that the comparison with Hermes no longer needs to focus only on final quality, but also on how much model work is actually required to reach a given result.

The most central result is that token cost in our six scenario runs does not primarily seem to be driven by general "agent chat" between roles. In these runs, the orchestrator steps handle routing and stop signals, but they have no token values in the exports. Instead, almost the entire token consumption lies in the steps where the Requirements Analyst, Test Design Agent, and Review Agent call the model backend.

It is also clear that the cost is not primarily in the first requirements analysis. That phase is relatively cheap and stable across scenarios. The major cost instead emerges in the repeated loop between the Test Design Agent and the Review Agent. When the Review Agent does not approve the result, feedback is sent back to the Test Design Agent, which must reread requirements, prior test design, feedback, and other working context. The Review Agent then performs a corresponding new pass with a larger input basis than in the previous cycle. This means that each extra cycle normally costs significantly more than the initial base round.

In the six collected runs, the same default limits were used: `max_rounds = 10`, `max_feedback_messages = 12`, and `max_feedback_per_agent_pair = 4`. Even so, all runs stopped in practice at five iterations and four feedback rounds, with all feedback flowing from the Review Agent to the Test Design Agent. That means that it was not the total round limit that practically controlled the stop, but rather the more specific limit for how many times the same agent pair was allowed to loop.

The measurement therefore shows three important things:

- the largest token cost lies in recurring design and review loops, not in the orchestrator's routing
- each extra cycle becomes progressively more expensive, which indicates that more context and more previous artifacts are carried forward in the prompts
- the Requirements Analyst accounts for only a small part of the total cost, while the Test Design Agent and Review Agent together dominate almost the entire token consumption

This in turn leads to a practical conclusion for further development. If the goal is to reduce cost, it is not primarily enough to swap model or reduce temperature. The most important step is probably to reduce the amount of context that is sent in again in every design and review loop, or to improve the quality of the first design round so that fewer backtracking cycles are needed. This could involve, for example, better selection of which requirements and which review findings actually need to be forwarded, clearer compression of prior artifacts, or a more constrained feedback format between the Review Agent and the Test Design Agent.

To make this line of analysis transparent, there is a separate appendix with tables for scenarios 1 to 6, including comparison against Hermes measurable token usage and a breakdown of what constitutes the base round versus extra cycles. See [Appendix: Token comparison between Hermes and our own QA agent service](../token-comparison-hermes-vs-qa-agent-service-en/).

## Comparison with the HF QA agent service

When Hermes is compared with the custom HF QA agent service solution, the focus should therefore be on several dimensions at once, not just final quality:

- orchestration model
- role separation
- verifier gate
- artifact output
- traceability
- reproducibility
- observability
- model capacity

In the Hermes case, orchestration was clearly expressed through Kanban tasks, [shared blackboard](../theoretical-background-and-central-concepts-en/#shared-blackboard), and a concluding [synthesizer](../theoretical-background-and-central-concepts-en/#synthesizer) role. In the HF solution, the corresponding strength lies more in the custom-built orchestrator, shared memory, agent-private memory, feedback limits, and the clear runtime visibility inside the app.

### Comparison between the solutions

In the comparison, it is important to distinguish between the agent framework itself and the underlying agent service. Both the custom-built `ai_agent` solution and the LangGraph solution use the HF QA agent service as the agent backend, while the Hermes Agent Kanban solution was run as a separate swarm structure.

| Dimension | Our own `ai_agent` solution | LangGraph solution | Hermes Agent Kanban solution |
|---|---|---|---|
| Agent backend | HF QA agent service | HF QA agent service | Hermes/Kanban swarm with GPT-5.5 in the tested run |
| Model strength | Mainly Qwen / Qwen2.5-7B-Instruct in the current comparison | Mainly Qwen / Qwen2.5-7B-Instruct in the current comparison | GPT-5.5 |
| Orchestration | Custom-built orchestrator in the app | Graph-based orchestration in LangGraph | Kanban tasks, shared blackboard, and synthesizer in the Hermes swarm track |
| Role separation | Clear and governed by our own architecture | Clear, but more formally defined through graph nodes | Very clear and quick to establish |
| Routing | Dynamic routing via the orchestrator and selective backtracking | More graph-driven and more explicitly defined in the flow | More workflow-driven through the swarm structure |
| Memory | Shared memory, agent-private memory, and memory timeline | Depends on the graph and state implementation, but supports clear state flow | Blackboard-like sharing between tasks |
| Verification | Review Agent and stop conditions, but `approve = true` has been difficult to reach consistently | Review and verification steps can be built in, but are more explicit in the flow definition | Clear verifier gate before the Hermes Synthesizer |
| Observability | Strong GUI insight into input, output, reasoning, memory, and runtime events | Good traceability in graph and node flows, but less integrated than our own GUI solution | Kanban/task traces and artifacts |
| Strength | Strong research platform for routing, memory, observability, and evaluation | Strong for explicit graph structure, node control, and MBT-like modeling | Fast path to a complete test-case generator |
| Limitation | The result is affected by smaller models and the difficulty of reaching stable `approve = true` | Can become more hardcoded and less free in dynamic agentic routing | The strength is likely influenced by the larger model |

The table should not be interpreted as meaning that one solution is generally best. It rather shows that the solutions have different strengths: the custom-built `ai_agent` solution gives the greatest control over agentic behavior and observability, LangGraph provides a strong and clear graph model for flows and states, while the Hermes Agent Kanban solution shows how quickly a useful test-case generator can be created in an external agent framework.

## Conclusion about Hermes in the report

Parts of the Hermes result should therefore be included in the POC report in support of two conclusions:

- it is relatively easy in Hermes to create a test-case generator with several QA-like roles
- the comparison against the custom HF QA agent service solution must be made with a clear reservation that the models are not equivalent

A correct interpretation is therefore that Hermes demonstrated high practical productivity and a fast path to a functioning QA flow, while the custom solution is still stronger as a research platform for studying routing, memory, observability, feedback loops, and agentic behavior at a more detailed level.

## Conclusions

The current QA agent POC has now reached a level where it provides a practical understanding of several central agent concepts that previously existed only as theory in the project brief. Several of the design choices implemented in the POC also recur in the reviewed literature. Examples include the use of specialized agent roles, a central orchestrator, shared working memory, iterative feedback loops, and an independent review function. This strengthens the view that the developed solution is close to the architectural principles that currently dominate research on agentic systems for Software Engineering and Software Quality Assurance. The POC shows in executable form how a multi-agent system can be organized around specialized roles, controlled by an orchestrator, and combined with both structured baseline execution and LLM-backed execution.

What has now clearly been achieved is:

- specialized agent roles with clear responsibility
- orchestrator-controlled routing
- selective backtracking instead of only full reruns
- shared working memory and agent-private memory
- per-agent model, provider, timeout, and directive configuration
- runtime visibility through GUI, runtime activity, and live log
- preservation of partial results on failure
- support for both local Ollama execution and external model strategies

This means that the project has, to a large extent, achieved the goal of understanding what agentic systems are at a practical level, especially within a QA-oriented workflow. The system shows not only that several agents can exist at the same time, but also how routing, feedback, memory, observability, and controllable execution affect the result.

At the same time, important steps remain before the solution can be described as a more general agent framework:

- agent expansion is still code-adjacent and not fully dynamic
- tool runtime and MCP-based integration are not yet a central part of the architecture
- persistence and checkpointing are not generic at the framework level
- the comparison with external agent frameworks has not yet been carried out empirically in the same level of detail as the internal POC
- the results of the test-case generations for the scenarios in the different solutions have not yet been reviewed in detail

An interesting continuation would therefore be to investigate how easy it would be to train or fine-tune a smaller model for exactly this type of QA-oriented task. If a smaller and more specialized model can deliver comparable quality in requirement interpretation and test design, that could provide lower cost, faster execution, and greater control over the solution.

The most accurate interpretation at this stage is therefore that the project has reached the goal of understanding and demonstrating central agent capabilities, but that the next step is to compare this POC more systematically with established agent platforms and determine which parts should be retained, generalized, or replaced. It would also be very interesting to try this in practice at a company.
