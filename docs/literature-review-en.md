## Literature study on AI agents for Software Quality Assurance

> **Status:** In progress (Version 0.3)  
> **Language:** English  
> **Last updated:** 2026-07-05

---

## About the document

This document is the literature study for the project **AI agents for Software Quality Assurance**.

The purpose of the literature study is to build a foundational understanding of AI agents, agentic systems, and their use in Software Engineering and Software Quality Assurance. The result is used as knowledge support for the continued development of the project's research prototype.

---

## Use of AI

This literature study is developed in collaboration between the author and generative AI.

AI is used to support:

- identification of relevant research papers
- summarization of research findings
- structuring of the literature study
- clarification of concepts
- language review

All summaries and conclusions are reviewed and verified before they are included in the document.

---

## Contents

1. Introduction
2. Method
3. Review of research papers
4. Summary
5. References

---

# 1. Introduction

The development of generative AI and large language models (LLMs) has changed how software development is carried out in recent years. What initially appeared as intelligent coding assistance has gradually evolved into agentic AI systems in which several specialized AI agents collaborate to solve complex tasks across the full software development lifecycle.

At the same time, Software Quality Assurance (QA) has become an area where AI is expected to contribute to improved requirements analysis, test design, test generation, and quality control. Despite the fast pace of change, the research field is still young, and several questions about architecture, collaboration between agents, and quality assurance remain open.

The purpose of this literature study is therefore to create an overview of current research in the area and identify which ideas, architectures, and working methods are relevant to the development of agentic QA systems.

---

## 2. Method

This study is a targeted literature study.

The goal has not been to conduct a complete systematic literature review, but to identify a limited set of research papers that together provide a solid understanding of the research area.

The selection has focused on three types of publications:

- survey papers
- research papers on agentic systems
- research papers in AI-assisted Software Quality Assurance

The emphasis is on publications from **2023-2026**, since development in Agentic AI has been particularly rapid during this period.

---

## 3. Review of research papers

The following research papers form the basis of this literature study.

---

## Survey papers

These papers form the foundation of the literature study and should be read first.

| No. | Paper | Year | Short description | Link |
|---:|----------|----|------------------|------|
| 1 | **Large Language Model-Based Agents for Software Engineering: A Survey** | 2024 | The most important survey paper in the area. It describes LLM-based agents, agent components, multi-agent systems, and the research landscape in Software Engineering. | https://arxiv.org/abs/2409.02977 |
| 2 | **Agents in Software Engineering: Survey, Landscape and Vision** | 2025 | Complements the first survey and presents the Perception-Memory-Action framework together with the research landscape for AI agents in Software Engineering. | https://arxiv.org/abs/2409.09030 |
| 3 | **The Rise of Agentic Testing: Multi-Agent Systems for Robust Software Quality Assurance** | 2026 | Describes how multiple AI agents collaborate to generate, execute, analyze, and improve tests in an iterative QA process. | https://arxiv.org/abs/2601.02454 |
| 4 | **AgentCoder: Multi-Agent-based Code Generation with Iterative Testing and Optimisation** | 2023 | One of the most influential works on agentic software development, where several specialized agents collaborate through feedback loops. | https://arxiv.org/abs/2312.13010 |
| 5 | **Automatic High-Level Test Case Generation using Large Language Models** | 2025 | Shows how large language models can generate high-level test cases directly from requirements and use cases. Very close to the project's focus on requirement-based test design. | https://arxiv.org/abs/2503.17998 |

---

## Research papers

These papers provide a deeper understanding of different agent architectures and modern working methods.

| No. | Paper | Year | Short description | Link |
|---:|----------|----|------------------|------|
| 6 | **MetaGPT: Meta Programming for Multi-Agent Collaborative Framework** | 2023 | Describes a role-based multi-agent system in which different AI agents correspond to classic software engineering roles such as Product Manager, Architect, Engineer, and QA. | https://arxiv.org/abs/2308.00352 |
| 7 | **SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering** | 2024 | Shows how AI agents can work directly with real codebases, terminals, Git repositories, and developer tooling. | https://arxiv.org/abs/2405.15793 |
| 8 | **Agentic AI in the Software Development Lifecycle: Architecture, Empirical Evidence, and the Reshaping of Software Engineering** | 2026 | Describes how agentic approaches affect the full software development process and presents a modern reference architecture for Agentic Software Engineering. | https://arxiv.org/abs/2604.26275 |

---

## Summary

This reading list contains a total of **eight selected research papers**.

