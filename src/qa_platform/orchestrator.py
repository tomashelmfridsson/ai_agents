from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict

from .agents import (
    RequirementsAnalystAgent,
    ReviewAgent,
    TestDesignAgent,
)
from .models import AgentRuntimeConfig, PipelineResult, RunControlConfig, StageTrace


@dataclass
class OrchestratorAgent:
    requirements_analyst: RequirementsAnalystAgent = field(default_factory=RequirementsAnalystAgent)
    test_designer: TestDesignAgent = field(default_factory=TestDesignAgent)
    reviewer: ReviewAgent = field(default_factory=ReviewAgent)
    max_iterations: int = 2

    def process(
        self,
        title: str,
        requirements_text: str,
        agent_configs: list[AgentRuntimeConfig] | None = None,
        run_controls: RunControlConfig | None = None,
    ) -> PipelineResult:
        requirements = []
        designs = []
        review = None
        stage_traces = []
        runtime_configs = agent_configs or []
        control_config = run_controls or RunControlConfig(
            max_rounds=self.max_iterations,
            max_feedback_messages=0,
            max_feedback_per_agent_pair=0,
        )
        pair_feedback_counts: dict[tuple[str, str], int] = defaultdict(int)
        total_feedback_messages = 0
        route_round = 1
        requirements_feedback: list[str] = []
        design_feedback: list[str] = []
        current_stage = "requirements"

        while True:
            if current_stage == "requirements":
                requirements = self.requirements_analyst.analyze(requirements_text, requirements_feedback)
                stage_traces.append(
                    self._build_requirements_trace(route_round, requirements_text, requirements)
                )
                requirements_feedback = []
                current_stage = "design"
                continue

            if current_stage == "design":
                designs = self.test_designer.design(requirements, design_feedback)
                stage_traces.append(self._build_design_trace(route_round, requirements, designs))
                design_feedback = []
                design_backtrack_feedback = self._build_design_backtrack_feedback(requirements)
                if (
                    design_backtrack_feedback
                    and route_round < control_config.max_rounds
                    and self._can_send_feedback(
                    from_agent="Test Design Agent",
                    to_agent="Requirements Analyst",
                    message_count=1,
                    run_controls=control_config,
                    total_feedback_messages=total_feedback_messages,
                    pair_feedback_counts=pair_feedback_counts,
                    )
                ):
                    total_feedback_messages += 1
                    pair_feedback_counts[("Test Design Agent", "Requirements Analyst")] += 1
                    stage_traces.append(
                        self._build_targeted_orchestrator_trace(
                            route_round=route_round,
                            from_agent="Test Design Agent",
                            to_agent="Requirements Analyst",
                            feedback_messages=design_backtrack_feedback,
                            run_controls=control_config,
                            total_feedback_messages=total_feedback_messages,
                        )
                    )
                    requirements_feedback = design_backtrack_feedback
                    route_round += 1
                    current_stage = "requirements"
                    continue
                current_stage = "review"
                continue

            review = self.reviewer.review(requirements, designs)
            stage_traces.append(
                self._build_review_trace(route_round, requirements, designs, review)
            )
            if review.approved:
                stage_traces.append(
                    self._build_stop_orchestrator_trace(
                        route_round=route_round,
                        review=review,
                        run_controls=control_config,
                        total_feedback_messages=total_feedback_messages,
                        stop_reason="Stop pipeline because the review approved the result.",
                    )
                )
                break

            backtrack_route = self._select_review_backtrack_route(requirements, review)
            if (
                backtrack_route
                and route_round < control_config.max_rounds
                and self._can_send_feedback(
                from_agent=backtrack_route["from_agent"],
                to_agent=backtrack_route["to_agent"],
                message_count=1,
                run_controls=control_config,
                total_feedback_messages=total_feedback_messages,
                pair_feedback_counts=pair_feedback_counts,
                )
            ):
                total_feedback_messages += 1
                pair_feedback_counts[(backtrack_route["from_agent"], backtrack_route["to_agent"])] += 1
                stage_traces.append(
                    self._build_targeted_orchestrator_trace(
                        route_round=route_round,
                        from_agent=backtrack_route["from_agent"],
                        to_agent=backtrack_route["to_agent"],
                        feedback_messages=backtrack_route["feedback_messages"],
                        run_controls=control_config,
                        total_feedback_messages=total_feedback_messages,
                    )
                )
                if backtrack_route["to_agent"] == "Requirements Analyst":
                    requirements_feedback = backtrack_route["feedback_messages"]
                    current_stage = "requirements"
                else:
                    design_feedback = backtrack_route["feedback_messages"]
                    current_stage = "design"
                route_round += 1
                continue

            stage_traces.append(
                self._build_stop_orchestrator_trace(
                    route_round=route_round,
                    review=review,
                    run_controls=control_config,
                    total_feedback_messages=total_feedback_messages,
                    stop_reason=(
                        "Stop pipeline because no more targeted feedback is allowed or no valid backtracking route was available."
                    ),
                )
            )
            break

        return PipelineResult(
            title=title,
            source_requirements=requirements_text,
            requirements=requirements,
            test_designs=designs,
            generated_artifacts=[],
            review=review,
            iterations=route_round,
            run_controls=control_config,
            agent_configs=runtime_configs,
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

    def _can_send_feedback(
        self,
        from_agent: str,
        to_agent: str,
        message_count: int,
        run_controls: RunControlConfig,
        total_feedback_messages: int,
        pair_feedback_counts: dict[tuple[str, str], int],
    ) -> bool:
        if run_controls.max_feedback_messages and (
            total_feedback_messages + message_count > run_controls.max_feedback_messages
        ):
            return False
        pair_limit = run_controls.max_feedback_per_agent_pair
        if pair_limit and pair_feedback_counts[(from_agent, to_agent)] + message_count > pair_limit:
            return False
        return True

    def _build_design_backtrack_feedback(self, requirements: list) -> list[str]:
        feedback = []
        for requirement in requirements:
            if requirement.assumptions:
                feedback.append(
                    f"{requirement.requirement_id} needs clearer acceptance criteria and explicit error handling before strong test design can continue."
                )
        return feedback[:2]

    def _select_review_backtrack_route(self, requirements: list, review) -> dict | None:
        weak_oracle_findings = [finding for finding in review.findings if "weak oracle definition" in finding]
        assumption_findings = [finding for finding in review.findings if "contains assumptions" in finding]
        missing_design_findings = [finding for finding in review.findings if "missing a designed test case" in finding]

        if weak_oracle_findings or missing_design_findings:
            feedback_messages = []
            if weak_oracle_findings:
                feedback_messages.append(
                    "Strengthen weak oracle definitions by adding more explicit expected results and negative scenarios."
                )
            if missing_design_findings:
                feedback_messages.append(
                    "Design missing test coverage for every uncovered requirement."
                )
            return {
                "from_agent": "Review Agent",
                "to_agent": "Test Design Agent",
                "feedback_messages": feedback_messages,
            }

        if assumption_findings:
            targeted_requirements = [item.requirement_id for item in requirements if item.assumptions]
            feedback_messages = [
                f"{requirement_id} must reduce assumptions by clarifying acceptance criteria and negative or error behavior."
                for requirement_id in targeted_requirements[:2]
            ]
            return {
                "from_agent": "Review Agent",
                "to_agent": "Requirements Analyst",
                "feedback_messages": feedback_messages,
            }

        return None

    def _build_targeted_orchestrator_trace(
        self,
        route_round: int,
        from_agent: str,
        to_agent: str,
        feedback_messages: list[str],
        run_controls: RunControlConfig,
        total_feedback_messages: int,
    ) -> StageTrace:
        return StageTrace(
            iteration=route_round,
            stage_index=4,
            agent_name="Orchestrator Agent",
            input_summary=[
                f"Backtracking request from: {from_agent}",
                f"Backtracking target: {to_agent}",
                f"Maximum rounds: {run_controls.max_rounds}",
                f"Maximum feedback messages: {run_controls.max_feedback_messages}",
                f"Maximum feedback per agent pair: {run_controls.max_feedback_per_agent_pair}",
                f"Feedback messages already used: {total_feedback_messages}",
            ],
            output_summary=[
                f"Send targeted feedback from {from_agent} to {to_agent}.",
                *feedback_messages,
            ],
            status=f"backtrack to {to_agent.lower()}",
            reasoning_trace=[
                "Read the feedback request and evaluate whether the configured feedback budgets still allow another targeted handoff.",
                "Choose the smallest possible backtracking step instead of restarting the whole pipeline.",
                f"Route the workflow directly from {from_agent} back to {to_agent} so downstream stages can be regenerated from the repaired state.",
            ],
            agent_explanation=(
                "The orchestrator now works as a routing controller. Instead of forcing a full rerun, "
                "it can send a targeted repair request back to the most relevant upstream agent."
            ),
            decision_explanation=(
                "This is selective backtracking. The orchestrator does not start over from scratch here. "
                "It routes the repair message to the exact agent that should respond next, then resumes the "
                "pipeline from that point."
            ),
        )

    def _build_stop_orchestrator_trace(
        self,
        route_round: int,
        review,
        run_controls: RunControlConfig,
        total_feedback_messages: int,
        stop_reason: str,
    ) -> StageTrace:
        return StageTrace(
            iteration=route_round,
            stage_index=4,
            agent_name="Orchestrator Agent",
            input_summary=[
                f"Review approval signal: {review.approved}",
                f"Improvement actions: {len(review.improvement_actions)}",
                f"Maximum rounds: {run_controls.max_rounds}",
                f"Maximum feedback messages: {run_controls.max_feedback_messages}",
                f"Maximum feedback per agent pair: {run_controls.max_feedback_per_agent_pair}",
                f"Feedback messages already used: {total_feedback_messages}",
            ],
            output_summary=[
                stop_reason,
                (
                    f"Primary reason: {review.findings[0]}"
                    if review.findings
                    else "Primary reason: no explicit finding was recorded."
                ),
                *review.improvement_actions[:3],
            ],
            status="stop",
            reasoning_trace=[
                "Read the current review status together with the remaining feedback budget.",
                "Stop when the result is approved, or when no further targeted backtracking route is allowed or available.",
                "Do not restart the whole pipeline here because this orchestrator now prefers selective routing.",
            ],
            agent_explanation=(
                "The orchestrator is the routing controller for the workflow. It either stops the run or sends targeted repair requests to earlier agents."
            ),
            decision_explanation=(
                "The run stops when approval is reached or when no more valid agent-to-agent backtracking step can be taken under the configured limits."
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
