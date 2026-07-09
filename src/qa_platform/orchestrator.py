from __future__ import annotations

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field
import copy
from datetime import datetime
import time

from .models import AgentRuntimeConfig, PipelineResult, RunControlConfig, RunSession, StageTrace
from .models import ReviewReport
from .registry import AgentRegistry, build_default_agent_registry
from .workflow import WorkflowGraph, build_default_workflow_graph

AGENT_TIMEOUT_SECONDS = 60


class AgentTimeoutError(RuntimeError):
    def __init__(self, agent_name: str, timeout_seconds: int):
        self.agent_name = agent_name
        self.timeout_seconds = timeout_seconds
        super().__init__(f"{agent_name} exceeded the {timeout_seconds}-second timeout.")


class WorkflowCancelledError(RuntimeError):
    pass


@dataclass
class OrchestrationState:
    route_round: int = 1
    current_stage: str = "orchestrator"
    requirements: list = field(default_factory=list)
    designs: list = field(default_factory=list)
    review: ReviewReport | None = None
    stage_traces: list[StageTrace] = field(default_factory=list)
    requirements_feedback: list[str] = field(default_factory=list)
    design_feedback: list[str] = field(default_factory=list)
    pair_feedback_counts: dict[tuple[str, str], int] = field(default_factory=lambda: defaultdict(int))
    total_feedback_messages: int = 0


