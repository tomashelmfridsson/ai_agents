from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qa_platform.orchestrator import OrchestratorAgent


class PipelineTests(unittest.TestCase):
    def test_pipeline_produces_traceable_artifacts(self) -> None:
        orchestrator = OrchestratorAgent()
        result = orchestrator.process(
            title="Login demo",
            requirements_text=(
                "Användaren måste kunna logga in med e-post och lösenord.\n"
                "Systemet ska visa ett tydligt felmeddelande vid ogiltiga uppgifter."
            ),
        )

        self.assertEqual(len(result.requirements), 2)
        self.assertEqual(len(result.test_designs), 2)
        self.assertEqual(len(result.generated_artifacts), 2)
        self.assertEqual(result.review.coverage_ratio, 1.0)
        self.assertGreaterEqual(result.iterations, 1)

        requirement_ids = {item.requirement_id for item in result.requirements}
        artifact_ids = {item.requirement_id for item in result.generated_artifacts}
        self.assertEqual(requirement_ids, artifact_ids)

    def test_review_flags_vague_requirements(self) -> None:
        orchestrator = OrchestratorAgent(max_iterations=1)
        result = orchestrator.process(
            title="Vague requirement demo",
            requirements_text="Systemet bör fungera bra.",
        )

        self.assertFalse(result.review.approved)
        self.assertTrue(result.review.findings)
        self.assertTrue(any("REQ-001" in finding for finding in result.review.findings))


if __name__ == "__main__":
    unittest.main()
