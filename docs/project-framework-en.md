# Project brief for the research study

## Study themes

- AI Agents
- Multi-Agent Systems
- Agentic Software Engineering
- Agent Orchestration
- AI-assisted Quality Assurance
- Verification and Validation
- Test-Driven Development

## Analysis questions to address during the study

### AI Agents

- How is an agent defined in current literature?
- Which characteristics recur: autonomy, planning, tool use, memory, reflection?
- How do simple agent loops differ from orchestrated multi-agent environments?

### Multi-Agent Systems

- Which collaboration patterns are used: hierarchy, market-based delegation, blackboard, reviewer loop?
- How are conflicts, coordination, and shared state handled?
- What risks exist around error propagation between agents?

### Agentic Software Engineering

- Which parts of the software lifecycle are best supported by agents?
- How are quality, traceability, and productivity measured?
- Which architectural choices improve controllability and auditability?

### AI-assisted Quality Assurance

- How is AI used for requirements analysis, test design, and test generation?
- Is there empirical support for improved requirement coverage or reduced lead time?
- How are test oracles, test data, and selectors handled?

### Verification and Validation

- How are V&V practices connected to agentic workflows?
- Which review mechanisms are required to limit hallucinations and weak traceability?

### TDD

- How does test-driven development relate to requirement-driven test generation?
- Can agentic approaches support a TDD-like feedback loop?

## Platform comparison framework

Assess each platform against the following criteria:

| Criterion | Question |
|---|---|
| Orchestration | How are flows, iterations, and routing expressed? |
| Role specialization | How easy is it to model multiple agent roles? |
| State management | How are intermediate results, memory, and traceability stored? |
| Tool integration | How well are external tools, RAG, and test execution supported? |
| Observability | Is logging, tracing, and debugging support available? |
| Local model support | How easily can Ollama or local inference be connected? |
| Cloud support | How well are commercial model APIs supported? |
| QA suitability | How well does the platform fit requirements analysis and test design? |

## Candidate platforms to compare

| Platform | Short description |
|---|---|
| OpenClaw | Experimental agent automation platform focused on rapid prototyping and flexible agent flows. |
| Hermes Agent Framework | Framework for structuring agent roles, responsibilities, and interaction in more controlled agent-based systems. |
| CrewAI | Role-based multi-agent framework where specialized agents collaborate in defined workflows. |
| LangGraph | Graph-based orchestration framework for building agent flows with explicit state, transitions, and feedback loops. |
| AutoGen | Framework for conversation-driven multi-agent systems with strong support for collaboration between agents and tools. |
| OpenAI Agents SDK | SDK for building AI agents with close integration to models, tools, guardrails, and executable orchestration. |

## Local vs cloud-based model execution

### Ollama / local models

Analyze:

- data protection and local control
- latency and operating cost
- model capacity for longer reasoning chains
- limitations in tool calls and function reliability

### Cloud-based models

Analyze:

- model quality and stability
- cost per run
- scalability and integration support
- risks related to confidentiality and vendor lock-in

## AI Agents POC Report

The status assessment against the project goal has been moved into a separate report:

- [AI Agents POC Report](../ai-agents-poc-report-en/)

This report serves as supporting material for the final report and collects the current state, achieved capabilities, limitations, and next steps for the current QA Agent proof of concept.
