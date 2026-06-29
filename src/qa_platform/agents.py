from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .llm_runtime import call_structured_llm, is_llm_enabled
from .models import AgentRuntimeConfig
from .models import RequirementItem, ReviewReport, TestCaseDesign


def _split_requirements(requirements_text: str) -> list[str]:
    lines = [line.strip(" -*\t") for line in requirements_text.splitlines()]
    items = [line for line in lines if line]
    if items:
        return items
    sentences = [part.strip() for part in re.split(r"[.!?]\s+", requirements_text) if part.strip()]
    return sentences or [requirements_text.strip()]


@dataclass
class RequirementsAnalystAgent:
    name: str = "Requirements Analyst"
    last_execution: dict[str, Any] = field(default_factory=dict)

    def analyze(
        self,
        requirements_text: str,
        feedback_messages: list[str] | None = None,
        runtime_config: AgentRuntimeConfig | None = None,
    ) -> list[RequirementItem]:
        feedback_messages = feedback_messages or []
        if is_llm_enabled(runtime_config):
            return self._analyze_with_llm(requirements_text, feedback_messages, runtime_config)

        items = []
        for index, raw_text in enumerate(_split_requirements(requirements_text), start=1):
            requirement_id = f"REQ-{index:03d}"
            normalized = raw_text.strip().rstrip(".")
            criteria = self._extract_acceptance_criteria(normalized)
            assumptions = self._build_assumptions(normalized, criteria)
            criteria, assumptions = self._apply_feedback(requirement_id, criteria, assumptions, feedback_messages)
            items.append(
                RequirementItem(
                    requirement_id=requirement_id,
                    original_text=raw_text,
                    normalized_text=normalized,
                    priority=self._classify_priority(normalized),
                    acceptance_criteria=criteria,
                    assumptions=assumptions,
                )
            )
        items, validation_findings = self._standardize_requirement_items(items)
        self.last_execution = {
            "mode": "structured",
            "reasoning_source": "structured_trace",
            "notes": [],
            "llm_used": False,
            "validation_findings": validation_findings,
            "contract_version": "requirements.v1",
        }
        return items

    def _analyze_with_llm(
        self,
        requirements_text: str,
        feedback_messages: list[str],
        runtime_config: AgentRuntimeConfig,
    ) -> list[RequirementItem]:
        system_prompt = (
            f"You are {runtime_config.agent_name}.\n"
            f"{runtime_config.directives}\n"
            "Return only structured output. Extract only what the requirement text supports. "
            "Make uncertainty explicit. Keep requirement order stable."
        )
        feedback_block = "\n".join(f"- {message}" for message in feedback_messages) or "- none"
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "requirements": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "original_text": {"type": "string"},
                            "normalized_text": {"type": "string"},
                            "priority": {"type": "string", "enum": ["high", "medium", "normal"]},
                            "acceptance_criteria": {"type": "array", "items": {"type": "string"}},
                            "assumptions": {"type": "array", "items": {"type": "string"}},
                            "trace_notes": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": [
                            "original_text",
                            "normalized_text",
                            "priority",
                            "acceptance_criteria",
                            "assumptions",
                            "trace_notes",
                        ],
                    },
                },
                "run_notes": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["requirements", "run_notes"],
        }
        user_prompt = (
            "Raw requirement text:\n"
            f"{requirements_text}\n\n"
            "Incoming upstream feedback:\n"
            f"{feedback_block}\n\n"
            "Return one requirement object per requirement statement. "
            "Acceptance criteria must be observable and testable. "
            "Assumptions must stay explicit instead of being silently resolved."
        )
        response, metadata = call_structured_llm(
            runtime_config=runtime_config,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema_name="requirements_analysis",
            schema=schema,
        )
        items = []
        raw_items = response.get("requirements") or []
        for index, item in enumerate(raw_items, start=1):
            original_text = _clean_text(item.get("original_text"))
            normalized_text = _clean_text(item.get("normalized_text")) or original_text.strip().rstrip(".")
            priority = _clean_priority(item.get("priority"))
            acceptance_criteria = _clean_string_list(item.get("acceptance_criteria"))
            assumptions = _clean_string_list(item.get("assumptions"))
            items.append(
                RequirementItem(
                    requirement_id=f"REQ-{index:03d}",
                    original_text=original_text,
                    normalized_text=normalized_text,
                    priority=priority,
                    acceptance_criteria=acceptance_criteria,
                    assumptions=assumptions,
                )
            )
        items, validation_findings = self._standardize_requirement_items(items)
        self.last_execution = {
            "mode": "llm",
            "reasoning_source": "llm_structured_output",
            "notes": _clean_string_list(response.get("run_notes"))
            + _flatten_trace_notes(raw_items, "trace_notes"),
            "llm_used": True,
            "metadata": metadata,
            "validation_findings": validation_findings,
            "contract_version": "requirements.v1",
        }
        return items

    def _standardize_requirement_items(
        self,
        items: list[RequirementItem],
    ) -> tuple[list[RequirementItem], list[str]]:
        standardized: list[RequirementItem] = []
        validation_findings: list[str] = []
        for item in items:
            original_text = item.original_text.strip()
            normalized_text = item.normalized_text.strip()
            acceptance_criteria = [criterion.strip() for criterion in item.acceptance_criteria if criterion.strip()]
            assumptions = [assumption.strip() for assumption in item.assumptions if assumption.strip()]

            if not original_text:
                validation_findings.append(f"{item.requirement_id} was dropped because original_text was empty.")
                continue
            if not normalized_text:
                validation_findings.append(f"{item.requirement_id} was dropped because normalized_text was empty.")
                continue
            if not acceptance_criteria:
                validation_findings.append(
                    f"{item.requirement_id} was dropped because acceptance_criteria was empty."
                )
                continue

            standardized.append(
                RequirementItem(
                    requirement_id=item.requirement_id,
                    original_text=original_text,
                    normalized_text=normalized_text,
                    priority=item.priority,
                    acceptance_criteria=acceptance_criteria,
                    assumptions=assumptions,
                )
            )

        if not standardized:
            validation_findings.append(
                "Requirements Analyst did not produce any valid requirement items that satisfy the requirements.v1 contract."
            )

        return standardized, validation_findings

    def _extract_acceptance_criteria(self, text: str) -> list[str]:
        lowered = text.lower()
        criteria = [f"The system shall satisfy the requirement: {text}"]
        if any(keyword in lowered for keyword in ("login", "logga in", "autentis", "sign in")):
            criteria.append("The user shall be authenticated when valid credentials are supplied.")
            criteria.append("Invalid credentials shall produce a clear error message.")
        if any(keyword in lowered for keyword in ("visa", "display", "list", "översikt", "dashboard")):
            criteria.append("Relevant information shall be presented without broken or empty states.")
        if any(keyword in lowered for keyword in ("skapa", "save", "spara", "registrera", "submit")):
            criteria.append("Input data shall be validated before it is stored.")
            criteria.append("A successful operation shall provide user confirmation.")
        if any(keyword in lowered for keyword in ("admin", "behörighet", "access", "roll")):
            criteria.append("Unauthorized access shall be blocked and logged.")
        return criteria

    def _build_assumptions(self, text: str, criteria: list[str]) -> list[str]:
        assumptions = []
        if len(criteria) == 1:
            assumptions.append("The requirement likely needs more explicit acceptance criteria.")
        if not any(word in text.lower() for word in ("fel", "error", "ogiltig", "invalid")):
            assumptions.append("Error handling is not explicit and should be reviewed.")
        return assumptions

    def _classify_priority(self, text: str) -> str:
        lowered = text.lower()
        if any(keyword in lowered for keyword in ("måste", "must", "critical", "viktig")):
            return "high"
        if any(keyword in lowered for keyword in ("bör", "should", "nice")):
            return "medium"
        return "normal"

    def _apply_feedback(
        self,
        requirement_id: str,
        criteria: list[str],
        assumptions: list[str],
        feedback_messages: list[str],
    ) -> tuple[list[str], list[str]]:
        if not feedback_messages:
            return criteria, assumptions

        combined_feedback = " ".join(feedback_messages).lower()
        updated_criteria = list(criteria)
        updated_assumptions = list(assumptions)
        feedback_targets_requirement = requirement_id.lower() in combined_feedback or "requirement" in combined_feedback

        if feedback_targets_requirement and "acceptance criteria" in combined_feedback:
            clarification = "Observable success and failure outcomes shall be explicitly defined."
            if clarification not in updated_criteria:
                updated_criteria.append(clarification)
            updated_assumptions = [
                assumption
                for assumption in updated_assumptions
                if "more explicit acceptance criteria" not in assumption.lower()
            ]

        if feedback_targets_requirement and any(
            phrase in combined_feedback
            for phrase in ("error handling", "negative path", "invalid credentials", "invalid input")
        ):
            clarification = "Negative and error flows shall be explicitly defined and testable."
            if clarification not in updated_criteria:
                updated_criteria.append(clarification)
            updated_assumptions = [
                assumption
                for assumption in updated_assumptions
                if "error handling is not explicit" not in assumption.lower()
            ]

        return updated_criteria, updated_assumptions


