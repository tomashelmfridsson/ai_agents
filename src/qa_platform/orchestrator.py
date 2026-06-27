from __future__ import annotations

from dataclasses import dataclass, field

from .agents import (
    RequirementsAnalystAgent,
    ReviewAgent,
    TestDesignAgent,
    TestGenerationAgent,
)
from .models import PipelineResult, StageTrace


@dataclass
class OrchestratorAgent:
    requirements_analyst: RequirementsAnalystAgent = field(default_factory=RequirementsAnalystAgent)
    test_designer: TestDesignAgent = field(default_factory=TestDesignAgent)
    test_generator: TestGenerationAgent = field(default_factory=TestGenerationAgent)
    reviewer: ReviewAgent = field(default_factory=ReviewAgent)
    max_iterations: int = 2

    def process(self, title: str, requirements_text: str) -> PipelineResult:
        requirements = []
        designs = []
        artifacts = []
        review = None
        stage_traces = []

        for iteration in range(1, self.max_iterations + 1):
            requirements = self.requirements_analyst.analyze(requirements_text)
            stage_traces.append(
                self._build_requirements_trace(iteration, requirements_text, requirements)
            )
            designs = self.test_designer.design(requirements)
            stage_traces.append(self._build_design_trace(iteration, requirements, designs))
            artifacts = self.test_generator.generate(requirements, designs)
            stage_traces.append(self._build_generation_trace(iteration, designs, artifacts))
            review = self.reviewer.review(requirements, designs, artifacts)
            stage_traces.append(self._build_review_trace(iteration, requirements, artifacts, review))
            stage_traces.append(self._build_orchestrator_trace(iteration, review))
            if review.approved:
                return PipelineResult(
                    title=title,
                    source_requirements=requirements_text,
                    requirements=requirements,
                    test_designs=designs,
                    generated_artifacts=artifacts,
                    review=review,
                    iterations=iteration,
                    stage_traces=stage_traces,
                )

        return PipelineResult(
            title=title,
            source_requirements=requirements_text,
            requirements=requirements,
            test_designs=designs,
            generated_artifacts=artifacts,
            review=review,
            iterations=self.max_iterations,
            stage_traces=stage_traces,
        )

    def _build_requirements_trace(self, iteration: int, requirements_text: str, requirements: list) -> StageTrace:
        return StageTrace(
            iteration=iteration,
            stage_index=1,
            agent_name="Requirements Analyst",
            input_summary=[
                f"Raw requirement lines: {len([line for line in requirements_text.splitlines() if line.strip()])}",
                f"Input characters: {len(requirements_text)}",
            ],
            output_summary=[
                f"Extracted {len(requirements)} requirement item(s).",
                *[
                    f"{item.requirement_id}: priority={item.priority}, criteria={len(item.acceptance_criteria)}, assumptions={len(item.assumptions)}"
                    for item in requirements[:4]
                ],
            ],
            status="completed",
        )

    def _build_design_trace(self, iteration: int, requirements: list, designs: list) -> StageTrace:
        return StageTrace(
            iteration=iteration,
            stage_index=2,
            agent_name="Test Design Agent",
            input_summary=[
                f"Requirements received: {len(requirements)}",
                f"Acceptance criteria seen: {sum(len(item.acceptance_criteria) for item in requirements)}",
            ],
            output_summary=[
                f"Created {len(designs)} design(s).",
                *[
                    f"{item.test_case_id}: type={item.test_type}, steps={len(item.steps)}, expected_results={len(item.expected_results)}"
                    for item in designs[:4]
                ],
            ],
            status="completed",
        )

    def _build_generation_trace(self, iteration: int, designs: list, artifacts: list) -> StageTrace:
        return StageTrace(
            iteration=iteration,
            stage_index=3,
            agent_name="Test Generation Agent",
            input_summary=[
                f"Designs received: {len(designs)}",
                f"Distinct test types: {len({item.test_type for item in designs})}",
            ],
            output_summary=[
                f"Generated {len(artifacts)} artifact(s).",
                *[
                    f"{item.artifact_id}: {item.test_name}, selectors={len(item.selectors)}, pseudocode_steps={len(item.pseudocode)}"
                    for item in artifacts[:4]
                ],
            ],
            status="completed",
        )

    def _build_review_trace(self, iteration: int, requirements: list, artifacts: list, review) -> StageTrace:
        return StageTrace(
            iteration=iteration,
            stage_index=4,
            agent_name="Review Agent",
            input_summary=[
                f"Requirements inspected: {len(requirements)}",
                f"Artifacts inspected: {len(artifacts)}",
            ],
            output_summary=[
                f"Approved={review.approved}",
                f"Coverage ratio={review.coverage_ratio}",
                f"Findings={len(review.findings)}",
                *review.findings[:3],
            ],
            status="approved" if review.approved else "changes requested",
        )

    def _build_orchestrator_trace(self, iteration: int, review) -> StageTrace:
        return StageTrace(
            iteration=iteration,
            stage_index=5,
            agent_name="Orchestrator Agent",
            input_summary=[
                f"Review approval signal: {review.approved}",
                f"Improvement actions: {len(review.improvement_actions)}",
            ],
            output_summary=[
                "Stop pipeline." if review.approved else "Start another full iteration.",
                *review.improvement_actions[:3],
            ],
            status="stop" if review.approved else "rerun",
        )
