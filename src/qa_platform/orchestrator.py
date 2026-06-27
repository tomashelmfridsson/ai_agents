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
                "Raw requirement text:",
                requirements_text,
            ],
            output_summary=[
                f"Extracted {len(requirements)} requirement item(s).",
                *[
                    (
                        f"{item.requirement_id}: \"{item.normalized_text}\" | "
                        f"priority={item.priority} | "
                        f"acceptance criteria={'; '.join(item.acceptance_criteria)} | "
                        f"assumptions={'; '.join(item.assumptions) if item.assumptions else 'none'}"
                    )
                    for item in requirements[:4]
                ],
            ],
            status="completed",
            agent_explanation=(
                "This agent is deterministic. It splits the requirement text by line or sentence, "
                "assigns IDs in order, classifies priority from simple keywords, and enriches each "
                "requirement with heuristic acceptance criteria and assumptions."
            ),
            decision_explanation=(
                "No model judgment is used here. The output depends only on the input text and the "
                "hard-coded keyword rules."
            ),
        )

    def _build_design_trace(self, iteration: int, requirements: list, designs: list) -> StageTrace:
        return StageTrace(
            iteration=iteration,
            stage_index=2,
            agent_name="Test Design Agent",
            input_summary=[
                f"Requirements received: {len(requirements)}",
                f"Acceptance criteria seen: {sum(len(item.acceptance_criteria) for item in requirements)}",
                *[
                    (
                        f"{item.requirement_id}: \"{item.normalized_text}\" | "
                        f"priority={item.priority} | "
                        f"acceptance criteria={'; '.join(item.acceptance_criteria)} | "
                        f"assumptions={'; '.join(item.assumptions) if item.assumptions else 'none'}"
                    )
                    for item in requirements[:4]
                ],
            ],
            output_summary=[
                f"Created {len(designs)} test case design(s).",
                *[
                    (
                        f"{item.test_case_id} for {item.requirement_id}: "
                        f"title=\"{item.title}\" | type={item.test_type} | "
                        f"steps={' | '.join(item.steps)} | "
                        f"expected results={' | '.join(item.expected_results)} | "
                        f"oracle={item.oracle}"
                    )
                    for item in designs[:4]
                ],
            ],
            status="completed",
            agent_explanation=(
                "This agent converts each structured requirement into a test case design. The test "
                "type is selected from keywords, and the rest of the design is filled from fixed templates."
            ),
            decision_explanation=(
                "The label 'designs' means draft test cases before code generation. In this app they "
                "are the planned test cases, each tied to a requirement ID."
            ),
        )

    def _build_generation_trace(self, iteration: int, designs: list, artifacts: list) -> StageTrace:
        return StageTrace(
            iteration=iteration,
            stage_index=3,
            agent_name="Test Generation Agent",
            input_summary=[
                f"Test case designs received: {len(designs)}",
                f"Distinct test types: {len({item.test_type for item in designs})}",
                *[
                    (
                        f"{item.test_case_id} for {item.requirement_id}: "
                        f"title=\"{item.title}\" | type={item.test_type} | "
                        f"steps={' | '.join(item.steps)} | "
                        f"expected results={' | '.join(item.expected_results)} | "
                        f"oracle={item.oracle}"
                    )
                    for item in designs[:4]
                ],
            ],
            output_summary=[
                f"Generated {len(artifacts)} artifact(s).",
                *[
                    (
                        f"{item.artifact_id} for {item.requirement_id}/{item.design_id}: "
                        f"test_name={item.test_name} | target={item.target} | "
                        f"selectors={' | '.join(item.selectors)} | "
                        f"test_data={item.test_data} | "
                        f"pseudocode={' | '.join(item.pseudocode)}"
                    )
                    for item in artifacts[:4]
                ],
            ],
            status="completed",
            agent_explanation=(
                "This agent generates concrete draft artifacts from the test case designs: names, "
                "test data placeholders, selectors, and pseudocode. It still uses deterministic templates."
            ),
            decision_explanation=(
                "This stage does not execute tests. It only creates candidate test artifacts that a "
                "later LLM-based or execution-based pipeline could refine and run."
            ),
        )

    def _build_review_trace(self, iteration: int, requirements: list, artifacts: list, review) -> StageTrace:
        return StageTrace(
            iteration=iteration,
            stage_index=4,
            agent_name="Review Agent",
            input_summary=[
                f"Requirements inspected: {len(requirements)}",
                f"Artifacts inspected: {len(artifacts)}",
                *[
                    (
                        f"{item.requirement_id}: artifact coverage present via {item.design_id} / {item.artifact_id} | "
                        f"test_name={item.test_name}"
                    )
                    for item in artifacts[:4]
                ],
            ],
            output_summary=[
                f"Approved={review.approved}",
                f"Coverage ratio={review.coverage_ratio}",
                f"Findings={len(review.findings)}",
                *[
                    self._explain_review_finding(finding)
                    for finding in review.findings[:4]
                ],
            ],
            status="approved" if review.approved else "changes requested",
            agent_explanation=(
                "This review stage acts as a hard quality gate. It checks coverage, the strength of "
                "expected results, and whether assumptions remain unresolved."
            ),
            decision_explanation=(
                "Approval becomes true only when coverage is complete and the number of findings is "
                "below the hard-coded threshold."
            ),
        )

    def _build_orchestrator_trace(self, iteration: int, review) -> StageTrace:
        should_rerun = (not review.approved) and iteration < self.max_iterations
        stopped_by_limit = (not review.approved) and iteration >= self.max_iterations
        return StageTrace(
            iteration=iteration,
            stage_index=5,
            agent_name="Orchestrator Agent",
            input_summary=[
                f"Review approval signal: {review.approved}",
                f"Improvement actions: {len(review.improvement_actions)}",
                f"Maximum iterations: {self.max_iterations}",
            ],
            output_summary=[
                "Stop pipeline because the review approved the result."
                if review.approved
                else (
                    "Start another full iteration because the review did not approve the result "
                    "and another pass is still allowed."
                    if should_rerun
                    else "Stop pipeline because the maximum number of iterations has been reached."
                ),
                *review.improvement_actions[:3],
            ],
            status="rerun" if should_rerun else "stop",
            agent_explanation=(
                "The orchestrator does not change prompts, data, or routing. It only decides whether "
                "to stop or rerun the same sequence based on the review result and the iteration cap."
            ),
            decision_explanation=(
                "A rerun happens when review.approved is false and the maximum iteration limit has not "
                "yet been reached. Otherwise the pipeline stops."
                if should_rerun
                else (
                    "The pipeline stops because review.approved is true."
                    if review.approved
                    else "The pipeline stops even though findings remain, because the maximum iteration limit was reached."
                )
            ),
        )

    def _explain_review_finding(self, finding: str) -> str:
        if "weak oracle definition" in finding:
            return (
                f"{finding} This means the test case does not describe enough expected results to "
                "judge clearly whether the behavior is correct or incorrect."
            )
        if "contains assumptions" in finding:
            return (
                f"{finding} This means the requirement text leaves something implicit, so an automated "
                "test may reflect a guess rather than a confirmed business rule."
            )
        if "missing a generated test artifact" in finding:
            return (
                f"{finding} This means the requirement currently has no generated candidate test output."
            )
        return finding