@dataclass
class TestDesignAgent:
    name: str = "Test Design Agent"
    last_execution: dict[str, Any] = field(default_factory=dict)

    def design(
        self,
        requirements: list[RequirementItem],
        feedback_messages: list[str] | None = None,
        runtime_config: AgentRuntimeConfig | None = None,
    ) -> list[TestCaseDesign]:
        feedback_messages = feedback_messages or []
        if is_llm_enabled(runtime_config):
            return self._design_with_llm(requirements, feedback_messages, runtime_config)

        designs = []
        for req in requirements:
            test_type = self._choose_test_type(req)
            design_id = f"TC-{req.requirement_id.split('-')[-1]}"
            title = self._build_title(req)
            steps = self._build_steps(req)
            expected_results = [criterion for criterion in req.acceptance_criteria]
            steps, expected_results, oracle = self._apply_feedback(
                req.requirement_id,
                steps,
                expected_results,
                feedback_messages,
            )
            risks = self._identify_risks(req)
            designs.append(
                TestCaseDesign(
                    test_case_id=design_id,
                    requirement_id=req.requirement_id,
                    title=title,
                    test_type=test_type,
                    preconditions=["The application is available.", "Test data is initialized."],
                    steps=steps,
                    expected_results=expected_results,
                    oracle=oracle,
                    risks=risks,
                )
            )
        self.last_execution = {
            "mode": "structured",
            "reasoning_source": "structured_trace",
            "notes": [],
            "llm_used": False,
            "feedback_messages_to_requirements": self._feedback_messages_to_requirements(requirements),
        }
        return designs

    def _design_with_llm(
        self,
        requirements: list[RequirementItem],
        feedback_messages: list[str],
        runtime_config: AgentRuntimeConfig,
    ) -> list[TestCaseDesign]:
        requirements_payload = [
            {
                "requirement_id": item.requirement_id,
                "normalized_text": item.normalized_text,
                "priority": item.priority,
                "acceptance_criteria": item.acceptance_criteria,
                "assumptions": item.assumptions,
            }
            for item in requirements
        ]
        feedback_block = "\n".join(f"- {message}" for message in feedback_messages) or "- none"
        system_prompt = (
            f"You are {runtime_config.agent_name}.\n"
            f"{runtime_config.directives}\n"
            "Produce concrete planned test cases, not placeholders. "
            "Use action-oriented test titles. Keep traceability to requirement IDs."
        )
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "test_designs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "requirement_id": {"type": "string"},
                            "title": {"type": "string"},
                            "test_type": {"type": "string"},
                            "preconditions": {"type": "array", "items": {"type": "string"}},
                            "steps": {"type": "array", "items": {"type": "string"}},
                            "expected_results": {"type": "array", "items": {"type": "string"}},
                            "oracle": {"type": "string"},
                            "risks": {"type": "array", "items": {"type": "string"}},
                            "trace_notes": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": [
                            "requirement_id",
                            "title",
                            "test_type",
                            "preconditions",
                            "steps",
                            "expected_results",
                            "oracle",
                            "risks",
                            "trace_notes",
                        ],
                    },
                },
                "feedback_messages_to_requirements": {"type": "array", "items": {"type": "string"}},
                "run_notes": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["test_designs", "feedback_messages_to_requirements", "run_notes"],
        }
        user_prompt = (
            "Structured requirements:\n"
            f"{requirements_payload}\n\n"
            "Incoming upstream feedback:\n"
            f"{feedback_block}\n\n"
            "Create one test case per requirement unless a requirement is too unclear to support strong design. "
            "If a requirement is too unclear, keep the test design as strong as possible but also add targeted "
            "feedback messages to the requirements analyst."
        )
        response, metadata = call_structured_llm(
            runtime_config=runtime_config,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema_name="test_design",
            schema=schema,
        )
        raw_designs = response.get("test_designs") or []
        designs = []
        requirements_by_id = {item.requirement_id: item for item in requirements}
        for index, item in enumerate(raw_designs, start=1):
            requirement_id = _clean_text(item.get("requirement_id")) or f"REQ-{index:03d}"
            mapped_requirement = requirements_by_id.get(requirement_id)
            designs.append(
                TestCaseDesign(
                    test_case_id=f"TC-{index:03d}",
                    requirement_id=requirement_id,
                    title=_clean_text(item.get("title")) or self._fallback_llm_title(mapped_requirement, requirement_id),
                    test_type=_clean_text(item.get("test_type")) or "scenario",
                    preconditions=_clean_string_list(item.get("preconditions")) or ["The application is available."],
                    steps=_clean_string_list(item.get("steps")) or self._build_steps(mapped_requirement) if mapped_requirement else [],
                    expected_results=_clean_string_list(item.get("expected_results")) or (
                        list(mapped_requirement.acceptance_criteria) if mapped_requirement else []
                    ),
                    oracle=_clean_text(item.get("oracle"))
                    or "All expected results are satisfied and no unauthorized side effects are observed.",
                    risks=_clean_string_list(item.get("risks")),
                )
            )
        self.last_execution = {
            "mode": "llm",
            "reasoning_source": "llm_structured_output",
            "notes": _clean_string_list(response.get("run_notes"))
            + _flatten_trace_notes(raw_designs, "trace_notes"),
            "llm_used": True,
            "metadata": metadata,
            "feedback_messages_to_requirements": _clean_string_list(
                response.get("feedback_messages_to_requirements")
            ),
        }
        return designs

    def _choose_test_type(self, req: RequirementItem) -> str:
        lowered = req.normalized_text.lower()
        if any(keyword in lowered for keyword in ("ui", "gui", "knapp", "formulär", "page", "sida")):
            return "gui/e2e"
        if any(keyword in lowered for keyword in ("api", "endpoint", "service")):
            return "api/integration"
        if any(keyword in lowered for keyword in ("beräkna", "validate", "regel", "business")):
            return "unit"
        return "scenario"

    def _build_steps(self, req: RequirementItem) -> list[str]:
        return [
            f"Identify the functionality associated with {req.requirement_id}.",
            "Prepare a positive test case with valid data.",
            "Execute the primary flow.",
            "Verify the expected result against the acceptance criteria.",
            "Execute a negative or boundary case when applicable.",
        ]

    def _build_title(self, req: RequirementItem) -> str:
        cleaned = req.normalized_text.strip()
        if cleaned:
            if len(cleaned) > 72:
                cleaned = cleaned[:69].rstrip() + "..."
            return cleaned
        return f"Test case for {req.requirement_id}"

    def _fallback_llm_title(self, req: RequirementItem | None, requirement_id: str) -> str:
        if not req:
            return f"Test case for {requirement_id}"
        text = req.normalized_text.strip().rstrip(".")
        lowered = text.lower()
        if any(keyword in lowered for keyword in ("sign in", "logga in", "login")):
            return "Successful sign-in with valid credentials"
        if any(keyword in lowered for keyword in ("error", "invalid", "ogiltig", "felmeddelande")):
            return "Display clear error for invalid credentials"
        if "admin" in lowered and any(keyword in lowered for keyword in ("overview", "översikt", "users", "användare")):
            return "Admin views registered users overview"
        if any(keyword in lowered for keyword in ("register", "registrera", "new account", "konto")):
            return "Register a new account through the form"
        return text if len(text) <= 72 else text[:69].rstrip() + "..."

    def _identify_risks(self, req: RequirementItem) -> list[str]:
        risks = []
        if req.assumptions:
            risks.append("The requirement contains assumptions that can distort test design.")
        if len(req.acceptance_criteria) < 2:
            risks.append("Limited specificity can reduce testability.")
        return risks

    def _feedback_messages_to_requirements(self, requirements: list[RequirementItem]) -> list[str]:
        feedback = []
        for requirement in requirements:
            if requirement.assumptions:
                feedback.append(
                    f"{requirement.requirement_id} needs clearer acceptance criteria and explicit error handling before strong test design can continue."
                )
        return feedback[:2]

    def _apply_feedback(
        self,
        requirement_id: str,
        steps: list[str],
        expected_results: list[str],
        feedback_messages: list[str],
    ) -> tuple[list[str], list[str], str]:
        combined_feedback = " ".join(feedback_messages).lower()
        targets_requirement = requirement_id.lower() in combined_feedback or not feedback_messages

        updated_steps = list(steps)
        updated_expected_results = list(expected_results)
        oracle = "All expected results are satisfied and no unauthorized side effects are observed."

        if feedback_messages and targets_requirement and any(
            phrase in combined_feedback
            for phrase in ("weak oracle", "more expected results", "negative scenarios", "negative case")
        ):
            extra_result = "Negative and boundary outcomes shall be verified explicitly against the acceptance criteria."
            if extra_result not in updated_expected_results:
                updated_expected_results.append(extra_result)
            extra_step = "Compare positive, negative, and boundary outcomes against explicit expected results."
            if extra_step not in updated_steps:
                updated_steps.append(extra_step)
            oracle = (
                "Every positive, negative, and boundary expectation must be explicitly satisfied, "
                "and the system must not introduce unauthorized side effects."
            )

        return updated_steps, updated_expected_results, oracle


