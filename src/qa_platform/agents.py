from __future__ import annotations

import re
from dataclasses import dataclass

from .models import RequirementItem, ReviewReport, TestCaseDesign


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug or "unnamed_requirement"


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

    def analyze(
        self,
        requirements_text: str,
        feedback_messages: list[str] | None = None,
    ) -> list[RequirementItem]:
        feedback_messages = feedback_messages or []
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
        return items

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

    def design(
        self,
        requirements: list[RequirementItem],
        feedback_messages: list[str] | None = None,
    ) -> list[TestCaseDesign]:
        feedback_messages = feedback_messages or []
        designs = []
        for req in requirements:
            test_type = self._choose_test_type(req)
            design_id = f"TC-{req.requirement_id.split('-')[-1]}"
            title = f"Verify {req.requirement_id.lower()} {_slugify(req.normalized_text)[:40]}"
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

    def _identify_risks(self, req: RequirementItem) -> list[str]:
        risks = []
        if req.assumptions:
            risks.append("The requirement contains assumptions that can distort test design.")
        if len(req.acceptance_criteria) < 2:
            risks.append("Limited specificity can reduce testability.")
        return risks

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

    def review(
        self,
        requirements: list[RequirementItem],
        test_designs: list[TestCaseDesign],
    ) -> ReviewReport:
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

        return ReviewReport(
            approved=approved,
            coverage_ratio=round(coverage_ratio, 2),
            findings=findings,
            improvement_actions=improvements,
        )
