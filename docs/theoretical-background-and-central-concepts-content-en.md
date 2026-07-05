# Theoretical background and central concepts

## Contents

- [Artificial Intelligence](#artificial-intelligence)
- [Machine Learning](#machine-learning)
- [Deep Learning](#deep-learning)
- [Foundation Models](#foundation-models)
- [Generative AI](#generative-ai)
- [Large Language Models](#large-language-models)
- [Prompt Engineering](#prompt-engineering)
- [Embeddings](#embeddings)
- [Vector Databases](#vector-databases)
- [Retrieval-Augmented Generation](#retrieval-augmented-generation)
- [AI Agent](#ai-agent)
- [Agentic AI](#agentic-ai)
- [Multi-Agent System](#multi-agent-system)
- [Orchestrator](#orchestrator)
- [Agent Memory](#agent-memory)
- [Shared Working Memory](#shared-working-memory)
- [Planning](#planning)
- [Reflection and Review](#reflection-and-review)
- [Review Gate](#review-gate)
- [Selective Backtracking](#selective-backtracking)
- [Observability](#observability)
- [Runtime Trace](#runtime-trace)
- [Shared Blackboard](#shared-blackboard)
- [Synthesizer](#synthesizer)
- [Tool Calling](#tool-calling)
- [Function Calling](#function-calling)
- [Model Context Protocol](#model-context-protocol)
- [Software Engineering](#software-engineering)
- [AI for Software Engineering](#ai-for-software-engineering)
- [Agentic Software Engineering](#agentic-software-engineering)
- [Software Quality Assurance](#software-quality-assurance)
- [Verification and Validation](#verification-and-validation)
- [Requirement](#requirement)
- [Acceptance Criteria](#acceptance-criteria)
- [Requirement Traceability](#requirement-traceability)
- [Test Design](#test-design)
- [Test Oracle](#test-oracle)
- [Unit Test](#unit-test)
- [Integration Test](#integration-test)
- [GUI Test](#gui-test)
- [End-to-End Test](#end-to-end-test)
- [Test Automation](#test-automation)
- [Test-Driven Development](#test-driven-development)
- [Self-Healing](#self-healing)
- [Code Coverage](#code-coverage)
- [Requirement Coverage](#requirement-coverage)
- [Test Pass Rate](#test-pass-rate)
- [Iteration Cycles](#iteration-cycles)
- [Execution Time](#execution-time)
- [Code Quality](#code-quality)
- [SonarQube](#sonarqube)
- [Agent Framework](#agent-framework)
- [LangChain](#langchain)
- [LangGraph](#langgraph)
- [Hermes Agent Framework](#hermes-agent-framework)
- [Model-Agnostic Architecture](#model-agnostic-architecture)
- [Local and Cloud-Based Models](#local-and-cloud-based-models)
- [Ollama](#ollama)
- [Hugging Face](#hugging-face)
- [Agent-as-a-Service](#agent-as-a-service)
- [REST API](#rest-api)
- [DeepEval](#deepeval)
- [Traceability Matrix](#traceability-matrix)
- [Gradio](#gradio)
- [Streamlit](#streamlit)
- [GitHub and GitHub Pages](#github-and-github-pages)
- [Continuous Integration](#continuous-integration)
- [Demonstrator](#demonstrator)
- [Artifact](#artifact)
- [Summary](#summary)

---

## Artificial Intelligence

Artificial intelligence, often abbreviated as AI, is a collective term for systems that can perform tasks that traditionally required human intelligence. Such tasks can include problem-solving, decision-making, pattern recognition, language processing, planning, and learning.

In this context, AI is mainly used in the sense of **generative AI** and **agentic AI**. The focus is therefore not on classic rule-based expert systems, but on modern language models and agent frameworks that can interpret requirements, generate test designs, and produce test artifacts.

AI can be divided into several layers. At the broadest level there is artificial intelligence as a research field. Within it there is machine learning, where systems learn from data. Within machine learning there is deep learning, where neural networks with many layers are used. Modern large language models are primarily based on deep learning and Transformer architectures.

In this project, AI is not a goal in itself, but a means of exploring how quality assurance work can be supported by agent-based systems.

## Machine Learning

Machine learning is an area of AI where models are trained on data in order to identify patterns and make predictions or generate output. Unlike traditional programming, where rules are specified explicitly, the model learns statistical relationships from examples.

Machine learning is often divided into three main categories:

- **Supervised learning**, where the model is trained on examples with known answers.
- **Unsupervised learning**, where the model identifies structure in data without explicit labels.
- **Reinforcement learning**, where the model learns through reward and punishment in an environment.

Machine learning is relevant because LLMs are built on models trained on large amounts of text and code. In many applications, new models are not trained from scratch; existing models are instead used as components in larger systems.

## Deep Learning

Deep learning is a subfield of machine learning in which neural networks with many layers are used to represent complex relationships in data. Deep learning has played a major role in the development of modern AI systems, especially in image analysis, speech recognition, natural language processing, and code generation.

Here, deep learning is mainly relevant as the technical foundation for the language models used by agents. It is not necessary to implement deep learning models directly, but it is important to understand that LLMs do not "understand" requirements and tests in a human way. They generate likely and context-dependent answers based on patterns in training data and instructions.

This matters in QA because generated test cases can look reasonable without being complete, correct, or traceable to requirements. Review, metrics, and iterative feedback mechanisms are therefore needed.

## Foundation Models

Foundation models are large, general-purpose AI models trained on very large datasets and adaptable to many different tasks. Language models such as GPT, Claude, Llama, Qwen, or Gemini can all be viewed as examples of foundation models.

A defining feature of foundation models is that they are not trained for one narrow task. Instead, they can be used for many kinds of tasks through instructions, prompts, fine-tuning, or tool integration. They can summarize text, generate code, analyze requirements, write test cases, or reason about architecture.

Foundation models are often used as the underlying intelligence inside agents. The model itself is not the same thing as an agent. A model generates text or code. An agent combines the model with goals, instructions, tools, memory, and a workflow.

## Generative AI

Generative AI refers to AI systems that can create new content. That content can be text, program code, images, audio, test cases, documentation, or other artifacts. In software development, generative AI is used for requirements analysis, code generation, test generation, documentation, refactoring, and debugging.

Generative AI is relevant here because agents can create new QA artifacts. Examples include:

- structured requirements
- acceptance criteria
- test design
- unit tests
- GUI or E2E tests
- test data
- review reports

An important limitation is that generative AI can produce output that looks correct but contains errors, lacks coverage, or is based on implicit assumptions. It is therefore not enough to generate test cases. The test cases must also be reviewed, traced back to requirements, and ideally executed.

## Large Language Models

Large Language Models, often abbreviated as LLMs, are large models trained on extensive text and code corpora. They are used to understand and generate natural language and program code. Modern LLMs usually rely on the Transformer architecture and have shown strong capability in text generation, code generation, summarization, and question answering.

An LLM receives a context, such as a user question, instruction, or document excerpt, and then generates a continuation. In an agentic system, the LLM acts as the core decision and generation component.

Examples of LLMs include:

- GPT
- Claude
- Gemini
- Llama
- Qwen
- DeepSeek
- Hermes
- Mistral

It is important to distinguish between a **model** and an **agent**. A model is the underlying language or code model. An agent is a system that uses the model to achieve a goal, often by using tools, reading and writing files, running tests, or interacting with other agents.

In such a system, different agents can use different models. For example, a cheaper or local model can be used for requirements analysis, while a stronger coding model can be used for test generation or implementation.

LLMs are central to many such systems, but they also have limitations:

- they can hallucinate
- they can miss requirements
- they can create inconsistent test cases
- they can generate code that does not run
- they can overfit to the prompt
- they may lack understanding of domain-specific constraints

This is why agent orchestration, review loops, and evaluation metrics are needed.

## Prompt Engineering

Prompt engineering means formulating instructions to a language model in a way that increases the probability of useful output. A prompt can contain the task, context, format requirements, examples, and constraints.

In agent-based systems, prompts are used to control agent behavior. For example, a Requirements Analyst Agent can be instructed to extract requirements and acceptance criteria in JSON format. A Test Design Agent can be instructed to create test cases with test type, test steps, test data, and a test oracle.

Prompt engineering matters because small differences in instructions can strongly influence output. For a QA system, it is especially important that prompts require:

- structured output format
- traceability to requirement IDs
- explicit assumptions
- identification of risks
- review of coverage
- consistent terminology

In a research project, prompts should be treated as part of the method. They should be versioned, documented, and reusable.

## Embeddings

Embeddings are numerical representations of text, code, or other objects. The purpose is to place semantically similar content close to each other in a vector space. This makes it possible to search for content based on meaning rather than exact keywords.

For example, two phrases such as "the app shall show an error message on network failure" and "the system shall inform the user when the API call fails" may end up close to each other in vector space even though the wording differs.

Embeddings are often used in RAG systems to find relevant documents, requirements, test cases, or previous bug reports. They become especially relevant when agents need to reuse earlier test designs, existing test cases, or domain knowledge.

## Vector Databases

A vector database stores embeddings and makes it possible to search for semantically similar content. Instead of matching only words, a vector database can retrieve content that is conceptually relevant.

In a QA context, a vector database can be used to store:

- requirement documents
- test cases
- acceptance criteria
- bug reports
- previous test design
- code snippets
- architecture decisions

Vector databases are often not the main focus in an initial analysis, but they can support an agentic system by giving agents access to previous knowledge. This becomes especially relevant when a simple demonstrator evolves into a more realistic QA support solution.

## Retrieval-Augmented Generation

Retrieval-Augmented Generation, or RAG, is a technique in which a language model is combined with information retrieval. Instead of relying only on the model's internal parameters, relevant information is fetched from external documents or databases and provided to the model as context. The original RAG idea combines parametric knowledge inside the model with non-parametric knowledge in an external source. ([arXiv](https://arxiv.org/abs/2005.11401?utm_source=chatgpt.com))

A typical RAG flow is:

```text
Question or task
  -> search for relevant information
  -> retrieve document excerpts
  -> send context to the LLM
  -> generate an answer
```

RAG can be used as a supporting component, but it does not have to be the main contribution in a study or prototype. The difference between RAG and agentic systems is important:

- RAG helps the model find relevant information.
- An agent can plan, use tools, create artifacts, modify files, and initiate new steps.
- A multi-agent system can distribute responsibility between several specialized agents.

RAG can therefore be integrated into, for example, a Test Design Agent that searches for previous test cases or previous requirements before creating new ones.

## AI Agent

An AI agent is a system that uses an AI model, often an LLM, to perform a task more autonomously than a normal chatbot. An agent can have a goal, instructions, access to tools, memory, the ability to read and write files, and the ability to interact with other systems.

A simple chatbot answers a question. An agent, by contrast, can execute a workflow. For example, an agent can:

- read a requirements document
- extract requirements
- save the result as JSON
- create test cases
- run tests
- analyze failures
- propose improvements

In research on LLM-based agents in software engineering, agents are often described as systems that extend LLM capabilities by giving them access to external resources and tools. ([arXiv](https://arxiv.org/abs/2409.02977?utm_source=chatgpt.com))

In a QA workflow, an agent can be described as a specialized component with a clear responsibility, such as requirements analysis, test design, test generation, or review.

## Agentic AI

Agentic AI describes AI systems that not only generate responses but can also act toward goals over multiple steps. This means the system can plan, choose tools, perform actions, evaluate outcomes, and potentially iterate.

Agentic AI differs from ordinary generative AI through its degree of agency. A generative AI model can write a test case. An agentic system can analyze requirements, decide which tests are needed, create test cases, check coverage, and request improvements if coverage is insufficient.

Agentic AI is often used to describe an overall architecture in which an orchestrator coordinates several specialized agents. This is central when the focus is not only on generating isolated artifacts, but on exploring how a multi-step flow can support requirement-based test design.

## Multi-Agent System

A multi-agent system consists of several agents that collaborate or are coordinated in order to solve a task. Each agent can have a particular role, specialization, or responsibility.

In traditional software architecture, this can be described as a separation of responsibilities. In a multi-agent system, this is strengthened by the fact that each agent can use an LLM and potentially make its own decisions within its scope.

One example of role division is the following set of agents:

- Orchestrator Agent
- Requirements Analyst Agent
- Test Design Agent
- Test Generation Agent
- Review Agent

The purpose of this separation is to mirror a QA workflow where requirements analysis, test design, test implementation, and review are different activities. A multi-agent architecture also makes it possible to use different models for different tasks.

## Orchestrator

An orchestrator is a component or agent that controls the workflow between other agents. The orchestrator is responsible for delegating tasks, collecting results, initiating iterations, and deciding when the workflow can continue.

In a simple agent flow, the sequence is hardcoded:

```text
Agent 1 -> Agent 2 -> Agent 3
```

In a more agentic system, the flow is controlled by an orchestrator:

```text
Requirements
  -> Orchestrator
  -> Requirements Analyst
  -> Review
  -> Test Design
  -> Review
  -> Test Generation
  -> Review
  -> Final result
```

The distinction matters. In a hardcoded chain, the steps always run in the same order. In an orchestrated system, output from one agent can be reviewed and sent back for improvement before the next step begins.

In agentic systems, the orchestrator is central because it makes it possible to go beyond a simple hardcoded agent chain.

## Agent Memory

Agent memory refers to information that an agent can retain or reuse over time. This can be short-term memory during a run or long-term memory across different runs.

Examples of memory in such a system include:

- previous requirements
- generated acceptance criteria
- previous test cases
- previous review comments
- model selections
- known error patterns
- test design decisions

Memory can be implemented in several ways, such as JSON files, database records, embeddings, or versioned artifacts. For an initial prototype, file-based memory may be sufficient.

Agent memory is important in QA because test design often benefits from past experience. A system that can reuse previous test patterns may be able to create more consistent and relevant tests.

## Shared Working Memory

Shared Working Memory is a more specific concept than general agent memory. It refers to a shared working memory that several agents can read from and write to during the same run.

In this project, the concept is central because the custom-built solution uses a visible run-scoped working memory with both shared and agent-private information. It is therefore not only a theoretical memory concept, but a concrete part of how the prototype controls context, feedback, and traceability between stages.

## Planning

Planning means that an agent or orchestrator breaks a goal down into substeps. In a QA system, the goal may be to create test artifacts from requirements. That can be decomposed into requirements analysis, acceptance criteria, test design, test generation, and review.

Planning is an important part of agentic systems because it allows the system to operate over several steps rather than only returning a direct answer. The planning can, for example, be handled by an Orchestrator Agent.

Example:

```text
Goal: Create test artifacts from requirements

Plan:
1. Extract requirements
2. Create acceptance criteria
3. Design tests
4. Generate concrete test cases
5. Review traceability
6. Iterate if needed
```

## Reflection and Review

Reflection means that an AI system reviews its own output or another agent's output and tries to identify weaknesses. In practice, this often appears as a Review Agent or a comparable review stage.

The Review Agent has an important QA role. It should not primarily create new test cases, but determine whether the generated artifacts are sufficient. Example review questions include:

- Is each requirement covered by at least one test case?
- Are there clear acceptance criteria?
- Are test oracles present?
- Are the test steps executable?
- Are assumptions documented?
- Are risks or gaps identified?

The Review Agent can therefore function as a quality gate between stages in the agent flow.

## Review Gate

Review Gate is not necessarily a universal standard term, but it is useful in this context to describe a review step that acts as a quality gate before the workflow is allowed to continue.

In the project, this appears both in the custom Review Agent logic and in the Hermes track, where verification and gate decisions were used as a clear control step before the final artifact was synthesized. The concept should therefore be understood as project-specific and workflow-specific.

## Selective Backtracking

Selective Backtracking describes a workflow in which the system does not always restart the whole process from the beginning, but instead returns only to the stage that needs improvement.

This is especially relevant in this prototype because the orchestrator attempts to send work back to the smallest reasonable earlier stage, such as Requirements Analyst or Test Design, instead of triggering a full rerun. The concept is therefore important here as a description of the project's routing strategy.

## Observability

Observability here means that the user can follow what the system actually does during execution, not only see the final result. This includes visibility into agent input, agent output, routing decisions, chosen model, timeout status, and memory updates.

Observability is highly central in this project and more concrete than in many general agent discussions. Here, it is not just about logging in a broad sense, but about a deliberate design choice to make agent behavior and run traces reviewable in both the GUI and the logs.

## Runtime Trace

Runtime Trace refers to the chain of events that arises during a run, for example when a stage starts, finishes, is forwarded, or is stopped.

The concept is especially relevant here because the prototype displays runtime activity and related execution traces in real time. A runtime trace makes it easier to understand why an agent flow succeeded, failed, or became stuck in iteration.

## Shared Blackboard

Shared Blackboard comes from blackboard-style collaboration patterns in which several agents share a common workspace. It is closely related to shared memory, but is more often used when the focus is on coordination between several roles writing to the same shared context.

In this project, the concept is primarily relevant to the Hermes solution, where a root task functioned as a shared blackboard for the swarm. It should therefore be explained as a comparison concept linked to the external framework track rather than as the main term for the custom-built solution.

## Synthesizer

A Synthesizer is an agent role whose purpose is to combine and refine results from several earlier agent stages into a final consolidated artifact. Unlike a typical worker agent, it does not primarily produce a partial result from raw input. Instead, it receives multiple intermediate results and assembles them into a more complete deliverable.

In the Hermes track, the Synthesizer was used as the final role after the verification stage. It received material from the earlier specialist roles and shaped the final test design. The concept is therefore relevant in this project as a description of the Hermes Agent solution, not as a central component of the custom HF QA agent service solution.

## Tool Calling

Tool Calling means that an agent can use external tools to perform actions. This might include reading files, writing JSON, searching documents, running tests, or calling an API.

Tool Calling is a central difference between a standard LLM and an agent. An LLM can suggest a command. An agent with tool access can potentially perform the command.

In such a system, tool calling can be used to:

- read requirement files
- write structured requirements as JSON
- create test cases as files
- run test tools
- read test results
- generate reports

This makes the system more integrated and closer to a real QA workflow.

## Function Calling

Function Calling is a specific form of tool calling in which the model calls predefined functions with structured arguments. For example, the model may return a JSON object that is then used to invoke a function in the program.

Example:

```json
{
  "requirement_id": "R1",
  "test_type": "unit",
  "priority": "high"
}
```

Function Calling is especially relevant when structured output from an LLM is needed. It can be used to create consistent requirement objects, test design objects, and review results.

## Model Context Protocol

Model Context Protocol, MCP, is an open standard for connecting AI applications to external data sources and tools. The purpose is to create a standardized way for AI systems to access context, data, and functions. ([Anthropic](https://www.anthropic.com/news/model-context-protocol?utm_source=chatgpt.com))

MCP can be described as an integration layer between AI models and surrounding systems. Instead of every agent framework building its own special solutions for filesystems, databases, GitHub, test tools, or document handling, MCP can provide a shared protocol.

MCP is relevant here as a possible integration pattern. For an initial prototype, MCP may not need to be implemented directly, but the concept matters because modern agent platforms increasingly rely on standardized tool integrations.

## Software Engineering

Software Engineering refers to the systematic development, operation, and maintenance of software systems. It includes requirements handling, design, implementation, testing, deployment, maintenance, and quality assurance.

This project belongs to software engineering because it explores how AI agents can support a concrete software workflow: from requirements to test artifacts.

The focus is not on AI as an isolated technology, but on how AI can be integrated into a software process.

## AI for Software Engineering

AI for Software Engineering means the use of AI techniques to support software development. Examples include code generation, requirements analysis, test generation, debugging, refactoring, documentation, and code review.

LLM-based agents have become particularly interesting in software engineering because they can combine language understanding, code generation, and tool use. A recent survey describes how LLM-based agents are used in software engineering and how multiple agents and human interaction can help address complex problems. ([arXiv](https://arxiv.org/abs/2409.02977?utm_source=chatgpt.com))

In this context, AI for Software Engineering is focused on QA and test-related activities rather than general code production.

## Agentic Software Engineering

Agentic Software Engineering means that agentic AI systems are used to support or automate parts of the software development process. Unlike simpler AI assistants, agentic systems can operate across multiple steps, use tools, and coordinate multiple specialized roles.

Examples of agentic software engineering flows include:

- requirements to code
- requirements to test cases
- bug report to fix
- code to test suite
- test result to code repair
- pull request review

Agentic Software Engineering can be used to create QA-oriented workflows where agents transform requirements into test design and test artifacts.

## Software Quality Assurance

Software Quality Assurance, or QA, includes processes, methods, and activities intended to ensure software quality. QA is not only about finding bugs through testing, but also about building quality through requirements handling, review, process control, traceability, and improvement.

The QA perspective is central here. The goal is not merely to generate code or tests, but to explore how agentic systems can support a quality-assured workflow.

Important QA aspects in the project are:

- requirement coverage
- test design
- traceability
- test oracles
- review loops
- measurable quality
- iteration cycles

## Verification and Validation

Verification and Validation, often abbreviated V&V, are central concepts in quality assurance.

- **Verification** means checking that the system is built correctly according to specification.
- **Validation** means checking that the right system is being built according to user needs.

In this context, verification can be linked to tracing generated tests back to requirements and ensuring that test artifacts follow specified formats. Validation is more difficult because it requires judging whether the requirements themselves reflect real user needs.

An agentic QA system can potentially support both verification and validation, but the first prototype should mainly focus on verification.

## Requirement

A requirement describes a property, function, constraint, or quality that a system must fulfill. Requirements can be functional or non-functional.

Example of a functional requirement:

```text
The system shall be able to display a joke from an external API.
```

Example of a non-functional requirement:

```text
The system shall show a response within two seconds.
```

In requirement-driven agent flows, requirements are often the main input. A Requirements Analyst Agent can break down requirement text into structured requirements with ID, description, actor, action, conditions, and acceptance criteria.

## Acceptance Criteria

Acceptance criteria describe the conditions under which a requirement is considered fulfilled. They make the requirement more testable and act as a bridge between requirements and test design.

Example:

```text
Requirement: The user shall be able to fetch a new joke.

Acceptance criteria:
- When the user clicks the "New joke" button, a new API request shall be sent.
- When the API request succeeds, a new joke shall be displayed.
- If the API request fails, an error message shall be displayed.
```

Acceptance criteria are central because a Test Design Agent can use them as the basis for creating test cases.

## Requirement Traceability

Requirement Traceability means that requirements can be linked to other artifacts, such as acceptance criteria, test cases, code, or bug reports. Traceability is important for showing that every requirement has been verified.

Traceability is often used to measure requirement coverage. Each generated test case should refer to one or more requirement IDs.

Example:

| Requirement ID | Test case | Test type |
|---|---|---|
| R1 | TC-001 | Unit test |
| R2 | TC-002 | GUI test |
| R3 | TC-003 | E2E test |

Traceability is also important for the Review Agent, which can identify requirements without test coverage.

## Test Design

Test design is the process of shaping test cases based on requirements, risks, system behavior, and acceptance criteria. Test design is not only about writing test code, but about deciding what should be tested, why it should be tested, and how the test should determine whether the result is correct.

A Test Design Agent may be responsible for creating a test design that includes:

- test type
- test purpose
- test steps
- test data
- test oracle
- linkage to requirements
- risks and assumptions

Test design is a central QA activity and should be distinguished from test generation. Test design describes what should be tested. Test generation creates the concrete test artifacts.

## Test Oracle

A test oracle determines whether a test result is correct or incorrect. Without a test oracle, a test can be executed, but it is not possible to know whether the result is right.

Example:

```text
If the API returns status 200 and a field called "value", the text in "value" shall be displayed in the user interface.
```

This is a test oracle because it defines the expected behavior.

In AI-generated test design, test oracles are especially important. A common problem is that models generate test steps without clear expected results. Test Design Agent should therefore always be required to state the test oracle.

## Unit Test

A unit test tests a small isolated part of the system, such as a function, class, or component. Unit tests are often fast and are used to verify low-level logic.

In systems like this, unit tests can be used to verify, for example:

- parsing of API responses
- error handling
- transformation logic
- input validation

Unit tests are especially important in a TDD workflow because they can be created early and used to guide implementation.

## Integration Test

An integration test verifies that several components work together. For example, an integration test can check that a backend component correctly calls an external API and handles the response.

Integration tests become relevant when a demonstrator or application includes frontend, backend, and an external API connection.

## GUI Test

A GUI test tests the system through the graphical user interface. It can, for example, verify that buttons, text fields, and error messages behave as expected.

GUI testing is relevant when generated tests should verify the user's visible interaction with a web application.

GUI tests often require selectors, for example:

```text
#new-joke-button
#joke-text
#error-message
```

The Test Design Agent therefore needs to define selectors that the later implementation must follow.

## End-to-End Test

An End-to-End test, or E2E test, verifies a system flow from the user's perspective across several layers of the system. An E2E test can, for example, open a webpage, click a button, wait for an API response, and check that the result is displayed.

E2E tests are often more realistic than unit tests, but they are also slower and more sensitive to environment problems.

E2E tests can be used to verify that the complete flow from requirement to working user interaction is correct.

## Test Automation

Test automation means that tests are executed automatically by tools instead of manually by a human. Test automation is central to modern CI/CD flows.

Test automation is relevant on two levels:

1. Agents generate test artifacts automatically.
2. The generated tests can be executed automatically to verify the system.

This places the project close to both AI-assisted test design and automated QA.

## Test-Driven Development

Test-Driven Development, or TDD, is a development method in which tests are written before production code. A classic TDD flow is often described as:

```text
Red -> Green -> Refactor
```

This means:

- write a test that initially fails
- implement the smallest possible amount of code to make the test pass
- improve the code without changing behavior

TDD can also be used as a design principle. In that case, the Test Design Agent and Test Generation Agent create test design and test cases before any implementation takes place. An Implementation Agent or equivalent component can then create or modify code until the tests pass.

## Self-Healing

Self-healing means that a system automatically detects an error, analyzes the cause, and tries to correct the problem. In the context of agentic software development, self-healing can mean that an agent runs tests, reads error messages, modifies code or test artifacts, and runs tests again.

Self-healing can be described as an iterative feedback loop:

```text
Generate artifact
  -> Review or test
  -> Identify error
  -> Improve artifact
  -> Run again
```

Self-healing is not the same as always finding the right solution. It means that the system has a mechanism for iterating based on feedback.

## Code Coverage

Code Coverage measures how much of the code is executed by the tests. Common forms of coverage include:

- line coverage
- function or method coverage
- branch coverage

Code coverage is a useful but limited metric. High code coverage does not necessarily mean that the tests are good. Tests can execute code without verifying the right behavior.

Code coverage can be used as a complementary metric, but it should not be the only measure of test quality.

## Requirement Coverage

Requirement Coverage measures how large a share of requirements are covered by test cases. This is especially relevant in contexts where the goal is requirement-based test design.

Example:

```text
Number of requirements with at least one test case / Total number of requirements
```

If 8 out of 10 requirements have at least one linked test case, requirement coverage is 80%.

Requirement coverage is central to the Review Agent, which can identify requirements without tests or with insufficient test design.

## Test Pass Rate

Test Pass Rate measures the proportion of tests that pass during execution.

Example:

```text
Number of passing tests / Total number of tests
```

This is a simple but important metric. In a self-healing flow, Test Pass Rate can be used to determine whether the system needs another iteration.

## Iteration Cycles

Iteration cycles measure how many times the system needs to go through a review or repair loop before the result is accepted.

This is an especially interesting metric because it captures how efficient an agentic system is. If a system requires many iterations, this can indicate weak prompts, a weak model, poor test design, or unclear requirement structure.

## Execution Time

Execution time measures how long an agent flow or test flow takes to run. This can be measured per agent stage or for the whole pipeline.

Example:

| Stage | Time |
|---|---|
| Requirements analysis | 20 seconds |
| Test design | 45 seconds |
| Test generation | 60 seconds |
| Review | 30 seconds |
| Total | 155 seconds |

Execution time is relevant because agentic systems can become slow, especially if several models, tools, and review loops are used.

## Code Quality

Code Quality refers to properties that affect how easy code is to understand, maintain, test, and extend. Examples of code quality metrics include:

- complexity
- duplication
- code smells
- maintainability
- security issues
- reliability issues

Code quality can be used as a metric if the system also generates code or test code. For Python, tools such as `ruff`, `pylint`, and `radon` can be used. For broader analysis, SonarQube can be relevant.

## SonarQube

SonarQube is a tool for static code analysis. It can analyze code quality, security issues, duplication, code smells, and in some configurations test coverage as well.

SonarQube can be used as one possible tool for measuring the quality of generated code or generated tests. For an initial prototype, simpler tools such as linting and coverage may be sufficient, but SonarQube is relevant as an established industrial tool.

## Agent Framework

An agent framework is a library or platform for creating, configuring, and running AI agents. Agent frameworks often provide support for roles, tool calls, memory, orchestration, communication between agents, and integration with different LLMs.

Examples of agent frameworks or agent platforms include:

- CrewAI
- LangGraph
- AutoGen
- OpenAI Agents SDK
- OpenClaw
- Hermes Agent Framework

The choice of agent framework is a central part of many literature studies and prototypes. One important goal is to understand which frameworks are best suited to QA workflows in which requirements, test design, test generation, and review need to be coordinated.

## LangChain

LangChain is a library ecosystem for building LLM-based applications. It provides building blocks for prompts, chains, tool calls, memory, document retrieval, and integration with different model providers.

LangChain is relevant because it has long been a common foundation for agent-like and tool-supported LLM flows. In this project, LangChain is mainly relevant as the broader ecosystem around LangGraph rather than as the main framework for the custom-built solution.

## LangGraph

LangGraph is a graph-based agent framework within the LangChain ecosystem. It is used to define nodes, state, and transitions in agentic workflows in a more explicit way than simpler prompt chains.

LangGraph is relevant here because it was used as a comparison track against the custom-built orchestrator solution. Its strength lies in explicit modeling of graph structure, state management, and transitions between stages. In this project, the limitation was that the flow became more hardcoded than in the custom-built solution with more dynamic routing.

## Hermes Agent Framework

Hermes Agent Framework is an agent framework that was used as an external comparison track in the project. It became particularly relevant through the swarm solution that was set up to compare how quickly and clearly a QA-like multi-agent flow could be built in another framework.

In the project, Hermes was used to create a Kanban-like swarm with clear roles, a shared blackboard, and verification stages. Hermes is therefore important both as a concept in the literature study and as a practical comparison object against the custom-built solution and the LangGraph track.

## Model-Agnostic Architecture

A model-agnostic architecture means that the system is not tightly bound to one specific LLM. Instead, different models can be used depending on the task, cost, availability, and quality requirements.

Example:

```yaml
requirements_model: qwen
test_design_model: deepseek
test_generation_model: gpt
review_model: claude
```

This matters in the project because different agents can have different needs. Requirements analysis may be handled by a local model, while test generation may require a stronger coding model.

## Local and Cloud-Based Models

Local models run on your own hardware or in your own environment, often through tools such as Ollama. Cloud-based models run through APIs from providers such as OpenAI, Anthropic, Google, or Hugging Face.

Local models can provide better control, lower marginal cost, and potentially better data privacy. Cloud-based models can provide higher quality, stronger coding ability, and easier operations.

Supporting both options can be valuable. It makes a prototype more flexible and allows comparison between different model strategies.

## Ollama

Ollama is a tool for running local language models. It is commonly used with models such as Llama, Qwen, Mistral, DeepSeek, and Hermes.

Ollama can be used when agents need to run on local models. This makes it possible to test how far the project can go without commercial APIs.

## Hugging Face

Hugging Face is a platform for AI models, datasets, and applications. Hugging Face Spaces can be used to publish simple AI demonstrators and web interfaces.

Hugging Face is relevant in two ways:

1. as a possible source of models and APIs
2. as a hosting environment for the demonstrator

Because the project already had experience from an earlier RAG prototype on Hugging Face, it is a natural option for the first demonstrator.

In this project, Hugging Face was also used to host `qa-agent-service` and make agent functionality available through public endpoints. Hugging Face therefore became not only a model platform, but also a practical operating environment for agent-adjacent services.

## Agent-as-a-Service

Agent-as-a-Service can be used as a term when agent functionality is exposed as a separate service instead of running all agent logic directly inside the same application. In practice, this means that clients call an agent backend over the network, for example through HTTP-based endpoints.

This concept fits the project's `qa-agent-service` well, where Requirements Analyst, Test Design, and Review could be exposed as public services on Hugging Face. Even though the term is not always used consistently in literature, it is useful here to describe the difference between:

- agents that run directly inside the same app
- agents that are used as a separately hosted service

## REST API

REST API is a common way of exposing functionality over HTTP. A client sends requests to defined endpoints and receives responses, for example in JSON format.

REST API is relevant in the project because `qa-agent-service` evolved from a more key-dependent Hugging Face setup toward public REST endpoints. That made the service easier to reuse from different clients and frameworks, including comparisons against Hermes and other integration tracks.

## DeepEval

DeepEval is a framework for evaluating LLM-based applications and agent flows. It is used to measure the quality of generated content through defined criteria and evaluation logic, rather than only subjective manual impressions.

DeepEval is relevant here because there were plans to use it to assess the quality of generated test cases. Even though practical evaluation later relied heavily on Hermes comparisons and manual senior QA review, DeepEval remains an important concept to include in the knowledge base.

## Traceability Matrix

Traceability Matrix is a QA concept for a structure that links requirements to corresponding test cases, verification steps, or other artifacts. The purpose is to show that each requirement can be followed to some form of validation.

The term is relevant here because traceability between requirements and test design is one of the project's core questions. In the Hermes comparison, a concrete traceability matrix was also produced, which makes the term practically grounded in the work that was actually carried out.

## Gradio

Gradio is a Python-based framework for building simple web interfaces for AI applications and demonstrators. It is often used for rapid prototyping, especially together with Hugging Face Spaces.

Gradio is central to the project because the AI Agents part was built in Gradio. An important reason was that there was already some prior experience with the tool, which made it a pragmatic choice for quickly producing a working public experimental environment.

## Streamlit

Streamlit is a Python framework for building data-driven web applications and interactive interfaces with relatively little code. It is often used for prototypes, dashboards, and AI demonstrators.

Streamlit is relevant in the project because the LangGraph track ended up being run in Streamlit. The reason was that Gradio introduced practical limitations for that part of the work, which made Streamlit the more workable alternative in that comparison.

## GitHub and GitHub Pages

GitHub is used for version control, source code, and documentation. GitHub Pages is used to publish the project's knowledge base as an open website.

GitHub can fill two roles:

- technical version control for code and documents
- a public documentation surface for the knowledge base

GitHub Pages makes it possible to publish the literature study and knowledge base continuously and make them available to supervisors, colleagues, and future readers.

## Continuous Integration

Continuous Integration, or CI, means that code and tests are run automatically when changes are made in a repository. CI can be used to build, test, and deploy software.

CI can be used to:

- run generated tests
- measure test results
- calculate code coverage
- deploy the demonstrator
- publish documentation

GitHub Actions is a common CI tool in GitHub-based projects.

## Demonstrator

A demonstrator is a prototype that shows that an idea is technically feasible. It does not have to be production-ready, but it should be concrete enough to be used for evaluation.

A demonstrator can be a web-based system where the user submits requirements and receives test artifacts. The demonstrator is then used to investigate whether a proposed agent architecture is practically viable.

## Artifact

An artifact is a concrete result produced in a development or QA process. In this context, artifacts can include:

- structured requirements
- acceptance criteria
- test design
- test cases
- test data
- selectors
- reports
- code files

The agent flow can be described as a process in which each agent produces or reviews artifacts.

## Summary

This chapter has introduced the central concepts on which the project is built. The most important distinction is the difference between an LLM, an AI agent, and an agentic multi-agent system.

An LLM is a model that generates text or code. An AI agent uses an LLM together with instructions, tools, and goals. A multi-agent system consists of several specialized agents that are coordinated, often by an orchestrator.

A central idea in this area is to use agentic AI to support QA workflows. The focus is then on transforming requirements into test design and test artifacts with traceability, review, and the possibility of iteration.

---

This material was produced together with generative AI and was then reviewed and refined as part of the project's documentation work.
---
