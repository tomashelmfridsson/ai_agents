from __future__ import annotations

from dataclasses import dataclass, field

from .agents import (
    RequirementsAnalystAgent,
    ReviewAgent,
    TestDesignAgent,
)
from .models import PipelineResult, StageTrace


@dataclass
class OrchestratorAgent:
    requirements_analyst: RequirementsAnalystAgent = field(default_factory=RequirementsAnalystAgent)
    test_designer: TestDesignAgent = field(default_factory=TestDesignAgent)
    reviewer: ReviewAgent = field(default_factory=ReviewAgent)
    max_iterations: int = 2

    def process(self, title: str, requirements_text: str) -> PipelineResult:
        requirements = []
        designs = []
        review = None
        stage_traces = []

        for iteration in range(1, self.max_iterations + 1):
            requirements = self.requirements_analyst.analyze(requirements_text)
            stage_traces.append(
                self._build_requirements_trace(iteration, requirements_text, requirements)
            )
            designs = self.test_designer.design(requirements)
            stage_traces.append(self._build_design_trace(iteration, requirements, designs))
            review = self.reviewer.review(requirements, designs)
            stage_traces.append(
                self._build_review_trace(iteration, requirements, designs, review)
            )
            stage_traces.append(self._build_orchestrator_trace(iteration, review))
            if review.approved:
                return PipelineResult(
                    title=title,
                    source_requirements=requirements_text,
                    requirements=requirements,
                    test_designs=designs,
                    generated_artifacts=[],
                    review=review,
                    iterations=iteration,
                    stage_traces=stage_traces,
                )

        return PipelineResult(
            title=title,
            source_requirements=requirements_text,
            requirements=requirements,
            test_designs=designs,
            generated_artifacts=[],
            review=review,
            iterations=self.max_iterations,
            stage_traces=stage_traces,
        )

    def _build_requirements_trace(self, iteration: int, requirements_text: str, requirements: list) -> StageTrace:
        detailed_reasoning = []
        for item in requirements[:4]:
            detailed_reasoning.extend(self._explain_requirement_derivation(item))

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
            reasoning_trace=[
                "Split the incoming requirement text into separate candidate requirement statements.",
                "Normalize each statement, assign deterministic IDs in sequence, and preserve the original wording.",
                "Classify priority from keyword matches such as 'must', 'måste', or 'should'.",
                "Expand each requirement with heuristic acceptance criteria and note missing or implicit error handling as assumptions.",
                *detailed_reasoning,
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
            reasoning_trace=[
                "Read each structured requirement together with its acceptance criteria and assumptions.",
                "Choose a test type from deterministic keyword routing such as gui/e2e, api/integration, unit, or scenario.",
                "Build a test-case shell with fixed preconditions, reusable steps, expected results, and a generic oracle.",
                "Carry forward requirement assumptions as design risks so later review can challenge weak testability.",
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

    def _build_review_trace(
        self, iteration: int, requirements: list, designs: list, review
    ) -> StageTrace:
        review_reasoning = self._build_review_reasoning(requirements, designs, review)
        return StageTrace(
            iteration=iteration,
            stage_index=3,
            agent_name="Review Agent",
            input_summary=[
                f"Requirements inspected: {len(requirements)}",
                f"Designed test cases inspected: {len(designs)}",
                *[
                    (
                        f"{item.requirement_id}: covered by designed test case {item.test_case_id} | "
                        f"title={item.title}"
                    )
                    for item in designs[:4]
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
            reasoning_trace=[
                "Compute requirement coverage by checking whether each requirement ID appears in at least one designed test case.",
                "Flag designs with too few expected results because weak oracles reduce confidence in the generated tests.",
                "Flag requirements that still contain assumptions because automation would otherwise encode guesses.",
                "Approve only when full coverage is reached and the number of findings stays below the hard-coded threshold.",
                *review_reasoning,
            ],
            agent_explanation=(
                "This review stage is a deterministic rule check, not an autonomous evaluator. It "
                "computes requirement coverage from designed test cases, flags test cases with too few "
                "expected results, and flags requirements that still contain assumptions."
            ),
            decision_explanation=(
                "Approval becomes true only when every requirement has at least one designed test case "
                "and the total number of findings stays at or below the hard-coded threshold. In this "
                "implementation, findings mainly come from three sources: missing designed coverage, weak "
                "oracle definitions, and unresolved assumptions."
            ),
        )

    def _build_orchestrator_trace(self, iteration: int, review) -> StageTrace:
        should_rerun = (not review.approved) and iteration < self.max_iterations
        stopped_by_limit = (not review.approved) and iteration >= self.max_iterations
        return StageTrace(
            iteration=iteration,
            stage_index=4,
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
                (
                    f"Primary reason: {review.findings[0]}"
                    if review.findings
                    else "Primary reason: no explicit finding was recorded."
                ),
                *review.improvement_actions[:3],
            ],
            status="rerun" if should_rerun else "stop",
            reasoning_trace=[
                "Read the review approval signal, current findings, and remaining iteration budget.",
                "Choose between full rerun and stop because this baseline orchestrator has no selective repair path.",
                (
                    "Route the workflow back to stage 1 for another full pass."
                    if should_rerun
                    else "Terminate the workflow because approval was reached or retry budget was exhausted."
                ),
            ],
            agent_explanation=(
                "The orchestrator is the central control component in this baseline. It is not acting "
                "like an autonomous specialist agent. It evaluates the review result and then decides "
                "whether to stop or rerun the whole pipeline."
            ),
            decision_explanation=(
                "A rerun happens when review.approved is false and the maximum iteration limit has not "
                "yet been reached. The whole pipeline is rerun because this baseline has no selective "
                "repair mechanism, no per-stage checkpoint resume, and no routing logic that can restart "
                "from only the failing stage. In other words, the orchestrator can only repeat the full "
                "sequence, not continue from the point where quality became insufficient."
                if should_rerun
                else (
                    "The pipeline stops because review.approved is true."
                    if review.approved
                    else "The pipeline stops even though findings remain, because the maximum iteration limit was reached and this baseline has no more retry budget."
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
        if "missing a designed test case" in finding:
            return (
                f"{finding} This means the requirement currently has no designed test candidate."
            )
        return finding

    def _explain_requirement_derivation(self, item) -> list[str]:
        lowered = item.normalized_text.lower()
        priority_signal = (
            "keyword match on 'must/måste/critical/viktig'"
            if item.priority == "high"
            else (
                "keyword match on 'should/bör/nice'"
                if item.priority == "medium"
                else "no priority keyword matched, so the fallback priority is 'normal'"
            )
        )

        acceptance_rules = [
            "base rule: every requirement gets a generic acceptance criterion that repeats the requirement intent"
        ]
        if any(keyword in lowered for keyword in ("login", "logga in", "autentis", "sign in")):
            acceptance_rules.append(
                "authentication rule triggered by 'login/logga in/autentis/sign in', so authentication success and invalid-credential error criteria were added"
            )
        if any(keyword in lowered for keyword in ("visa", "display", "list", "översikt", "dashboard")):
            acceptance_rules.append(
                "presentation rule triggered by 'display/list/översikt/dashboard', so a visibility and non-empty-state criterion was added"
            )
        if any(keyword in lowered for keyword in ("skapa", "save", "spara", "registrera", "submit")):
            acceptance_rules.append(
                "submission rule triggered by 'save/spara/registrera/submit', so validation and success-confirmation criteria were added"
            )
        if any(keyword in lowered for keyword in ("admin", "behörighet", "access", "roll")):
            acceptance_rules.append(
                "authorization rule triggered by 'admin/behörighet/access/roll', so unauthorized-access protection was added"
            )

        assumption_rules = []
        if "The requirement likely needs more explicit acceptance criteria." in item.assumptions:
            assumption_rules.append(
                "only one acceptance criterion was produced at first, so the requirement was marked as underspecified"
            )
        if "Error handling is not explicit and should be reviewed." in item.assumptions:
            assumption_rules.append(
                "the raw requirement text does not explicitly mention error handling keywords such as 'error', 'invalid', 'fel', or 'ogiltig', so an error-handling assumption was added"
            )
        if not assumption_rules:
            assumption_rules.append("no extra assumption rule was triggered for this requirement")

        return [
            f"{item.requirement_id}: raw text -> \"{item.original_text}\"",
            f"{item.requirement_id}: normalized text -> \"{item.normalized_text}\" after trimming whitespace and trailing punctuation.",
            f"{item.requirement_id}: priority -> {item.priority} because of {priority_signal}.",
            f"{item.requirement_id}: acceptance-criteria derivation -> {'; '.join(acceptance_rules)}.",
            f"{item.requirement_id}: assumptions derivation -> {'; '.join(assumption_rules)}.",
        ]

    def _build_review_reasoning(self, requirements: list, designs: list, review) -> list[str]:
        covered_requirements = {design.requirement_id for design in designs}
        coverage_target = len(requirements)
        coverage_hits = len(covered_requirements)
        threshold = max(1, len(requirements) // 2)
        reasoning = [
            (
                f"Coverage check: {coverage_hits}/{coverage_target} requirements have at least one designed test case, "
                f"so coverage_ratio={review.coverage_ratio}."
            ),
            (
                "Covered requirement IDs: "
                + (", ".join(sorted(covered_requirements)) if covered_requirements else "none")
                + "."
            ),
        ]

        missing_requirements = [
            requirement.requirement_id
            for requirement in requirements
            if requirement.requirement_id not in covered_requirements
        ]
        reasoning.append(
            "Missing designed test coverage: "
            + (", ".join(missing_requirements) if missing_requirements else "none")
            + "."
        )

        weak_oracle_designs = [
            f"{design.test_case_id} ({len(design.expected_results)} expected result(s))"
            for design in designs
            if len(design.expected_results) < 2
        ]
        reasoning.append(
            "Weak-oracle checks triggered for: "
            + (", ".join(weak_oracle_designs) if weak_oracle_designs else "none")
            + "."
        )

        assumption_requirements = [
            f"{requirement.requirement_id} ({len(requirement.assumptions)} assumption(s))"
            for requirement in requirements
            if requirement.assumptions
        ]
        reasoning.append(
            "Assumption checks triggered for: "
            + (", ".join(assumption_requirements) if assumption_requirements else "none")
            + "."
        )

        reasoning.append(
            f"Approval threshold: findings must be <= {threshold} when coverage_ratio is 1.0."
        )
        reasoning.append(
            f"Observed findings: {len(review.findings)}. Coverage OK: {review.coverage_ratio == 1.0}. "
            f"Findings threshold OK: {len(review.findings) <= threshold}."
        )
        reasoning.append(
                "Final decision: Approved=False because coverage passed but the findings count exceeded the threshold."
                if not review.approved and review.coverage_ratio == 1.0 and len(review.findings) > threshold
                else (
                "Final decision: Approved=False because designed test coverage was incomplete."
                if not review.approved and review.coverage_ratio < 1.0
                else "Final decision: Approved=True because coverage passed and findings stayed within threshold."
            )
        )
        return reasoning