@dataclass
class ReviewAgent:
    name: str = "Review Agent"
    last_execution: dict[str, Any] = field(default_factory=dict)

    def review(
        self,
        requirements: list[RequirementItem],
        test_designs: list[TestCaseDesign],
        runtime_config: AgentRuntimeConfig | None = None,
    ) -> ReviewReport:
        if is_llm_enabled(runtime_config):
            return self._review_with_llm(requirements, test_designs, runtime_config)

        findings = []
        improvements = []

        covered_requirements = {design.requirement_id for design in test_designs}
        coverage_ratio = len(covered_requirements) / len(requirements) if requirements else 0.0

        for requirement in requirements:
            if requirement.requirement_id not in covered_requirements:
                findings.append(f"{requirement.requirement_id} is missing a designed test case.")
                improvements.append(f"Design at least one test for {requirement.requirement_id}.")

        for design in test_designs:
            if len(design.expected_results) < 2:
                findings.append(
                    f"{design.test_case_id} has a weak oracle definition and needs more expected results."
                )
                improvements.append(
                    f"Clarify acceptance criteria or add negative scenarios for {design.test_case_id}."
                )

        for requirement in requirements:
            if requirement.assumptions:
                findings.append(
                    f"{requirement.requirement_id} contains assumptions that should be confirmed before automation."
                )
                improvements.append(
                    f"Clarify requirement {requirement.requirement_id} to reduce misinterpretation."
                )

        approved = coverage_ratio == 1.0 and len(findings) <= max(1, len(requirements) // 2)
        if approved and not findings:
            findings.append("No critical issues were identified.")

        report = ReviewReport(
            approved=approved,
            coverage_ratio=round(coverage_ratio, 2),
            findings=findings,
            improvement_actions=improvements,
        )
        self.last_execution = {
            "mode": "structured",
            "reasoning_source": "structured_trace",
            "notes": [],
            "llm_used": False,
            "routing_focus": self._infer_routing_focus(findings),
        }
        return report

    def _review_with_llm(
        self,
        requirements: list[RequirementItem],
        test_designs: list[TestCaseDesign],
        runtime_config: AgentRuntimeConfig,
    ) -> ReviewReport:
        requirements_payload = [
            {
                "requirement_id": item.requirement_id,
                "normalized_text": item.normalized_text,
                "acceptance_criteria": item.acceptance_criteria,
                "assumptions": item.assumptions,
            }
            for item in requirements
        ]
        designs_payload = [
            {
                "test_case_id": item.test_case_id,
                "requirement_id": item.requirement_id,
                "title": item.title,
                "test_type": item.test_type,
                "preconditions": item.preconditions,
                "steps": item.steps,
                "expected_results": item.expected_results,
                "oracle": item.oracle,
                "risks": item.risks,
            }
            for item in test_designs
        ]
        system_prompt = (
            f"You are {runtime_config.agent_name}.\n"
            f"{runtime_config.directives}\n"
            "Review the planned test cases rigorously. "
            "Do not approve generic placeholders just because there is nominal coverage."
        )
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "approved": {"type": "boolean"},
                "coverage_ratio": {"type": "number"},
                "findings": {"type": "array", "items": {"type": "string"}},
                "improvement_actions": {"type": "array", "items": {"type": "string"}},
                "routing_focus": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["requirements", "test_design"]},
                },
                "evaluation_notes": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "approved",
                "coverage_ratio",
                "findings",
                "improvement_actions",
                "routing_focus",
                "evaluation_notes",
            ],
        }
        user_prompt = (
            "Requirements under review:\n"
            f"{requirements_payload}\n\n"
            "Planned test cases under review:\n"
            f"{designs_payload}\n\n"
            "Return concrete findings. Use routing_focus to indicate whether the next repair should go to "
            "the requirements analyst or the test design agent."
        )
        response, metadata = call_structured_llm(
            runtime_config=runtime_config,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema_name="review_report",
            schema=schema,
        )
        report = ReviewReport(
            approved=bool(response.get("approved")),
            coverage_ratio=round(_clean_ratio(response.get("coverage_ratio")), 2),
            findings=_clean_string_list(response.get("findings")),
            improvement_actions=_clean_string_list(response.get("improvement_actions")),
        )
        if report.approved and not report.findings:
            report.findings.append("No critical issues were identified.")
        self.last_execution = {
            "mode": "llm",
            "reasoning_source": "llm_structured_output",
            "notes": _clean_string_list(response.get("evaluation_notes")),
            "llm_used": True,
            "metadata": metadata,
            "routing_focus": _clean_string_list(response.get("routing_focus")),
        }
        return report

    def _infer_routing_focus(self, findings: list[str]) -> list[str]:
        focus = []
        if any("assumptions" in finding for finding in findings):
            focus.append("requirements")
        if any("weak oracle definition" in finding or "missing a designed test case" in finding for finding in findings):
            focus.append("test_design")
        return focus


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _clean_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _clean_priority(value: Any) -> str:
    lowered = str(value or "").strip().lower()
    if lowered in {"high", "medium", "normal"}:
        return lowered
    return "normal"


def _clean_ratio(value: Any) -> float:
    try:
        ratio = float(value)
    except (TypeError, ValueError):
        return 0.0
    return min(1.0, max(0.0, ratio))


def _flatten_trace_notes(items: list[dict[str, Any]], key: str) -> list[str]:
    notes = []
    for item in items:
        for note in _clean_string_list(item.get(key)):
            notes.append(note)
    return notes[:12]