The selection is judged to provide a good balance between:

- foundational theory on AI agents
- modern agent architectures
- Agentic Software Engineering
- Software Quality Assurance
- requirements analysis
- test design
- test generation

The goal is not to provide a complete overview of the research field, but to create a sufficient knowledge base to understand the area and justify the design choices later made in the project's research prototype.


## 3.1 Publication 1: Large Language Model-Based Agents for Software Engineering: A Survey (2024)

This survey paper provides a broad review of the research field around LLM-based AI agents in Software Engineering. The authors analyze 124 scientific publications and summarize how AI agents are used across different parts of the software lifecycle, such as requirements handling, design, code generation, testing, code review, and maintenance. The purpose is to map the research landscape, identify recurring architectural patterns, and point out areas where additional research is needed.

The paper shows that AI agents have evolved from simple language-model use toward more advanced agentic systems that combine planning, memory, tool use, and feedback loops. At the same time, it concludes that most solutions are still at the research or prototype stage and that established architectures are missing for many application areas.

An important conclusion is that AI agent usage is growing across the full field of Software Engineering, but that the research is unevenly distributed. Areas such as code generation and programming assistance dominate, while Software Quality Assurance, requirement-driven test design, and verification remain significantly less explored. The authors therefore identify these areas as promising directions for future research.

Significance for this study

This paper primarily serves as an overview of the research field and provides a broad understanding of how AI agents are used in Software Engineering. Unlike later papers, it does not present a specific agent architecture, but summarizes the current state of research and identifies recurring design principles and research gaps. For this study, the paper is important because it motivates why agentic QA systems are a relevant research area and shows that there is still limited research on AI agents for requirements analysis, test design, and Software Quality Assurance.

---

## 3.2 Publication 2: Agents in Software Engineering: Survey, Landscape and Vision (2025)

This survey paper aims to create a shared understanding of what an AI agent is in Software Engineering and how modern agentic systems can be described through a unified framework. The authors note that the term AI agent is used in many different ways in the literature, ranging from simple language models with a prompt to advanced systems with planning, memory, tool use, and several collaborating agents. The paper's main contribution is therefore a conceptual model that describes the central components of a modern AI agent.

The authors identify four foundational pillars that together describe the agent's functionality: Perception, Reasoning, Action, and Evolution. Perception concerns the agent's ability to observe and interpret information from its environment, such as requirement specifications, source code, test results, or user instructions. Reasoning describes how the agent analyzes information, draws conclusions, and makes decisions with the help of the language model. Action covers the agent's ability to perform concrete tasks, such as generating code, creating test cases, updating files, or using external tools. The fourth pillar, Evolution, describes how the agent can gradually improve its behavior through feedback, experience, reflection, and iteration.

The paper also highlights memory as a central component in agent architecture. The authors distinguish between several forms of memory. Short-Term Memory is used to keep current context during an ongoing task, while Long-Term Memory stores more persistent knowledge, such as past experience, domain knowledge, or historical solutions. Working Memory is used to share information between multiple collaborating agents during the same run and thereby supports a shared workflow. Finally, the paper also describes External Memory, where the agent retrieves information from external knowledge sources such as RAG solutions, vector databases, Git repositories, or document management systems.

Another important conclusion is that modern agentic systems increasingly rely on specialized agent roles rather than a single general-purpose agent. By dividing the work between, for example, a Requirements Agent, a Test Design Agent, and a Review Agent, each agent can focus on a narrower task, which improves quality, traceability, and the ability to incorporate feedback. The paper also shows that an orchestrator is often used to coordinate collaboration between agents and control the workflow.

For this study, the paper is particularly relevant because it provides a clear theoretical model for how agentic systems can be structured. The four pillars and the described memory architecture form a useful framework for analyzing and comparing different agent solutions. At the same time, the paper's description is closely aligned with the agent architecture later used in the project's research prototype, where specialized QA agents collaborate under the control of an orchestrator and share information through a common working memory. This paper is one of the most important theoretical references in the literature study.

---

## 3.3 Publication 3: The Rise of Agentic Testing: Multi-Agent Systems for Robust Software Quality Assurance (2026)

This paper examines how agentic AI systems can be used to automate and improve Software Quality Assurance. Unlike traditional AI solutions, where a single language model is used to generate test cases or answer questions, the authors advocate a multi-agent architecture in which several specialized agents collaborate throughout the full testing process. The aim is to create a more robust, traceable, and iterative way of working in which different agent roles are responsible for different parts of the testing process.