@dataclass
class OrchestratorAgent:
    registry: AgentRegistry = field(default_factory=build_default_agent_registry)
    workflow_graph: WorkflowGraph = field(default_factory=build_default_workflow_graph)
    max_iterations: int = 2

    @property
    def requirements_analyst(self):
        return self.registry.get_agent("requirements_analyst")

    @property
    def test_designer(self):
        return self.registry.get_agent("test_design")

    @property
    def reviewer(self):
        return self.registry.get_agent("review")

    def process(
        self,
        title: str,
        requirements_text: str,
        agent_configs: list[AgentRuntimeConfig] | None = None,
        run_controls: RunControlConfig | None = None,
        event_callback=None,
        stop_requested=None,
    ) -> PipelineResult:
        runtime_configs = agent_configs or []
        runtime_lookup = {config.agent_key: config for config in runtime_configs}
        control_config = run_controls or RunControlConfig(
            max_rounds=self.max_iterations,
            max_feedback_messages=0,
            max_feedback_per_agent_pair=0,
        )
        run_session = RunSession(title=title, source_requirements=requirements_text)
        run_session.working_memory.write_shared("source_requirements", requirements_text, author="system")
        run_session.working_memory.add_note("Run session started.")
        state = OrchestrationState(current_stage=self.workflow_graph.start_stage)
        stage_handlers = {
            "orchestrator": self._handle_orchestrator_stage,
            "requirements": self._handle_requirements_stage,
            "design": self._handle_design_stage,
            "review": self._handle_review_stage,
        }

        while state.review is None or state.current_stage != "stop":
            self._raise_if_cancelled(stop_requested)
            handler = stage_handlers[state.current_stage]
            next_stage = handler(
                state=state,
                requirements_text=requirements_text,
                runtime_lookup=runtime_lookup,
                run_controls=control_config,
                run_session=run_session,
                event_callback=event_callback,
            )
            self._raise_if_cancelled(stop_requested)
            if next_stage == "stop":
                state.current_stage = "stop"
                break
            state.current_stage = next_stage

        return PipelineResult(
            title=title,
            source_requirements=requirements_text,
            requirements=state.requirements,
            test_designs=state.designs,
            generated_artifacts=[],
            review=state.review,
            iterations=state.route_round,
            run_controls=control_config,
            total_feedback_messages=state.total_feedback_messages,
            pair_feedback_counts={
                f"{from_agent} -> {to_agent}": count
                for (from_agent, to_agent), count in state.pair_feedback_counts.items()
            },
            agent_configs=runtime_configs,
            stage_traces=state.stage_traces,
            run_session=run_session,
        )

    def _handle_orchestrator_stage(
        self,
        *,
        state: OrchestrationState,
        requirements_text: str,
        runtime_lookup: dict[str, AgentRuntimeConfig],
        run_controls: RunControlConfig,
        run_session: RunSession,
        event_callback,
    ) -> str:
        del requirements_text
        orchestrator_runtime = runtime_lookup.get("orchestrator")
        initial_trace = self._build_initial_orchestrator_trace(
            route_round=state.route_round,
            runtime_config=orchestrator_runtime,
            run_controls=run_controls,
        )
        state.stage_traces.append(initial_trace)
        run_session.working_memory.write_shared("current_stage", "requirements", author="Orchestrator Agent")
        self._emit_event(
            event_callback,
            event_type="routing",
            agent_name="Orchestrator Agent",
            iteration=state.route_round,
            stage_index=self.workflow_graph.get_node("orchestrator").stage_index,
            message=(
                "Orchestrator selected Requirements Analyst as the first agent because "
                "the raw scenario must be turned into structured requirements before downstream work can start."
            ),
            trace=initial_trace.__dict__,
            run_session=run_session,
            metrics=self._build_event_metrics(state, run_controls),
        )
        return "requirements"

    def _handle_requirements_stage(
        self,
        *,
        state: OrchestrationState,
        requirements_text: str,
        runtime_lookup: dict[str, AgentRuntimeConfig],
        run_controls: RunControlConfig,
        run_session: RunSession,
        event_callback,
    ) -> str:
        requirements_runtime = runtime_lookup.get("requirements_analyst")
        self._emit_event(
            event_callback,
            event_type="stage_started",
            agent_name="Requirements Analyst",
            iteration=state.route_round,
            stage_index=self.workflow_graph.get_node("requirements").stage_index,
            message=(
                "Running Requirements Analyst because the workflow needs structured requirement items, "
                "acceptance criteria, and assumptions before test design can continue."
            ),
            run_session=run_session,
        )
        started_at = time.perf_counter()
        state.requirements = self._run_with_timeout(
            agent_name="Requirements Analyst",
            runtime_config=requirements_runtime,
            func=self.requirements_analyst.analyze,
            args=(
                requirements_text,
                state.requirements_feedback,
                requirements_runtime,
                run_session,
            ),
        )
        duration_ms = self._elapsed_ms(started_at)
        requirements_trace = self._build_requirements_trace(
            state.route_round,
            requirements_text,
            state.requirements,
            state.requirements_feedback,
            requirements_runtime,
            duration_ms,
        )
        state.stage_traces.append(requirements_trace)
        self._emit_event(
            event_callback,
            event_type="stage_completed",
            agent_name="Requirements Analyst",
            iteration=state.route_round,
            stage_index=self.workflow_graph.get_node("requirements").stage_index,
            duration_ms=duration_ms,
            message=(
                f"Requirements Analyst completed in {duration_ms} ms and produced "
                f"{len(state.requirements)} structured requirement item(s)."
            ),
            trace=requirements_trace.__dict__,
            run_session=run_session,
        )
        requirements_validation_findings = list(
            self.requirements_analyst.last_execution.get("validation_findings") or []
        )
        if not state.requirements:
            contract_feedback = self._build_requirements_contract_feedback(requirements_validation_findings)
            if (
                state.route_round < run_controls.max_rounds
                and self._can_send_feedback(
                    from_agent="Orchestrator Agent",
                    to_agent="Requirements Analyst",
                    message_count=1,
                    run_controls=run_controls,
                    total_feedback_messages=state.total_feedback_messages,
                    pair_feedback_counts=state.pair_feedback_counts,
                )
            ):
                state.total_feedback_messages += 1
                state.pair_feedback_counts[("Orchestrator Agent", "Requirements Analyst")] += 1
                state.stage_traces.append(
                    self._build_targeted_orchestrator_trace(
                        route_round=state.route_round,
                        from_agent="Orchestrator Agent",
                        to_agent="Requirements Analyst",
                        feedback_messages=contract_feedback,
                        runtime_config=runtime_lookup.get("orchestrator"),
                        run_controls=run_controls,
                        total_feedback_messages=state.total_feedback_messages,
                        duration_ms=0,
                    )
                )
                self._emit_event(
                    event_callback,
                    event_type="routing",
                    agent_name="Orchestrator Agent",
                    iteration=state.route_round,
                    stage_index=4,
                    message=(
                        "Orchestrator routed contract-repair feedback back to Requirements Analyst because "
                        f"{self._summarize_feedback_reason(contract_feedback)}"
                    ),
                    run_session=run_session,
                    metrics=self._build_event_metrics(state, run_controls),
                )
                state.requirements_feedback = contract_feedback
                state.route_round += 1
                run_session.working_memory.write_shared(
                    "pending_feedback",
                    {"target": "requirements_analyst", "messages": list(contract_feedback)},
                    author="Orchestrator Agent",
                )
                return "requirements"

            state.stage_traces.append(
                self._build_contract_failure_stop_trace(
                    route_round=state.route_round,
                    runtime_config=runtime_lookup.get("orchestrator"),
                    run_controls=run_controls,
                    total_feedback_messages=state.total_feedback_messages,
                    failure_messages=contract_feedback,
                )
            )
            state.review = self._build_contract_failure_review(contract_feedback)
            run_session.working_memory.write_shared("review", state.review.__dict__, author="Orchestrator Agent")
            return "stop"

        state.requirements_feedback = []
        run_session.working_memory.write_shared("current_stage", "design", author="Orchestrator Agent")
        return "design"

    def _handle_design_stage(
        self,
        *,
        state: OrchestrationState,
        requirements_text: str,
        runtime_lookup: dict[str, AgentRuntimeConfig],
        run_controls: RunControlConfig,
        run_session: RunSession,
        event_callback,
    ) -> str:
        del requirements_text
        design_runtime = runtime_lookup.get("test_design")
        self._emit_event(
            event_callback,
            event_type="stage_started",
            agent_name="Test Design Agent",
            iteration=state.route_round,
            stage_index=self.workflow_graph.get_node("design").stage_index,
            message=(
                "Running Test Design Agent because the structured requirements are ready "
                "and must now be expanded into planned test coverage."
            ),
            run_session=run_session,
        )
        started_at = time.perf_counter()
        state.designs = self._run_with_timeout(
            agent_name="Test Design Agent",
            runtime_config=design_runtime,
            func=self.test_designer.design,
            args=(state.requirements, state.design_feedback, design_runtime, run_session),
        )
        duration_ms = self._elapsed_ms(started_at)
        design_trace = self._build_design_trace(
            state.route_round,
            state.requirements,
            state.designs,
            state.design_feedback,
            design_runtime,
            duration_ms,
        )
        state.stage_traces.append(design_trace)
        self._emit_event(
            event_callback,
            event_type="stage_completed",
            agent_name="Test Design Agent",
            iteration=state.route_round,
            stage_index=self.workflow_graph.get_node("design").stage_index,
            duration_ms=duration_ms,
            message=(
                f"Test Design Agent completed in {duration_ms} ms and produced "
                f"{len(state.designs)} planned test case(s)."
            ),
            trace=design_trace.__dict__,
            run_session=run_session,
        )
        state.design_feedback = []
        design_backtrack_feedback = self._build_design_backtrack_feedback(state.requirements)
        if (
            design_backtrack_feedback
            and state.route_round < run_controls.max_rounds
            and self._can_send_feedback(
                from_agent="Test Design Agent",
                to_agent="Requirements Analyst",
                message_count=1,
                run_controls=run_controls,
                total_feedback_messages=state.total_feedback_messages,
                pair_feedback_counts=state.pair_feedback_counts,
            )
        ):
            state.total_feedback_messages += 1
            state.pair_feedback_counts[("Test Design Agent", "Requirements Analyst")] += 1
            self._emit_event(
                event_callback,
                event_type="routing",
                agent_name="Orchestrator Agent",
                iteration=state.route_round,
                stage_index=4,
                message=(
                    "Orchestrator routed targeted feedback from Test Design Agent to Requirements Analyst because "
                    f"{self._summarize_feedback_reason(design_backtrack_feedback)}"
                ),
                run_session=run_session,
                metrics=self._build_event_metrics(state, run_controls),
            )
            state.stage_traces.append(
                self._build_targeted_orchestrator_trace(
                    route_round=state.route_round,
                    from_agent="Test Design Agent",
                    to_agent="Requirements Analyst",
                    feedback_messages=design_backtrack_feedback,
                    runtime_config=runtime_lookup.get("orchestrator"),
                    run_controls=run_controls,
                    total_feedback_messages=state.total_feedback_messages,
                    duration_ms=0,
                )
            )
            state.requirements_feedback = design_backtrack_feedback
            state.route_round += 1
            run_session.working_memory.write_shared(
                "pending_feedback",
                {"target": "requirements_analyst", "messages": list(design_backtrack_feedback)},
                author="Orchestrator Agent",
            )
            return "requirements"
        run_session.working_memory.write_shared("current_stage", "review", author="Orchestrator Agent")
        return "review"

    def _handle_review_stage(
        self,
        *,
        state: OrchestrationState,
        requirements_text: str,
        runtime_lookup: dict[str, AgentRuntimeConfig],
        run_controls: RunControlConfig,
        run_session: RunSession,
        event_callback,
    ) -> str:
        del requirements_text
        review_runtime = runtime_lookup.get("review")
        self._emit_event(
            event_callback,
            event_type="stage_started",
            agent_name="Review Agent",
            iteration=state.route_round,
            stage_index=self.workflow_graph.get_node("review").stage_index,
            message=(
                "Running Review Agent because the current requirements and planned test cases "
                "must be checked for coverage quality and routing decisions."
            ),
            run_session=run_session,
        )
        started_at = time.perf_counter()
        state.review = self._run_with_timeout(
            agent_name="Review Agent",
            runtime_config=review_runtime,
            func=self.reviewer.review,
            args=(state.requirements, state.designs, review_runtime, run_session),
        )
        duration_ms = self._elapsed_ms(started_at)
        review_trace = self._build_review_trace(
            state.route_round,
            state.requirements,
            state.designs,
            state.review,
            review_runtime,
            duration_ms,
        )
        state.stage_traces.append(review_trace)
        self._emit_event(
            event_callback,
            event_type="stage_completed",
            agent_name="Review Agent",
            iteration=state.route_round,
            stage_index=self.workflow_graph.get_node("review").stage_index,
            duration_ms=duration_ms,
            message=(
                f"Review Agent completed in {duration_ms} ms with approved={state.review.approved}, "
                f"coverage_ratio={state.review.coverage_ratio}, and {len(state.review.findings)} finding(s)."
            ),
            trace=review_trace.__dict__,
            run_session=run_session,
        )
        if state.review.approved:
            self._emit_event(
                event_callback,
                event_type="routing",
                agent_name="Orchestrator Agent",
                iteration=state.route_round,
                stage_index=4,
                message=(
                    "Orchestrator stopped the run because the review approved the current result "
                    f"with coverage_ratio={state.review.coverage_ratio}."
                ),
                run_session=run_session,
                metrics=self._build_event_metrics(state, run_controls),
            )
            state.stage_traces.append(
                self._build_stop_orchestrator_trace(
                    route_round=state.route_round,
                    review=state.review,
                    runtime_config=runtime_lookup.get("orchestrator"),
                    run_controls=run_controls,
                    total_feedback_messages=state.total_feedback_messages,
                    stop_reason="Stop pipeline because the review approved the result.",
                    stop_details=[
                        f"Approved at round: {state.route_round}",
                        f"Coverage ratio: {state.review.coverage_ratio:.2f}",
                    ],
                    duration_ms=0,
                )
            )
            return "stop"

        backtrack_route = self._select_review_backtrack_route(state.requirements, state.review)
        if (
            backtrack_route
            and state.route_round < run_controls.max_rounds
            and self._can_send_feedback(
                from_agent=backtrack_route["from_agent"],
                to_agent=backtrack_route["to_agent"],
                message_count=1,
                run_controls=run_controls,
                total_feedback_messages=state.total_feedback_messages,
                pair_feedback_counts=state.pair_feedback_counts,
            )
        ):
            state.total_feedback_messages += 1
            state.pair_feedback_counts[(backtrack_route["from_agent"], backtrack_route["to_agent"])] += 1
            self._emit_event(
                event_callback,
                event_type="routing",
                agent_name="Orchestrator Agent",
                iteration=state.route_round,
                stage_index=4,
                message=(
                    f"Orchestrator routed targeted feedback from {backtrack_route['from_agent']} "
                    f"to {backtrack_route['to_agent']} because "
                    f"{self._summarize_feedback_reason(backtrack_route['feedback_messages'])}"
                ),
                run_session=run_session,
                metrics=self._build_event_metrics(state, run_controls),
            )
            state.stage_traces.append(
                self._build_targeted_orchestrator_trace(
                    route_round=state.route_round,
                    from_agent=backtrack_route["from_agent"],
                    to_agent=backtrack_route["to_agent"],
                    feedback_messages=backtrack_route["feedback_messages"],
                    runtime_config=runtime_lookup.get("orchestrator"),
                    run_controls=run_controls,
                    total_feedback_messages=state.total_feedback_messages,
                    duration_ms=0,
                )
            )
            run_session.working_memory.write_shared(
                "pending_feedback",
                {
                    "target": (
                        "requirements_analyst"
                        if backtrack_route["to_agent"] == "Requirements Analyst"
                        else "test_design"
                    ),
                    "messages": list(backtrack_route["feedback_messages"]),
                },
                author="Orchestrator Agent",
            )
            if backtrack_route["to_agent"] == "Requirements Analyst":
                state.requirements_feedback = backtrack_route["feedback_messages"]
                next_stage = "requirements"
            else:
                state.design_feedback = backtrack_route["feedback_messages"]
                next_stage = "design"
            state.route_round += 1
            return next_stage

        stop_reason, stop_details = self._determine_review_stop_reason(
            review=state.review,
            backtrack_route=backtrack_route,
            run_controls=run_controls,
            route_round=state.route_round,
            total_feedback_messages=state.total_feedback_messages,
            pair_feedback_counts=state.pair_feedback_counts,
        )
        state.stage_traces.append(
            self._build_stop_orchestrator_trace(
                route_round=state.route_round,
                review=state.review,
                runtime_config=runtime_lookup.get("orchestrator"),
                run_controls=run_controls,
                total_feedback_messages=state.total_feedback_messages,
                stop_reason=stop_reason,
                stop_details=stop_details,
                duration_ms=0,
            )
        )
        self._emit_event(
            event_callback,
            event_type="routing",
            agent_name="Orchestrator Agent",
            iteration=state.route_round,
            stage_index=4,
            message=stop_reason,
            run_session=run_session,
            metrics=self._build_event_metrics(state, run_controls),
        )
        return "stop"

    def _build_requirements_trace(
        self,
        iteration: int,
        requirements_text: str,
        requirements: list,
        feedback_messages: list[str],
        runtime_config: AgentRuntimeConfig | None = None,
        duration_ms: int = 0,
    ) -> StageTrace:
        detailed_reasoning = []
        execution = self.requirements_analyst.last_execution
        token_usage = execution.get("token_usage") if isinstance(execution, dict) else {}
        llm_active = bool(execution.get("llm_used"))
        validation_findings = execution.get("validation_findings") or []
        if llm_active:
            detailed_reasoning.extend(execution.get("notes") or [])
        else:
            for item in requirements[:4]:
                detailed_reasoning.extend(self._explain_requirement_derivation(item))
                detailed_reasoning.extend(self._explain_requirement_feedback_application(item, feedback_messages))

        return StageTrace(
            iteration=iteration,
            stage_index=1,
            agent_name="Requirements Analyst",
            input_summary=[
                f"Raw requirement lines: {len([line for line in requirements_text.splitlines() if line.strip()])}",
                f"Input characters: {len(requirements_text)}",
                (
                    "Incoming feedback messages: none"
                    if not feedback_messages
                    else f"Incoming feedback messages: {len(feedback_messages)}"
                ),
                "Raw requirement text:",
                requirements_text,
                *feedback_messages,
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
                *(
                    [
                        f"Submit the raw requirement text and feedback messages to {runtime_config.model_id} for structured extraction."
                        if runtime_config
                        else "Submit the raw requirement text to the configured LLM for structured extraction.",
                        "Validate the returned JSON structure, then normalize requirement IDs into stable REQ-### order.",
                        (
                            "No targeted feedback was applied in this pass."
                            if not feedback_messages
                            else "Apply targeted backtracking feedback before finalizing acceptance criteria and assumptions."
                        ),
                    ]
                    if llm_active
                    else [
                        "Split the incoming requirement text into separate candidate requirement statements.",
                        "Normalize each statement, assign deterministic IDs in sequence, and preserve the original wording.",
                        "Classify priority from keyword matches such as 'must', 'måste', or 'should'.",
                        "Expand each requirement with heuristic acceptance criteria and note missing or implicit error handling as assumptions.",
                        (
                            "No targeted feedback was applied in this pass."
                            if not feedback_messages
                            else "Apply targeted backtracking feedback to the specific requirements mentioned by upstream agents before finalizing acceptance criteria and assumptions."
                        ),
                    ]
                ),
                *validation_findings,
                *detailed_reasoning,
            ],
            status="completed",
            agent_explanation=(
                (
                    "This agent used a live LLM to extract structured requirements, acceptance criteria, and assumptions from the raw scenario text."
                    if llm_active
                    else "This agent is deterministic. It splits the requirement text by line or sentence, assigns IDs in order, classifies priority from simple keywords, and enriches each requirement with heuristic acceptance criteria and assumptions."
                )
            ),
            decision_explanation=(
                (
                    f"Live model call used: {runtime_config.model_id} via {runtime_config.provider_strategy}."
                    if llm_active and runtime_config
                    else "No model judgment is used here. The output depends only on the input text and the hard-coded keyword rules."
                )
            ),
            reasoning_source=execution.get("reasoning_source", "structured_trace"),
            duration_ms=duration_ms,
            prompt_tokens=self._read_token_metric(token_usage, "prompt_tokens"),
            completion_tokens=self._read_token_metric(token_usage, "completion_tokens"),
            total_tokens=self._read_token_metric(token_usage, "total_tokens"),
        )

    def _summarize_feedback_reason(self, feedback_messages: list[str]) -> str:
        cleaned = [message.strip().rstrip(".") for message in feedback_messages if message.strip()]
        if not cleaned:
            return "the upstream review requested another targeted repair pass."
        first_message = cleaned[0]
        if len(cleaned) == 1:
            return first_message[0].lower() + first_message[1:] + "."
        return first_message[0].lower() + first_message[1:] + f", plus {len(cleaned) - 1} more feedback item(s)."

    def _build_design_trace(
        self,
        iteration: int,
        requirements: list,
        designs: list,
        feedback_messages: list[str],
        runtime_config: AgentRuntimeConfig | None = None,
        duration_ms: int = 0,
    ) -> StageTrace:
        execution = self.test_designer.last_execution
        token_usage = execution.get("token_usage") if isinstance(execution, dict) else {}
        llm_active = bool(execution.get("llm_used"))
        return StageTrace(
            iteration=iteration,
            stage_index=2,
            agent_name="Test Design Agent",
            input_summary=[
                f"Requirements received: {len(requirements)}",
                f"Acceptance criteria seen: {sum(len(item.acceptance_criteria) for item in requirements)}",
                (
                    "Incoming feedback messages: none"
                    if not feedback_messages
                    else f"Incoming feedback messages: {len(feedback_messages)}"
                ),
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
                *(
                    [
                        f"Submit the structured requirements to {runtime_config.model_id} to generate concrete test cases."
                        if runtime_config
                        else "Submit the structured requirements to the configured LLM to generate concrete test cases.",
                        "Validate the structured test-design JSON, then preserve realistic one-to-many requirement coverage when the model returns multiple test cases for the same requirement.",
                        (
                            "No targeted design feedback was applied in this pass."
                            if not feedback_messages
                            else "Incorporate targeted review feedback before finalizing steps, expected results, and oracle wording."
                        ),
                        *(execution.get("notes") or []),
                    ]
                    if llm_active
                    else [
                        "Read each structured requirement together with its acceptance criteria and assumptions.",
                        "Choose a test type from deterministic keyword routing such as gui/e2e, api/integration, unit, or scenario.",
                        "Generate one or more test-case designs per requirement when the requirement implies positive, negative, authorization, validation, or boundary behavior.",
                        "Carry forward requirement assumptions as design risks so later review can challenge weak testability.",
                        (
                            "No targeted design feedback was applied in this pass."
                            if not feedback_messages
                            else "Incorporate targeted review feedback before finalizing steps, expected results, and oracle wording."
                        ),
                    ]
                ),
            ],
            status="completed",
            agent_explanation=(
                (
                    "This agent used a live LLM to convert structured requirements into concrete planned test cases with titles, steps, expected results, and oracle text."
                    if llm_active
                    else "This agent converts structured requirements into one or more concrete test case designs. It expands requirements that imply multiple behaviors into separate positive, negative, validation, or authorization-focused cases."
                )
            ),
            decision_explanation=(
                (
                    f"Live model call used: {runtime_config.model_id} via {runtime_config.provider_strategy}."
                    if llm_active and runtime_config
                    else "The label 'designs' means draft test cases before code generation. In this app they are the planned test cases, and a single requirement can map to several test cases."
                )
            ),
            reasoning_source=execution.get("reasoning_source", "structured_trace"),
            duration_ms=duration_ms,
            prompt_tokens=self._read_token_metric(token_usage, "prompt_tokens"),
            completion_tokens=self._read_token_metric(token_usage, "completion_tokens"),
            total_tokens=self._read_token_metric(token_usage, "total_tokens"),
        )

    def _build_review_trace(
        self,
        iteration: int,
        requirements: list,
        designs: list,
        review,
        runtime_config: AgentRuntimeConfig | None = None,
        duration_ms: int = 0,
    ) -> StageTrace:
        execution = self.reviewer.last_execution
        token_usage = execution.get("token_usage") if isinstance(execution, dict) else {}
        llm_active = bool(execution.get("llm_used"))
        review_reasoning = (
            execution.get("notes") or self._build_review_reasoning(requirements, designs, review)
            if llm_active
            else self._build_review_reasoning(requirements, designs, review)
        )
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
                *(
                    [
                        f"Submit the requirements and planned test cases to {runtime_config.model_id} for a structured QA review."
                        if runtime_config
                        else "Submit the requirements and planned test cases to the configured LLM for structured QA review.",
                        "Use the model response to judge approval, coverage ratio, findings, and routing focus for the next repair step.",
                    ]
                    if llm_active
                    else [
                        "Compute requirement coverage by checking whether each requirement ID appears in at least one designed test case.",
                        "Check whether requirements that imply multiple behaviors were expanded into more than one focused test case.",
                        "Flag designs with too few expected results because weak oracles reduce confidence in the generated tests.",
                        "Flag requirements that still contain assumptions because automation would otherwise encode guesses.",
                        "Approve only when full coverage is reached and the number of findings stays below the hard-coded threshold.",
                    ]
                ),
                *review_reasoning,
            ],
            agent_explanation=(
                (
                    "This review stage used a live LLM to evaluate coverage quality, oracle strength, unresolved assumptions, and the most relevant backtracking target."
                    if llm_active
                    else "This review stage is a deterministic rule check, not an autonomous evaluator. It computes requirement coverage, flags suspicious one-to-one mappings for multi-behavior requirements, flags test cases with too few expected results, and flags requirements that still contain assumptions."
                )
            ),
            decision_explanation=(
                (
                    f"Live model call used: {runtime_config.model_id} via {runtime_config.provider_strategy}."
                    if llm_active and runtime_config
                    else "Approval becomes true only when every requirement has at least one designed test case and the total number of findings stays at or below the hard-coded threshold. In this implementation, findings mainly come from four sources: missing designed coverage, suspiciously thin one-to-one coverage, weak oracle definitions, and unresolved assumptions."
                )
            ),
            reasoning_source=execution.get("reasoning_source", "structured_trace"),
            duration_ms=duration_ms,
            prompt_tokens=self._read_token_metric(token_usage, "prompt_tokens"),
            completion_tokens=self._read_token_metric(token_usage, "completion_tokens"),
            total_tokens=self._read_token_metric(token_usage, "total_tokens"),
        )

    @staticmethod
    def _read_token_metric(token_usage: object, field_name: str) -> int | None:
        if not isinstance(token_usage, dict):
            return None
        value = token_usage.get(field_name)
        return value if isinstance(value, int) else None

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
        llm_feedback = self.test_designer.last_execution.get("feedback_messages_to_requirements") or []
        if llm_feedback:
            return llm_feedback[:2]
        del requirements
        return []

    def _build_requirements_contract_feedback(self, validation_findings: list[str]) -> list[str]:
        feedback = [
            "Requirements Analyst must return at least one valid requirement item under the requirements.v1 contract."
        ]
        feedback.extend(validation_findings[:3])
        feedback.append(
            "Each requirement item must have non-empty original_text, normalized_text, and acceptance_criteria."
        )
        return feedback

    def _select_review_backtrack_route(self, requirements: list, review) -> dict | None:
        routing_focus = self._normalize_routing_focus(
            self.reviewer.last_execution.get("routing_focus") or [],
            review.findings,
            review.improvement_actions,
        )
        if "test_design" in routing_focus and "requirements" not in routing_focus:
            return {
                "from_agent": "Review Agent",
                "to_agent": "Test Design Agent",
                "feedback_messages": review.improvement_actions[:2]
                or ["Strengthen oracle quality and expected results in the current test designs."],
            }
        if "requirements" in routing_focus and "test_design" not in routing_focus:
            return {
                "from_agent": "Review Agent",
                "to_agent": "Requirements Analyst",
                "feedback_messages": review.improvement_actions[:2]
                or ["Clarify ambiguous requirements and reduce assumptions before redesign."],
            }

        weak_oracle_findings = [finding for finding in review.findings if "weak oracle definition" in finding]
        assumption_findings = [finding for finding in review.findings if "contains assumptions" in finding]
        missing_design_findings = [finding for finding in review.findings if "missing a designed test case" in finding]

        thin_design_findings = [finding for finding in review.findings if "has only one designed test case" in finding]
        lowered_findings = [finding.lower() for finding in review.findings]
        lowered_actions = [action.lower() for action in review.improvement_actions]

        if weak_oracle_findings or missing_design_findings or thin_design_findings:
            feedback_messages = []
            if weak_oracle_findings:
                feedback_messages.append(
                    "Strengthen weak oracle definitions by adding more explicit expected results and negative scenarios."
                )
            if missing_design_findings:
                feedback_messages.append(
                    "Design missing test coverage for every uncovered requirement."
                )
            if thin_design_findings:
                feedback_messages.append(
                    "Expand thin one-to-one mappings into multiple focused test cases when a requirement implies positive, negative, validation, authorization, or boundary behavior."
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

        if any(
            keyword in " ".join(lowered_findings + lowered_actions)
            for keyword in (
                "oracle",
                "expected result",
                "test design",
                "test coverage",
                "negative scenario",
                "boundary",
                "missing test",
                "more test case",
            )
        ):
            feedback_messages = review.improvement_actions[:2] or [
                "Strengthen the planned test coverage and make expected results more explicit."
            ]
            return {
                "from_agent": "Review Agent",
                "to_agent": "Test Design Agent",
                "feedback_messages": feedback_messages,
            }

        if any(
            keyword in " ".join(lowered_findings + lowered_actions)
            for keyword in (
                "assumption",
                "ambiguous requirement",
                "unclear requirement",
                "acceptance criteria",
                "clarify requirement",
                "clarify ambiguous",
                "reduce ambiguity",
            )
        ):
            feedback_messages = review.improvement_actions[:2] or [
                "Clarify ambiguous requirements and acceptance criteria before redesign."
            ]
            return {
                "from_agent": "Review Agent",
                "to_agent": "Requirements Analyst",
                "feedback_messages": feedback_messages,
            }

        return None

    def _normalize_routing_focus(
        self,
        raw_focus: list[str],
        findings: list[str],
        improvement_actions: list[str],
    ) -> set[str]:
        focus: set[str] = set()
        combined = " ".join([*raw_focus, *findings, *improvement_actions]).lower()
        for entry in raw_focus:
            normalized = str(entry or "").strip().lower()
            if normalized in {"requirements", "requirement", "requirements analyst"}:
                focus.add("requirements")
            elif normalized in {"test_design", "test design", "designer", "test design agent"}:
                focus.add("test_design")
        if any(
            keyword in combined
            for keyword in (
                "assumption",
                "ambiguous requirement",
                "unclear requirement",
                "acceptance criteria",
                "clarify requirement",
                "requirements analyst",
            )
        ):
            focus.add("requirements")
        if any(
            keyword in combined
            for keyword in (
                "oracle",
                "expected result",
                "test case",
                "test design",
                "test coverage",
                "negative scenario",
                "boundary",
                "missing test",
            )
        ):
            focus.add("test_design")
        return focus

    def _build_targeted_orchestrator_trace(
        self,
        route_round: int,
        from_agent: str,
        to_agent: str,
        feedback_messages: list[str],
        runtime_config: AgentRuntimeConfig | None,
        run_controls: RunControlConfig,
        total_feedback_messages: int,
        duration_ms: int,
    ) -> StageTrace:
        llm_active = bool(runtime_config and runtime_config.execution_mode == "LLM-backed")
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
                *(
                    [
                        f"Apply live orchestration rules under {runtime_config.model_id}, while still enforcing the configured feedback budgets locally.",
                        "Choose the smallest possible backtracking step instead of restarting the whole pipeline.",
                        f"Route the workflow directly from {from_agent} back to {to_agent} so downstream stages can be regenerated from the repaired state.",
                    ]
                    if llm_active
                    else [
                        "Read the feedback request and evaluate whether the configured feedback budgets still allow another targeted handoff.",
                        "Choose the smallest possible backtracking step instead of restarting the whole pipeline.",
                        f"Route the workflow directly from {from_agent} back to {to_agent} so downstream stages can be regenerated from the repaired state.",
                    ]
                ),
            ],
            agent_explanation=(
                "The orchestrator works as a routing controller. Instead of forcing a full rerun, it can send a targeted repair request back to the most relevant upstream agent."
            ),
            decision_explanation=(
                (
                    f"Configured execution mode is LLM-backed with {runtime_config.model_id}, but budget enforcement is still applied locally for safety."
                    if llm_active and runtime_config
                    else "This is selective backtracking. The orchestrator does not start over from scratch here. It routes the repair message to the exact agent that should respond next, then resumes the pipeline from that point."
                )
            ),
            reasoning_source="llm_assisted_routing" if llm_active else "structured_trace",
            duration_ms=duration_ms,
        )

    def _build_initial_orchestrator_trace(
        self,
        route_round: int,
        runtime_config: AgentRuntimeConfig | None,
        run_controls: RunControlConfig,
    ) -> StageTrace:
        llm_active = bool(runtime_config and runtime_config.execution_mode == "LLM-backed")
        return StageTrace(
            iteration=route_round,
            stage_index=0,
            agent_name="Orchestrator Agent",
            input_summary=[
                "Initial routing decision before any worker agent starts.",
                f"Maximum rounds: {run_controls.max_rounds}",
                f"Maximum feedback messages: {run_controls.max_feedback_messages}",
                f"Maximum feedback per agent pair: {run_controls.max_feedback_per_agent_pair}",
            ],
            output_summary=[
                "Start the workflow with Requirements Analyst.",
                "Requirements must be extracted before test design or review can continue.",
            ],
            status="route to requirements analyst",
            reasoning_trace=[
                *(
                    [
                        f"Use the configured orchestration mode under {runtime_config.model_id} to decide the first valid handoff.",
                        "Requirements Analyst must run first because the downstream agents depend on structured requirements.",
                        "Do not start Test Design or Review before the requirement contract exists.",
                    ]
                    if llm_active and runtime_config
                    else [
                        "Evaluate which agent has the minimum required inputs at the start of the run.",
                        "Requirements Analyst must run first because the downstream agents depend on structured requirements.",
                        "Do not start Test Design or Review before the requirement contract exists.",
                    ]
                ),
            ],
            agent_explanation=(
                "The orchestrator starts the workflow by selecting the first agent that has enough information to act."
            ),
            decision_explanation=(
                (
                    f"Configured execution mode is LLM-backed with {runtime_config.model_id}, but the first routing decision is still constrained by the local workflow contract."
                    if llm_active and runtime_config
                    else "The run starts with Requirements Analyst because raw scenario text must be turned into structured requirements before downstream work can start."
                )
            ),
            reasoning_source="llm_assisted_routing" if llm_active else "structured_trace",
            duration_ms=0,
        )

    def _build_contract_failure_stop_trace(
        self,
        route_round: int,
        runtime_config: AgentRuntimeConfig | None,
        run_controls: RunControlConfig,
        total_feedback_messages: int,
        failure_messages: list[str],
    ) -> StageTrace:
        llm_active = bool(runtime_config and runtime_config.execution_mode == "LLM-backed")
        return StageTrace(
            iteration=route_round,
            stage_index=4,
            agent_name="Orchestrator Agent",
            input_summary=[
                "Contract check after Requirements Analyst failed.",
                f"Maximum rounds: {run_controls.max_rounds}",
                f"Maximum feedback messages: {run_controls.max_feedback_messages}",
                f"Maximum feedback per agent pair: {run_controls.max_feedback_per_agent_pair}",
                f"Feedback messages already used: {total_feedback_messages}",
            ],
            output_summary=[
                "Stop pipeline because the Requirements Analyst output did not satisfy the requirements.v1 contract.",
                *failure_messages,
            ],
            status="stop",
            reasoning_trace=[
                "Validate the Requirements Analyst output before allowing Test Design to start.",
                "Do not let downstream agents continue when no valid structured requirements are available.",
                "Stop the run when the contract is still broken and no further backtracking step is allowed.",
            ],
            agent_explanation=(
                "The orchestrator now enforces a hard contract between Requirements Analyst and Test Design. "
                "If no valid requirement items are produced, the pipeline is not allowed to continue."
            ),
            decision_explanation=(
                f"Configured execution mode is LLM-backed with {runtime_config.model_id}, but contract enforcement is still local."
                if llm_active and runtime_config
                else "The orchestrator blocked downstream work because the standardized requirements.v1 contract was not met."
            ),
            reasoning_source="contract_guard",
            duration_ms=0,
        )

    def _build_contract_failure_review(self, failure_messages: list[str]) -> ReviewReport:
        return ReviewReport(
            approved=False,
            coverage_ratio=0.0,
            findings=list(failure_messages),
            improvement_actions=[
                "Requirements Analyst must return at least one valid requirement item with non-empty text and acceptance criteria."
            ],
        )

    def _determine_review_stop_reason(
        self,
        *,
        review=None,
        backtrack_route: dict | None,
        run_controls: RunControlConfig,
        route_round: int,
        total_feedback_messages: int,
        pair_feedback_counts: dict[tuple[str, str], int],
    ) -> tuple[str, list[str]]:
        if route_round >= run_controls.max_rounds:
            return (
                f"Stop pipeline because Maximum rounds ({run_controls.max_rounds}) was reached.",
                [
                    f"Current round: {route_round}",
                    f"Configured maximum rounds: {run_controls.max_rounds}",
                ],
            )

        if not backtrack_route:
            raw_focus = self.reviewer.last_execution.get("routing_focus") or []
            findings = list(review.findings) if review else []
            improvement_actions = list(review.improvement_actions) if review else []
            normalized_focus = sorted(
                self._normalize_routing_focus(raw_focus, findings, improvement_actions)
            )
            return (
                "Stop pipeline because no valid backtracking route was available.",
                [
                    "The review step did not produce a usable routing target.",
                    "No targeted repair route to Requirements Analyst or Test Design Agent could be selected.",
                    f"Raw routing focus from review: {raw_focus or ['none']}",
                    f"Normalized routing focus: {normalized_focus or ['none']}",
                    (
                        f"Primary finding that could not be mapped: {findings[0]}"
                        if findings
                        else "Primary finding that could not be mapped: none"
                    ),
                ],
            )

        from_agent = backtrack_route["from_agent"]
        to_agent = backtrack_route["to_agent"]
        pair_used = pair_feedback_counts[(from_agent, to_agent)]
        pair_limit = run_controls.max_feedback_per_agent_pair

        if run_controls.max_feedback_messages and total_feedback_messages + 1 > run_controls.max_feedback_messages:
            return (
                f"Stop pipeline because Maximum feedback messages ({run_controls.max_feedback_messages}) was reached.",
                [
                    f"Feedback messages already used: {total_feedback_messages}",
                    f"Attempted next route: {from_agent} -> {to_agent}",
                ],
            )

        if pair_limit and pair_used + 1 > pair_limit:
            return (
                (
                    "Stop pipeline because Maximum feedback messages per agent pair "
                    f"was reached for {from_agent} -> {to_agent} ({pair_used}/{pair_limit})."
                ),
                [
                    f"Blocked pair: {from_agent} -> {to_agent}",
                    f"Feedback already used for this pair: {pair_used}",
                    f"Configured pair limit: {pair_limit}",
                ],
            )

        return (
            "Stop pipeline because no more targeted feedback is allowed or no valid backtracking route was available.",
            [],
        )

    def _build_stop_orchestrator_trace(
        self,
        route_round: int,
        review,
        runtime_config: AgentRuntimeConfig | None,
        run_controls: RunControlConfig,
        total_feedback_messages: int,
        stop_reason: str,
        stop_details: list[str],
        duration_ms: int,
    ) -> StageTrace:
        llm_active = bool(runtime_config and runtime_config.execution_mode == "LLM-backed")
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
                *stop_details,
                (
                    f"Primary reason: {review.findings[0]}"
                    if review.findings
                    else "Primary reason: no explicit finding was recorded."
                ),
                *review.improvement_actions[:3],
            ],
            status="stop",
            reasoning_trace=[
                *(
                    [
                        f"Use the configured orchestration mode under {runtime_config.model_id} together with the local feedback-budget guards.",
                        "Stop when the Review Agent returns approved=true, or when no further targeted backtracking route is allowed or available.",
                        "Do not restart the whole pipeline here because this orchestrator now prefers selective routing.",
                    ]
                    if llm_active
                    else [
                        "Read the current review status together with the remaining feedback budget.",
                        "Stop when the Review Agent returns approved=true, or when no further targeted backtracking route is allowed or available.",
                        "Do not restart the whole pipeline here because this orchestrator now prefers selective routing.",
                    ]
                ),
            ],
            agent_explanation=(
                "The orchestrator is the routing controller for the workflow. It either stops the run or sends targeted repair requests to earlier agents."
            ),
            decision_explanation=(
                (
                    f"Configured execution mode is LLM-backed with {runtime_config.model_id}, but the final stop rule is still enforced locally against the configured limits and the Review Agent's approved=true signal."
                    if llm_active and runtime_config
                    else "The run stops when the Review Agent returns approved=true or when no more valid agent-to-agent backtracking step can be taken under the configured limits."
                )
            ),
            reasoning_source="llm_assisted_routing" if llm_active else "structured_trace",
            duration_ms=duration_ms,
        )

    def _elapsed_ms(self, started_at: float) -> int:
        return max(0, int(round((time.perf_counter() - started_at) * 1000)))

    def _raise_if_cancelled(self, stop_requested) -> None:
        if stop_requested and stop_requested():
            raise WorkflowCancelledError("Workflow was stopped by the user.")

    def _run_with_timeout(self, agent_name: str, runtime_config: AgentRuntimeConfig | None, func, args: tuple):
        timeout_seconds = max(1, int(runtime_config.timeout_seconds if runtime_config else AGENT_TIMEOUT_SECONDS))
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(func, *args)
        try:
            return future.result(timeout=timeout_seconds)
        except FuturesTimeoutError as exc:
            future.cancel()
            raise AgentTimeoutError(agent_name=agent_name, timeout_seconds=timeout_seconds) from exc
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def _emit_event(
        self,
        event_callback,
        *,
        event_type: str,
        agent_name: str,
        iteration: int,
        stage_index: int,
        message: str,
        duration_ms: int = 0,
        trace: dict | None = None,
        run_session: RunSession | None = None,
        metrics: dict | None = None,
    ) -> None:
        if not event_callback:
            return
        payload = {
            "event_type": event_type,
            "agent_name": agent_name,
            "iteration": iteration,
            "stage_index": stage_index,
            "message": message,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        if trace is not None:
            payload["trace"] = trace
        if run_session is not None:
            payload["memory_snapshot"] = self._snapshot_working_memory(run_session)
        if metrics is not None:
            payload["metrics"] = metrics
        event_callback(payload)

    def _build_event_metrics(self, state: OrchestrationState, run_controls: RunControlConfig) -> dict[str, object]:
        pair_feedback_counts = {
            f"{from_agent} -> {to_agent}": count
            for (from_agent, to_agent), count in state.pair_feedback_counts.items()
        }
        return {
            "current_round": state.route_round,
            "max_rounds": run_controls.max_rounds,
            "total_feedback_messages": state.total_feedback_messages,
            "max_feedback_messages": run_controls.max_feedback_messages,
            "max_feedback_per_agent_pair": run_controls.max_feedback_per_agent_pair,
            "pair_feedback_counts": pair_feedback_counts,
        }

    def _snapshot_working_memory(self, run_session: RunSession) -> dict:
        working_memory = run_session.working_memory
        return {
            "shared": copy.deepcopy(working_memory.shared),
            "agent_private": copy.deepcopy(working_memory.agent_private),
            "timeline": list(working_memory.timeline),
        }

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
        if "has only one designed test case" in finding:
            return (
                f"{finding} This means the requirement looks broader than the current coverage and should likely be split into several focused test cases."
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

    def _explain_requirement_feedback_application(
        self,
        item,
        feedback_messages: list[str],
    ) -> list[str]:
        if not feedback_messages:
            return []

        combined_feedback = " ".join(feedback_messages).lower()
        if item.requirement_id.lower() not in combined_feedback:
            return [f"{item.requirement_id}: no targeted upstream feedback matched this requirement in this pass."]

        effects = []
        if "Observable success and failure outcomes shall be explicitly defined." in item.acceptance_criteria:
            effects.append("added explicit observable-outcome acceptance criteria")
        if "Negative and error flows shall be explicitly defined and testable." in item.acceptance_criteria:
            effects.append("added explicit negative/error-flow acceptance criteria")
        if not item.assumptions:
            effects.append("removed prior assumptions that were addressed by the feedback")
        if not effects:
            effects.append("feedback matched this requirement but did not change the final structured output")

        return [f"{item.requirement_id}: upstream feedback was applied -> {'; '.join(effects)}."]

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

        design_counts = {}
        for design in designs:
            design_counts[design.requirement_id] = design_counts.get(design.requirement_id, 0) + 1
        reasoning.append(
            "Designed test cases per requirement: "
            + (
                ", ".join(f"{requirement_id}={count}" for requirement_id, count in sorted(design_counts.items()))
                if design_counts
                else "none"
            )
            + "."
        )

        thin_coverage_findings = [
            finding for finding in review.findings if "has only one designed test case" in finding
        ]
        reasoning.append(
            "Thin one-to-one coverage findings: "
            + (", ".join(thin_coverage_findings) if thin_coverage_findings else "none")
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
