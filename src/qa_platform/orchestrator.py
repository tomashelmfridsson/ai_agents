from __future__ import annotations

from dataclasses import dataclass, field

from .agents import (
    RequirementsAnalystAgent,
    ReviewAgent,
    TestDesignAgent,
    TestGenerationAgent,
)
from .models import PipelineResult


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

        for iteration in range(1, self.max_iterations + 1):
            requirements = self.requirements_analyst.analyze(requirements_text)
            designs = self.test_designer.design(requirements)
            artifacts = self.test_generator.generate(requirements, designs)
            review = self.reviewer.review(requirements, designs, artifacts)
            if review.approved:
                return PipelineResult(
                    title=title,
                    source_requirements=requirements_text,
                    requirements=requirements,
                    test_designs=designs,
                    generated_artifacts=artifacts,
                    review=review,
                    iterations=iteration,
                )

        return PipelineResult(
            title=title,
            source_requirements=requirements_text,
            requirements=requirements,
            test_designs=designs,
            generated_artifacts=artifacts,
            review=review,
            iterations=self.max_iterations,
        )