The paper presents a reference architecture consisting of several collaborating agents. A Test Generation Agent is responsible for analyzing requirements and generating test cases, an Execution Agent runs the tests and collects the results, and a Review Agent analyzes the outcome and identifies weaknesses or improvement opportunities. The result is then used as feedback to earlier steps, creating an iterative improvement process in which the test cases can gradually be refined.

A central idea in the paper is that testing should no longer be viewed as a linear workflow but as a continuous feedback loop. By combining test generation, execution, and review, the system can identify weaknesses in the test cases and automatically initiate new iterations. The authors argue that this leads to better test quality, higher requirement coverage, and more robust test suites than if each step is performed in isolation.

The paper also discusses several challenges in agentic testing. Because multiple agents collaborate, coordination, communication, and traceability become important concerns. The authors therefore emphasize the need for an orchestrator that controls the workflow, transfers information between agents, and decides when a new iteration should be carried out or when the process can stop. They also highlight the importance of shared memory and clear review mechanisms to reduce the risk of incorrect or hallucinatory results.

For this study, the paper is particularly relevant because it describes an agent architecture that is close to the project's overall idea. Even though the proposed solution mainly focuses on test generation and test execution, while the planned research prototype starts from requirements analysis and test design, both solutions are built on the same core principles: specialized agent roles, a central orchestrator, and iterative feedback loops. The paper also shows that the Review Agent has a central role in improving the quality of generated test artifacts, which strengthens the idea that quality review should be a distinct agent function and not only a final step in the process.

Significance for this study

One important lesson from the paper is that more agents do not automatically lead to better results. Every additional agent increases complexity through more handoffs, more communication, and stronger orchestration requirements. At the same time, the paper shows that some agent roles add clear value and are therefore justified.

One such role is the Review Agent. Just as a person rarely catches all errors in their own work, there is a risk that an agent will fail to identify weaknesses in its own output. An independent review agent can therefore analyze the produced material, check quality, traceability, and coverage, and provide feedback before the result is sent forward or approved. By analogy, this is similar to not grading your own mathematics exam, but letting someone else perform an independent review.

This reasoning provides strong support for using a separate Review Agent in an agentic QA system, while also arguing against splitting the workflow into an unnecessarily large number of specialized agents. A well-balanced agent architecture should therefore contain as few agents as possible, but as many as needed to ensure quality and traceability.

---

## 3.4 Publication 4: AgentCoder: Multi-Agent-based Code Generation with Iterative Testing and Optimisation (2023)

AgentCoder presents a multi-agent framework for automatic code generation using large language models. Unlike traditional solutions, where a single model is responsible for both code generation and testing, AgentCoder is built around three specialized agent roles: a Programmer Agent, which generates the program code; a Test Designer Agent, which independently constructs test cases from the problem formulation; and a Test Executor Agent, which executes the tests and feeds the result back to the other agents.

A central idea in the paper is to separate code generation from test design. By letting an independent agent create the test cases, the risk is reduced that the same reasoning or incorrect assumptions will appear both in the code and in the tests. This increases the probability that logical errors, edge cases, and other defects will be detected before the solution is accepted.

The agents work iteratively through a feedback loop in which the results from test execution are used to improve the generated code. If tests fail, the Programmer Agent receives feedback and can generate an improved version of the solution. The process is repeated until the tests pass or a predefined stopping condition is reached.

The experiments show that AgentCoder achieves better results than several earlier methods for automatic code generation. The authors show that the combination of specialized agent roles and iterative feedback improves both code quality and the use of computational resources compared with several alternative solutions.

Significance for this study

AgentCoder is particularly relevant because it shows how specialized AI agents can collaborate to solve a complex software engineering task. Even though the framework focuses on code generation rather than Software Quality Assurance, several of its underlying principles transfer directly to this study. In particular, the paper highlights the value of clear agent roles, independent test design, and iterative feedback loops. These principles are closely aligned with the planned QA architecture, where an orchestrator coordinates specialized agents for requirements analysis, test design, and quality review.

AgentCoder has had major influence on this study because it shows how specialized agents can collaborate through iterative feedback loops. Not because the goal is to build a code generator, but because it demonstrates two important principles:

1. Specialization works. An agent should have a clear responsibility instead of trying to do everything.
2. The one producing a result should not be the only one verifying it. An independent test or review agent produces higher quality.

