from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class AgentRuntimeConfig:
    agent_key: str
    agent_name: str
    execution_mode: str
    provider_strategy: str = ""
    model_family: str = ""
    model_id: str = ""
    directives: str = ""


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


@dataclass
class PipelineResult:
    title: str
    source_requirements: str
    requirements: list[RequirementItem]
    test_designs: list[TestCaseDesign]
    generated_artifacts: list[GeneratedArtifact]
    review: ReviewReport
    iterations: int
    agent_configs: list[AgentRuntimeConfig] = field(default_factory=list)
    stage_traces: list[StageTrace] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
