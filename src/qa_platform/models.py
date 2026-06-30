from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class AgentRuntimeConfig:
    agent_key: str
    agent_name: str
    execution_mode: str
    timeout_seconds: int = 60
    provider_strategy: str = ""
    model_family: str = ""
    model_override: str = ""
    model_id: str = ""
    directives: str = ""


@dataclass
class RunControlConfig:
    max_rounds: int
    max_feedback_messages: int
    max_feedback_per_agent_pair: int


@dataclass
class WorkingMemory:
    shared: dict[str, Any] = field(default_factory=dict)
    agent_private: dict[str, dict[str, Any]] = field(default_factory=dict)
    timeline: list[str] = field(default_factory=list)

    def read_shared(self, key: str, default: Any = None) -> Any:
        return self.shared.get(key, default)

    def write_shared(self, key: str, value: Any, *, author: str | None = None) -> None:
        self.shared[key] = value
        if author:
            self.timeline.append(f"{author} wrote shared memory key '{key}'.")

    def read_agent(self, agent_key: str, key: str, default: Any = None) -> Any:
        return self.agent_private.get(agent_key, {}).get(key, default)

    def write_agent(self, agent_key: str, key: str, value: Any) -> None:
        self.agent_private.setdefault(agent_key, {})[key] = value
        self.timeline.append(f"{agent_key} updated private memory key '{key}'.")

    def add_note(self, note: str) -> None:
        if note.strip():
            self.timeline.append(note.strip())


@dataclass
class RunSession:
    title: str
    source_requirements: str
    working_memory: WorkingMemory = field(default_factory=WorkingMemory)


@dataclass
class RequirementItem:
    requirement_id: str
    original_text: str
    normalized_text: str
    priority: str
    acceptance_criteria: list[str]
    assumptions: list[str] = field(default_factory=list)


@dataclass
class TestCaseDesign:
    test_case_id: str
    requirement_id: str
    title: str
    test_type: str
    preconditions: list[str]
    steps: list[str]
    expected_results: list[str]
    oracle: str
    risks: list[str] = field(default_factory=list)


@dataclass
class GeneratedArtifact:
    artifact_id: str
    requirement_id: str
    design_id: str
    target: str
    test_name: str
    test_data: dict[str, Any]
    selectors: list[str]
    pseudocode: list[str]


@dataclass
class ReviewReport:
    approved: bool
    coverage_ratio: float
    findings: list[str]
    improvement_actions: list[str]


@dataclass
class StageTrace:
    iteration: int
    stage_index: int
    agent_name: str
    input_summary: list[str]
    output_summary: list[str]
    status: str
    reasoning_trace: list[str] = field(default_factory=list)
    reasoning_source: str = "structured_trace"
    agent_explanation: str = ""
    decision_explanation: str = ""
    duration_ms: int = 0


@dataclass
class PipelineResult:
    title: str
    source_requirements: str
    requirements: list[RequirementItem]
    test_designs: list[TestCaseDesign]
    generated_artifacts: list[GeneratedArtifact]
    review: ReviewReport
    iterations: int
    run_controls: RunControlConfig
    agent_configs: list[AgentRuntimeConfig] = field(default_factory=list)
    stage_traces: list[StageTrace] = field(default_factory=list)
    run_session: RunSession | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