Both AgentCoder and The Rise of Agentic Testing show that specialized agent roles combined with iterative feedback loops provide better quality and robustness than a single general-purpose agent. Even though the papers focus on different application areas, they are built on the same underlying architectural principles.

---

## 3.5 Publication 5: Automatic High-Level Test Case Generation using Large Language Models (2025)

A concluding paper will be selected within AI-assisted testing or Requirements Engineering depending on which area proves most relevant to the continued research prototype.

---

## 3.6 Publication 6: MetaGPT: Meta Programming for Multi-Agent Collaborative Framework (2023)

MetaGPT presents a multi-agent framework in which the development process is modeled after how a real software development team works. Instead of allowing one language model to perform all tasks, the work is divided among several specialized agent roles, such as Product Manager, Architect, Project Manager, Engineer, and QA Engineer. Each agent is responsible for a clearly delimited work area and produces artifacts that are used by later agents.

A central idea in MetaGPT is that software development can be described as a chain of well-defined work products. Each agent therefore works toward a specific artifact, such as a requirement specification, system design, or code, creating a clear structure and traceability throughout the development process.

The paper places strong emphasis on communication between agents. The authors show that free dialogue between many agents quickly leads to large amounts of text, which both increases cost and reduces efficiency. To reduce this, they introduce the principle "Code = SOP (Standard Operating Procedure)," where communication is standardized through clear workflows and predefined information formats. In this way, only the information that the next agent actually needs is transferred.

Another important conclusion is that token consumption becomes a critical factor in larger multi-agent systems. If every agent forwards the full conversation history to the next agent, a great deal of information noise quickly accumulates. MetaGPT therefore shows how summaries, structured artifacts, and selective information transfer can reduce the number of tokens used without reducing result quality. This makes the system both faster and cheaper to run.

The paper also emphasizes the importance of specialization. Giving each agent a clear area of responsibility reduces complexity in each step while making the overall solution easier to understand, extend, and debug.

Significance for this study

MetaGPT is particularly relevant because it shows how a larger agentic system can be organized in a structured and resource-efficient way. For this study, the most important contributions are not the specific agent roles but the architectural principles presented in the paper. In particular, it highlights the importance of clear agent roles, standardized communication between agents, and transferring only the information needed for the next step. These principles are directly applicable when developing an agentic QA system in which several agents collaborate around requirements analysis, test design, and quality review.

Own reflections

The most important lesson from MetaGPT is that communication between agents is at least as important as the intelligence of the agents themselves. A well-functioning multi-agent system is therefore not only about choosing the right language model, but also about designing effective information flows. By transferring structured artifacts instead of whole conversations, both token usage and execution time can be reduced while traceability improves. For a QA system, this means that agents should communicate through well-defined objects, such as requirement lists, test designs, or review reports, rather than through long free-form dialogues.

---

## 3.7 Publication 7: SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering (2024)

*Summary will be written after review.*

---

## 3.8 Publication 8: Agentic AI in the Software Development Lifecycle: Architecture, Empirical Evidence, and the Reshaping of Software Engineering (2026)

*Summary will be written after review.*

## 4. Reflections from the literature study

After reviewing the selected research papers, the most important conclusions will be summarized around:

- AI agents
- Multi-Agent Systems
- Agentic Software Engineering
- AI for Software Quality Assurance
- research gaps
- implications for future agentic QA systems

The result from the literature study is used as knowledge support for the project's continued design work.

---

## 5. References


1. **Large Language Model-Based Agents for Software Engineering: A Survey (2024)**  
   https://arxiv.org/abs/2409.02977

2. **Agents in Software Engineering: Survey, Landscape and Vision (2025)**  
   https://arxiv.org/abs/2409.09030


3. **The Rise of Agentic Testing: Multi-Agent Systems for Robust Software Quality Assurance (2026)**  
   https://arxiv.org/abs/2601.02454

4. **AgentCoder: Multi-Agent-based Code Generation with Iterative Testing and Optimisation (2023)**  
   https://arxiv.org/abs/2312.13010

5. **Automatic High-Level Test Case Generation using Large Language Models (2025)**  
   https://arxiv.org/abs/2503.17998

6. **MetaGPT: Meta Programming for Multi-Agent Collaborative Framework (2023)**  
   https://arxiv.org/abs/2308.00352

7. **SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering (2024)**  
   https://arxiv.org/abs/2405.15793

8. **Agentic AI in the Software Development Lifecycle: Architecture, Empirical Evidence, and the Reshaping of Software Engineering (2026)**  
   https://arxiv.org/abs/2604.26275

---
