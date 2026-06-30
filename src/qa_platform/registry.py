from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .agents import RequirementsAnalystAgent, ReviewAgent, TestDesignAgent


@dataclass(frozen=True)
class AgentSpec:
    agent_key: str
    agent_name: str
    description: str
    default_directives: str
    default_provider_strategy: str
    default_model_family: str
    default_model_override: str = ""
    default_timeout_seconds: int = 60
    stage_key: str = ""
    stage_index: int = 0


@dataclass
class RegisteredAgent:
    spec: AgentSpec
    implementation: Any = None


@dataclass
class AgentRegistry:
    _entries: dict[str, RegisteredAgent] = field(default_factory=dict)
    _order: list[str] = field(default_factory=list)

    def register(self, spec: AgentSpec, implementation: Any = None) -> None:
        self._entries[spec.agent_key] = RegisteredAgent(spec=spec, implementation=implementation)
        if spec.agent_key not in self._order:
            self._order.append(spec.agent_key)

    def get_spec(self, agent_key: str) -> AgentSpec:
        return self._entries[agent_key].spec

    def get_agent(self, agent_key: str) -> Any:
        return self._entries[agent_key].implementation

    def set_agent(self, agent_key: str, implementation: Any) -> None:
        self._entries[agent_key].implementation = implementation

    def specs(self) -> list[AgentSpec]:
        return [self._entries[agent_key].spec for agent_key in self._order]


def build_default_agent_registry() -> AgentRegistry:
    registry = AgentRegistry()
    registry.register(
        AgentSpec(
            agent_key="orchestrator",
            agent_name="Orchestrator Agent",
            description="Controls routing and decides whether the run should stop or continue.",
            default_directives=(
                "Purpose: route the workflow to the next most relevant agent and minimize unnecessary work.\n"
                "Required behavior: prefer the smallest valid backtracking step, send concrete actionable feedback, and stop when quality is sufficient or control limits are exhausted.\n"
                "Forbidden behavior: do not restart the full pipeline when a narrower backtracking route is available; do not send vague feedback.\n"
                "Quality bar: every routing decision must name the reason, the target agent, and the exact issue that triggered the handoff."
            ),
            default_provider_strategy="Ollama local",
            default_model_family="Qwen 3 32B",
            default_timeout_seconds=60,
            stage_key="orchestrator",
            stage_index=0,
        ),
    )
    registry.register(
        AgentSpec(
            agent_key="requirements_analyst",
            agent_name="Requirements Analyst Agent",
            description="Extracts structured requirements, priorities, assumptions, and acceptance criteria.",
            default_directives=(
                "Purpose: extract only what the requirement text supports and make uncertainty explicit.\n"
                "Required output: stable requirement IDs, normalized requirement text, priority, explicit acceptance criteria, assumptions, and open clarification points when needed.\n"
                "Forbidden behavior: do not invent missing business rules or silently resolve ambiguity.\n"
                "Quality bar: requirements must be testable, traceable, and clearly separated from assumptions."
            ),
            default_provider_strategy="Ollama local",
            default_model_family="Qwen 3 32B",
            default_timeout_seconds=120,
            stage_key="requirements",
            stage_index=1,
        ),
        implementation=RequirementsAnalystAgent(),
    )
    registry.register(
        AgentSpec(
            agent_key="test_design",
            agent_name="Test Design Agent",
            description="Turns requirements into test cases with type, steps, expected results, and oracle.",
            default_directives=(
                "Purpose: create concrete, reviewable test cases rather than placeholders.\n"
                "Required output: preconditions, concrete test data, executable steps, observable expected results, explicit oracle logic, and traceability to requirement IDs.\n"
                "Forbidden behavior: do not use vague steps such as 'execute the primary flow' or generic expected results without observable outcomes.\n"
                "Quality bar: every test case must be specific enough to run and judge as pass or fail."
            ),
            default_provider_strategy="Ollama local",
            default_model_family="Qwen 3 32B",
            default_timeout_seconds=90,
            stage_key="design",
            stage_index=2,
        ),
        implementation=TestDesignAgent(),
    )
    registry.register(
        AgentSpec(
            agent_key="review",
            agent_name="Review Agent",
            description="Evaluates coverage, unresolved assumptions, and the strength of each planned test case.",
            default_directives=(
                "Purpose: challenge weak test design and decide whether the current result is good enough.\n"
                "Required checks: traceability, oracle strength, negative coverage, edge cases, unresolved assumptions, and placeholder language.\n"
                "Forbidden behavior: do not approve generic or weakly testable cases just because coverage looks complete.\n"
                "Quality bar: explain exactly why quality passes or fails, identify the weakest test cases first, and send targeted feedback to the most relevant upstream agent."
            ),
            default_provider_strategy="Ollama local",
            default_model_family="DeepSeek R1",
            default_timeout_seconds=60,
            stage_key="review",
            stage_index=3,
        ),
        implementation=ReviewAgent(),
    )
    return registry
